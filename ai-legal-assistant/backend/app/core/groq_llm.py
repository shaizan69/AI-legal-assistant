"""
Groq LLM Service for Legal Document Analysis using openai/gpt-oss-120b
"""

import asyncio
import logging
from typing import List, Dict, Optional
import requests
import json
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class GroqLLMService:
    """Service for interacting with Groq API using openai/gpt-oss-120b"""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.base_url = settings.GROQ_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Groq LLM service initialized with model: {self.model}")
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using Groq API"""
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                raise Exception(f"Groq API error: {response.status_code}")
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.Timeout:
            logger.error("Groq API request timed out")
            raise Exception("Groq API request timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Groq API")
            raise Exception("Groq API service is not available")
        except Exception as e:
            logger.error(f"Error generating text with Groq: {e}")
            raise
    
    async def answer_question(self, question: str, context: str) -> Dict[str, str]:
        """Answer a question based on context using Groq"""
        try:
            prompt = f"""Based on the following legal document context, answer the question accurately and concisely.

Context:
{context}

Question: {question}

Answer:"""
            
            answer = await self.generate_text(prompt, max_tokens=500, temperature=0.3)
            
            return {
                "answer": answer,
                "confidence": 0.8,  # Default confidence score for Groq
                "model_used": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise Exception(f"Failed to answer question: {e}")
    
    async def summarize_document(self, text: str, document_type: str = "legal") -> Dict[str, str]:
        """Summarize a legal document using Groq"""
        try:
            # Truncate text if too long (Groq has token limits)
            max_chars = 8000  # Conservative limit for Groq
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = f"""Summarize the following {document_type} document. Provide a clear, structured summary with key points.

Document:
{text}

Summary:"""
            
            summary = await self.generate_text(prompt, max_tokens=300, temperature=0.3)
            
            return {
                "summary": summary,
                "structured": {},
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "confidence": 0.8  # Default confidence for Groq
            }
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            raise Exception(f"Failed to summarize document: {e}")
    
    async def detect_risks(self, text: str, document_type: str = "legal") -> Dict[str, str]:
        """Detect risks in a legal document using Groq"""
        try:
            # Truncate text if too long
            max_chars = 6000  # Conservative limit for Groq
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = f"""Analyze the following {document_type} document for potential legal risks. Identify key risk factors and provide recommendations.

Document:
{text}

Risk Analysis:"""
            
            risk_analysis = await self.generate_text(prompt, max_tokens=200, temperature=0.3)
            
            return {
                "analysis": risk_analysis,
                "risk_level": "Medium",
                "risk_factors": [risk_analysis] if risk_analysis else ["Manual review needed"],
                "recommendations": ["Review with legal expert"],
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "confidence": 0.8  # Default confidence for Groq
            }
            
        except Exception as e:
            logger.error(f"Error detecting risks: {e}")
            raise Exception(f"Failed to detect risks: {e}")
    
    async def compare_documents(self, doc1: str, doc2: str) -> Dict[str, str]:
        """Compare two legal documents using Groq"""
        try:
            # Truncate documents if too long
            max_chars = 4000  # Conservative limit for Groq
            if len(doc1) > max_chars:
                doc1 = doc1[:max_chars] + "..."
            if len(doc2) > max_chars:
                doc2 = doc2[:max_chars] + "..."
            
            prompt = f"""Compare the following two legal documents and highlight key differences, similarities, and potential issues.

Document 1:
{doc1}

Document 2:
{doc2}

Comparison Analysis:"""
            
            comparison = await self.generate_text(prompt, max_tokens=400, temperature=0.3)
            
            return {
                "comparison": comparison,
                "differences": [],
                "similarities": [],
                "recommendations": [],
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "confidence": 0.8  # Default confidence for Groq
            }
            
        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            raise Exception(f"Failed to compare documents: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Groq API"""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test connection"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Groq API connection successful")
                return True
            else:
                logger.error(f"❌ Groq API connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Groq API connection error: {e}")
            return False
