#!/usr/bin/env python3
"""
Evaluation metrics for Indian Legal Document Assistant
"""

import re
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import logging

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Evaluation result container"""
    answer_accuracy: float
    clause_accuracy: float
    amount_accuracy: float
    structure_compliance: float
    hallucination_rate: float
    overall_score: float

class IndianLegalEvaluator:
    """Evaluator for Indian Legal Document Assistant"""
    
    def __init__(self):
        self.amount_patterns = [
            r'INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*/-',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*rupees?',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*%'
        ]
        
        self.clause_patterns = [
            r'Section\s+(\d+)',
            r'Clause\s+(\d+)',
            r'Article\s+(\d+)',
            r'Paragraph\s+(\d+)',
            r'Sub-section\s+(\d+)'
        ]
    
    def extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts from text"""
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        return amounts
    
    def extract_clause_references(self, text: str) -> List[str]:
        """Extract clause references from text"""
        references = []
        for pattern in self.clause_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        return references
    
    def check_structure_compliance(self, response: str) -> float:
        """Check if response follows the required structure"""
        required_sections = ['Answer:', 'Clause Reference:', 'Amount:', 'Summary:']
        found_sections = sum(1 for section in required_sections if section in response)
        
        # Bonus points for table data handling
        table_indicators = ['TABLE DATA:', '|', 'table', 'Table']
        has_table_handling = any(indicator in response for indicator in table_indicators)
        
        base_score = found_sections / len(required_sections)
        if has_table_handling:
            base_score = min(1.0, base_score + 0.1)  # Small bonus for table handling
        
        return base_score
    
    def detect_hallucination(self, response: str, context: str) -> bool:
        """Detect if response contains hallucinated information"""
        # Simple heuristic: check if response contains information not in context
        response_lower = response.lower()
        context_lower = context.lower()
        
        # Check for common hallucination patterns
        hallucination_indicators = [
            'no monetary figure is present',
            'the excerpt contains only',
            'no amounts found',
            'not mentioned in the document',
            'cannot find any information'
        ]
        
        for indicator in hallucination_indicators:
            if indicator in response_lower and any(amount in context_lower for amount in ['rs.', 'inr', '/-', 'rupees']):
                return True
        
        return False
    
    def evaluate_single_response(self, response: str, expected: str, context: str) -> Dict[str, Any]:
        """Evaluate a single response"""
        # Extract elements
        response_amounts = self.extract_amounts(response)
        expected_amounts = self.extract_amounts(expected)
        
        response_clauses = self.extract_clause_references(response)
        expected_clauses = self.extract_clause_references(expected)
        
        # Calculate metrics
        amount_accuracy = 1.0 if response_amounts == expected_amounts else 0.0
        clause_accuracy = 1.0 if response_clauses == expected_clauses else 0.0
        
        # Structure compliance
        structure_compliance = self.check_structure_compliance(response)
        
        # Hallucination detection
        is_hallucination = self.detect_hallucination(response, context)
        
        return {
            'amount_accuracy': amount_accuracy,
            'clause_accuracy': clause_accuracy,
            'structure_compliance': structure_compliance,
            'is_hallucination': is_hallucination,
            'response_amounts': response_amounts,
            'expected_amounts': expected_amounts,
            'response_clauses': response_clauses,
            'expected_clauses': expected_clauses
        }
    
    def evaluate_batch(self, responses: List[str], expected: List[str], contexts: List[str]) -> EvaluationResult:
        """Evaluate a batch of responses"""
        if len(responses) != len(expected) or len(responses) != len(contexts):
            raise ValueError("All lists must have the same length")
        
        results = []
        for response, exp, context in zip(responses, expected, contexts):
            result = self.evaluate_single_response(response, exp, context)
            results.append(result)
        
        # Calculate aggregate metrics
        amount_accuracies = [r['amount_accuracy'] for r in results]
        clause_accuracies = [r['clause_accuracy'] for r in results]
        structure_compliances = [r['structure_compliance'] for r in results]
        hallucinations = [r['is_hallucination'] for r in results]
        
        # Overall metrics
        answer_accuracy = np.mean([acc for acc in amount_accuracies if acc > 0])
        clause_accuracy = np.mean(clause_accuracies)
        amount_accuracy = np.mean(amount_accuracies)
        structure_compliance = np.mean(structure_compliances)
        hallucination_rate = np.mean(hallucinations)
        
        # Overall score (weighted average)
        overall_score = (
            0.3 * answer_accuracy +
            0.25 * clause_accuracy +
            0.25 * amount_accuracy +
            0.15 * structure_compliance +
            0.05 * (1 - hallucination_rate)  # Lower hallucination rate is better
        )
        
        return EvaluationResult(
            answer_accuracy=answer_accuracy,
            clause_accuracy=clause_accuracy,
            amount_accuracy=amount_accuracy,
            structure_compliance=structure_compliance,
            hallucination_rate=hallucination_rate,
            overall_score=overall_score
        )
    
    def generate_evaluation_report(self, evaluation_result: EvaluationResult) -> str:
        """Generate a detailed evaluation report"""
        report = f"""
INDIAN LEGAL DOCUMENT ASSISTANT - EVALUATION REPORT
==================================================

OVERALL PERFORMANCE SCORE: {evaluation_result.overall_score:.2%}

DETAILED METRICS:
-----------------
Answer Accuracy:        {evaluation_result.answer_accuracy:.2%}
Clause Reference:       {evaluation_result.clause_accuracy:.2%}
Amount Extraction:      {evaluation_result.amount_accuracy:.2%}
Structure Compliance:   {evaluation_result.structure_compliance:.2%}
Hallucination Rate:     {evaluation_result.hallucination_rate:.2%}

INTERPRETATION:
---------------
- Answer Accuracy: How well the model provides correct answers
- Clause Reference: Accuracy of legal clause/section references
- Amount Extraction: Precision in extracting monetary values
- Structure Compliance: Adherence to required response format
- Hallucination Rate: Frequency of fabricated information

RECOMMENDATIONS:
----------------
"""
        
        if evaluation_result.overall_score >= 0.8:
            report += "✅ Model performance is excellent. Ready for production use."
        elif evaluation_result.overall_score >= 0.6:
            report += "⚠️ Model performance is good but needs improvement in some areas."
        else:
            report += "❌ Model performance needs significant improvement before production use."
        
        if evaluation_result.hallucination_rate > 0.1:
            report += "\n⚠️ High hallucination rate detected. Consider additional training data."
        
        if evaluation_result.amount_accuracy < 0.7:
            report += "\n⚠️ Amount extraction accuracy is low. Focus on financial data training."
        
        if evaluation_result.structure_compliance < 0.8:
            report += "\n⚠️ Response structure compliance is low. Improve prompt engineering."
        
        return report

def load_validation_data(file_path: str) -> List[Dict[str, Any]]:
    """Load validation data from JSONL file"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def run_evaluation(validation_file: str, model_responses: List[str]) -> EvaluationResult:
    """Run complete evaluation"""
    evaluator = IndianLegalEvaluator()
    
    # Load validation data
    validation_data = load_validation_data(validation_file)
    
    # Extract expected responses and contexts
    expected_responses = [item['expected_output'] for item in validation_data]
    contexts = [item['input'] for item in validation_data]
    
    # Run evaluation
    result = evaluator.evaluate_batch(model_responses, expected_responses, contexts)
    
    # Generate report
    report = evaluator.generate_evaluation_report(result)
    print(report)
    
    return result

if __name__ == "__main__":
    # Example usage
    validation_file = "validation_data.jsonl"
    
    # Example model responses (replace with actual model outputs)
    model_responses = [
        "**Answer:** Breach penalty is INR 200,000\n**Clause Reference:** Clause 15\n**Amount:** INR 200,000\n**Summary:** Penalty for contract breach",
        "**Answer:** Contract renewal period is 12 months\n**Clause Reference:** Section 8\n**Amount:** None\n**Summary:** 12-month renewal periods upon mutual agreement",
        "**Answer:** Advance payment is 30% (INR 300,000)\n**Clause Reference:** Article 6\n**Amount:** INR 300,000\n**Summary:** 30% advance before commencement"
    ]
    
    # Run evaluation
    result = run_evaluation(validation_file, model_responses)
