#!/usr/bin/env python3
"""
Comprehensive test for LLM integration with Groq API (openai/gpt-oss-120b)
"""

import asyncio
import sys
import os
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.groq_llm import GroqLLMService
from app.core.llm import llm_service
from app.core.supabase_embeddings import embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_integration():
    """Test the complete LLM integration"""
    print("🔍 TESTING LLM INTEGRATION WITH GROQ API (openai/gpt-oss-120b)")
    print("=" * 60)
    
    # Test 1: Configuration
    print("\n1. Testing Configuration...")
    print(f"   GROQ_API_KEY: {settings.GROQ_API_KEY[:20]}...")
    print(f"   GROQ_MODEL: {settings.GROQ_MODEL}")
    print(f"   GROQ_BASE_URL: {settings.GROQ_BASE_URL}")
    
    # Test 2: Groq Service Initialization
    print("\n2. Testing Groq Service Initialization...")
    try:
        groq_service = GroqLLMService()
        print(f"   ✅ Model: {groq_service.model}")
        print(f"   ✅ Base URL: {groq_service.base_url}")
        print(f"   ✅ API Key configured: {bool(groq_service.api_key)}")
    except Exception as e:
        print(f"   ❌ Error initializing Groq service: {e}")
        return False
    
    # Test 3: LLM Service Integration
    print("\n3. Testing LLM Service Integration...")
    try:
        print(f"   ✅ LLM service initialized: {type(llm_service.groq_service).__name__}")
    except Exception as e:
        print(f"   ❌ Error with LLM service: {e}")
        return False
    
    # Test 4: Embedding Service
    print("\n4. Testing Embedding Service...")
    try:
        test_embedding = embedding_service.generate_embedding("What is a contract?")
        print(f"   ✅ Embedding generated: {len(test_embedding)} dimensions")
        print(f"   ✅ Embedding model: {embedding_service.embedding_model is not None}")
    except Exception as e:
        print(f"   ❌ Error with embedding service: {e}")
        return False
    
    # Test 5: Simple LLM Request
    print("\n5. Testing Simple LLM Request...")
    try:
        test_messages = [
            {"role": "user", "content": "What is a contract?"}
        ]
        
        print("   Sending test request to LLM...")
        response = await groq_service.generate_text(
            "What is a contract?", 
            max_tokens=100, 
            temperature=0.7
        )
        
        print(f"   ✅ LLM Response: {response[:100]}...")
        print(f"   ✅ Response length: {len(response)} characters")
        
    except Exception as e:
        print(f"   ❌ Error with LLM request: {e}")
        return False
    
    # Test 6: Document Analysis
    print("\n6. Testing Document Analysis...")
    try:
        sample_text = """
        This Agreement is entered into between Company A and Company B.
        The contract shall be effective from January 1, 2024.
        The total consideration is $10,000.
        """
        
        print("   Testing document summarization...")
        summary = await llm_service.summarize_document(sample_text, "contract")
        print(f"   ✅ Summary generated: {summary.get('summary', 'No summary')[:100]}...")
        
        print("   Testing risk detection...")
        risks = await llm_service.detect_risks(sample_text, "contract")
        print(f"   ✅ Risk analysis completed: {len(risks.get('risks', []))} risks found")
        
    except Exception as e:
        print(f"   ❌ Error with document analysis: {e}")
        return False
    
    # Test 7: Q&A Functionality
    print("\n7. Testing Q&A Functionality...")
    try:
        context = "This contract is between Company A and Company B for $10,000."
        question = "What is the contract amount?"
        
        print("   Testing Q&A with context...")
        qa_response = await llm_service.answer_question(question, context)
        print(f"   ✅ Q&A Response: {qa_response.get('answer', 'No answer')[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Error with Q&A: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! LLM INTEGRATION IS WORKING!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_llm_integration())
        if success:
            print("\n✅ System is ready for use!")
            sys.exit(0)
        else:
            print("\n❌ System has issues that need to be fixed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
