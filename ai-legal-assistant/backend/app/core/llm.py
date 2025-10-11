"""
Large Language Model wrapper and utilities using Gemini API (gemini-2.5-flash)
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any

from app.core.gemini_llm import GeminiLLMService

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Large Language Models via Gemini API (gemini-2.5-flash)"""
    
    def __init__(self):
        # Use Gemini service as primary and only provider
        self.gemini_service = GeminiLLMService()
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using the Gemini LLM"""
        return await self.gemini_service.generate_text(prompt, max_tokens, temperature)
    
    async def summarize_document(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Summarize a legal document using Gemini gemini-2.5-flash"""
        return await self.gemini_service.summarize_document(text, document_type)
    
    async def detect_risks(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Detect potential risks in a legal document using Gemini gemini-2.5-flash"""
        return await self.gemini_service.detect_risks(text, document_type)
    
    async def compare_documents(self, doc1_text: str, doc2_text: str, doc1_type: str = "contract", doc2_type: str = "contract") -> Dict[str, Any]:
        """Compare two legal documents using Gemini gemini-2.5-flash"""
        return await self.gemini_service.compare_documents(doc1_text, doc2_text)
    
    async def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer a question about a legal document using Gemini gemini-2.5-flash"""
        return await self.gemini_service.answer_question(question, context)
    
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from summary text"""
        try:
            structured: Dict[str, Any] = {}
            
            parties_match = re.search(r'Parties?[:\s]+([^\n]+)', text, re.IGNORECASE)
            if parties_match:
                structured["parties"] = [party.strip() for party in parties_match.group(1).split(',')]
            
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            dates = re.findall(date_pattern, text)
            if dates:
                structured["dates"] = dates
            
            financial_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|usd)\b'
            financial_terms = re.findall(financial_pattern, text, re.IGNORECASE)
            if financial_terms:
                structured["financial_terms"] = financial_terms
            
            return structured
            
        except Exception as exc:
            logger.error("Error extracting structured data: %s", exc)
            return {}
    
    def _extract_risk_data(self, text: str) -> Dict[str, Any]:
        """Extract risk data from analysis text"""
        try:
            risk_data: Dict[str, Any] = {
                "risk_level": "Medium",
                "risk_factors": [],
                "recommendations": [],
        }
    
            if re.search(r'\b(high|severe|critical)\b', text, re.IGNORECASE):
                risk_data["risk_level"] = "High"
            elif re.search(r'\b(low|minimal|minor)\b', text, re.IGNORECASE):
                risk_data["risk_level"] = "Low"
            
            risk_factors = re.findall(r'•\s*([^•\n]+)', text)
            if not risk_factors:
                risk_factors = re.findall(r'-\s*([^-\n]+)', text)
            if not risk_factors:
                risk_factors = re.findall(r'\d+\.\s*([^\d\n]+)', text)
            
            risk_data["risk_factors"] = [factor.strip() for factor in risk_factors[:10]]
            
            rec_pattern = r'(?:recommend|suggest|advise|consider)[^.!?]*[.!?]'
            recommendations = re.findall(rec_pattern, text, re.IGNORECASE)
            risk_data["recommendations"] = [rec.strip() for rec in recommendations[:5]]
            
            return risk_data
            
        except Exception as exc:
            logger.error("Error extracting risk data: %s", exc)
            return {"risk_level": "Unknown", "risk_factors": [], "recommendations": []}


# Global instance
llm_service = LLMService()