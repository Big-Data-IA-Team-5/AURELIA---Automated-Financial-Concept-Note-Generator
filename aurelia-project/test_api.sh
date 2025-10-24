#!/bin/bash

echo "🧪 AURELIA API - COMPLETE TEST SUITE"
echo "===================================="
echo ""

API_URL="https://aurelia-backend-1074058468365.us-central1.run.app"

# TEST 1: Health Check
echo "TEST 1: Health Check"
echo "-------------------"
curl -s ${API_URL}/health | jq .
echo ""
read -p "Press Enter to continue..."

# TEST 2: CAPM (The Bug We Fixed!)
echo ""
echo "TEST 2: CAPM Query (Previously Failed with key_points error)"
echo "------------------------------------------------------------"
curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d '{"concept": "CAPM", "force_refresh": true}' | jq .
echo ""
echo "✅ PASS if: No 'key_points' error and concept note is complete"
read -p "Press Enter to continue..."

# TEST 3: Check Gemini Model
echo ""
echo "TEST 3: New Concept (Tests Gemini Model Fix)"
echo "--------------------------------------------"
curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d '{"concept": "Monte Carlo Simulation", "force_refresh": true}' | jq .
echo ""
echo "✅ PASS if: ai_model shows 'gemini-1.5-flash' and no 404 errors"
read -p "Press Enter to continue..."

# TEST 4: Cached Query (Speed Test)
echo ""
echo "TEST 4: Cached Query (Speed Test)"
echo "---------------------------------"
curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d '{"concept": "Duration", "force_refresh": false}' | jq '{cached, processing_time_ms, ai_model}'
echo ""
echo "✅ PASS if: cached=true and processing_time_ms < 100"
read -p "Press Enter to continue..."

# TEST 5: Wikipedia Fallback
echo ""
echo "TEST 5: Wikipedia Fallback"
echo "--------------------------"
curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d '{"concept": "Cryptocurrency", "force_refresh": true}' | jq '{source: .concept_note.source, fallback_used, ai_model}'
echo ""
echo "✅ PASS if: source='wikipedia' and fallback_used=true"
read -p "Press Enter to continue..."

# TEST 6: Batch Seed (Previously 2/3 Success)
echo ""
echo "TEST 6: Batch Seed (3 Concepts)"
echo "-------------------------------"
curl -s -X POST "${API_URL}/seed" \
  -H "Content-Type: application/json" \
  -d '{"concepts": ["VaR", "CVaR", "Treynor Ratio"], "overwrite": false}' | jq '{total_requested, successful, failed}'
echo ""
echo "✅ PASS if: successful=3 and failed=0"
read -p "Press Enter to continue..."

# TEST 7: List Concepts
echo ""
echo "TEST 7: List All Concepts"
echo "------------------------"
curl -s "${API_URL}/concepts?limit=10" | jq 'length'
echo " concepts returned"
echo ""
echo "✅ PASS if: Returns at least 5 concepts"
read -p "Press Enter to continue..."

# TEST 8: Statistics
echo ""
echo "TEST 8: API Statistics"
echo "---------------------"
curl -s "${API_URL}/stats" | jq .
echo ""
echo "✅ PASS if: Shows total_concepts, cache_hit_rate, gemini_calls"
read -p "Press Enter to continue..."

# TEST 9: Metrics
echo ""
echo "TEST 9: System Metrics"
echo "---------------------"
curl -s "${API_URL}/metrics" | jq '{total_queries, cache_hit_rate, gemini_calls, integrations}'
echo ""
echo "✅ PASS if: Shows valid metrics"
read -p "Press Enter to continue..."

# TEST 10: Check Logs for Errors
echo ""
echo "TEST 10: Check Cloud Logs for Errors"
echo "------------------------------------"
gcloud run services logs read aurelia-backend \
  --region us-central1 \
  --project mineral-concord-474700-v2 \
  --limit 100 | grep -E "(ERROR|Gemini generation error|key_points)" | tail -10
echo ""
echo "✅ PASS if: No ERROR messages about key_points or Gemini 404"

echo ""
echo "========================================"
echo "🎉 TEST SUITE COMPLETE!"
echo "========================================"
echo ""
echo "Summary:"
echo "--------"
echo "All tests should PASS with:"
echo "  ✅ No key_points errors"
echo "  ✅ CAPM generates successfully"
echo "  ✅ Gemini model working (no 404)"
echo "  ✅ Cached queries fast (<100ms)"
echo "  ✅ Wikipedia fallback works"
echo "  ✅ Batch seed: 3/3 success"
echo ""