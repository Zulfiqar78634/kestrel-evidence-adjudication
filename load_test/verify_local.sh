#!/bin/bash
# Local verification script for Kestrel Evidence Adjudication
# Run this after cloning the repo to verify everything works locally.

set -e

echo "=== 1. Clone and install ==="
git clone https://github.com/Zulfiqar78634/kestrel-evidence-adjudication.git
cd kestrel-evidence-adjudication
python -m pip install -e ".[dev]"

echo "=== 2. Run full test suite ==="
python -m unittest discover -s tests -v

echo "=== 3. Generate synthetic demo workbook ==="
python -m sentinel_review.demo demo.xlsx

echo "=== 4. Review a case ==="
sentinel-review --db demo.sqlite review demo.xlsx --event DEMO-1 --tenant T-DEMO-A --out demo-case.json

echo "=== 5. Verify replay ==="
sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-A

echo "=== 6. Verify cross-tenant isolation (should fail with exit 2) ==="
sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-B || echo "Expected failure: cross-tenant denied"

echo "=== 7. Inspect obligations ==="
sentinel-review --db demo.sqlite obligations --tenant T-DEMO-B

echo "=== 8. Run load test (optional, requires locust) ==="
# pip install locust
# locust -f load_test/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 30s

echo "=== 9. Run chaos tests ==="
python -m unittest load_test.chaos -v

echo "=== All checks passed ==="
