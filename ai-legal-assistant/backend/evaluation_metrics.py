#!/usr/bin/env python3
"""
Evaluation Metrics for Contextual Reasoning Legal Document Assistant
"""

import json
import re
from typing import Dict, List, Any, Tuple
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np

class LegalDocumentEvaluator:
    """Evaluator for legal document understanding tasks"""
    
    def __init__(self):
        self.required_fields = ["answer", "reasoning", "clause_reference", "confidence"]
        
    def extract_structured_output(self, text: str) -> Dict[str, str]:
        """Extract structured output from model response"""
        result = {}
        
        # Extract Answer
        answer_match = re.search(r'\*\*Answer:\*\*\s*(.+?)(?=\*\*|$)', text, re.DOTALL)
        if answer_match:
            result["answer"] = answer_match.group(1).strip()
        
        # Extract Reasoning
        reasoning_match = re.search(r'\*\*Reasoning:\*\*\s*(.+?)(?=\*\*|$)', text, re.DOTALL)
        if reasoning_match:
            result["reasoning"] = reasoning_match.group(1).strip()
        
        # Extract Clause Reference
        clause_match = re.search(r'\*\*Clause Reference:\*\*\s*(.+?)(?=\*\*|$)', text, re.DOTALL)
        if clause_match:
            result["clause_reference"] = clause_match.group(1).strip()
        
        # Extract Confidence
        confidence_match = re.search(r'\*\*Confidence:\*\*\s*(.+?)(?=\*\*|$)', text, re.DOTALL)
        if confidence_match:
            result["confidence"] = confidence_match.group(1).strip()
        
        return result
    
    def evaluate_contextual_accuracy(self, predicted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Evaluate if answer aligns with full clause meaning"""
        if "answer" not in predicted or "answer" not in expected:
            return 0.0
        
        pred_answer = predicted["answer"].lower().strip()
        exp_answer = expected["answer"].lower().strip()
        
        # Simple string similarity (can be enhanced with semantic similarity)
        if pred_answer == exp_answer:
            return 1.0
        
        # Check for key financial terms and amounts
        pred_amounts = re.findall(r'[\d,]+(?:\.\d{2})?', pred_answer)
        exp_amounts = re.findall(r'[\d,]+(?:\.\d{2})?', exp_answer)
        
        if pred_amounts and exp_amounts:
            # Check if amounts match
            pred_amounts_clean = [amt.replace(',', '') for amt in pred_amounts]
            exp_amounts_clean = [amt.replace(',', '') for amt in exp_amounts]
            
            if set(pred_amounts_clean) == set(exp_amounts_clean):
                return 0.8  # Partial credit for correct amounts
        
        # Check for key terms
        key_terms = ['payment', 'schedule', 'installment', 'advance', 'penalty', 'interest', 'refund']
        pred_terms = [term for term in key_terms if term in pred_answer]
        exp_terms = [term for term in key_terms if term in exp_answer]
        
        if pred_terms and exp_terms:
            term_overlap = len(set(pred_terms) & set(exp_terms)) / len(set(exp_terms))
            return term_overlap * 0.6
        
        return 0.0
    
    def evaluate_monetary_parsing(self, predicted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Evaluate correct extraction of INR values, %, and timelines"""
        if "answer" not in predicted or "answer" not in expected:
            return 0.0
        
        pred_answer = predicted["answer"]
        exp_answer = expected["answer"]
        
        # Extract monetary values
        pred_amounts = re.findall(r'[\d,]+(?:\.\d{2})?', pred_answer)
        exp_amounts = re.findall(r'[\d,]+(?:\.\d{2})?', exp_answer)
        
        # Extract percentages
        pred_percentages = re.findall(r'(\d+(?:\.\d+)?%)', pred_answer)
        exp_percentages = re.findall(r'(\d+(?:\.\d+)?%)', exp_answer)
        
        # Extract time periods
        pred_time = re.findall(r'(\d+\s*(?:days?|months?|years?))', pred_answer.lower())
        exp_time = re.findall(r'(\d+\s*(?:days?|months?|years?))', exp_answer.lower())
        
        # Calculate precision for each type
        amount_precision = self._calculate_precision(pred_amounts, exp_amounts)
        percentage_precision = self._calculate_precision(pred_percentages, exp_percentages)
        time_precision = self._calculate_precision(pred_time, exp_time)
        
        # Weighted average
        total_weight = len(exp_amounts) + len(exp_percentages) + len(exp_time)
        if total_weight == 0:
            return 1.0 if not pred_amounts and not pred_percentages and not pred_time else 0.0
        
        weighted_score = (
            amount_precision * len(exp_amounts) +
            percentage_precision * len(exp_percentages) +
            time_precision * len(exp_time)
        ) / total_weight
        
        return weighted_score
    
    def _calculate_precision(self, predicted: List[str], expected: List[str]) -> float:
        """Calculate precision between predicted and expected lists"""
        if not expected:
            return 1.0 if not predicted else 0.0
        
        # Normalize values for comparison
        pred_normalized = [val.replace(',', '').strip() for val in predicted]
        exp_normalized = [val.replace(',', '').strip() for val in expected]
        
        correct = 0
        for exp_val in exp_normalized:
            if exp_val in pred_normalized:
                correct += 1
        
        return correct / len(expected)
    
    def evaluate_reasoning_consistency(self, predicted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Evaluate correctness of reasoning section"""
        if "reasoning" not in predicted or "reasoning" not in expected:
            return 0.0
        
        pred_reasoning = predicted["reasoning"].lower()
        exp_reasoning = expected["reasoning"].lower()
        
        # Check for key reasoning indicators
        reasoning_indicators = [
            'extracted from', 'based on', 'according to', 'clause', 'section',
            'explicitly', 'implicitly', 'conditional', 'dependent on'
        ]
        
        pred_indicators = [ind for ind in reasoning_indicators if ind in pred_reasoning]
        exp_indicators = [ind for ind in reasoning_indicators if ind in exp_reasoning]
        
        if not exp_indicators:
            return 1.0 if not pred_indicators else 0.5
        
        indicator_overlap = len(set(pred_indicators) & set(exp_indicators)) / len(set(exp_indicators))
        return indicator_overlap
    
    def evaluate_hallucination_rate(self, predicted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Penalize unsupported or fabricated answers"""
        if "answer" not in predicted or "answer" not in expected:
            return 1.0  # Full penalty for missing answer
        
        pred_answer = predicted["answer"].lower()
        exp_answer = expected["answer"].lower()
        
        # Check for hallucination indicators
        hallucination_indicators = [
            'not specified', 'not mentioned', 'not defined', 'not available',
            'not included', 'not disclosed', 'not provided', 'not stated'
        ]
        
        pred_has_negation = any(ind in pred_answer for ind in hallucination_indicators)
        exp_has_negation = any(ind in exp_answer for ind in hallucination_indicators)
        
        # If expected has negation but predicted doesn't, it's a hallucination
        if exp_has_negation and not pred_has_negation:
            return 1.0
        
        # If predicted has negation but expected doesn't, it's a hallucination
        if pred_has_negation and not exp_has_negation:
            return 1.0
        
        # If both have negation, check if they're consistent
        if pred_has_negation and exp_has_negation:
            return 0.0  # No hallucination penalty
        
        # Check for fabricated information
        pred_amounts = re.findall(r'[\d,]+(?:\.\d{2})?', pred_answer)
        exp_amounts = re.findall(r'[\d,]+(?:\.\d{2})?', exp_answer)
        
        # If predicted has amounts but expected doesn't, it's a hallucination
        if pred_amounts and not exp_amounts:
            return 1.0
        
        # If expected has amounts but predicted doesn't, it's a hallucination
        if exp_amounts and not pred_amounts:
            return 1.0
        
        return 0.0
    
    def evaluate_clause_identification(self, predicted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Evaluate correct clause reference recognition"""
        if "clause_reference" not in predicted or "clause_reference" not in expected:
            return 0.0
        
        pred_ref = predicted["clause_reference"].lower().strip()
        exp_ref = expected["clause_reference"].lower().strip()
        
        # Exact match
        if pred_ref == exp_ref:
            return 1.0
        
        # Partial match for clause numbers
        pred_clause_num = re.search(r'clause\s*(\d+)', pred_ref)
        exp_clause_num = re.search(r'clause\s*(\d+)', exp_ref)
        
        if pred_clause_num and exp_clause_num:
            if pred_clause_num.group(1) == exp_clause_num.group(1):
                return 0.8
        
        # Check for section numbers
        pred_section_num = re.search(r'section\s*(\d+(?:\.\d+)?)', pred_ref)
        exp_section_num = re.search(r'section\s*(\d+(?:\.\d+)?)', exp_ref)
        
        if pred_section_num and exp_section_num:
            if pred_section_num.group(1) == exp_section_num.group(1):
                return 0.8
        
        return 0.0
    
    def evaluate_confidence_calibration(self, predicted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Evaluate if confidence levels are appropriately calibrated"""
        if "confidence" not in predicted or "confidence" not in expected:
            return 0.0
        
        pred_conf = predicted["confidence"].lower().strip()
        exp_conf = expected["confidence"].lower().strip()
        
        # Map confidence levels to numeric values
        conf_map = {"high": 3, "medium": 2, "low": 1}
        
        pred_num = conf_map.get(pred_conf, 0)
        exp_num = conf_map.get(exp_conf, 0)
        
        if pred_num == exp_num:
            return 1.0
        
        # Partial credit for close confidence levels
        if abs(pred_num - exp_num) == 1:
            return 0.5
        
        return 0.0
    
    def evaluate_single_example(self, predicted: str, expected: Dict[str, str]) -> Dict[str, float]:
        """Evaluate a single example"""
        pred_structured = self.extract_structured_output(predicted)
        
        return {
            "contextual_accuracy": self.evaluate_contextual_accuracy(pred_structured, expected),
            "monetary_parsing": self.evaluate_monetary_parsing(pred_structured, expected),
            "reasoning_consistency": self.evaluate_reasoning_consistency(pred_structured, expected),
            "hallucination_rate": self.evaluate_hallucination_rate(pred_structured, expected),
            "clause_identification": self.evaluate_clause_identification(pred_structured, expected),
            "confidence_calibration": self.evaluate_confidence_calibration(pred_structured, expected)
        }
    
    def evaluate_batch(self, predictions: List[str], expected: List[Dict[str, str]]) -> Dict[str, float]:
        """Evaluate a batch of examples"""
        if len(predictions) != len(expected):
            raise ValueError("Predictions and expected outputs must have the same length")
        
        all_scores = []
        for pred, exp in zip(predictions, expected):
            scores = self.evaluate_single_example(pred, exp)
            all_scores.append(scores)
        
        # Calculate average scores
        avg_scores = {}
        for metric in all_scores[0].keys():
            avg_scores[metric] = np.mean([score[metric] for score in all_scores])
        
        # Calculate overall score (weighted average)
        weights = {
            "contextual_accuracy": 0.3,
            "monetary_parsing": 0.25,
            "reasoning_consistency": 0.15,
            "hallucination_rate": 0.15,
            "clause_identification": 0.1,
            "confidence_calibration": 0.05
        }
        
        overall_score = sum(avg_scores[metric] * weight for metric, weight in weights.items())
        avg_scores["overall_score"] = overall_score
        
        return avg_scores

def main():
    """Example usage of the evaluator"""
    evaluator = LegalDocumentEvaluator()
    
    # Example evaluation
    predicted = """**Answer:** Rs. 5,00,000/- advance at execution, balance Rs. 45,00,000/- within 90 days of possession.
**Reasoning:** Two-stage payment structure with specific amounts and timelines.
**Clause Reference:** Section 3.2
**Confidence:** High"""
    
    expected = {
        "answer": "Rs. 5,00,000/- advance at execution, balance Rs. 45,00,000/- within 90 days of possession.",
        "reasoning": "Two-stage payment structure with specific amounts and timelines.",
        "clause_reference": "Section 3.2",
        "confidence": "High"
    }
    
    scores = evaluator.evaluate_single_example(predicted, expected)
    print("Evaluation scores:", scores)

if __name__ == "__main__":
    main()