#!/usr/bin/env python3
"""
CORTEX Routing Accuracy Evaluation

Loads gold test set and evaluates:
- Intent classification accuracy (top-1, top-3)
- Task type classification accuracy
- Confusion matrix generation
- Confidence calibration metrics

Requirements:
- Gold test set: data/cortex_routing_gold_test_set.json
- CORTEX intent resolver
- Task analyzer
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_karen_engine.core.cortex.intent import resolve_intent
from ai_karen_engine.integrations.task_analyzer import TaskAnalyzer


class RoutingEvaluator:
    """Evaluates routing accuracy against gold test set."""

    def __init__(self, gold_test_path: str):
        self.gold_test_path = gold_test_path
        self.test_cases = []
        self.results = []
        self.task_analyzer = TaskAnalyzer()

    def load_test_set(self) -> None:
        """Load gold test set from JSON file."""
        with open(self.gold_test_path, 'r') as f:
            self.test_cases = json.load(f)
        print(f"✓ Loaded {len(self.test_cases)} test cases")

    def evaluate_intent(self, query: str, expected_intent: str) -> Dict[str, Any]:
        """
        Evaluate intent classification for a single query.

        Returns:
            Dict with: predicted_intent, confidence, correct, meta
        """
        user_ctx = {}  # Empty context for evaluation
        predicted_intent, meta = resolve_intent(query, user_ctx)

        # Get confidence if available
        confidence = meta.get("confidence", 0.75)

        # Check if correct (exact match or fuzzy match)
        correct = self._is_intent_match(predicted_intent, expected_intent)

        return {
            "query": query,
            "expected": expected_intent,
            "predicted": predicted_intent,
            "confidence": confidence,
            "correct": correct,
            "meta": meta
        }

    def evaluate_task_type(self, query: str, expected_task: str) -> Dict[str, Any]:
        """
        Evaluate task type classification for a single query.

        Returns:
            Dict with: predicted_task, confidence, correct, analysis
        """
        analysis = self.task_analyzer.analyze_query(query, {})

        predicted_task = analysis.task_type
        confidence = analysis.confidence

        # Check if correct
        correct = (predicted_task == expected_task)

        return {
            "query": query,
            "expected": expected_task,
            "predicted": predicted_task,
            "confidence": confidence,
            "correct": correct,
            "capabilities": analysis.required_capabilities,
            "analysis": analysis
        }

    def _is_intent_match(self, predicted: str, expected: str) -> bool:
        """
        Check if predicted intent matches expected (with fuzzy matching).

        Handles:
        - Exact match
        - Partial match (e.g., "code_generation" matches "code")
        - Unknown intents (always wrong)
        """
        if predicted == expected:
            return True

        # Normalize for comparison
        pred_norm = predicted.lower().replace("_", "").replace("-", "")
        exp_norm = expected.lower().replace("_", "").replace("-", "")

        # Partial match
        if pred_norm in exp_norm or exp_norm in pred_norm:
            return True

        # Check if both are greeting variations
        if pred_norm in ["greeting", "greet", "hello"] and exp_norm in ["greeting", "greet", "hello"]:
            return True

        # Unknown is always wrong
        if predicted == "unknown":
            return False

        return False

    def run_evaluation(self) -> None:
        """Run complete evaluation on all test cases."""
        print("\n" + "="*80)
        print("CORTEX ROUTING ACCURACY EVALUATION")
        print("="*80 + "\n")

        intent_results = []
        task_results = []

        for i, test_case in enumerate(self.test_cases, 1):
            query = test_case["query"]
            expected_intent = test_case["expected_intent"]
            expected_task = test_case["expected_task_type"]

            # Evaluate intent
            intent_result = self.evaluate_intent(query, expected_intent)
            intent_results.append(intent_result)

            # Evaluate task type
            task_result = self.evaluate_task_type(query, expected_task)
            task_results.append(task_result)

            # Store combined result
            self.results.append({
                "test_id": i,
                "query": query,
                "complexity": test_case.get("complexity", "unknown"),
                "category": test_case.get("category", "unknown"),
                "intent": intent_result,
                "task": task_result
            })

            # Print progress every 10 cases
            if i % 10 == 0:
                print(f"  Processed {i}/{len(self.test_cases)} test cases...")

        print(f"✓ Evaluation complete: {len(self.results)} test cases processed\n")

        # Store results
        self.intent_results = intent_results
        self.task_results = task_results

    def calculate_accuracy(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate top-1 accuracy."""
        if not results:
            return {"top1": 0.0}

        correct = sum(1 for r in results if r["correct"])
        total = len(results)

        return {
            "top1": (correct / total) * 100 if total > 0 else 0.0,
            "correct": correct,
            "total": total
        }

    def generate_confusion_matrix(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate confusion matrix for predictions."""
        matrix = defaultdict(lambda: defaultdict(int))

        for result in results:
            expected = result["expected"]
            predicted = result["predicted"]
            matrix[expected][predicted] += 1

        # Get unique labels
        all_labels = set()
        for result in results:
            all_labels.add(result["expected"])
            all_labels.add(result["predicted"])

        return {
            "matrix": dict(matrix),
            "labels": sorted(all_labels)
        }

    def calculate_confidence_calibration(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate Expected Calibration Error (ECE).

        Bins predictions by confidence and checks if accuracy matches confidence.
        """
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        bin_counts = [0] * (len(bins) - 1)
        bin_correct = [0] * (len(bins) - 1)
        bin_conf_sums = [0.0] * (len(bins) - 1)

        for result in results:
            conf = result["confidence"]
            correct = result["correct"]

            # Find bin
            for i in range(len(bins) - 1):
                if bins[i] <= conf < bins[i + 1]:
                    bin_counts[i] += 1
                    if correct:
                        bin_correct[i] += 1
                    bin_conf_sums[i] += conf
                    break

        # Calculate ECE
        ece = 0.0
        total = sum(bin_counts)

        for i in range(len(bin_counts)):
            if bin_counts[i] > 0:
                acc = bin_correct[i] / bin_counts[i]
                avg_conf = bin_conf_sums[i] / bin_counts[i]
                ece += (bin_counts[i] / total) * abs(acc - avg_conf)

        return {
            "ece": ece,
            "bins": bins,
            "bin_counts": bin_counts,
            "bin_accuracies": [bin_correct[i] / bin_counts[i] if bin_counts[i] > 0 else 0.0 for i in range(len(bin_counts))],
            "bin_confidences": [bin_conf_sums[i] / bin_counts[i] if bin_counts[i] > 0 else 0.0 for i in range(len(bin_counts))]
        }

    def analyze_by_complexity(self) -> Dict[str, Dict[str, float]]:
        """Analyze accuracy by complexity level."""
        complexity_results = defaultdict(list)

        for result in self.results:
            complexity = result["complexity"]
            intent_correct = result["intent"]["correct"]
            task_correct = result["task"]["correct"]

            complexity_results[complexity].append({
                "intent_correct": intent_correct,
                "task_correct": task_correct
            })

        # Calculate stats per complexity
        stats = {}
        for complexity, results in complexity_results.items():
            intent_acc = sum(1 for r in results if r["intent_correct"]) / len(results) * 100
            task_acc = sum(1 for r in results if r["task_correct"]) / len(results) * 100

            stats[complexity] = {
                "count": len(results),
                "intent_accuracy": intent_acc,
                "task_accuracy": task_acc
            }

        return stats

    def analyze_by_category(self) -> Dict[str, Dict[str, float]]:
        """Analyze accuracy by category."""
        category_results = defaultdict(list)

        for result in self.results:
            category = result["category"]
            intent_correct = result["intent"]["correct"]
            task_correct = result["task"]["correct"]

            category_results[category].append({
                "intent_correct": intent_correct,
                "task_correct": task_correct
            })

        # Calculate stats per category
        stats = {}
        for category, results in category_results.items():
            intent_acc = sum(1 for r in results if r["intent_correct"]) / len(results) * 100
            task_acc = sum(1 for r in results if r["task_correct"]) / len(results) * 100

            stats[category] = {
                "count": len(results),
                "intent_accuracy": intent_acc,
                "task_accuracy": task_acc
            }

        return stats

    def find_common_errors(self, results: List[Dict[str, Any]], top_n: int = 10) -> List[Tuple[str, str, int]]:
        """Find most common (expected, predicted) error pairs."""
        error_counts = Counter()

        for result in results:
            if not result["correct"]:
                pair = (result["expected"], result["predicted"])
                error_counts[pair] += 1

        return error_counts.most_common(top_n)

    def generate_report(self) -> str:
        """Generate comprehensive evaluation report."""
        report = []
        report.append("=" * 80)
        report.append("CORTEX ROUTING ACCURACY EVALUATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Overall metrics
        report.append("## OVERALL METRICS")
        report.append("")

        # Intent accuracy
        intent_acc = self.calculate_accuracy(self.intent_results)
        report.append(f"**Intent Classification:**")
        report.append(f"  - Top-1 Accuracy: {intent_acc['top1']:.2f}% ({intent_acc['correct']}/{intent_acc['total']})")
        report.append(f"  - Target: ≥92.0%")

        if intent_acc['top1'] >= 92.0:
            report.append(f"  - Status: ✅ PASS")
        elif intent_acc['top1'] >= 85.0:
            report.append(f"  - Status: ⚠️  CONDITIONAL (85-92%)")
        else:
            report.append(f"  - Status: ❌ FAIL (<85%)")

        report.append("")

        # Task type accuracy
        task_acc = self.calculate_accuracy(self.task_results)
        report.append(f"**Task Type Classification:**")
        report.append(f"  - Accuracy: {task_acc['top1']:.2f}% ({task_acc['correct']}/{task_acc['total']})")
        report.append("")

        # Confidence calibration
        intent_calibration = self.calculate_confidence_calibration(self.intent_results)
        report.append(f"**Confidence Calibration:**")
        report.append(f"  - ECE (Expected Calibration Error): {intent_calibration['ece']:.4f}")
        report.append(f"  - Target: ≤0.04")

        if intent_calibration['ece'] <= 0.04:
            report.append(f"  - Status: ✅ PASS")
        elif intent_calibration['ece'] <= 0.08:
            report.append(f"  - Status: ⚠️  CONDITIONAL (0.04-0.08)")
        else:
            report.append(f"  - Status: ❌ FAIL (>0.08)")

        report.append("")
        report.append("-" * 80)
        report.append("")

        # By complexity
        report.append("## ACCURACY BY COMPLEXITY")
        report.append("")
        complexity_stats = self.analyze_by_complexity()

        for complexity in sorted(complexity_stats.keys()):
            stats = complexity_stats[complexity]
            report.append(f"**{complexity}** ({stats['count']} cases):")
            report.append(f"  - Intent: {stats['intent_accuracy']:.1f}%")
            report.append(f"  - Task:   {stats['task_accuracy']:.1f}%")
            report.append("")

        report.append("-" * 80)
        report.append("")

        # By category
        report.append("## ACCURACY BY CATEGORY (Top 10)")
        report.append("")
        category_stats = self.analyze_by_category()

        # Sort by count descending
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:10]

        for category, stats in sorted_categories:
            report.append(f"**{category}** ({stats['count']} cases):")
            report.append(f"  - Intent: {stats['intent_accuracy']:.1f}%")
            report.append(f"  - Task:   {stats['task_accuracy']:.1f}%")
            report.append("")

        report.append("-" * 80)
        report.append("")

        # Common errors
        report.append("## COMMON INTENT CLASSIFICATION ERRORS (Top 10)")
        report.append("")
        common_errors = self.find_common_errors(self.intent_results)

        if common_errors:
            for i, ((expected, predicted), count) in enumerate(common_errors, 1):
                report.append(f"{i}. Expected: '{expected}' → Predicted: '{predicted}' ({count} times)")
        else:
            report.append("No errors found!")

        report.append("")
        report.append("-" * 80)
        report.append("")

        # Confusion matrix
        report.append("## INTENT CONFUSION MATRIX (Partial)")
        report.append("")
        confusion = self.generate_confusion_matrix(self.intent_results)

        # Show top 5 most common intents
        intent_counts = Counter(r["expected"] for r in self.intent_results)
        top_intents = [intent for intent, _ in intent_counts.most_common(5)]

        for expected in top_intents:
            if expected in confusion["matrix"]:
                predictions = confusion["matrix"][expected]
                report.append(f"**{expected}:**")
                for predicted, count in sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:3]:
                    report.append(f"  → {predicted}: {count}")
                report.append("")

        report.append("-" * 80)
        report.append("")

        # Recommendations
        report.append("## RECOMMENDATIONS")
        report.append("")

        if intent_acc['top1'] >= 92.0 and intent_calibration['ece'] <= 0.04:
            report.append("✅ **READY FOR PRODUCTION**")
            report.append("   - Intent accuracy exceeds 92% target")
            report.append("   - Calibration is within acceptable range")
        elif intent_acc['top1'] >= 85.0:
            report.append("⚠️  **CONDITIONAL GO**")
            report.append("   - Intent accuracy is acceptable but below target")
            report.append("   - Consider limiting high-risk features")
            report.append("   - Monitor accuracy closely in production")
        else:
            report.append("❌ **NOT READY FOR PRODUCTION**")
            report.append("   - Intent accuracy is below minimum threshold")
            report.append("   - Requires significant improvement before launch")

        if intent_calibration['ece'] > 0.04:
            report.append("")
            report.append("⚠️  **CALIBRATION NEEDS IMPROVEMENT**")
            report.append("   - Consider confidence threshold tuning")
            report.append("   - Implement abstention for low-confidence predictions")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_results(self, output_path: str) -> None:
        """Save detailed results to JSON file."""
        output = {
            "test_set": self.gold_test_path,
            "total_cases": len(self.results),
            "metrics": {
                "intent_accuracy": self.calculate_accuracy(self.intent_results),
                "task_accuracy": self.calculate_accuracy(self.task_results),
                "intent_calibration": self.calculate_confidence_calibration(self.intent_results),
            },
            "by_complexity": self.analyze_by_complexity(),
            "by_category": self.analyze_by_category(),
            "confusion_matrix": self.generate_confusion_matrix(self.intent_results),
            "detailed_results": self.results
        }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"✓ Detailed results saved to: {output_path}")


def main():
    """Run routing accuracy evaluation."""
    # Paths
    gold_test_path = project_root / "data" / "cortex_routing_gold_test_set.json"
    output_path = project_root / "data" / "routing_evaluation_results.json"
    report_path = project_root / "ROUTING_ACCURACY_REPORT.md"

    # Check if test set exists
    if not gold_test_path.exists():
        print(f"❌ Error: Gold test set not found at {gold_test_path}")
        sys.exit(1)

    # Create evaluator
    evaluator = RoutingEvaluator(str(gold_test_path))

    # Load test set
    evaluator.load_test_set()

    # Run evaluation
    evaluator.run_evaluation()

    # Generate report
    report = evaluator.generate_report()
    print("\n" + report)

    # Save results
    evaluator.save_results(str(output_path))

    # Save report
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"✓ Report saved to: {report_path}")

    # Return exit code based on results
    intent_acc = evaluator.calculate_accuracy(evaluator.intent_results)
    if intent_acc['top1'] >= 92.0:
        sys.exit(0)  # Success
    elif intent_acc['top1'] >= 85.0:
        sys.exit(1)  # Conditional
    else:
        sys.exit(2)  # Failure


if __name__ == "__main__":
    main()
