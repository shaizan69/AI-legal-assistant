"""
Large Language Model wrapper and utilities using Llama 3-8B with Ollama
"""

import requests
import logging
import json
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class LlamaLLMService:
    """Service for interacting with Llama 3-8B via Ollama API"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = settings.LLAMA_MODEL or "llama3:8b"
        self.lora_model = settings.LORA_MODEL or "llama3-legal-lora"
        self.use_lora = settings.USE_LORA or False
        self._configure_ollama()
    
    def _configure_ollama(self):
        """Configure Ollama client and ensure model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama server not responding at {self.ollama_url}")
            
            # Check if base model is available
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.model_name not in model_names:
                logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                logger.info("You may need to pull the model: ollama pull llama3:8b")
            
            if self.use_lora and self.lora_model not in model_names:
                logger.warning(f"LoRA model {self.lora_model} not found. Will use base model.")
                self.use_lora = False
            
            logger.info(f"Ollama LLM service configured with model: {self.lora_model if self.use_lora else self.model_name}")
            
        except Exception as e:
            logger.error(f"Error configuring Ollama: {e}")
            raise
    
    def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Make a request to Ollama API"""
        try:
            # Convert messages to Ollama format
            prompt = self._format_messages_for_ollama(messages)
            
            # Use LoRA model if available, otherwise use base model
            model = self.lora_model if self.use_lora else self.model_name
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "stop": ["</s>", "Human:", "Assistant:"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Error making Ollama API request: {e}")
            raise
    
    def _format_messages_for_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Ollama's prompt format"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using the Llama LLM"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful legal document assistant specialized in analyzing contracts, agreements, and legal documents. Provide accurate, detailed, and professional responses."},
                {"role": "user", "content": prompt}
            ]
            
            return self._make_request(messages, max_tokens, temperature)
            
        except Exception as e:
            logger.error(f"Error generating text with Llama: {e}")
            raise
    
    async def summarize_document(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Summarize a legal document using Llama 3-8B"""
        try:
            prompt = f"""
            You are an expert legal document analyst. Analyze and summarize the following {document_type} document.
            
            Provide a comprehensive summary with these sections:
            
            1. **Document Overview**: Brief description of the document's purpose and nature
            2. **Key Parties**: All parties involved in the agreement
            3. **Main Terms and Conditions**: Core obligations, rights, and responsibilities
            4. **Important Dates**: Deadlines, effective dates, and time-sensitive provisions
            5. **Financial Terms**: Payment amounts, schedules, penalties, and financial obligations
            6. **Risk Factors**: Potential risks, liabilities, and areas of concern
            7. **Action Items**: Required actions, deliverables, and next steps
            8. **Key Clauses**: Important legal provisions that need attention
            
            Document Text:
            {text[:4000]}
            
            Provide clear, structured analysis that highlights the most critical aspects of this document.
            Use bullet points and clear headings for easy reading.
            """
            
            messages = [
                {"role": "system", "content": "You are a senior legal analyst with expertise in contract review and document analysis. Provide detailed, accurate, and professional summaries."},
                {"role": "user", "content": prompt}
            ]
            
            summary_text = self._make_request(messages, max_tokens=2500, temperature=0.3)
            
            # Extract structured data
            structured_data = self._extract_structured_data(summary_text)
            
            return {
                "summary": summary_text,
                "structured": structured_data,
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {
                "summary": "Unable to generate summary due to an error.",
                "structured": {},
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
    
    async def detect_risks(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Detect potential risks in a legal document using Llama 3-8B"""
        try:
            prompt = f"""
            You are a legal risk assessment expert. Analyze the following {document_type} document for potential legal risks and issues.
            
            Focus on identifying:
            
            1. **Unfavorable Terms**: Clauses that may be disadvantageous to the client
            2. **Missing Clauses**: Important legal protections that are absent
            3. **Ambiguous Language**: Vague or unclear provisions that could cause disputes
            4. **Unusual Provisions**: Non-standard or concerning terms
            5. **Compliance Issues**: Potential regulatory or legal compliance problems
            6. **Financial Risks**: Payment terms, penalties, or financial obligations that pose risks
            7. **Liability Concerns**: Areas where the client may face excessive liability
            8. **Enforcement Issues**: Terms that may be difficult to enforce or defend
            
            Document Text:
            {text[:4000]}
            
            Provide a detailed risk assessment including:
            - Overall risk level (High/Medium/Low) with justification
            - Specific risk factors with explanations
            - Potential impact of each risk
            - Recommendations for risk mitigation
            - Priority actions needed
            """
            
            messages = [
                {"role": "system", "content": "You are a senior legal risk analyst with extensive experience in contract review and risk assessment. Provide thorough, accurate, and actionable risk analysis."},
                {"role": "user", "content": prompt}
            ]
            
            risk_analysis = self._make_request(messages, max_tokens=2000, temperature=0.2)
            
            # Extract risk level and factors
            risk_data = self._extract_risk_data(risk_analysis)
            
            return {
                "analysis": risk_analysis,
                "risk_level": risk_data.get("risk_level", "Medium"),
                "risk_factors": risk_data.get("risk_factors", []),
                "recommendations": risk_data.get("recommendations", []),
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error detecting risks: {e}")
            return {
                "analysis": "Unable to analyze risks due to an error.",
                "risk_level": "Unknown",
                "risk_factors": [],
                "recommendations": [],
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
    
    async def compare_documents(self, doc1_text: str, doc2_text: str, doc1_type: str = "contract", doc2_type: str = "contract") -> Dict[str, Any]:
        """Compare two legal documents using Llama 3-8B"""
        try:
            prompt = f"""
            You are a legal document comparison expert. Compare the following two legal documents and provide a comprehensive analysis.
            
            Document 1 ({doc1_type}):
            {doc1_text[:2000]}
            
            Document 2 ({doc2_type}):
            {doc2_text[:2000]}
            
            Please analyze and compare:
            
            1. **Key Differences**: Major differences in terms, conditions, and provisions
            2. **Similarities**: Common clauses and shared terms
            3. **Favorability Analysis**: Which document is more favorable to each party
            4. **Missing Elements**: Important clauses missing from each document
            5. **Risk Comparison**: Relative risk levels between the documents
            6. **Financial Terms**: Comparison of payment terms, amounts, and financial obligations
            7. **Legal Protections**: Differences in liability, indemnification, and protection clauses
            8. **Recommendations**: Suggestions for improving either document
            9. **Priority Changes**: Most critical changes needed in each document
            """
            
            messages = [
                {"role": "system", "content": "You are a senior legal counsel specializing in contract comparison and negotiation. Provide detailed, professional document comparisons."},
                {"role": "user", "content": prompt}
            ]
            
            comparison = self._make_request(messages, max_tokens=2500, temperature=0.3)
            
            return {
                "comparison": comparison,
                "document1_type": doc1_type,
                "document2_type": doc2_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {
                "comparison": "Unable to compare documents due to an error.",
                "document1_type": doc1_type,
                "document2_type": doc2_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
    
    async def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer a question about a legal document using Llama 3-8B"""
        try:
            prompt = f"""
            You are a precise legal document Q&A assistant specialized in contract analysis.
            
            Instructions:
            - Answer ONLY using the provided document context
            - If the information is not in the context, clearly state "I don't find this information in the document"
            - Extract exact amounts, dates, and terms as written in the document
            - Cite specific clauses, sections, or paragraphs when possible
            - Provide concise, accurate answers based on the document content
            - If uncertain, indicate the level of confidence in your answer
            
            Document Context:
            {context[:3000]}
            
            Question: {question}
            
            Answer:
            """
            
            messages = [
                {"role": "system", "content": "You are a legal assistant specialized in contract Q&A. Provide accurate, evidence-based answers from document context."},
                {"role": "user", "content": prompt}
            ]
            
            answer_text = self._make_request(messages, max_tokens=1000, temperature=0.1)
            
            # Calculate confidence based on answer content
            confidence = self._calculate_confidence(answer_text, context, question)
            
            return {
                "answer": answer_text,
                "confidence": confidence,
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question.",
                "confidence": 0.0,
                "model_used": self.lora_model if self.use_lora else self.model_name
            }
    
    def _calculate_confidence(self, answer: str, context: str, question: str) -> float:
        """Calculate confidence score for the answer"""
        try:
            answer_lower = answer.lower()
            
            # Penalize if model says it can't find information
            if any(phrase in answer_lower for phrase in [
                "don't find", "not found", "insufficient", "cannot determine", 
                "no information", "not in the document", "not available"
            ]):
                return 0.2
            
            # Boost confidence if answer cites specific document elements
            citation_indicators = [
                "section", "clause", "article", "paragraph", "according to",
                "states that", "specifies", "indicates", "provides that"
            ]
            
            if any(indicator in answer_lower for indicator in citation_indicators):
                return 0.85
            
            # Check if answer contains specific details from context
            context_words = set(context.lower().split())
            answer_words = set(answer.lower().split())
            overlap = len(context_words.intersection(answer_words))
            
            if overlap > 10:  # Good overlap with context
                return 0.75
            elif overlap > 5:  # Moderate overlap
                return 0.6
            else:  # Low overlap
                return 0.4
                
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from summary text"""
        try:
            structured = {}
            
            # Extract parties
            parties_match = re.search(r'parties?[:\s]+([^\n]+)', text, re.IGNORECASE)
            if parties_match:
                structured['parties'] = [party.strip() for party in parties_match.group(1).split(',')]
            
            # Extract dates
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            dates = re.findall(date_pattern, text)
            if dates:
                structured['dates'] = dates
            
            # Extract financial terms
            financial_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|usd)\b'
            financial_terms = re.findall(financial_pattern, text, re.IGNORECASE)
            if financial_terms:
                structured['financial_terms'] = financial_terms
            
            return structured
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {}
    
    def _extract_risk_data(self, text: str) -> Dict[str, Any]:
        """Extract risk data from analysis text"""
        try:
            risk_data = {
                "risk_level": "Medium",
                "risk_factors": [],
                "recommendations": []
            }
            
            # Extract risk level
            if re.search(r'\b(high|severe|critical|significant)\b', text, re.IGNORECASE):
                risk_data["risk_level"] = "High"
            elif re.search(r'\b(low|minimal|minor|insignificant)\b', text, re.IGNORECASE):
                risk_data["risk_level"] = "Low"
            
            # Extract risk factors
            risk_factors = re.findall(r'•\s*([^•\n]+)', text)
            if not risk_factors:
                risk_factors = re.findall(r'-\s*([^-\n]+)', text)
            if not risk_factors:
                risk_factors = re.findall(r'\d+\.\s*([^\d\n]+)', text)
            
            risk_data["risk_factors"] = [factor.strip() for factor in risk_factors[:10]]
            
            # Extract recommendations
            rec_pattern = r'(?:recommend|suggest|advise|consider|should|must)[^.!?]*[.!?]'
            recommendations = re.findall(rec_pattern, text, re.IGNORECASE)
            risk_data["recommendations"] = [rec.strip() for rec in recommendations[:5]]
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Error extracting risk data: {e}")
            return {"risk_level": "Unknown", "risk_factors": [], "recommendations": []}


# Global instance
llm_service = LlamaLLMService()
