# Estoque - Supply Chain & Soroban Escrow Platform

Estoque is an inventory and supply chain management platform for SMEs, suppliers, wholesalers, and retailers. It connects off-chain inventory tracking, purchase orders, stock handover verification, and secure supplier payments through Stellar and Soroban.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       Client / Frontend / Swagger     |
                      +---------------------------------------+
                                          |
                                          v (REST / OpenAPI 3.0)
+---------------------------------------------------------------------------------+
| Estoque Backend (Django REST Framework)                                         |
|                                                                                 |
|  [apps.accounts]   - Supplier & Retailer Profiles, Dashboards, Auth             |
|  [apps.inventory]  - Catalog, Batches, Stock Movements, SHA-256 Hashing         |
|  [apps.orders]     - Purchase Orders, Item Reservations, Dispatch & Delivery    |
|  [apps.blockchain] - Soroban Smart Contract Integration & Audit Trails          |
|  [apps.analytics]  - AI Demand Forecasting, Expiry Risk & OpenAI Agent Tools    |
+---------------------------------------------------------------------------------+
           |                                  |
           v                                  v
+--------------------+             +----------------------------------------------+
| Redis & Celery     |             | Stellar Testnet (Soroban Smart Contract)     |
| - Async Anchoring  |             | - Batch Proof Registration                   |
| - Escrow Funding   |             | - Authorized Custody Handovers               |
| - Payment Release  |             | - Non-custodial USDC Payment Escrow          |
| - Refund Workers   |             | - Duplicate Settlement Prevention            |
+--------------------+             +----------------------------------------------+
```

---

## Tech Stack

1. **Backend**: Python 3.13, Django 5+, Django REST Framework (DRF)
2. **Containerization**: Docker & Docker Compose (`docker-compose.yml`)
3. **Async Tasks & Caching**: Redis 7, Celery 5.7
4. **API Documentation**: OpenAPI 3.0, Swagger UI (`/api/docs/`), ReDoc (`/api/redoc/`) via `drf-spectacular`
5. **Smart Contract**: Soroban Rust SDK (`soroban-sdk = "22.0.11"`) compiled to `wasm32-unknown-unknown`
6. **Blockchain Integration**: py-stellar-base (`stellar-sdk`), Stellar Testnet Horizon & Soroban RPC
7. **Administration**: Full Django Admin suite registering all domain models with filters, search, and inline relationships

---

## Directory Layout

```
Estoque/
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── manage.py
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── estoque_project/      # Django settings, Celery config, URLs
│   ├── apps/
│   │   ├── accounts/         # User roles, business profiles, dashboards, admin
│   │   ├── inventory/        # Products, batches, stock movements, admin
│   │   ├── orders/           # Purchase order lifecycle & inventory locks, admin
│   │   ├── blockchain/       # Soroban smart contract services & audit logs, admin
│   │   └── analytics/        # AI forecasting & OpenAI tool calling schemas
│   └── tests/                # 21 comprehensive backend unit tests
├── contracts/
│   ├── Cargo.toml            # Soroban SDK 22 configuration
│   └── src/
│       ├── lib.rs            # Soroban contract (batch proof, handover, escrow)
│       └── test.rs           # 4 unit tests (escrow, refund, duplicate prevention)
├── docker-compose.yml        # Orchestration: web, redis, celery_worker
├── scripts/
│   ├── deploy_contract.sh    # Builds wasm & deploys to Stellar Testnet
│   └── run_all_tests.sh      # Runs all tests 3 times for backend and contract
└── project.txt               # Original specification brief
```

---

## Running with Docker Compose

To build and start all services (Backend, Redis, and Celery Worker):

```bash
docker compose up --build -d
```

Check the health and running status of containers:
```bash
docker compose ps
```

Expected output:
```
NAME                    IMAGE                   STATUS                    PORTS
estoque_backend         estoque-web             Up (running)              0.0.0.0:8000->8000/tcp
estoque_celery_worker   estoque-celery_worker   Up (running)              8000/tcp
estoque_redis           redis:7-alpine          Up (healthy)              0.0.0.0:6379->6379/tcp
```

### Endpoints Available
- **API Root**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **OpenAPI 3.0 Schema**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
- **Django Administration**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## Django Admin Models Registration

All domain models are fully registered in `admin.py` with custom list displays, filters, search fields, and inlines:

1. **`accounts.admin`**:
   - `User`: Custom user administration with role selector (`SUPPLIER`, `RETAILER`, `ADMIN`), Stellar wallet address, and inlined profiles.
   - `SupplierProfile`: Company details, business verification status, and Stellar payout addresses.
   - `RetailerProfile`: Business profile, contact info, credit limits, and Stellar payment wallets.
2. **`inventory.admin`**:
   - `Product`: Catalog items, pricing in USDC, category filtering, and inlined batch management.
   - `InventoryBatch`: Batch tracking with SHA-256 cryptographic hashes, on-chain registration flags, transaction hashes, and inlined stock movements.
   - `StockMovement`: Comprehensive audit trail for stock entries, reservations, dispatches, and adjustments.
3. **`orders.admin`**:
   - `PurchaseOrder`: Full lifecycle status tracking, locked amounts, carrier info, on-chain escrow, release, refund, and handover tx hashes with inlined order items.
   - `OrderItem`: Quantity, unit pricing, calculated subtotals, and linked inventory batches.
4. **`blockchain.admin`**:
   - `BlockchainTransactionRecord`: Complete on-chain transaction logs (Batch Proofs, Escrow Funding, Payment Release, Refunds, Custody Handovers) with formatted hash previews and JSON payload inspector.

---

## OpenAPI / Swagger & ReDoc Configuration

Configured in `estoque_project/settings.py` via `drf-spectacular`:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Estoque Supply Chain & Escrow API',
    'DESCRIPTION': (
        'Comprehensive REST API for SMEs, suppliers, and retailers on Estoque. '
        'Connects off-chain inventory management, purchase orders, custody handovers, '
        'and Soroban smart-contract escrow payments in simulated USDC on Stellar Testnet.'
    ),
    'VERSION': '1.0.0',
    # Pin to a stable version without the import.meta bundle bug:
    'REDOC_DIST': 'https://cdn.jsdelivr.net/npm/redoc@2.1.5',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Authentication & Accounts', 'description': 'Supplier & Retailer authentication, registration and business profiles'},
        {'name': 'Inventory & Products', 'description': 'Product catalog, inventory batch registration, stock tracking and movements'},
        {'name': 'Purchase Orders', 'description': 'Purchase order lifecycle, dispatch, receipt, and inventory linking'},
        {'name': 'Soroban Blockchain & Escrow', 'description': 'Stellar Testnet Soroban smart contract interactions: batch proofs, custody handovers, USDC escrow funding, release and refunds'},
        {'name': 'Analytics & AI Insights', 'description': 'AI-assisted inventory optimization, reorder demand forecasts, and supply-chain metrics'},
    ],
}
```

---

## Soroban Smart Contract

### Features
1. **Batch Proof Anchoring (`register_batch_proof`)**:
   - Stores cryptographic SHA-256 fingerprint of the batch.
   - Prevents duplicate registration.
2. **Authorized Stock Handover (`record_handover`)**:
   - Records physical custody transfer from supplier to logistics/retailer.
3. **Custody Acknowledgment (`acknowledge_custody`)**:
   - Retailer authenticates and verifies physical custody receipt on-chain.
4. **USDC Supplier Escrow (`create_and_fund_escrow`)**:
   - Locks purchase order payment tokens in escrow contract.
5. **Authorized Payment Release (`release_payment`)**:
   - Retailer delivery confirmation triggers payment release to supplier payout address.
   - Checks-Effects-Interactions (CEI) pattern prevents duplicate settlement and re-entrancy.
6. **Pre-dispatch Refund (`refund_payment`)**:
   - Returns locked funds back to retailer upon pre-dispatch cancellation.

### Building & Testing the Contract
```bash
cd contracts
cargo test
cargo build --target wasm32-unknown-unknown --release
```

### Deploying to Stellar Testnet
```bash
./scripts/deploy_contract.sh
```

---

## Automated Unit Testing (3 Consecutive Rounds)

Run unit tests 3 times across both the Soroban smart contract and Django backend:

```bash
./scripts/run_all_tests.sh
```

Or run directly inside the Docker container:
```bash
docker compose exec -T web pytest -v
```

### Verification Results
- **Smart Contract Tests (`cargo test`)**: 4 tests per round x 3 rounds = 12 runs (100% Passed)
- **Backend Tests (`pytest`)**: 21 tests per round x 3 rounds = 63 runs (100% Passed)
- **Total Test Runs**: 75 tests executed, **0 failures**.
