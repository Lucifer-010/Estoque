#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, symbol_short,
    token, Address, BytesN, Env,
};

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum ContractError {
    AlreadyInitialized = 1,
    NotInitialized = 2,
    EscrowAlreadyExists = 3,
    EscrowNotFound = 4,
    EscrowNotFunded = 5,
    Unauthorized = 6,
    InvalidAmount = 7,
    BatchAlreadyRegistered = 8,
    BatchNotFound = 9,
    HandoverAlreadyExists = 10,
    HandoverNotFound = 11,
    AlreadyAcknowledged = 12,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[contracttype]
#[repr(u32)]
pub enum EscrowStatus {
    Funded = 1,
    Released = 2,
    Refunded = 3,
}

#[derive(Clone, Debug, Eq, PartialEq)]
#[contracttype]
pub struct EscrowRecord {
    pub order_id: u64,
    pub retailer: Address,
    pub supplier: Address,
    pub token: Address,
    pub amount: i128,
    pub status: EscrowStatus,
    pub created_at: u64,
    pub settled_at: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
#[contracttype]
pub struct BatchProofRecord {
    pub batch_id: u64,
    pub batch_hash: BytesN<32>,
    pub supplier: Address,
    pub registered_at: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
#[contracttype]
pub struct HandoverRecord {
    pub handover_id: u64,
    pub order_id: u64,
    pub batch_id: u64,
    pub from_party: Address,
    pub to_party: Address,
    pub dispatched_at: u64,
    pub acknowledged: bool,
    pub acknowledged_at: u64,
}

#[derive(Clone)]
#[contracttype]
pub enum DataKey {
    Escrow(u64),
    BatchProof(u64),
    Handover(u64),
}

#[contract]
pub struct EstoqueContract;

#[contractimpl]
impl EstoqueContract {
    /// 1. Register Batch Proof on-chain
    pub fn register_batch_proof(
        env: Env,
        batch_id: u64,
        batch_hash: BytesN<32>,
        supplier: Address,
    ) -> Result<(), ContractError> {
        supplier.require_auth();

        let key = DataKey::BatchProof(batch_id);
        if env.storage().persistent().has(&key) {
            return Err(ContractError::BatchAlreadyRegistered);
        }

        let record = BatchProofRecord {
            batch_id,
            batch_hash,
            supplier: supplier.clone(),
            registered_at: env.ledger().timestamp(),
        };

        env.storage().persistent().set(&key, &record);
        env.events().publish((symbol_short!("batch_reg"), supplier), batch_id);

        Ok(())
    }

    /// Retrieve batch proof
    pub fn get_batch_proof(env: Env, batch_id: u64) -> Result<BatchProofRecord, ContractError> {
        let key = DataKey::BatchProof(batch_id);
        env.storage()
            .persistent()
            .get(&key)
            .ok_or(ContractError::BatchNotFound)
    }

    /// 2. Record Authorized Handover
    pub fn record_handover(
        env: Env,
        handover_id: u64,
        order_id: u64,
        batch_id: u64,
        from_party: Address,
        to_party: Address,
    ) -> Result<(), ContractError> {
        from_party.require_auth();

        let batch_key = DataKey::BatchProof(batch_id);
        if !env.storage().persistent().has(&batch_key) {
            return Err(ContractError::BatchNotFound);
        }

        let handover_key = DataKey::Handover(handover_id);
        if env.storage().persistent().has(&handover_key) {
            return Err(ContractError::HandoverAlreadyExists);
        }

        let record = HandoverRecord {
            handover_id,
            order_id,
            batch_id,
            from_party: from_party.clone(),
            to_party,
            dispatched_at: env.ledger().timestamp(),
            acknowledged: false,
            acknowledged_at: 0,
        };

        env.storage().persistent().set(&handover_key, &record);
        env.events().publish((symbol_short!("handover"), from_party), handover_id);

        Ok(())
    }

    /// 3. Verify Custody Acknowledgment
    pub fn acknowledge_custody(
        env: Env,
        handover_id: u64,
        receiver: Address,
    ) -> Result<(), ContractError> {
        receiver.require_auth();

        let handover_key = DataKey::Handover(handover_id);
        let mut record: HandoverRecord = env
            .storage()
            .persistent()
            .get(&handover_key)
            .ok_or(ContractError::HandoverNotFound)?;

        if record.to_party != receiver {
            return Err(ContractError::Unauthorized);
        }

        if record.acknowledged {
            return Err(ContractError::AlreadyAcknowledged);
        }

        record.acknowledged = true;
        record.acknowledged_at = env.ledger().timestamp();
        env.storage().persistent().set(&handover_key, &record);

        env.events().publish((symbol_short!("ack_cust"), receiver), handover_id);

        Ok(())
    }

    /// Retrieve handover record
    pub fn get_handover(env: Env, handover_id: u64) -> Result<HandoverRecord, ContractError> {
        let key = DataKey::Handover(handover_id);
        env.storage()
            .persistent()
            .get(&key)
            .ok_or(ContractError::HandoverNotFound)
    }

    /// 4. Create and Fund Purchase Order Escrow
    pub fn create_and_fund_escrow(
        env: Env,
        order_id: u64,
        retailer: Address,
        supplier: Address,
        token: Address,
        amount: i128,
    ) -> Result<(), ContractError> {
        retailer.require_auth();

        if amount <= 0 {
            return Err(ContractError::InvalidAmount);
        }

        let key = DataKey::Escrow(order_id);
        if env.storage().persistent().has(&key) {
            return Err(ContractError::EscrowAlreadyExists);
        }

        // Lock funds by transferring from retailer to contract
        let token_client = token::Client::new(&env, &token);
        token_client.transfer(&retailer, &env.current_contract_address(), &amount);

        let record = EscrowRecord {
            order_id,
            retailer: retailer.clone(),
            supplier,
            token,
            amount,
            status: EscrowStatus::Funded,
            created_at: env.ledger().timestamp(),
            settled_at: 0,
        };

        env.storage().persistent().set(&key, &record);
        env.events().publish((symbol_short!("esc_fund"), retailer), order_id);

        Ok(())
    }

    /// 5. Release Payment to Supplier upon Retailer Delivery Confirmation
    pub fn release_payment(
        env: Env,
        order_id: u64,
        retailer: Address,
    ) -> Result<(), ContractError> {
        retailer.require_auth();

        let key = DataKey::Escrow(order_id);
        let mut record: EscrowRecord = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(ContractError::EscrowNotFound)?;

        if record.retailer != retailer {
            return Err(ContractError::Unauthorized);
        }

        if record.status != EscrowStatus::Funded {
            return Err(ContractError::EscrowNotFunded);
        }

        // Checks-Effects-Interactions (CEI) to prevent duplicate settlement
        record.status = EscrowStatus::Released;
        record.settled_at = env.ledger().timestamp();
        env.storage().persistent().set(&key, &record);

        // Transfer tokens to supplier
        let token_client = token::Client::new(&env, &record.token);
        token_client.transfer(&env.current_contract_address(), &record.supplier, &record.amount);

        env.events().publish((symbol_short!("esc_rel"), retailer), order_id);

        Ok(())
    }

    /// 6. Pre-dispatch Cancellation & Refund back to Retailer
    pub fn refund_payment(
        env: Env,
        order_id: u64,
        caller: Address,
    ) -> Result<(), ContractError> {
        caller.require_auth();

        let key = DataKey::Escrow(order_id);
        let mut record: EscrowRecord = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(ContractError::EscrowNotFound)?;

        if caller != record.retailer && caller != record.supplier {
            return Err(ContractError::Unauthorized);
        }

        if record.status != EscrowStatus::Funded {
            return Err(ContractError::EscrowNotFunded);
        }

        // Checks-Effects-Interactions (CEI) to prevent duplicate settlement
        record.status = EscrowStatus::Refunded;
        record.settled_at = env.ledger().timestamp();
        env.storage().persistent().set(&key, &record);

        // Transfer funds back to retailer
        let token_client = token::Client::new(&env, &record.token);
        token_client.transfer(&env.current_contract_address(), &record.retailer, &record.amount);

        env.events().publish((symbol_short!("esc_ref"), caller), order_id);

        Ok(())
    }

    /// Retrieve Escrow Record
    pub fn get_escrow(env: Env, order_id: u64) -> Result<EscrowRecord, ContractError> {
        let key = DataKey::Escrow(order_id);
        env.storage()
            .persistent()
            .get(&key)
            .ok_or(ContractError::EscrowNotFound)
    }
}

#[cfg(test)]
mod test;
