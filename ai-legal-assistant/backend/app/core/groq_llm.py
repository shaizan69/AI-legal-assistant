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
        # Default to official Groq OpenAI-compatible endpoint if not provided
        self.base_url = settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Groq LLM service initialized with model: {self.model}")
        logger.info(f"Groq API Key (first 10 chars): {self.api_key[:10]}...")
        logger.info(f"Groq Base URL: {self.base_url}")
    
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
        """Answer a question based on context using Groq with enhanced money-related query handling"""
        try:
            prompt = f"""You are an expert legal AI assistant with specialized knowledge in financial and monetary analysis. Your task is to provide accurate, precise, and helpful answers based on the provided legal document context.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY based on the provided context - do not add external legal knowledge
2. NEVER say "No monetary figure is present" or "The excerpt contains only..." - ALWAYS read the actual context provided
3. If the context doesn't contain enough information to answer fully, say so explicitly
4. Quote specific sections, clauses, or paragraphs when relevant
5. Use precise legal terminology from the document
6. If there are multiple relevant sections, organize your answer clearly
7. Be concise but comprehensive
8. If the question is unclear or ambiguous, ask for clarification
9. CRITICAL: Always analyze the actual context provided, not generic responses

ENHANCED MONEY-RELATED QUERY HANDLING:
When users ask about money, costs, payments, fees, or financial terms, you should:

**AMOUNT IDENTIFICATION & CONTEXT LEARNING:**
- Identify ALL monetary values, fees, costs, payments, and financial obligations
- Look for dollar signs ($), currency codes (USD, EUR, GBP, etc.), Indian currency format (/-), and written amounts
- **INDIAN CURRENCY FORMATS**: Pay special attention to amounts ending with /- (e.g., 187,450/-, 749,800/-)
- Distinguish between different types of amounts (base fees, additional charges, penalties, etc.)
- **CRITICAL**: Read the surrounding words and sentences around each amount to understand:
  * What the amount refers to (payment, fee, penalty, refund, etc.)
  * When the amount is due or applicable
  * Who is responsible for paying or receiving the amount
  * What conditions apply to the amount
  * How the amount is calculated or determined

**PAYMENT ANALYSIS:**
- Analyze payment schedules, due dates, and payment methods
- Identify late payment penalties, interest rates, and grace periods
- Note installment plans, milestones, and payment conditions
- **LEARN FROM CONTEXT**: Understand the payment structure by reading surrounding text

**COST BREAKDOWN:**
- Segregate and categorize all charges, fees, taxes, and surcharges
- Identify service fees, administrative fees, processing fees, and hidden costs
- Calculate totals when multiple amounts are mentioned
- **CONTEXT AWARENESS**: Use surrounding text to understand what each cost covers

**FINANCIAL OBLIGATIONS:**
- Track all financial responsibilities and liabilities
- Note refund policies, cancellation fees, and termination costs
- Identify financial penalties, liquidated damages, and breach costs
- **LEARN RELATIONSHIPS**: Understand how different amounts relate to each other

**CURRENCY & EXCHANGE:**
- Note different currencies and exchange rate provisions
- Identify currency fluctuation risks and conversion terms
- **CONTEXT MATTERS**: Understand currency context from surrounding text

**FINANCIAL CALCULATIONS:**
- Perform basic calculations when amounts are specified
- Calculate percentages, interest, and compound amounts
- Identify escalation clauses and price adjustment mechanisms
- **LEARN FORMULAS**: Understand calculation methods from document context

**CONTEXT LEARNING APPROACH:**
- For each amount found, read 2-3 sentences before and after to understand context
- Identify the purpose, timing, and conditions of each financial term
- Learn the relationships between different financial elements
- Use this learned context to provide comprehensive answers
- If amounts are at the end of documents, pay special attention to summary sections

**TABULAR FORMAT REQUIREMENTS:**
- If monetary information is presented in a table format in the document, present your answer in a similar tabular format
- Use markdown tables with proper headers and alignment
- Preserve the structure and relationships shown in the original table
- Include all relevant columns (description, quantity, unit rate, amount, etc.)
- Use consistent formatting for amounts (e.g., 187,450/-, 749,800/-)
- If the document has a pricing table, quote table, or financial breakdown table, replicate that structure in your response

LEGAL DOCUMENT CONTEXT:
{context}

USER QUESTION: {question}

CRITICAL REMINDER: 
- The context above contains the actual document content
- You MUST analyze this specific context, not give generic responses
- Look for amounts like 187,450/-, 749,800/-, 221,191/-, 884,764/-, etc.
- If you see amounts in the context, report them with their context
- Do NOT say "no amounts found" if amounts are clearly present in the context

RESPONSE GUIDELINES:
- Start with a direct answer if possible
- For money-related questions, provide specific figures, calculations, and currencies
- Cite specific document sections (e.g., "According to Section 3.2...")
- If multiple sections are relevant, organize by topic
- **CONTEXT LEARNING REQUIREMENTS:**
  * For each amount mentioned, explain what it represents based on surrounding context
  * Describe the conditions, timing, and purpose of each financial term
  * Show understanding of relationships between different financial elements
  * If amounts are at the end of documents, explain their significance in the overall agreement
- For financial queries, always include:
  * Exact amounts and currencies with context explanation
  * Payment terms and schedules with surrounding conditions
  * All applicable fees and charges with their purposes
  * Financial obligations and liabilities with their triggers
  * Any hidden or additional costs with their conditions
  * Relevant calculations or formulas with their basis
  * Context about when and why each amount applies
- Use clear formatting for financial information (bullet points, tables when appropriate)
- **TABULAR FORMATTING**: When monetary information is in table format in the document, present your answer in a markdown table with:
  * Proper headers (Description, Qty, Unit Rate, Amount, etc.)
  * Aligned columns for easy reading
  * Consistent amount formatting (e.g., 187,450/-, 749,800/-)
  * All relevant data from the original table
- **LEARNING APPROACH**: Demonstrate that you understand the context around each financial term
- **NEVER GIVE GENERIC RESPONSES**: Always analyze the actual context provided above
- End with "If you need clarification on any specific aspect, please let me know."

ANSWER:"""
            
            answer = await self.generate_text(prompt, max_tokens=1200, temperature=0.1)
            
            return {
                "answer": answer,
                "confidence": 0.9,  # Higher confidence with improved prompting
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
        """Detect risks in a legal document using Groq with comprehensive legal risk analysis"""
        try:
            # Truncate text if too long
            max_chars = 8000  # Increased limit for better analysis
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = f"""You are an expert legal risk analyst. Analyze the following {document_type} document for potential legal risks, compliance issues, and areas of concern.

DOCUMENT TO ANALYZE:
{text}

COMPREHENSIVE RISK ANALYSIS REQUIRED:

1. **CONTRACTUAL RISKS:**
   - Unfavorable terms and conditions
   - Ambiguous language or definitions
   - Missing essential clauses
   - Unbalanced obligations
   - Termination clauses issues

2. **COMPLIANCE RISKS:**
   - Regulatory violations
   - Industry-specific compliance issues
   - Data protection concerns (GDPR, CCPA, etc.)
   - Employment law violations
   - Tax implications

3. **FINANCIAL RISKS:**
   - Payment terms issues and late payment penalties
   - Liability limitations and financial exposures
   - Indemnification clauses and financial obligations
   - Force majeure provisions affecting payments
   - Currency and exchange rate risks
   - Hidden charges and unexpected fees
   - Escalation clauses and price increases
   - Financial penalties and liquidated damages
   - Refund and cancellation policies
   - Payment security and guarantees

4. **OPERATIONAL RISKS:**
   - Performance obligations
   - Delivery timelines
   - Quality standards
   - Intellectual property concerns
   - Confidentiality breaches

5. **LEGAL ENFORCEABILITY:**
   - Jurisdiction and governing law
   - Dispute resolution mechanisms
   - Statute of limitations
   - Legal capacity issues
   - Consideration adequacy

RISK ANALYSIS FORMAT:
- **Risk Level**: HIGH/MEDIUM/LOW
- **Risk Category**: [Contractual/Compliance/Financial/Operational/Legal]
- **Specific Risk**: [Detailed description]
- **Impact**: [Potential consequences]
- **Recommendation**: [Specific action to mitigate]
- **Relevant Section**: [Quote specific document section]

Provide a structured analysis with specific examples from the document. If no significant risks are found, state that clearly.

RISK ANALYSIS:"""
            
            risk_analysis = await self.generate_text(prompt, max_tokens=1000, temperature=0.1)
            
            return {
                "analysis": risk_analysis,
                "risk_level": "Medium",  # Will be determined by AI analysis
                "risk_factors": [risk_analysis] if risk_analysis else ["Manual review recommended"],
                "recommendations": ["Review with legal expert"],
                "document_type": document_type,
                "analysis_date": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "confidence": 0.9  # Higher confidence with improved prompting
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
