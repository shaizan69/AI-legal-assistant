#!/usr/bin/env python3
"""
Integration script for fine-tuned Indian Legal Document Assistant
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FineTunedLegalAssistant:
    """Fine-tuned Indian Legal Document Assistant"""
    
    def __init__(self, model_path: str, device: str = "auto"):
        """
        Initialize the fine-tuned model
        
        Args:
            model_path: Path to the fine-tuned model
            device: Device to run the model on
        """
        self.model_path = model_path
        self.device = device
        self.tokenizer = None
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the fine-tuned model and tokenizer"""
        try:
            logger.info(f"Loading fine-tuned model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                device_map=self.device if self.device == "auto" else None
            )
            
            if self.device != "auto":
                self.model = self.model.to(self.device)
            
            logger.info("Fine-tuned model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading fine-tuned model: {e}")
            raise
    
    def format_legal_prompt(self, question: str, context: str) -> str:
        """Format the prompt for legal document analysis"""
        prompt = f"""You are an AI-powered Legal Document Assistant specialized in Indian law, contracts, and financial agreements.

INSTRUCTION: {question}

DOCUMENT CONTEXT: {context}

RESPONSE FORMAT:
- Answer: <direct answer>
- Clause Reference: <clause number / section>
- Amount (if any): <INR value>
- Summary: <one-line explanation>

TABLE DATA HANDLING:
- When you see "TABLE DATA:" in context, treat it as structured tabular information
- Extract specific values from tables and reference them accurately
- Calculate totals, subtotals, and percentages from table data when relevant
- Present table information in a clear, organized manner

RESPONSE:"""
        
        return prompt
    
    def generate_response(self, question: str, context: str, max_tokens: int = 200) -> str:
        """Generate a response using the fine-tuned model"""
        try:
            # Format the prompt
            prompt = self.format_legal_prompt(question, context)
            
            # Tokenize
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=4096
            )
            
            if self.device != "auto":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = response[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def analyze_document(self, question: str, document_context: str) -> Dict[str, Any]:
        """Analyze a legal document and provide structured response"""
        try:
            # Generate response
            response = self.generate_response(question, document_context)
            
            # Parse the structured response
            parsed_response = self.parse_structured_response(response)
            
            return {
                "answer": parsed_response.get("answer", ""),
                "clause_reference": parsed_response.get("clause_reference", ""),
                "amount": parsed_response.get("amount", ""),
                "summary": parsed_response.get("summary", ""),
                "raw_response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return {
                "answer": f"Error analyzing document: {str(e)}",
                "clause_reference": "",
                "amount": "",
                "summary": "",
                "raw_response": "",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def parse_structured_response(self, response: str) -> Dict[str, str]:
        """Parse the structured response into components"""
        parsed = {}
        
        # Extract answer
        answer_match = re.search(r'Answer:\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        if answer_match:
            parsed["answer"] = answer_match.group(1).strip()
        
        # Extract clause reference
        clause_match = re.search(r'Clause Reference:\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        if clause_match:
            parsed["clause_reference"] = clause_match.group(1).strip()
        
        # Extract amount
        amount_match = re.search(r'Amount \(if any\):\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        if amount_match:
            parsed["amount"] = amount_match.group(1).strip()
        
        # Extract summary
        summary_match = re.search(r'Summary:\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        if summary_match:
            parsed["summary"] = summary_match.group(1).strip()
        
        return parsed

# Integration with existing system
def integrate_with_existing_system(model_path: str):
    """Integrate the fine-tuned model with the existing legal assistant system"""
    
    # Initialize the fine-tuned assistant
    fine_tuned_assistant = FineTunedLegalAssistant(model_path)
    
    # Replace the existing LLM service with the fine-tuned model
    def fine_tuned_answer_question(question: str, context: str) -> Dict[str, Any]:
        """Fine-tuned version of answer_question"""
        result = fine_tuned_assistant.analyze_document(question, context)
        
        return {
            "answer": result["answer"],
            "confidence": 0.9,  # High confidence for fine-tuned model
            "model_used": "fine_tuned_legal_assistant",
            "timestamp": result["timestamp"]
        }
    
    return fine_tuned_answer_question

# Example usage
if __name__ == "__main__":
    # Example usage
    model_path = "fine_tuned_legal_assistant_20241201_120000"  # Replace with actual path
    
    # Initialize the assistant
    assistant = FineTunedLegalAssistant(model_path)
    
    # Example question and context
    question = "What is the penalty amount for delayed payment?"
    context = "Section 12. Penalty for delayed payment shall be Rs. 50,000 per month for any delay beyond the due date."
    
    # Generate response
    result = assistant.analyze_document(question, context)
    
    print("Fine-tuned Legal Assistant Response:")
    print("=" * 50)
    print(f"Question: {question}")
    print(f"Answer: {result['answer']}")
    print(f"Clause Reference: {result['clause_reference']}")
    print(f"Amount: {result['amount']}")
    print(f"Summary: {result['summary']}")
    print("=" * 50)
