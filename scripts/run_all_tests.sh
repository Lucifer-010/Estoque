#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.cargo/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
CONTRACT_DIR="$REPO_ROOT/contracts"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
VENV_PYTEST="$REPO_ROOT/.venv/bin/pytest"

echo "========================================================================"
echo "           ESTOQUE: 3-ROUND COMPREHENSIVE TEST SUITE EXECUTION           "
echo "========================================================================"

for ROUND in 1 2 3; do
    echo ""
    echo "========================================================================"
    echo "  >>> STARTING ROUND $ROUND OF 3: SMART CONTRACT UNIT TESTS <<<"
    echo "========================================================================"
    cd "$CONTRACT_DIR"
    cargo test -- --nocapture

    echo ""
    echo "========================================================================"
    echo "  >>> STARTING ROUND $ROUND OF 3: DJANGO BACKEND & INTEGRATION TESTS <<<"
    echo "========================================================================"
    cd "$BACKEND_DIR"
    "$VENV_PYTEST" -v

    echo ""
    echo "✓ ROUND $ROUND / 3 COMPLETED SUCCESSFULLY!"
done

echo ""
echo "========================================================================"
echo "  ALL 3 TEST ROUNDS PASSED WITH 100% SUCCESS ON CONTRACT AND BACKEND!   "
echo "========================================================================"

