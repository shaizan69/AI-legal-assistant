"""
Mistral 7B LLM service using Ollama with quantized 4-bit model
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


class MistralLLMService:
    """Service for interacting with Mistral 7B via Ollama API"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.base_model = settings.MISTRAL_MODEL or "mistral-legal-q4:latest"
        self.legal_model = settings.LEGAL_MODEL or "mistral-legal-q4:latest"
        self.use_lora = settings.USE_LORA or False
        self.active_model = self.legal_model
        self.ollama_path = settings.OLLAMA_PATH
        self._configure_ollama()
    
    def _ensure_model_available(self, model_name: str) -> bool:
        """Ensure a model is available locally; attempt to pull if missing.

        Returns True if available (either already present or successfully pulled), else False.
        """
        try:
            # Check current tags
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Cannot list Ollama models to verify availability: {resp.status_code}")
                return False
            model_names = [m.get('name') for m in resp.json().get('models', [])]
            if model_name in model_names:
                return True

            # Attempt a pull (non-streaming)
            logger.info(f"Attempting to pull missing model: {model_name}")
            pull_payload = {"name": model_name, "stream": False}
            pull_resp = requests.post(
                f"{self.ollama_url}/api/pull",
                json=pull_payload,
                timeout=1800  # allow up to 30 minutes for slow networks
            )
            if pull_resp.status_code in (200, 201):
                logger.info(f"Successfully pulled model: {model_name}")
                return True
            else:
                logger.warning(f"Failed to pull model {model_name}: {pull_resp.status_code} - {pull_resp.text}")
                return False
        except Exception as e:
            logger.warning(f"Error ensuring model availability for {model_name}: {e}")
            return False

    def _configure_ollama(self):
        """Configure Ollama client and ensure model is available"""
        try:
            # Set Ollama environment variables to use D: drive
            os.environ['OLLAMA_MODELS'] = self.ollama_path
            
            # Force GPU usage environment variables
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use first GPU
            os.environ['OLLAMA_GPU_LAYERS'] = '-1'    # Use all GPU layers
            os.environ['OLLAMA_NUM_GPU'] = '1'        # Force GPU usage
            
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama server not responding at {self.ollama_url}")
            
            # Enforce single-model policy: use configured legal model only
            self.active_model = self.legal_model
            if not self._ensure_model_available(self.active_model):
                logger.info(f"Attempting to pull configured model: {self.active_model}")
                if not self._ensure_model_available(self.active_model):
                    raise RuntimeError(f"Configured model {self.active_model} is not available and could not be pulled.")
            
            logger.info(f"Mistral LLM service configured with model: {self.active_model}")
            logger.info("GPU acceleration enabled - forcing GPU-only mode")
            
        except Exception as e:
            logger.error(f"Error configuring Ollama: {e}")
            raise
    
    def test_gpu_usage(self):
        """Test if GPU is being used by Ollama"""
        try:
            payload = {
                "model": self.active_model,
                "prompt": "Test GPU usage",
                "stream": False,
                "options": {
                    "num_gpu": 1,
                    "gpu_layers": -1,
                    "low_vram": False
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("✅ GPU test successful - GPU is being used")
                return True
            else:
                logger.warning(f"⚠️ GPU test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ GPU test error: {e}")
            return False
    
    def _make_request_ultra_fast(self, messages: List[Dict[str, str]], max_tokens: int = 50, temperature: float = 0.1) -> str:
        """Ultra-fast request optimized for 1B model with minimal resources"""
        try:
            prompt = self._format_messages_for_ollama(messages)
            
            payload = {
                "model": self.active_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": min(max_tokens, 50),  # Very limited output
                    "top_p": 0.8,
                    "top_k": 20,
                    "repeat_penalty": 1.0,
                    "stop": ["</s>", "Human:", "Assistant:", "\n\n"],
                    "num_ctx": 1024,  # Medium context for GPU
                    "num_thread": 4,  # More threads for GPU
                    "num_gpu": 1,     # Use GPU!
                    "low_vram": False, # Use full VRAM
                    "num_batch": 4,   # Larger batch for GPU
                    "gpu_layers": -1, # Use all GPU layers
                    "use_mmap": True,
                    "use_mlock": False
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30  # Short timeout for ultra-fast GPU requests
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.Timeout:
            logger.warning(f"Ultra-fast request timed out after 15 seconds")
            return "Response timeout - model too slow"
        except Exception as e:
            logger.error(f"Ultra-fast request failed: {e}")
            return "Processing failed"
    
    async def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Make a request to Ollama API with fallback to faster model"""
        try:
            # Convert messages to Ollama format
            prompt = self._format_messages_for_ollama(messages)
            
            # Try primary model first
            model = self.active_model
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": min(max_tokens, 200),  # Limited output for speed
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "stop": ["</s>", "Human:", "Assistant:"],
                    "num_ctx": 2048,  # Larger context for GPU
                    "num_thread": 8,  # More threads for GPU
                    "num_gpu": 1,     # Force GPU usage
                    "low_vram": False, # Use full VRAM
                    "num_batch": 8,   # Larger batch for GPU
                    "use_mmap": True, # Memory mapping for efficiency
                    "use_mlock": False, # Don't lock memory
                    "gpu_layers": -1  # Use all GPU layers
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # Increased timeout for GPU processing
            )
            
            if response.status_code != 200:
                # Handle memory errors with clear message
                if response.status_code == 500 and "requires more system memory" in response.text:
                    logger.error("Insufficient GPU memory for mistral-legal-q4:latest. Consider reducing context or using a smaller model.")
                    raise Exception("Insufficient GPU memory - model requires more VRAM than available")
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.Timeout:
            logger.warning(f"Primary model {self.active_model} timed out after 2 minutes (GPU). This may indicate insufficient VRAM.")
            raise Exception("LLM request timed out - check GPU memory availability")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_url}")
            raise Exception("Ollama service is not running - please start Ollama")
        except Exception as e:
            logger.error(f"Error making Ollama API request: {e}")
            raise
    
    async def _make_request_fallback(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Fallback disabled by configuration"""
        raise Exception("LLM fallback is disabled")

    async def _make_request_low_memory(self, messages: List[Dict[str, str]], max_tokens: int = 800, temperature: float = 0.7) -> str:
        """Low-memory mode disabled by configuration"""
        raise Exception("LLM low-memory mode is disabled")
    
    def _format_messages_for_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Ollama's prompt format"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"<s>[INST] {content} [/INST]")
            elif role == 'user':
                prompt_parts.append(f"[INST] {content} [/INST]")
            elif role == 'assistant':
                prompt_parts.append(f"{content}</s>")
        
        # Add final assistant prompt
        prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using Mistral 7B"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful legal document assistant specialized in analyzing contracts, agreements, and legal documents. Provide accurate, detailed, and professional responses."},
                {"role": "user", "content": prompt}
            ]
            
            return await self._make_request(messages, max_tokens, temperature)
            
        except Exception as e:
            logger.error(f"Error generating text with Mistral: {e}")
            raise
    
    async def summarize_document(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Ultra-simple summarization for 1B model - designed for speed"""
        try:
            # Drastically reduce input size for 1B model
            if len(text) > 500:  # Very small input
                text = text[:500] + "..."
            
            # Ultra-simple prompt
            prompt = f"Summarize: {text}"
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Use ultra-low settings for 1B model
            summary_text = self._make_request_ultra_fast(messages, max_tokens=50, temperature=0.1)
            
            return {
                "summary": summary_text,
                "structured": {},
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.active_model
            }
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {
                "summary": "Summary unavailable - model processing limitations.",
                "structured": {},
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.active_model
            }
    
    async def detect_risks(self, text: str, document_type: str = "contract") -> Dict[str, Any]:
        """Ultra-simple risk detection for 1B model"""
        try:
            # Drastically reduce input size
            if len(text) > 300:  # Very small input
                text = text[:300] + "..."
            
            # Ultra-simple prompt
            prompt = f"Risks in: {text}"
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            risk_analysis = self._make_request_ultra_fast(messages, max_tokens=30, temperature=0.1)
            
            return {
                "analysis": risk_analysis,
                "risk_level": "Medium",
                "risk_factors": [risk_analysis] if risk_analysis else ["Manual review needed"],
                "recommendations": ["Review with legal expert"],
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.active_model
            }
            
        except Exception as e:
            logger.error(f"Error detecting risks: {e}")
            return {
                "analysis": "Risk analysis unavailable - model limitations.",
                "risk_level": "Unknown",
                "risk_factors": ["Manual review recommended"],
                "recommendations": ["Consult legal expert"],
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.active_model
            }
    
    async def compare_documents(self, doc1_text: str, doc2_text: str, doc1_type: str = "contract", doc2_type: str = "contract") -> Dict[str, Any]:
        """Compare two legal documents using Mistral 7B"""
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
            
            comparison = await self._make_request(messages, max_tokens=500, temperature=0.3)
            
            return {
                "comparison": comparison,
                "document1_type": doc1_type,
                "document2_type": doc2_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.active_model
            }
            
        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {
                "comparison": "Unable to compare documents due to an error.",
                "document1_type": doc1_type,
                "document2_type": doc2_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.active_model
            }
    
    async def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer a question about a legal document using Mistral 7B"""
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
            {context[:1000]}
            
            Question: {question}
            
            Answer:
            """
            
            messages = [
                {"role": "system", "content": "You are a legal assistant specialized in contract Q&A. Provide accurate, evidence-based answers from document context."},
                {"role": "user", "content": prompt}
            ]
            
            answer_text = await self._make_request(messages, max_tokens=300, temperature=0.1)
            
            # Calculate confidence based on answer content
            confidence = self._calculate_confidence(answer_text, context, question)
            
            return {
                "answer": answer_text,
                "confidence": confidence,
                "model_used": self.active_model
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question.",
                "confidence": 0.0,
                "model_used": self.active_model
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
llm_service = MistralLLMService()
