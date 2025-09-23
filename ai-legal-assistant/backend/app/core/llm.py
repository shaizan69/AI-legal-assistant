"""
Large Language Model wrapper and utilities using Gemini (primary)
"""

import requests
import logging
from typing import List, Dict, Optional, Any
import json
import re
from datetime import datetime

from app.core.config import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Large Language Models via Gemini API"""
    
    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL or "gemini-1.5-flash-8b"
        self._configure_gemini()
    
    def _configure_gemini(self):
        """Configure Gemini client"""
        try:
            if not self.gemini_api_key:
                logger.warning("No Gemini API key provided. LLM features will be limited.")
                return
            genai.configure(api_key=self.gemini_api_key)
            logger.info(f"Gemini LLM service configured with model: {self.gemini_model}")
        except Exception as e:
            logger.error(f"Error configuring Gemini: {e}")
            raise
    
    def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Make a request to Gemini API (text-only)"""
        try:
            if not self.gemini_api_key:
                raise ValueError("Gemini API key not configured")

            # Gemini uses a simpler prompt interface; concatenate roles
            system_msgs = "\n".join(m["content"] for m in messages if m["role"] == "system")
            user_msgs = "\n".join(m["content"] for m in messages if m["role"] == "user")
            full_prompt = (system_msgs + "\n\n" + user_msgs).strip()

            model = genai.GenerativeModel(self.gemini_model)
            resp = model.generate_content(full_prompt, generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            })
            return (resp.text or "").strip()
        except Exception as e:
            logger.error(f"Error making Gemini API request: {e}")
            raise
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using the Gemini LLM"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful legal document assistant."},
                {"role": "user", "content": prompt}
            ]
            
            return self._make_request(messages, max_tokens, temperature)
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            raise
    
    async def summarize_document(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Summarize a legal document"""
        try:
            prompt = f"""
            Please analyze and summarize the following {document_type} document. 
            Provide a structured summary with the following sections:
            
            1. Document Overview
            2. Key Parties Involved
            3. Main Terms and Conditions
            4. Important Dates and Deadlines
            5. Financial Terms (if applicable)
            6. Risk Factors
            7. Action Items
            
            Document Text:
            {text[:4000]}  # Limit to first 4000 characters
            
            Please provide a clear, concise summary that highlights the most important aspects of this document.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert legal document analyst. Provide clear, structured summaries of legal documents."},
                {"role": "user", "content": prompt}
            ]
            
            summary_text = self._make_request(messages, max_tokens=2000, temperature=0.3)
            
            # Extract structured data
            structured_data = self._extract_structured_data(summary_text)
            
            return {
                "summary": summary_text,
                "structured": structured_data,
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {
                "summary": "Unable to generate summary due to an error.",
                "structured": {},
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat()
            }
    
    async def detect_risks(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Detect potential risks in a legal document"""
        try:
            prompt = f"""
            Analyze the following {document_type} document for potential legal risks and issues.
            Focus on:
            
            1. Unfavorable terms for the client
            2. Missing important clauses
            3. Ambiguous language
            4. Unusual or concerning provisions
            5. Compliance issues
            6. Financial risks
            7. Liability concerns
            
            Document Text:
            {text[:4000]}  # Limit to first 4000 characters
            
            Provide a risk assessment with:
            - Risk level (High/Medium/Low)
            - Specific risk factors
            - Recommendations for mitigation
            """
            
            messages = [
                {"role": "system", "content": "You are a legal risk assessment expert. Identify potential risks and issues in legal documents."},
                {"role": "user", "content": prompt}
            ]
            
            risk_analysis = self._make_request(messages, max_tokens=1500, temperature=0.2)
            
            # Extract risk level and factors
            risk_data = self._extract_risk_data(risk_analysis)
            
            return {
                "analysis": risk_analysis,
                "risk_level": risk_data.get("risk_level", "Medium"),
                "risk_factors": risk_data.get("risk_factors", []),
                "recommendations": risk_data.get("recommendations", []),
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting risks: {e}")
            return {
                "analysis": "Unable to analyze risks due to an error.",
                "risk_level": "Unknown",
                "risk_factors": [],
                "recommendations": [],
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat()
            }
    
    async def compare_documents(self, doc1_text: str, doc2_text: str, doc1_type: str = "contract", doc2_type: str = "contract") -> Dict[str, Any]:
        """Compare two legal documents"""
        try:
            prompt = f"""
            Compare the following two legal documents and provide a detailed comparison:
            
            Document 1 ({doc1_type}):
            {doc1_text[:2000]}
            
            Document 2 ({doc2_type}):
            {doc2_text[:2000]}
            
            Please analyze:
            1. Key differences in terms and conditions
            2. Similarities and common clauses
            3. Which document is more favorable
            4. Missing elements in each document
            5. Recommendations for improvement
            """
            
            messages = [
                {"role": "system", "content": "You are a legal document comparison expert. Provide detailed comparisons of legal documents."},
                {"role": "user", "content": prompt}
            ]
            
            comparison = self._make_request(messages, max_tokens=2000, temperature=0.3)
            
            return {
                "comparison": comparison,
                "document1_type": doc1_type,
                "document2_type": doc2_type,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {
                "comparison": "Unable to compare documents due to an error.",
                "document1_type": doc1_type,
                "document2_type": doc2_type,
                "analysis_date": datetime.utcnow().isoformat()
            }
    
    async def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer a question about a legal document using Gemini and return structured output"""
        try:
            prompt = (
                "You are a precise legal document Q&A assistant.\n"
                "Rules: Answer ONLY using the provided context. If insufficient evidence, say 'I don't find this in the document.'\n"
                "When amounts appear, extract the exact numeric value and currency as written.\n"
                "Cite exact clauses or sentences from the context when possible. Keep answers concise.\n\n"
                f"Context (truncated to 3000 chars):\n{context[:3000]}\n\n"
                f"Question: {question}"
            )

            messages = [
                {"role": "system", "content": "You are a legal assistant specialized in contract Q&A."},
                {"role": "user", "content": prompt}
            ]

            answer_text = self._make_request(messages, max_tokens=800, temperature=0.2)

            # Heuristic confidence: penalize if the model claims lack of info
            lowered = answer_text.lower()
            if any(phrase in lowered for phrase in [
                "don't find", "not found", "insufficient", "cannot determine", "no information"
            ]):
                confidence = 0.35
            else:
                # Boost if it appears to cite context
                confidence = 0.8 if any(x in lowered for x in ["section", "clause", "article", "according to"]) else 0.6

            return {"answer": answer_text, "confidence": confidence}

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {"answer": "I'm sorry, I encountered an error while processing your question.", "confidence": 0.0}
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from summary text"""
        try:
            structured = {}
            
            # Extract parties
            parties_match = re.search(r'Parties?[:\s]+([^\n]+)', text, re.IGNORECASE)
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
            if re.search(r'\b(high|severe|critical)\b', text, re.IGNORECASE):
                risk_data["risk_level"] = "High"
            elif re.search(r'\b(low|minimal|minor)\b', text, re.IGNORECASE):
                risk_data["risk_level"] = "Low"
            
            # Extract risk factors (simple pattern matching)
            risk_factors = re.findall(r'•\s*([^•\n]+)', text)
            if not risk_factors:
                risk_factors = re.findall(r'-\s*([^-\n]+)', text)
            if not risk_factors:
                risk_factors = re.findall(r'\d+\.\s*([^\d\n]+)', text)
            
            risk_data["risk_factors"] = [factor.strip() for factor in risk_factors[:10]]  # Limit to 10
            
            # Extract recommendations
            rec_pattern = r'(?:recommend|suggest|advise|consider)[^.!?]*[.!?]'
            recommendations = re.findall(rec_pattern, text, re.IGNORECASE)
            risk_data["recommendations"] = [rec.strip() for rec in recommendations[:5]]  # Limit to 5
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Error extracting risk data: {e}")
            return {"risk_level": "Unknown", "risk_factors": [], "recommendations": []}


# Global instance
llm_service = LLMService()