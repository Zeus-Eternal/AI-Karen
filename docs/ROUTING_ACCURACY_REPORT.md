================================================================================
CORTEX ROUTING ACCURACY EVALUATION REPORT
================================================================================

## OVERALL METRICS

**Intent Classification:**
  - Top-1 Accuracy: 63.83% (30/47)
  - Target: ≥92.0%
  - Status: ❌ FAIL (<85%)

**Task Type Classification:**
  - Accuracy: 78.72% (37/47)

**Confidence Calibration:**
  - ECE (Expected Calibration Error): 0.1330
  - Target: ≤0.04
  - Status: ❌ FAIL (>0.08)

--------------------------------------------------------------------------------

## ACCURACY BY COMPLEXITY

**edge_case** (7 cases):
  - Intent: 71.4%
  - Task:   85.7%

**high** (9 cases):
  - Intent: 22.2%
  - Task:   77.8%

**low** (21 cases):
  - Intent: 66.7%
  - Task:   81.0%

**medium** (10 cases):
  - Intent: 90.0%
  - Task:   70.0%

--------------------------------------------------------------------------------

## COMMON INTENT CLASSIFICATION ERRORS (Top 10)

1. Expected: 'summarization' → Predicted: 'greet' (1 times)
2. Expected: 'analysis' → Predicted: 'greet' (1 times)
3. Expected: 'test_generation' → Predicted: 'greet' (1 times)
4. Expected: 'translation' → Predicted: 'greet' (1 times)
5. Expected: 'routing_control' → Predicted: 'unknown' (1 times)
6. Expected: 'routing_control' → Predicted: 'greet' (1 times)
7. Expected: 'code_refactoring' → Predicted: 'greet' (1 times)
8. Expected: 'reasoning' → Predicted: 'code_debugging' (1 times)
9. Expected: 'streaming_request' → Predicted: 'test_generation' (1 times)
10. Expected: 'security_review' → Predicted: 'code_generation' (1 times)

--------------------------------------------------------------------------------

## RECOMMENDATIONS

❌ **NOT READY FOR PRODUCTION**
   - Intent accuracy is below minimum threshold
   - Requires significant improvement before launch

⚠️  **CALIBRATION NEEDS IMPROVEMENT**
   - Consider confidence threshold tuning
   - Implement abstention for low-confidence predictions

================================================================================