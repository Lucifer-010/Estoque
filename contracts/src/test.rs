#![cfg(test)]

use super::*;
use soroban_sdk::{
    testutils::Address as _,
    token::{StellarAssetClient, TokenClient},
    Address, BytesN, Env,
};

fn create_token_contract<'a>(
    env: &Env,
    admin: &Address,
) -> (TokenClient<'a>, StellarAssetClient<'a>) {
    let contract_id = env.register_stellar_asset_contract_v2(admin.clone());
    (
        TokenClient::new(env, &contract_id.address()),
        StellarAssetClient::new(env, &contract_id.address()),
    )
}

#[test]
fn test_batch_proof_registration_and_duplicate_prevention() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register(EstoqueContract, ());
    let client = EstoqueContractClient::new(&env, &contract_id);

    let supplier = Address::generate(&env);
    let batch_id = 101u64;
    let batch_hash = BytesN::from_array(&env, &[7u8; 32]);

    // 1. Successful batch registration
    let res = client.try_register_batch_proof(&batch_id, &batch_hash, &supplier);
    assert!(res.is_ok());

    let fetched = client.get_batch_proof(&batch_id);
    assert_eq!(fetched.batch_id, batch_id);
    assert_eq!(fetched.batch_hash, batch_hash);
    assert_eq!(fetched.supplier, supplier);

    // 2. Duplicate registration must fail
    let duplicate_res = client.try_register_batch_proof(&batch_id, &batch_hash, &supplier);
    assert_eq!(
        duplicate_res.err(),
        Some(Ok(ContractError::BatchAlreadyRegistered))
    );
}

#[test]
fn test_handover_and_custody_acknowledgment() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register(EstoqueContract, ());
    let client = EstoqueContractClient::new(&env, &contract_id);

    let supplier = Address::generate(&env);
    let logistics_or_retailer = Address::generate(&env);
    let unauthorized_party = Address::generate(&env);

    let batch_id = 202u64;
    let batch_hash = BytesN::from_array(&env, &[9u8; 32]);
    client.register_batch_proof(&batch_id, &batch_hash, &supplier);

    let handover_id = 1u64;
    let order_id = 5001u64;

    // Record handover from supplier to retailer
    client.record_handover(
        &handover_id,
        &order_id,
        &batch_id,
        &supplier,
        &logistics_or_retailer,
    );

    let handover = client.get_handover(&handover_id);
    assert_eq!(handover.order_id, order_id);
    assert_eq!(handover.acknowledged, false);

    // Unauthorized party cannot acknowledge custody
    let unauth_res = client.try_acknowledge_custody(&handover_id, &unauthorized_party);
    assert_eq!(unauth_res.err(), Some(Ok(ContractError::Unauthorized)));

    // Authorized party acknowledges custody
    let ack_res = client.try_acknowledge_custody(&handover_id, &logistics_or_retailer);
    assert!(ack_res.is_ok());

    let updated_handover = client.get_handover(&handover_id);
    assert_eq!(updated_handover.acknowledged, true);

    // Cannot acknowledge twice
    let double_ack = client.try_acknowledge_custody(&handover_id, &logistics_or_retailer);
    assert_eq!(double_ack.err(), Some(Ok(ContractError::AlreadyAcknowledged)));
}

#[test]
fn test_escrow_funding_and_release_to_supplier() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register(EstoqueContract, ());
    let client = EstoqueContractClient::new(&env, &contract_id);

    let token_admin = Address::generate(&env);
    let (token_client, token_asset) = create_token_contract(&env, &token_admin);

    let retailer = Address::generate(&env);
    let supplier = Address::generate(&env);

    let amount = 10_000_0000000i128; // 10,000 USDC with 7 decimals
    token_asset.mint(&retailer, &amount);
    assert_eq!(token_client.balance(&retailer), amount);

    let order_id = 8888u64;

    // 1. Create and fund escrow
    client.create_and_fund_escrow(
        &order_id,
        &retailer,
        &supplier,
        &token_client.address,
        &amount,
    );

    // Retailer funds transferred to escrow contract
    assert_eq!(token_client.balance(&retailer), 0);
    assert_eq!(token_client.balance(&contract_id), amount);

    let escrow = client.get_escrow(&order_id);
    assert_eq!(escrow.status, EscrowStatus::Funded);
    assert_eq!(escrow.amount, amount);
    assert_eq!(escrow.retailer, retailer);
    assert_eq!(escrow.supplier, supplier);

    // Duplicate funding for same order must be rejected
    let dup_fund = client.try_create_and_fund_escrow(
        &order_id,
        &retailer,
        &supplier,
        &token_client.address,
        &amount,
    );
    assert_eq!(dup_fund.err(), Some(Ok(ContractError::EscrowAlreadyExists)));

    // Unauthorized caller cannot release
    let stranger = Address::generate(&env);
    let unauth_rel = client.try_release_payment(&order_id, &stranger);
    assert_eq!(unauth_rel.err(), Some(Ok(ContractError::Unauthorized)));

    // Retailer confirms delivery -> releases payment
    let rel_res = client.try_release_payment(&order_id, &retailer);
    assert!(rel_res.is_ok());

    // Supplier received payment, contract balance is 0
    assert_eq!(token_client.balance(&supplier), amount);
    assert_eq!(token_client.balance(&contract_id), 0);

    let final_escrow = client.get_escrow(&order_id);
    assert_eq!(final_escrow.status, EscrowStatus::Released);

    // Prevent duplicate release (duplicate settlement guard)
    let dup_release = client.try_release_payment(&order_id, &retailer);
    assert_eq!(dup_release.err(), Some(Ok(ContractError::EscrowNotFunded)));
}

#[test]
fn test_escrow_pre_dispatch_cancellation_and_refund() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register(EstoqueContract, ());
    let client = EstoqueContractClient::new(&env, &contract_id);

    let token_admin = Address::generate(&env);
    let (token_client, token_asset) = create_token_contract(&env, &token_admin);

    let retailer = Address::generate(&env);
    let supplier = Address::generate(&env);

    let amount = 5_000_0000000i128; // 5,000 USDC
    token_asset.mint(&retailer, &amount);

    let order_id = 9999u64;

    client.create_and_fund_escrow(
        &order_id,
        &retailer,
        &supplier,
        &token_client.address,
        &amount,
    );

    assert_eq!(token_client.balance(&retailer), 0);
    assert_eq!(token_client.balance(&contract_id), amount);

    // Cancel order and refund to retailer
    let refund_res = client.try_refund_payment(&order_id, &retailer);
    assert!(refund_res.is_ok());

    // Retailer got refunded
    assert_eq!(token_client.balance(&retailer), amount);
    assert_eq!(token_client.balance(&contract_id), 0);

    let escrow = client.get_escrow(&order_id);
    assert_eq!(escrow.status, EscrowStatus::Refunded);

    // Cannot refund twice
    let dup_refund = client.try_refund_payment(&order_id, &retailer);
    assert_eq!(dup_refund.err(), Some(Ok(ContractError::EscrowNotFunded)));

    // Cannot release after refund
    let rel_after_refund = client.try_release_payment(&order_id, &retailer);
    assert_eq!(
        rel_after_refund.err(),
        Some(Ok(ContractError::EscrowNotFunded))
    );
}
