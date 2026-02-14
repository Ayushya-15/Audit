#!/bin/bash
# RiskShield 2-Minute Demo Script
# Demonstrates: device discovery, ML training, risk scanning, treatment, and reporting.

set -e

API="http://localhost:8000"

echo "=============================================="
echo "  RiskShield - 2 Minute Demo"
echo "  ISO 31000 GRC Compliance Tool"
echo "=============================================="
echo ""

echo "[Step 1] Check API health..."
curl -s "$API/health" | python3 -m json.tool
echo ""

echo "[Step 2] Discover 5 network devices..."
curl -s -X POST "$API/api/devices/discover?count=5" | python3 -m json.tool
echo ""

echo "[Step 3] List discovered devices..."
curl -s "$API/api/devices/" | python3 -m json.tool
echo ""

echo "[Step 4] Run full risk scan (collect telemetry + ML analysis)..."
curl -s -X POST "$API/api/risks/scan" | python3 -m json.tool
echo ""

echo "[Step 5] Run scan again for more data..."
curl -s -X POST "$API/api/risks/scan" | python3 -m json.tool
echo ""

echo "[Step 6] Train ML models on collected data..."
curl -s -X POST "$API/api/ml/train" | python3 -m json.tool
echo ""

echo "[Step 7] Run post-training risk scan..."
curl -s -X POST "$API/api/risks/scan" | python3 -m json.tool
echo ""

echo "[Step 8] View dashboard stats..."
curl -s "$API/api/risks/dashboard" | python3 -m json.tool
echo ""

echo "[Step 9] View risk heatmap..."
curl -s "$API/api/risks/heatmap" | python3 -m json.tool
echo ""

echo "[Step 10] View ML model status..."
curl -s "$API/api/ml/status" | python3 -m json.tool
echo ""

echo "[Step 11] View alerts..."
curl -s "$API/api/risks/alerts" | python3 -m json.tool
echo ""

echo "[Step 12] View audit trail..."
curl -s "$API/api/treatment/audit-log?limit=10" | python3 -m json.tool
echo ""

echo "[Step 13] Generate PDF report..."
curl -s -o /tmp/riskshield_report.pdf "$API/api/reports/pdf"
echo "Report saved to /tmp/riskshield_report.pdf"
echo ""

echo "=============================================="
echo "  Demo Complete!"
echo "  Open http://localhost:5173 for the web UI"
echo "=============================================="
