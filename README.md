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
│   ├── config/               # Dokploy / Gunicorn production entrypoint & settings
│   ├── estoque_project/      # Django settings, Celery config, URLs
│   ├── apps/
│   │   ├── accounts/         # User roles, business profiles, dashboards, admin
│   │   ├── inventory/        # Products, batches, stock movements, admin
│   │   ├── orders/           # Purchase order lifecycle & inventory locks, admin
│   │   ├── blockchain/       # Soroban smart contract services, event listener & audit logs
│   │   └── analytics/        # AI forecasting & OpenAI tool calling schemas
│   └── tests/                # 21 comprehensive backend unit tests
├── contracts/
│   ├── Cargo.toml            # Soroban SDK 22 configuration
│   └── src/
│       ├── lib.rs            # Soroban contract (batch proof, handover, escrow)
│       └── test.rs           # 4 unit tests (escrow, refund, duplicate prevention)
├── docker-compose.yml        # Development Docker Compose (Backend, Redis, Celery)
├── production-compose.yml   # Dokploy Production Compose (PostgreSQL, Redis, Web, Celery Worker/Beat, Indexer)
├── scripts/
│   ├── deploy_contract.sh    # Builds wasm & deploys to Stellar Testnet
│   └── run_all_tests.sh      # Runs all tests 3 times for backend and contract
└── project.txt               # Original specification brief
```

---

## Environment Variables & Credentials (`.env` and `example-env`)

All secret credentials, blockchain keys, database connections, and domains are managed strictly via environment variables.

For version control safety, `.env` is git-ignored. An [example-env](file:///home/lucifer/Desktop/Estoque/example-env) template is provided for GitHub:

```bash
# Setup your environment file
cp example-env .env
```

### Key Configuration Variables in `.env`:
- **Django Core**: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- **Domain & Traefik Routing**: `API_DOMAIN=api.estoquee.xyz`
- **CORS & CSRF**: `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
- **PostgreSQL**: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- **Redis & Celery**: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_ALWAYS_EAGER`
- **Stellar & Soroban Testnet**: `STELLAR_NETWORK`, `STELLAR_HORIZON_URL`, `SOROBAN_RPC_URL`, `SOROBAN_CONTRACT_ID`, `TESTNET_USDC_ADDRESS`
- **Stellar Deployer Keypair**: `STELLAR_DEPLOYER_PUBLIC_KEY`, `STELLAR_DEPLOYER_SECRET_KEY`

---

## Production Deployment with Dokploy (`production-compose.yml`)

The platform is designed to be deployed seamlessly on **Dokploy** (or any Traefik-managed Docker Swarm / compose setup) pointing to `api.estoquee.xyz`.

### Architecture & Services in `production-compose.yml`:
1. **`db`**: PostgreSQL 16 Alpine with persistent volume `postgres_data` and health checks.
2. **`redis`**: Redis 7 Alpine with persistent volume `redis_data` and health checks.
3. **`web`**: Gunicorn running 4 workers, automatic migration execution (`RUN_MIGRATIONS=true`), static/media handling, and Traefik labels routing `api.estoquee.xyz` with automatic Let's Encrypt TLS.
4. **`celery_worker`**: Celery worker daemon (`concurrency=4`) executing background tasks.
5. **`celery_beat`**: Celery periodic task scheduler.
6. **`soroban_indexer`**: Soroban on-chain event listener (`python manage.py run_soroban_event_listener`) continuously indexing ledger events.

### Traefik & Domain Routing:
- **Router Rule**: `Host("api.estoquee.xyz")`
- **Entrypoint**: `websecure` (port 443 with TLS enabled)
- **Cert Resolver**: `letsencrypt`
- **Internal Networks**: `internal` (bridge) + `dokploy-network` (external)

### Domain Security & Configuration (`api.estoquee.xyz`):
- `ALLOWED_HOSTS`: Configured for `api.estoquee.xyz`, `estoquee.xyz`, `www.estoquee.xyz`, and `.estoquee.xyz`.
- `CORS_ALLOWED_ORIGINS`: Permits `https://estoquee.xyz`, `https://www.estoquee.xyz`, `https://api.estoquee.xyz`, and regex `^https:\/\/.*\.estoquee\.xyz$`.
- `CSRF_TRUSTED_ORIGINS`: Set for `https://api.estoquee.xyz` and `https://estoquee.xyz`.
- `SECURE_PROXY_SSL_HEADER`: Configured for `('HTTP_X_FORWARDED_PROTO', 'https')` behind Traefik reverse proxy.

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
