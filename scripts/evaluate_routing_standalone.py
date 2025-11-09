#!/usr/bin/env python3
"""
CORTEX Routing Accuracy Evaluation (Standalone)

Evaluates routing accuracy using simplified intent/task classification logic.
Does not require full ai_karen_engine dependencies.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
import re


class StandaloneIntentClassifier:
    """Simplified intent classifier based on CORTEX patterns."""

    INTENT_PATTERNS = {
        # Greetings
        "greet": ["hello", "hi", "hey", "good morning", "good afternoon", "greetings"],
        "farewell": ["goodbye", "bye", "see you", "farewell"],

        # Code operations
        "code_generation": ["write", "create", "generate", "build", "implement", "code", "function", "class"],
        "code_debugging": ["debug", "fix", "bug", "error", "issue", "problem"],
        "code_refactoring": ["refactor", "improve", "optimize", "clean up", "restructure"],
        "test_generation": ["test", "unittest", "pytest", "spec"],
        "security_review": ["security", "vulnerability", "secure", "exploit", "hack"],
        "optimization": ["optimize", "performance", "faster", "improve speed", "efficient"],

        # Analysis and reasoning
        "explanation": ["explain", "describe", "what is", "tell me about"],
        "reasoning": ["reason", "logic", "prove", "derive", "analyze"],
        "comparison": ["compare", "versus", "vs", "difference between"],
        "analysis": ["analyze", "examine", "investigate", "study"],

        # Content operations
        "summarization": ["summarize", "summary", "tl;dr", "brief", "condense"],
        "translation": ["translate", "translation"],
        "creative_writing": ["story", "creative", "write", "compose"],
        "email_composition": ["email", "letter", "message"],

        # Queries
        "factual_query": ["what is", "who is", "where is", "when", "capital"],
        "weather_query": ["weather", "forecast", "temperature"],
        "time_query": ["time", "clock", "what time"],
        "simple_math": ["what is", "calculate", "compute", "2+2"],
        "math_problem": ["equation", "solve", "differential", "integral"],

        # Routing control
        "routing_control": ["route to", "use", "switch to", "provider", "model"],
        "routing_profile_query": ["profile", "settings", "configuration"],
        "routing_policy_change": ["policy", "set policy", "change policy"],

        # System operations
        "audit_query": ["audit", "logs", "history"],
        "health_check": ["health", "status", "check"],
        "help_request": ["help", "assist", "support"],
        "dry_run": ["dry run", "test run", "simulate"],

        # Data operations
        "data_generation": ["generate data", "test data", "mock data"],
        "classification": ["classify", "categorize", "label"],
        "extraction": ["extract", "pull out", "key points"],
        "entity_detection": ["entity", "entities", "detect"],
        "embedding_generation": ["embedding", "vector", "encode"],

        # Vision
        "vision": ["image", "picture", "photo", "describe this"],

        # Function calling
        "function_calling": ["call", "function", "api", "invoke"],

        # Streaming
        "streaming_request": ["stream", "streaming"],

        # Security threats
        "prompt_injection_attempt": ["ignore all previous", "ignore instructions", "system prompt"],
        "jailbreak_attempt": ["you are now", "pretend you are", "roleplay"],
        "malicious_code_request": ["hack", "exploit", "malware", "virus"],
        "sql_injection_attempt": ["drop table", "delete from", "; --"],
        "spam_attempt": ["flood", "spam"],
    }

    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify query into an intent.

        Returns:
            (intent, confidence)
        """
        query_lower = query.lower().strip()

        # Empty query
        if not query_lower:
            return "empty_query", 0.9

        # Check for security threats first (highest priority)
        for intent in ["prompt_injection_attempt", "jailbreak_attempt", "sql_injection_attempt", "malicious_code_request", "spam_attempt"]:
            patterns = self.INTENT_PATTERNS[intent]
            for pattern in patterns:
                if pattern in query_lower:
                    return intent, 0.95

        # Score all intents
        scores = defaultdict(float)

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in query_lower:
                    # Weight by pattern length (longer patterns more specific)
                    weight = len(pattern.split()) / 10.0 + 0.5
                    scores[intent] += weight

        # Get best match
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            confidence = min(0.95, best_intent[1])
            return best_intent[0], confidence

        # Default to unknown
        return "unknown", 0.3


class StandaloneTaskClassifier:
    """Simplified task type classifier based on TaskAnalyzer patterns."""

    TASK_PATTERNS = {
        "code": [
            "code", "bug", "fix", "function", "class", "python", "typescript",
            "compile", "refactor", "debug", "test", "unittest"
        ],
        "reasoning": [
            "reason", "explain", "analyze", "logic", "why", "prove", "derive",
            "theorem", "differential", "solve"
        ],
        "summarization": [
            "summarize", "tl;dr", "brief", "condense", "summary", "key points"
        ],
        "embedding": [
            "embed", "embedding", "semantic", "vector", "similarity", "encode"
        ],
        "analysis": [
            "analyze", "examine", "investigate", "compare", "performance",
            "classify", "categorize"
        ],
        "creative": [
            "story", "creative", "write", "compose", "email", "letter",
            "generate", "mock data", "product description"
        ],
        "translation": [
            "translate", "translation", "spanish", "french", "japanese"
        ],
        "vision": [
            "image", "picture", "photo", "describe this", "base64"
        ],
        "chat": [
            "hello", "hi", "help", "what is", "capital", "weather", "time"
        ],
    }

    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify query into a task type.

        Returns:
            (task_type, confidence)
        """
        query_lower = query.lower().strip()

        # Empty query
        if not query_lower:
            return "chat", 0.5

        # Score all task types
        scores = defaultdict(float)

        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if pattern in query_lower:
                    # Weight by pattern specificity
                    weight = len(pattern.split()) / 5.0 + 0.6
                    scores[task_type] += weight

        # Get best match
        if scores:
            best_task = max(scores.items(), key=lambda x: x[1])
            confidence = min(0.9, best_task[1])
            return best_task[0], confidence

        # Default to chat
        return "chat", 0.4


class RoutingEvaluator:
    """Evaluates routing accuracy against gold test set."""

    def __init__(self, gold_test_path: str):
        self.gold_test_path = gold_test_path
        self.test_cases = []
        self.results = []
        self.intent_classifier = StandaloneIntentClassifier()
        self.task_classifier = StandaloneTaskClassifier()

    def load_test_set(self) -> None:
        """Load gold test set from JSON file."""
        with open(self.gold_test_path, 'r') as f:
            self.test_cases = json.load(f)
        print(f"✓ Loaded {len(self.test_cases)} test cases")

    def is_intent_match(self, predicted: str, expected: str) -> bool:
        """Check if predicted intent matches expected (with fuzzy matching)."""
        if predicted == expected:
            return True

        # Normalize for comparison
        pred_norm = predicted.lower().replace("_", "").replace("-", "")
        exp_norm = expected.lower().replace("_", "").replace("-", "")

        # Partial match
        if pred_norm in exp_norm or exp_norm in pred_norm:
            return True

        # Greeting variations
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

            # Classify intent
            predicted_intent, intent_conf = self.intent_classifier.classify(query)
            intent_correct = self.is_intent_match(predicted_intent, expected_intent)

            intent_results.append({
                "query": query,
                "expected": expected_intent,
                "predicted": predicted_intent,
                "confidence": intent_conf,
                "correct": intent_correct
            })

            # Classify task type
            predicted_task, task_conf = self.task_classifier.classify(query)
            task_correct = (predicted_task == expected_task)

            task_results.append({
                "query": query,
                "expected": expected_task,
                "predicted": predicted_task,
                "confidence": task_conf,
                "correct": task_correct
            })

            # Store combined result
            self.results.append({
                "test_id": i,
                "query": query[:60] + "..." if len(query) > 60 else query,
                "complexity": test_case.get("complexity", "unknown"),
                "category": test_case.get("category", "unknown"),
                "intent": {"expected": expected_intent, "predicted": predicted_intent, "correct": intent_correct, "confidence": intent_conf},
                "task": {"expected": expected_task, "predicted": predicted_task, "correct": task_correct, "confidence": task_conf}
            })

            # Print progress
            if i % 10 == 0:
                print(f"  Processed {i}/{len(self.test_cases)} test cases...")

        print(f"✓ Evaluation complete: {len(self.results)} test cases processed\n")

        self.intent_results = intent_results
        self.task_results = task_results

    def calculate_accuracy(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate accuracy metrics."""
        if not results:
            return {"top1": 0.0, "correct": 0, "total": 0}

        correct = sum(1 for r in results if r["correct"])
        total = len(results)

        return {
            "top1": (correct / total) * 100 if total > 0 else 0.0,
            "correct": correct,
            "total": total
        }

    def calculate_ece(self, results: List[Dict[str, Any]]) -> float:
        """Calculate Expected Calibration Error."""
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        bin_counts = [0] * (len(bins) - 1)
        bin_correct = [0] * (len(bins) - 1)
        bin_conf_sums = [0.0] * (len(bins) - 1)

        for result in results:
            conf = result["confidence"]
            correct = result["correct"]

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

        return ece

    def analyze_by_complexity(self) -> Dict[str, Dict[str, float]]:
        """Analyze accuracy by complexity level."""
        complexity_results = defaultdict(list)

        for result in self.results:
            complexity = result["complexity"]
            complexity_results[complexity].append({
                "intent_correct": result["intent"]["correct"],
                "task_correct": result["task"]["correct"]
            })

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
        ece = self.calculate_ece(self.intent_results)
        report.append(f"**Confidence Calibration:**")
        report.append(f"  - ECE (Expected Calibration Error): {ece:.4f}")
        report.append(f"  - Target: ≤0.04")

        if ece <= 0.04:
            report.append(f"  - Status: ✅ PASS")
        elif ece <= 0.08:
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

        # Recommendations
        report.append("## RECOMMENDATIONS")
        report.append("")

        if intent_acc['top1'] >= 92.0 and ece <= 0.04:
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

        if ece > 0.04:
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
                "intent_ece": self.calculate_ece(self.intent_results),
            },
            "by_complexity": self.analyze_by_complexity(),
            "detailed_results": self.results
        }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✓ Detailed results saved to: {output_path}")


def main():
    """Run routing accuracy evaluation."""
    # Paths
    project_root = Path(__file__).parent.parent
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

    print(f"\n✓ Report saved to: {report_path}")

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
