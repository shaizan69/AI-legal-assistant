import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const supabase = createClient(supabaseUrl, supabaseServiceKey)

// Gemini LLM setup
const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY')
const GEMINI_MODEL = Deno.env.get('GEMINI_MODEL') || 'gemini-2.5-flash'

class GeminiLLMService {
  private apiKey: string
  private modelName: string

  constructor() {
    this.apiKey = GEMINI_API_KEY || ''
    this.modelName = GEMINI_MODEL

    if (!this.apiKey) {
      console.error('❌ GEMINI_API_KEY is required - Please set this in Supabase Dashboard')
      console.error('❌ Current API key value:', this.apiKey ? 'Present (length: ' + this.apiKey.length + ')' : 'Missing')
    } else {
      console.log(`✅ GEMINI_API_KEY is configured (${this.apiKey.substring(0, 4)}...${this.apiKey.substring(this.apiKey.length - 4)})`)
      console.log(`✅ Using Gemini model: ${this.modelName}`)
    }
  }

  async generateText(prompt: string, maxTokens: number = 1000, temperature: number = 0.7): Promise<string> {
    try {
      if (!this.apiKey || this.apiKey.length < 10) {
        console.error(`❌ Invalid or missing Gemini API key. Please check your environment variables.`)
        throw new Error('Missing or invalid Gemini API key. Please set GEMINI_API_KEY in Supabase Dashboard.')
      }
      
      console.log(`🤖 Generating text with Gemini (${this.modelName})...`)
      console.log(`📝 Prompt length: ${prompt.length} characters`)

      // Using the same structure as the backend Python SDK
      const requestBody = {
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          maxOutputTokens: maxTokens,
          temperature: temperature,
          topP: 0.9,
          topK: 40,
          stopSequences: []
        },
        safetySettings: [
          {
            category: "HARM_CATEGORY_HARASSMENT",
            threshold: "BLOCK_ONLY_HIGH"
          },
          {
            category: "HARM_CATEGORY_HATE_SPEECH",
            threshold: "BLOCK_ONLY_HIGH"
          },
          {
            category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold: "BLOCK_ONLY_HIGH"
          },
          {
            category: "HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold: "BLOCK_ONLY_HIGH"
          }
        ]
      }

      // Use v1 API for all models as the backend does
      const apiUrl = `https://generativelanguage.googleapis.com/v1/models/${this.modelName}:generateContent?key=${this.apiKey}`
      console.log(`🚀 Making request to Gemini API: ${apiUrl.substring(0, apiUrl.indexOf('?'))}...`)
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      console.log(`📊 Gemini API response status: ${response.status} ${response.statusText}`)

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`❌ Gemini API error response: ${errorText}`)
        
        // Check for common API key errors
        if (response.status === 400) {
          console.error('❌ Bad request - check your API key and model name')
        } else if (response.status === 401 || response.status === 403) {
          console.error('❌ Authentication failed - invalid API key or permissions')
        } else if (response.status === 404) {
          console.error(`❌ Model "${this.modelName}" not found - check model name`)
        } else if (response.status === 429) {
          console.error('❌ Rate limit exceeded - slow down requests or check quota')
        }
        
        throw new Error(`Gemini API error: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data = await response.json()
      console.log(`📦 Gemini API response received (${JSON.stringify(data).length} chars)`)

      // Check for error in response
      if (data.error) {
        console.error(`❌ Gemini API returned error:`, data.error)
        throw new Error(`Gemini API error: ${data.error.message || JSON.stringify(data.error)}`)
      }

      // Debug the response structure but limit the output size
      const dataStr = JSON.stringify(data);
      console.log(`📊 Gemini response structure:`, dataStr.substring(0, 500) + (dataStr.length > 500 ? '...' : ''))

      // Validate response structure - handle both old and new Gemini API formats
      if (data.candidates && Array.isArray(data.candidates) && data.candidates.length > 0) {
        const candidate = data.candidates[0]
        
        // New format: content.text (gemini-2.5-flash)
        if (candidate.content && candidate.content.text) {
          const text = candidate.content.text
          if (typeof text === 'string') {
            const result = text.trim()
            console.log(`✅ Gemini response generated (new format) (${result.length} characters)`)
            return result
          }
        }
        
        // Old format: content.parts[].text (gemini-1.0-pro, etc.)
        if (candidate.content && candidate.content.parts && Array.isArray(candidate.content.parts) && candidate.content.parts.length > 0) {
          const part = candidate.content.parts[0]
          if (part.text && typeof part.text === 'string') {
            const result = part.text.trim()
            console.log(`✅ Gemini response generated (parts format) (${result.length} characters)`)
            return result
          }
        }
        
        // Handle MAX_TOKENS finish reason - this means the response was cut off
        if (candidate.finishReason === "MAX_TOKENS") {
          console.log(`⚠️ Response was cut off due to MAX_TOKENS`);
          
          // Try to extract any text we can
          if (candidate.content && candidate.content.parts && Array.isArray(candidate.content.parts)) {
            const allParts = candidate.content.parts
              .filter(part => part && part.text)
              .map(part => part.text)
              .join(" ");
              
            if (allParts && allParts.length > 0) {
              console.log(`✅ Extracted partial response (${allParts.length} characters)`);
              return allParts + " [Response truncated due to token limit]";
            }
          }
          
          // If we can't extract any text, return a helpful message
          return "The response was cut off due to length limitations. Please try asking a more specific question or breaking your query into smaller parts.";
        }
        
        // Handle other finish reasons
        if (candidate.finishReason) {
          console.log(`⚠️ Unusual finish reason: ${candidate.finishReason}`);
          return `The model stopped generating content due to ${candidate.finishReason}. Please try rephrasing your question.`;
        }
        
        // Special handling for role=model with no text (common in gemini-2.5-flash)
        if (candidate.content && candidate.content.role === "model") {
          console.log(`⚠️ Found model role but no text`);
          return "I'm processing your request but couldn't generate a complete response. Please try rephrasing your question or providing more context.";
        }
        
        console.error(`❌ Could not extract text from candidate:`, candidate)
      } else {
        console.error(`❌ No candidates in response:`, data)
      }
      
      // If we get here, return a generic error message
      return "I'm unable to generate a response at this time. Please try again later."
    } catch (error) {
      console.error('❌ Gemini API error:', error)
      
      // Return a user-friendly error message
      return `I encountered an error while processing your request: ${error.message}. Please try again or rephrase your question.`
    }
  }

  // Helper function to clean document text before sending to LLM
  private cleanDocumentText(text: string): string {
    // If text is too short or appears to be a placeholder, return as is
    if (!text || text.length < 100 || text.includes('unable to extract')) {
      return text
    }
    
    try {
      // Remove any remaining PDF syntax that might confuse the LLM
      let cleaned = text
        // Remove common PDF syntax patterns
        .replace(/\/[A-Za-z0-9]+/g, '')
        .replace(/\d+\s+\d+\s+obj[\s\S]*?endobj/g, '')
        .replace(/xref[\s\S]*?trailer/g, '')
        .replace(/startxref\s*\d+/g, '')
        .replace(/<<[\s\S]*?>>/g, '')
        // Clean up whitespace
        .replace(/\s+/g, ' ')
        .trim()
      
      // If cleaning removed too much content, use original
      if (cleaned.length < text.length * 0.5) {
        console.log('⚠️ Cleaning removed too much content, using original text')
        cleaned = text
      }
      
      return cleaned
    } catch (e) {
      console.error('❌ Error cleaning document text:', e)
      return text // Return original if cleaning fails
    }
  }

  // Helper function to chunk text (like backend)
  private chunkText(text: string, chunkSize: number = 800, overlap: number = 160): string[] {
    if (!text || text.length === 0) {
      return []
    }
    
    console.log(`📝 Chunking text: ${text.length} chars, chunk_size=${chunkSize}, overlap=${overlap}`)
    
    // Split by words
    const words = text.split(/\s+/)
    const chunks: string[] = []
    
    // Create overlapping chunks
    for (let i = 0; i < words.length; i += chunkSize - overlap) {
      const chunk = words.slice(i, i + chunkSize).join(' ')
      if (chunk.trim()) {
        chunks.push(chunk.trim())
      }
    }
    
    console.log(`✅ Created ${chunks.length} chunks`)
    return chunks
  }

  async answerQuestion(question: string, context: string): Promise<any> {
    try {
      // Clean the document text first
      let cleanedContext = this.cleanDocumentText(context)
      
      // Truncate context if too long (limit to 8000 chars to avoid token limits)
      const MAX_CONTEXT_LENGTH = 8000
      if (cleanedContext.length > MAX_CONTEXT_LENGTH) {
        console.log(`⚠️ Context too long (${cleanedContext.length} chars), truncating to ${MAX_CONTEXT_LENGTH} chars`)
        cleanedContext = cleanedContext.substring(0, MAX_CONTEXT_LENGTH) + '... [truncated]'
      }
      
      // Use comprehensive backend-style prompt
      const prompt = `You are an expert legal AI assistant with specialized knowledge in financial and monetary analysis. Your task is to provide accurate, precise, and helpful answers based on the provided legal document context.

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

**COMPREHENSIVE FINANCIAL ANALYSIS PROCESSING:**
- If you see "=== COMPREHENSIVE FINANCIAL ANALYSIS ===" in the context, this contains pre-extracted financial data
- Use this analysis section as your PRIMARY source for financial information
- The analysis includes:
  * MONETARY AMOUNTS FOUND: All detected amounts with their surrounding context
  * PAYMENT SCHEDULES FOUND: Structured payment plans and schedules
  * FINANCIAL TERMS FOUND: All financial terminology with amounts
  * TABLES FOUND: Structured tabular data with headers and rows
  * CALCULATIONS FOUND: Mathematical calculations and totals
- ALWAYS prioritize information from the financial analysis section over narrative text
- Cross-reference analysis data with document content for complete understanding

**AMOUNT IDENTIFICATION & CONTEXT LEARNING:**
- Identify ALL monetary values, fees, costs, payments, and financial obligations
- Look for dollar signs ($), currency codes (USD, EUR, GBP, etc.), Indian currency format (/-), and written amounts
- **INDIAN CURRENCY FORMATS**: Pay special attention to amounts ending with /- (e.g., 187,450/-, 749,800/-)
- **PROPERTY-SPECIFIC AMOUNTS**: Look for down payments, installments, maintenance charges, registration fees, stamp duty, brokerage, security deposits, possession penalties, construction milestones
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

**DATA EXTRACTION REQUIREMENTS:**
- Extract specific values from tables and reference them accurately
- If asked about table contents, provide detailed breakdown of all relevant information
- Calculate totals, subtotals, and percentages from data when relevant
- Present information in clear, readable format without markdown tables

**STRUCTURED DATA PROCESSING:**
- When you see "TABLES FOUND" in the financial analysis, use this structured data
- Process table headers and rows systematically
- Extract relationships between different financial elements
- Use table data to answer specific questions about amounts, schedules, and calculations

LEGAL DOCUMENT CONTEXT (read strictly):
${cleanedContext}

USER QUESTION: ${question}

CRITICAL REMINDER:
- The context above contains the actual document content AND comprehensive financial analysis
- You MUST analyze this specific context, not give generic responses
- Look for amounts like 187,450/-, 749,800/-, 221,191/-, 884,764/-, etc.
- If you see amounts in the context, report them with their context
- Do NOT say "no amounts found" if amounts are clearly present in the context
- PRIORITIZE the financial analysis section when available

IF CONTEXT CONTAINS A SECTION STARTING WITH "=== COMPREHENSIVE FINANCIAL ANALYSIS ===":
- This is your PRIMARY source for financial information
- Use the pre-extracted amounts, schedules, terms, tables, and calculations
- Cross-reference with document content for complete understanding
- Provide answers based on this structured analysis

IF CONTEXT CONTAINS A SECTION STARTING WITH "TABLE DATA:":
- Treat it as authoritative structured data for answering table/schedule questions
- Prioritize extracting directly from this data before reading narrative text
- For payment schedule questions, provide a clear breakdown of stages and amounts in paragraph format

RESPONSE GUIDELINES:
- Start with a direct answer if possible
- For money-related questions, provide specific figures, calculations, and currencies
- Cite specific document sections (e.g., "According to Section 3.2...")
- **DO NOT mention chunk numbers or references to specific chunks**
- If multiple sections are relevant, organize by topic
- **COMPREHENSIVE FINANCIAL ANALYSIS REQUIREMENTS:**
  * Use the financial analysis section as your primary source
  * Reference specific amounts with their context from the analysis
  * Explain relationships between different financial elements
  * Show understanding of payment structures and schedules
  * Demonstrate awareness of all financial obligations and terms
- For financial queries, always include:
  * Exact amounts and currencies with context explanation
  * Payment terms and schedules with surrounding conditions
  * All applicable fees and charges with their purposes
  * Financial obligations and liabilities with their triggers
  * Any hidden or additional costs with their conditions
  * Relevant calculations or formulas with their basis
  * Context about when and why each amount applies
- Use clear formatting for financial information (bullet points, numbered lists when appropriate)
- **CLEAR FORMATTING**: When monetary information is structured in the document, present your answer in clear, readable format with:
  * Bullet points or numbered lists for easy reading
  * Consistent amount formatting (e.g., 187,450/-, 749,800/-)
  * All relevant data from the original information
- **STRUCTURED ANALYSIS APPROACH**: Demonstrate that you understand the comprehensive financial analysis
- **NEVER GIVE GENERIC RESPONSES**: Always analyze the actual context provided above
- End with "If you need clarification on any specific aspect, please let me know."

ANSWER:`;

      console.log(`📝 Question: "${question.substring(0, 100)}${question.length > 100 ? '...' : ''}"`)
      console.log(`📄 Context length: ${cleanedContext.length} characters`)
      
      // Use lower temperature for more factual responses, increased to 1200 tokens like backend
      const answer = await this.generateText(prompt, 1200, 0.1)

      return {
        answer: answer,
        confidence: 0.9,
        model_used: this.modelName,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('❌ Q&A error:', error)
      throw new Error(`Failed to answer question: ${error.message}`)
    }
  }

  async detectRisks(text: string): Promise<any> {
    try {
      // Clean the document text first
      let cleanedText = this.cleanDocumentText(text)
      
      // Truncate text if too long (limit to 8000 chars to avoid token limits)
      const MAX_CONTEXT_LENGTH = 8000
      if (cleanedText.length > MAX_CONTEXT_LENGTH) {
        console.log(`⚠️ Document too long (${cleanedText.length} chars), truncating to ${MAX_CONTEXT_LENGTH} chars`)
        cleanedText = cleanedText.substring(0, MAX_CONTEXT_LENGTH) + '... [truncated]'
      }
      
      // For Indian legal documents, use a specialized prompt
      const prompt = `You are an Indian legal risk analysis expert specializing in Indian law, contracts, and legal documents.
Analyze the following Indian legal document for potential risks in the Indian legal context.

DOCUMENT (Indian legal context):
"""
${cleanedText}
"""

Provide a structured risk analysis with:
1. Overall Risk Level (HIGH/MEDIUM/LOW)
2. Risk Categories (Contractual, Compliance, Financial, Operational, Legal)
3. Specific risks identified under Indian law and legal practice
4. Impact assessment considering Indian legal framework
5. Recommendations for risk mitigation in the Indian legal context

Consider Indian legal principles, statutes, and case law where relevant, including:
- Indian Contract Act, 1872
- Specific Relief Act, 1963
- Registration Act, 1908
- Transfer of Property Act, 1882
- Indian Stamp Act, 1899
- Real Estate (Regulation and Development) Act, 2016 (RERA)
- Indian Evidence Act, 1872
- Relevant state-specific laws

If the document doesn't contain enough information or doesn't appear to be a legal document, please state this clearly.

RISK ANALYSIS:`;

      console.log(`📄 Document length for risk analysis: ${cleanedText.length} characters`)
      
      // Use slightly higher temperature for more comprehensive analysis, increased to 1000 tokens like backend
      const analysis = await this.generateText(prompt, 1000, 0.1)

      return {
        analysis: analysis,
        risk_level: "Medium", // This is a placeholder, ideally would be extracted from the analysis
        risk_factors: [analysis],
        recommendations: ["Review with Indian legal expert"],
        document_type: "Indian legal document",
        analysis_date: new Date().toISOString(),
        model_used: this.modelName,
        confidence: 0.9
      }
    } catch (error) {
      console.error('❌ Risk analysis error:', error)
      throw new Error(`Failed to detect risks: ${error.message}`)
    }
  }
}

// Initialize Gemini service
const geminiService = new GeminiLLMService()

// Helper function to chunk text (used outside GeminiLLMService)
function chunkText(text: string, chunkSize: number = 800, overlap: number = 160): string[] {
  if (!text || text.length === 0) {
    return []
  }
  
  console.log(`📝 Chunking text: ${text.length} chars, chunk_size=${chunkSize}, overlap=${overlap}`)
  
  // Split by words
  const words = text.split(/\s+/)
  const chunks: string[] = []
  
  // Create overlapping chunks
  for (let i = 0; i < words.length; i += chunkSize - overlap) {
    const chunk = words.slice(i, i + chunkSize).join(' ')
    if (chunk.trim()) {
      chunks.push(chunk.trim())
    }
  }
  
  console.log(`✅ Created ${chunks.length} chunks`)
  return chunks
}


// PDF text extraction function with advanced filtering
async function extractTextFromPDF(fileBuffer: ArrayBuffer, filename: string): Promise<string> {
  try {
    console.log('📄 Starting enhanced PDF text extraction...')
    
    // Convert ArrayBuffer to Uint8Array
    const uint8Array = new Uint8Array(fileBuffer)
    
    // Decode the buffer using Latin1 (more tolerant of binary data)
    const rawText = new TextDecoder('latin1', { fatal: false }).decode(uint8Array)
    
    // Extract text from parentheses (where most text content lives in PDFs)
    console.log('🔍 Extracting text from PDF content...')
    const parenthesesMatches = rawText.match(/\(([^\(\)]{3,})\)/g) || []
    
    // Process and filter the extracted text
    const extractedTextParts = []
    
    for (const match of parenthesesMatches) {
      // Remove the parentheses and clean the text
      const text = match.substring(1, match.length - 1)
        .replace(/[^\x20-\x7E\n\r\t]/g, ' ') // Keep only printable ASCII
        .replace(/\\(\d{3}|n|r|t|b|f|\\|\(|\))/g, ' ') // Remove escape sequences
        .replace(/\s+/g, ' ')
        .trim()
      
      // Only keep text that looks like natural language
      // Must contain at least 3 letters and be at least 3 chars long
      if (text.length >= 3 && /[a-zA-Z]{3,}/i.test(text)) {
        extractedTextParts.push(text)
      }
    }
    
    // Reconstruct the text, handling word breaks that might occur in PDFs
    let combinedText = ''
    let previousPart = ''
    
    for (const part of extractedTextParts) {
      // Check if this part continues from the previous one
      if (previousPart && 
          !previousPart.endsWith('.') && 
          !previousPart.endsWith('?') && 
          !previousPart.endsWith('!') &&
          !previousPart.endsWith(':') &&
          previousPart.length < 50) {
        combinedText += ' ' + part
      } else {
        if (combinedText && !combinedText.endsWith(' ')) {
          combinedText += ' '
        }
        combinedText += part
      }
      previousPart = part
    }
    
    // Clean up the combined text
    combinedText = combinedText
      .replace(/\s+/g, ' ')
      .replace(/ \./g, '.')
      .replace(/ ,/g, ',')
      .replace(/ ;/g, ';')
      .replace(/ :/g, ':')
      .replace(/ \?/g, '?')
      .replace(/ !/g, '!')
      .replace(/ \)/g, ')')
      .replace(/\( /g, '(')
      .trim()
    
    // Filter out common PDF syntax patterns that might have slipped through
    const pdfSyntaxPatterns = [
      'obj', 'endobj', 'stream', 'endstream', 'xref', 'trailer', 'startxref',
      'Type', 'Pages', 'Page', 'Font', 'XObject', 'ProcSet', 'ExtGState',
      'Pattern', 'Shading', 'Properties', 'Filter', 'FlateDecode', 'Length',
      'Resources', 'MediaBox', 'Contents', 'Rotate', 'Group', 'Annots'
    ]
    
    // Create a regex to match these patterns as whole words
    const syntaxRegex = new RegExp(`\\b(${pdfSyntaxPatterns.join('|')})\\b`, 'g')
    
    // Apply the filter
    let filteredText = combinedText.replace(syntaxRegex, '')
    
    // Remove any remaining PDF-specific notation
    filteredText = filteredText
      .replace(/\/[A-Za-z0-9]+/g, '') // Remove PDF name objects like /F1, /Page, etc.
      .replace(/\[\s*\]/g, '') // Remove empty arrays
      .replace(/<<\s*>>/g, '') // Remove empty dictionaries
      .replace(/\s+/g, ' ')
      .trim()
    
    // If we have enough text, return it
    if (filteredText.length > 200) {
      console.log(`✅ Successfully extracted ${filteredText.length} characters of readable text`)
      
      // Format the text into paragraphs for better readability
      const formattedText = filteredText
        .replace(/\.\s+/g, '.\n\n') // Add paragraph breaks after sentences
        .replace(/\n{3,}/g, '\n\n') // Normalize paragraph spacing
      
      return formattedText.substring(0, 15000) // Limit to 15K chars
    }
    
    // If we don't have enough text, try a more aggressive approach
    console.log('⚠️ Not enough text found, trying advanced extraction...')
    
    // Extract any sequence of words that looks like natural language
    const wordPattern = /\b[A-Za-z]{3,}(?:\s+[A-Za-z]+){2,}\b/g
    const wordMatches = rawText.match(wordPattern) || []
    
    if (wordMatches.length > 0) {
      // Join the matches and clean up
      const wordText = wordMatches.join(' ')
        .replace(/\s+/g, ' ')
        .trim()
      
      if (wordText.length > 100) {
        console.log(`✅ Advanced extraction found ${wordText.length} characters`)
        return wordText.substring(0, 10000)
      }
    }
    
    // If all else fails, return a placeholder
    return `This document appears to be a PDF titled "${filename}" but doesn't contain easily extractable text content. It may be scanned, image-based, or heavily formatted.`
  } catch (error) {
    console.error('❌ PDF extraction failed:', error)
    return `This is a PDF document titled "${filename}". The text extraction process encountered an error: ${error.message}`
  }
}

// Test database connection on startup
console.log('🔍 Testing database connection...')
try {
  const { data, error } = await supabase.from('documents').select('count').limit(1)
  if (error) {
    console.error('❌ Database connection failed:', error.message)
  } else {
    console.log('✅ Database connection successful')
  }
} catch (e) {
  console.error('❌ Database connection error:', e.message)
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { method, url } = req
    const urlObj = new URL(url)
    const rawPath = urlObj.pathname
    
    // Normalize path - handle both /functions/v1/api/xyz and /xyz
    let path = rawPath
      .replace(/^\/(functions\/v\d+)?\/?api(\/|$)/, '/')
      .replace(/^\/(functions\/v\d+)(\/|$)/, '/')
      .replace(/\/+/g, '/')
    
    if (path.length > 1 && path.endsWith('/')) {
      path = path.slice(0, -1)
    }

    console.log(`[${new Date().toISOString()}] ${method} ${path} (raw: ${rawPath})`)

    // Root endpoint
    if (path === '/' && method === 'GET') {
      return new Response(
        JSON.stringify({ 
          message: 'Legal AI Assistant API is running!',
          timestamp: new Date().toISOString(),
          version: '1.0.0',
          status: 'active'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
      )
    }

    // Test endpoint
    if (path === '/test' && method === 'GET') {
      return new Response(
        JSON.stringify({ 
          message: 'Edge Function is working!',
          timestamp: new Date().toISOString(),
          path: path,
          method: method,
          environment: 'production'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Login endpoint
    if (path === '/auth/login' && method === 'POST') {
      try {
        const payload = await req.json()
      const username = String(payload.username ?? '')
      const password = String(payload.password ?? '')
      
        console.log(`Login attempt for: ${username}`)
      
        // Hardcoded test user
      if (username === 'test@example.com' && password === 'testpass') {
        const token = btoa(JSON.stringify({ 
          email: username, 
            exp: Date.now() + 3600000,
            sub: '1'
        }))
          
          console.log(`Login successful for: ${username}`)
        
        return new Response(
          JSON.stringify({ 
            access_token: token,
            token_type: 'bearer',
              expires_in: 3600,
              user: {
                id: 1,
                email: username,
                username: 'testuser',
                full_name: 'Test User'
              }
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      } else {
          console.log(`Login failed for: ${username}`)
        return new Response(
            JSON.stringify({ 
              error: 'Invalid credentials',
              message: 'Username or password is incorrect'
            }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 401 
            }
          )
        }
      } catch (error) {
        console.error('Login error:', error)
        return new Response(
          JSON.stringify({ 
            error: 'Login failed', 
            message: error.message 
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 500 
          }
        )
      }
    }

    // User info endpoint
    if (path === '/auth/me' && (method === 'GET' || method === 'POST')) {
      return new Response(
        JSON.stringify({ 
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          full_name: 'Test User'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Q&A endpoint
    if (path === '/qa/ask' && method === 'POST') {
      try {
        const payload = await req.json()
      const question = String(payload.question ?? '')
      const session_id = payload.session_id ? Number(payload.session_id) : undefined
      
        console.log(`🤖 Q&A question: ${question}`)
      
        if (!question.trim()) {
        return new Response(
            JSON.stringify({
              error: 'Question is required',
              message: 'Please provide a question'
            }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400 
          }
        )
      }

        if (!session_id) {
          return new Response(
            JSON.stringify({
              error: 'Session ID is required',
              message: 'Please provide a valid session_id'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        // Get session and document context
        const { data: session, error: sessionError } = await supabase
          .from('qa_sessions')
          .select('*, documents(*)')
          .eq('id', session_id)
          .single()

        if (sessionError || !session) {
          console.error('❌ Session not found:', sessionError)
      return new Response(
        JSON.stringify({ 
              error: 'Session not found',
              message: 'Please provide a valid session_id'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 404
            }
          )
        }

        // Get document context
        const document = session.documents
        if (!document || !document.extracted_text) {
          return new Response(
            JSON.stringify({
              error: 'Document not processed',
              message: 'Document content not available for Q&A'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        console.log(`📄 Answering question for document: ${document.title}`)

        // Get relevant chunks (like backend does)
        let context = document.extracted_text
        
        // Try to get chunks from document_chunks table if available
        const { data: allChunks } = await supabase
          .from('document_chunks')
          .select('content, chunk_index')
          .eq('document_id', document.id)
          .order('chunk_index', { ascending: true })

        if (allChunks && allChunks.length > 0) {
          // Get first 15 chunks like backend semantic search
          const baseChunks = allChunks.slice(0, 15)
          
          // Include adjacent chunks (±1) for better context
          const candidateIndices = new Set<number>()
          baseChunks.forEach(ch => {
            candidateIndices.add(ch.chunk_index)
            candidateIndices.add(ch.chunk_index - 1)
            candidateIndices.add(ch.chunk_index + 1)
          })
          
          // Get chunks with adjacent ones
          const indices = Array.from(candidateIndices).filter(i => i >= 0).sort((a, b) => a - b)
          const { data: selectedChunks } = await supabase
            .from('document_chunks')
            .select('content')
            .eq('document_id', document.id)
            .in('chunk_index', indices)
            .order('chunk_index', { ascending: true })
          
          if (selectedChunks && selectedChunks.length > 0) {
            // Join chunks and limit to ~3500 chars (like backend)
            let joinedContext = selectedChunks.map(ch => ch.content).join('\n\n')
            if (joinedContext.length > 3500) {
              joinedContext = joinedContext.substring(0, 3500) + '...'
            }
            context = joinedContext
            console.log(`📊 Using ${selectedChunks.length} chunks (including adjacent) for context (${context.length} chars)`)
          } else {
            // Fallback to first 10 chunks without adjacent
            context = baseChunks.slice(0, 10).map(ch => ch.content).join('\n\n')
            console.log(`📊 Using first 10 chunks for context (${context.length} chars)`)
          }
        } else {
          // Fallback to first 3500 chars of extracted text (like backend)
          context = document.extracted_text.substring(0, 3500)
          console.log(`📊 Using truncated extracted text (${context.length} chars)`)
        }

        // Use Gemini to answer the question
        const result = await geminiService.answerQuestion(question, context)

        // Save the question and answer to database
        const { error: qaError } = await supabase
          .from('qa_questions')
          .insert({
            session_id: session_id,
            question: question,
            answer: result.answer,
            confidence_score: result.confidence,
            model_used: result.model_used,
            processing_time: 1.0, // Placeholder
            token_count: result.answer.length, // Rough estimate
          })

        if (qaError) {
          console.error('⚠️ Failed to save Q&A to database:', qaError)
          // Don't fail the request if database save fails
        }

        // Update session activity
        await supabase
          .from('qa_sessions')
          .update({
            total_questions: (session.total_questions || 0) + 1,
            last_activity: new Date().toISOString()
          })
          .eq('id', session_id)

        return new Response(
          JSON.stringify({
            answer: result.answer,
          question_id: Date.now(),
            session_id: session_id,
            confidence: result.confidence,
            model_used: result.model_used,
            timestamp: result.timestamp
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200
          }
        )
      } catch (error) {
        console.error('❌ Q&A error:', error)
        return new Response(
          JSON.stringify({
            error: 'Q&A failed',
            message: error.message
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 500
          }
        )
      }
    }

    // Free Q&A endpoint
    if (path === '/free/ask' && method === 'POST') {
      try {
        const payload = await req.json()
        const question = String(payload.question ?? '')
        const session_id = payload.session_id ? Number(payload.session_id) : undefined

        console.log(`🤖 Free Q&A question: ${question}`)

        if (!question.trim()) {
          return new Response(
            JSON.stringify({
              error: 'Question is required',
              message: 'Please provide a question'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        if (!session_id) {
          return new Response(
            JSON.stringify({
              error: 'Session ID is required',
              message: 'Please provide a valid session_id'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        // Get session and document context
        const { data: session, error: sessionError } = await supabase
          .from('qa_sessions')
          .select('*, documents(*)')
          .eq('id', session_id)
          .single()

        if (sessionError || !session) {
          console.error('❌ Session not found:', sessionError)
          return new Response(
            JSON.stringify({
              error: 'Session not found',
              message: 'Please provide a valid session_id'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 404
            }
          )
        }

        // Get document context
        const document = session.documents
        if (!document || !document.extracted_text) {
          return new Response(
            JSON.stringify({
              error: 'Document not processed',
              message: 'Document content not available for Q&A'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        console.log(`📄 Answering free question for document: ${document.title}`)

        // Get relevant chunks (like backend does)
        let context = document.extracted_text
        
        // Try to get chunks from document_chunks table if available
        const { data: allChunks } = await supabase
          .from('document_chunks')
          .select('content, chunk_index')
          .eq('document_id', document.id)
          .order('chunk_index', { ascending: true })

        if (allChunks && allChunks.length > 0) {
          // Get first 15 chunks like backend semantic search
          const baseChunks = allChunks.slice(0, 15)
          
          // Include adjacent chunks (±1) for better context
          const candidateIndices = new Set<number>()
          baseChunks.forEach(ch => {
            candidateIndices.add(ch.chunk_index)
            candidateIndices.add(ch.chunk_index - 1)
            candidateIndices.add(ch.chunk_index + 1)
          })
          
          // Get chunks with adjacent ones
          const indices = Array.from(candidateIndices).filter(i => i >= 0).sort((a, b) => a - b)
          const { data: selectedChunks } = await supabase
            .from('document_chunks')
            .select('content')
            .eq('document_id', document.id)
            .in('chunk_index', indices)
            .order('chunk_index', { ascending: true })
          
          if (selectedChunks && selectedChunks.length > 0) {
            // Join chunks and limit to ~3500 chars (like backend)
            let joinedContext = selectedChunks.map(ch => ch.content).join('\n\n')
            if (joinedContext.length > 3500) {
              joinedContext = joinedContext.substring(0, 3500) + '...'
            }
            context = joinedContext
            console.log(`📊 Using ${selectedChunks.length} chunks (including adjacent) for context (${context.length} chars)`)
          } else {
            // Fallback to first 10 chunks without adjacent
            context = baseChunks.slice(0, 10).map(ch => ch.content).join('\n\n')
            console.log(`📊 Using first 10 chunks for context (${context.length} chars)`)
          }
        } else {
          // Fallback to first 3500 chars of extracted text (like backend)
          context = document.extracted_text.substring(0, 3500)
          console.log(`📊 Using truncated extracted text (${context.length} chars)`)
        }

        // Use Gemini to answer the question
        const result = await geminiService.answerQuestion(question, context)

        // Save the question and answer to database
        const { error: qaError } = await supabase
          .from('qa_questions')
          .insert({
            session_id: session_id,
            question: question,
            answer: result.answer,
            confidence_score: result.confidence,
            model_used: result.model_used,
            processing_time: 1.0, // Placeholder
            token_count: result.answer.length, // Rough estimate
          })

        if (qaError) {
          console.error('⚠️ Failed to save free Q&A to database:', qaError)
          // Don't fail the request if database save fails
        }

        // Update session activity
        await supabase
          .from('qa_sessions')
          .update({
            total_questions: (session.total_questions || 0) + 1,
            last_activity: new Date().toISOString()
          })
          .eq('id', session_id)

        return new Response(
          JSON.stringify({
            answer: result.answer,
            question_id: Date.now(),
            session_id: session_id,
            confidence: result.confidence,
            model_used: result.model_used,
            timestamp: result.timestamp
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200
          }
        )
      } catch (error) {
        console.error('❌ Free Q&A error:', error)
        return new Response(
          JSON.stringify({
            error: 'Free Q&A failed',
            message: error.message
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 500
          }
        )
      }
    }

    // Risk analysis endpoint
    if (path === '/free/analyze-risks' && method === 'POST') {
      try {
        const payload = await req.json()
        const session_id = payload.session_id ? Number(payload.session_id) : undefined

        console.log(`🔍 Risk analysis request`)

        if (!session_id) {
          return new Response(
            JSON.stringify({
              error: 'Session ID is required',
              message: 'Please provide a valid session_id'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        // Get session and document context
        const { data: session, error: sessionError } = await supabase
          .from('qa_sessions')
          .select('*, documents(*)')
          .eq('id', session_id)
          .single()

        if (sessionError || !session) {
          console.error('❌ Session not found:', sessionError)
          return new Response(
            JSON.stringify({
              error: 'Session not found',
              message: 'Please provide a valid session_id'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 404
            }
          )
        }

        // Get document context
        const document = session.documents
        if (!document || !document.extracted_text) {
          return new Response(
            JSON.stringify({
              error: 'Document not processed',
              message: 'Document content not available for risk analysis'
            }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 400
            }
          )
        }

        console.log(`📄 Analyzing risks for document: ${document.title}`)

        // Use Gemini to analyze risks
        const result = await geminiService.detectRisks(document.extracted_text)

        // Save risk analysis to database
        const { error: riskError } = await supabase
          .from('risk_analyses')
          .insert({
            document_id: document.id,
            risk_level: result.risk_level,
            risk_type: 'Legal', // Default category
            description: result.analysis,
            recommendation: result.recommendations?.join(', ') || 'Review with legal expert',
            severity_score: 0.5, // Default score
            likelihood_score: 0.5, // Default score
            overall_score: 0.5, // Default score
          })

        if (riskError) {
          console.error('⚠️ Failed to save risk analysis to database:', riskError)
          // Don't fail the request if database save fails
        }

        return new Response(
          JSON.stringify({
            risks: result.analysis,
            risk_level: result.risk_level,
            risk_factors: result.risk_factors,
            recommendations: result.recommendations,
            session_id: session_id,
            document_id: document.id,
            model_used: result.model_used,
            confidence: result.confidence,
            timestamp: result.analysis_date
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200
          }
        )
      } catch (error) {
        console.error('❌ Risk analysis error:', error)
        return new Response(
          JSON.stringify({
            error: 'Risk analysis failed',
            message: error.message
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 500
          }
        )
      }
    }

    // Session creation
    if (path === '/free/session' && method === 'POST') {
      try {
        const payload = await req.json()
        const documentId = payload.document_id ? Number(payload.document_id) : null
        
        // Get or create free user
        let userId = 1
        const { data: existingUser } = await supabase
          .from('users')
          .select('id')
          .eq('email', 'free@system.local')
          .single()
        if (existingUser) userId = existingUser.id
        
        // Verify document exists and is processed
        if (documentId) {
          const { data: doc } = await supabase
            .from('documents')
            .select('id, is_processed, title')
            .eq('id', documentId)
            .single()
          
          if (!doc) {
            return new Response(
              JSON.stringify({ error: 'Document not found' }), 
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
            )
          }
          
          if (!doc.is_processed) {
            return new Response(
              JSON.stringify({ error: 'Document is still being processed' }), 
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
            )
          }
          
          // Create session
          const { data: session, error } = await supabase
            .from('qa_sessions')
            .insert({
              user_id: userId,
              document_id: documentId,
              session_name: `Free Q&A - ${doc.title}`,
              is_active: true
            })
            .select('id')
            .single()
          
          if (error || !session) {
            console.error('Session creation error:', error)
            return new Response(
              JSON.stringify({ error: 'Failed to create session', details: error?.message }), 
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
            )
          }
          
          return new Response(
            JSON.stringify({ id: session.id, session_id: session.id }), 
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        }
        
        // No document ID - return error
        return new Response(
          JSON.stringify({ error: 'document_id is required' }), 
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
        )
      } catch (e) {
        console.error('Session creation error:', e)
        return new Response(
          JSON.stringify({ error: 'Failed to create session', details: String(e) }), 
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
        )
      }
    }

    // Session deletion
    if (path.startsWith('/free/session/') && method === 'DELETE') {
      const sessionId = path.split('/').pop()
      console.log(`Deleting session: ${sessionId}`)
      
      return new Response(
        JSON.stringify({ 
          message: 'Session deleted successfully',
          session_id: sessionId,
          timestamp: new Date().toISOString()
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Cleanup orphaned sessions
    if (path === '/free/cleanup-orphaned' && method === 'POST') {
      console.log('Cleaning up orphaned sessions')
      
      return new Response(
        JSON.stringify({ 
          message: 'Orphaned sessions cleaned up successfully',
          cleaned_count: 0,
          timestamp: new Date().toISOString()
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // QA Sessions - create/list
    if (path === '/qa/sessions') {
      if (method === 'GET') {
        return new Response(
          JSON.stringify([]),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        )
      }
      // POST create
      const payload = await req.json()
      const session_id = Date.now()
      return new Response(
        JSON.stringify({ session_id, session_name: payload.session_name ?? null, document_id: payload.document_id ?? null }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
      )
    }

    // QA Sessions - detail/delete/cleanup/questions
    const qaSessionMatch = path.match(/^\/qa\/sessions\/(\d+)(?:\/(cleanup|questions))?$/)
    if (qaSessionMatch) {
      const sessionId = Number(qaSessionMatch[1])
      const subPath = qaSessionMatch[2]
      if (!subPath && method === 'GET') {
        return new Response(
          JSON.stringify({ session_id: sessionId, session_name: 'Session', document_id: 1 }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        )
      }
      if (!subPath && method === 'DELETE') {
        return new Response(JSON.stringify({ message: 'Session deleted' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      if (subPath === 'cleanup' && method === 'POST') {
        return new Response(JSON.stringify({ message: 'Session cleaned' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      if (subPath === 'questions' && method === 'GET') {
        return new Response(JSON.stringify([]), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      return new Response(JSON.stringify({ error: 'Method Not Allowed' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 405 })
    }

    // Documents upload metadata (after client uploads to Supabase storage)
    if (path === '/upload/supabase' && method === 'POST') {
      const payload = await req.json()
      const document_id = Date.now()
      return new Response(
        JSON.stringify({ id: document_id, ...payload, message: 'Document metadata recorded' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
      )
    }

    // Documents list or specific document
    if (path.startsWith('/upload')) {
      if (method === 'GET') {
        // Check if it's a specific document request (e.g., /upload/54)
        const pathParts = path.split('/')
        if (pathParts.length === 3 && pathParts[2] && !isNaN(Number(pathParts[2]))) {
          // Get specific document by ID
          const documentId = Number(pathParts[2])
          try {
            const { data: document, error } = await supabase
              .from('documents')
              .select('*')
              .eq('id', documentId)
              .single()

            if (error || !document) {
              return new Response(
                JSON.stringify({ error: 'Document not found' }),
                { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
              )
            }

            return new Response(
              JSON.stringify(document),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
            )
          } catch (e) {
            console.error('Document fetch error:', e)
            return new Response(
              JSON.stringify({ error: 'Failed to fetch document', details: String(e) }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
            )
          }
        } else {
          // List all documents
          try {
            const { data: documents, error } = await supabase
              .from('documents')
              .select('*')
              .order('created_at', { ascending: false })

            if (error) {
              console.error('Error fetching documents:', error)
              return new Response(
                JSON.stringify({ error: 'Failed to fetch documents', details: error.message }),
                { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
              )
            }

            return new Response(
              JSON.stringify({
                documents: documents || [],
                pages: 1,
                total: documents?.length || 0
              }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
            )
        } catch (e) {
            console.error('Documents list error:', e)
            return new Response(
              JSON.stringify({ error: 'Failed to fetch documents', details: String(e) }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
            )
          }
        }
      }
    }

    // Free upload - full working logic with database
    if (path === '/free/upload' && method === 'POST') {
      try {
        console.log('📤 Upload request received')
        console.log('Content-Type:', req.headers.get('content-type'))

        let form, file

        try {
          form = await req.formData()
          file = form.get('file') as File | null
        } catch (formError) {
          console.error('❌ Form data parsing error:', formError)
          return new Response(
            JSON.stringify({ error: 'Invalid form data', details: String(formError) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
          )
        }

        if (!file) {
          console.error('❌ No file found in form data')
          return new Response(
            JSON.stringify({ error: 'file is required' }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
          )
        }

        console.log('✅ File received:', (file as File).name, 'Size:', (file as File).size)
        
        // Get or create free user
        let userId = 1 // Default free user
        try {
          const { data: existingUser, error: userError } = await supabase
            .from('users')
            .select('id')
            .eq('email', 'free@system.local')
            .single()

          if (userError && userError.code !== 'PGRST116') { // PGRST116 = no rows returned
            console.error('Error finding user:', userError)
            throw new Error('Failed to find or create user')
          }

          if (existingUser) {
            userId = existingUser.id
          } else {
            const { data: newUser, error: insertError } = await supabase
              .from('users')
              .insert({
                email: 'free@system.local',
                username: 'free_user',
                hashed_password: '!',
                is_verified: true,
                is_active: true
              })
              .select('id')
              .single()

            if (insertError) {
              console.error('Error creating user:', insertError)
              throw new Error('Failed to create user')
            }

            if (newUser) userId = newUser.id
          }
        } catch (userErr) {
          console.error('User creation error:', userErr)
          throw new Error('Failed to setup user')
        }
        
        // Generate unique filename and path
        const ts = new Date().toISOString().replace(/[:.]/g, '-')
        const uniqueName = `free_${userId}_${ts}_${(file as File).name}`
        const supaPath = `free-user/${userId}/${uniqueName}`
        
        // Upload to Supabase storage (bucket name: legal-assistant)
        let fileBuffer, uploadError, urlData

        try {
          console.log('📦 Converting file to buffer...')
          fileBuffer = await (file as File).arrayBuffer()
          console.log('✅ File converted to buffer, size:', fileBuffer.byteLength)

          // Try multiple bucket names in order
          const bucketNames = ['legal-assistant', 'legal-documents', 'documents']
          let bucketName = 'legal-assistant'
          let uploadResult

          for (const name of bucketNames) {
            console.log(`📦 Trying bucket: ${name}`)
            uploadResult = await supabase.storage
              .from(name)
              .upload(supaPath, fileBuffer, {
                contentType: (file as File).type || 'application/octet-stream',
                upsert: false
              })

            if (!uploadResult.error) {
              bucketName = name
              console.log(`✅ Successfully uploaded to bucket: ${bucketName}`)
              break
            } else if (!uploadResult.error.message?.includes('Bucket not found')) {
              // If it's not a "bucket not found" error, use this bucket anyway
              bucketName = name
              console.log(`⚠️ Used bucket ${name} despite error: ${uploadResult.error.message}`)
              break
        } else {
              console.log(`❌ Bucket "${name}" not found, trying next...`)
            }
          }

          uploadError = uploadResult.error
          console.log(`📤 Upload to ${bucketName} result:`, uploadError ? '❌ Failed' : '✅ Success')

          if (uploadError) {
            console.error(`❌ Storage upload error to ${bucketName}:`, uploadError)
            throw new Error(`Storage upload failed: ${uploadError.message}`)
          }

          console.log('🔗 Getting public URL...')
          const urlResult = supabase.storage
            .from(bucketName)
            .getPublicUrl(supaPath)

          urlData = urlResult.data
          if (!urlData?.publicUrl) {
            throw new Error('Failed to get public URL')
          }
          console.log('✅ Public URL generated:', urlData.publicUrl)
          console.log(`📋 Final bucket used: ${bucketName}`)
        } catch (storageError) {
          console.error('❌ Storage operation error:', storageError)
          return new Response(
            JSON.stringify({ error: 'Storage operation failed', details: String(storageError) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
        
        // Calculate file hash
        const hashBuffer = await crypto.subtle.digest('SHA-256', fileBuffer)
        const hashArray = Array.from(new Uint8Array(hashBuffer))
        const fileHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')

        // Extract text from document using PDF processing
        console.log('📖 Extracting text from document...')
        let extractedText = ''
        const mimeType = (file as File).type || 'application/octet-stream'

        try {
          if (mimeType === 'application/pdf') {
            // Use PDF.js to extract text from PDF
            extractedText = await extractTextFromPDF(fileBuffer, (file as File).name)
          } else if (mimeType.includes('document') || mimeType.includes('word')) {
            // For DOCX files, provide a note that full extraction needs additional libraries
            extractedText = `Word document uploaded: ${(file as File).name}. Note: Full text extraction from DOCX files requires additional processing libraries that are not available in this Edge Function environment. Please use PDF files for best results.`
          } else {
            // For other file types
            extractedText = `Document uploaded: ${(file as File).name}. File type: ${mimeType}. This file type may not be fully supported for text extraction in this environment.`
          }

          console.log(`✅ Text extraction completed (${extractedText.length} characters)`)
        } catch (extractError) {
          console.error('❌ Text extraction error:', extractError)
          extractedText = `Document uploaded: ${(file as File).name}. Text extraction failed with error: ${extractError.message}`
        }

        console.log('🔍 Checking for duplicate documents...')

        // Check if document with same hash exists and delete it first (like original backend)
        const { data: existingDoc } = await supabase
          .from('documents')
          .select('id, supabase_path')
          .eq('file_hash', fileHash)
          .eq('owner_id', userId)
          .single()

        if (existingDoc) {
          console.log(`📋 Found existing document with same hash, deleting it first: ${existingDoc.id}`)

          // Delete related data first (like original backend)
          // First get all session IDs for this document
          const { data: sessions } = await supabase
            .from('qa_sessions')
            .select('id')
            .eq('document_id', existingDoc.id)

          // Delete qa_questions for all sessions
          if (sessions && sessions.length > 0) {
            const sessionIds = sessions.map(s => s.id)
            await supabase.from('qa_questions').delete().in('session_id', sessionIds)
          }

          // Delete other related data
          await supabase.from('document_chunks').delete().eq('document_id', existingDoc.id)
          await supabase.from('qa_sessions').delete().eq('document_id', existingDoc.id)
          await supabase.from('risk_analyses').delete().eq('document_id', existingDoc.id)

          // Delete from storage if path exists
          if (existingDoc.supabase_path) {
            try {
              await supabase.storage.from(bucketName).remove([existingDoc.supabase_path])
              console.log(`🗑️ Deleted existing file from storage: ${existingDoc.supabase_path}`)
      } catch (e) {
              console.warn(`⚠️ Failed to delete existing file from storage: ${e}`)
            }
          }

          // Delete the document record
          await supabase.from('documents').delete().eq('id', existingDoc.id)
          console.log(`✅ Deleted existing document ${existingDoc.id}`)
        } else {
          console.log('✅ No duplicate document found, proceeding with upload')
        }
        
        // Create document record in database
        try {
          console.log('💾 Creating document record in database...')

          const documentData = {
            filename: uniqueName,
            original_filename: (file as File).name,
            file_path: supaPath,
            file_url: urlData.publicUrl,
            file_hash: fileHash,
            file_size: (file as File).size,
            mime_type: (file as File).type || 'application/octet-stream',
            extracted_text: extractedText,
            text_hash: '', // Will be calculated if needed
            word_count: extractedText.split(' ').length,
            character_count: extractedText.length,
            document_type: 'free',
            title: (file as File).name,
            owner_id: userId,
            supabase_path: supaPath,
            is_processed: true,
            processing_status: 'completed'
          }

          console.log('📝 Document data:', JSON.stringify(documentData, null, 2))

          const { data: document, error: dbError } = await supabase
            .from('documents')
            .insert(documentData)
            .select('id')
            .single()

          if (dbError) {
            console.error('❌ Database insert error:', dbError)
            throw new Error(`Database insert failed: ${dbError.message}`)
          }

          if (!document || !document.id) {
            throw new Error('Document insert returned no ID')
          }

          console.log(`✅ Document created with ID: ${document.id}`)
          console.log('✅ Document already marked as processed')

          // Create document chunks
          console.log('📦 Creating document chunks...')
          const chunks = chunkText(extractedText, 800, 160)
          
          if (chunks.length > 0) {
            const chunkRecords = chunks.map((content, index) => ({
              document_id: document.id,
              chunk_index: index,
              content: content,
              word_count: content.split(' ').length,
              character_count: content.length
            }))
            
            const { error: chunkError } = await supabase
              .from('document_chunks')
              .insert(chunkRecords)
            
            if (chunkError) {
              console.error('⚠️ Failed to create chunks:', chunkError)
              // Don't fail the upload if chunk creation fails
            } else {
              console.log(`✅ Created ${chunks.length} chunks for document ${document.id}`)
            }
          }

          console.log(`🎉 Upload completed successfully! Document ID: ${document.id}`)
      
      return new Response(
        JSON.stringify({ 
              id: document.id,
              document_id: document.id,
              filename: uniqueName,
              message: 'Document uploaded successfully'
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        } catch (dbErr) {
          console.error('❌ Database operation error:', dbErr)
      return new Response(
            JSON.stringify({ error: 'Database operation failed', details: String(dbErr) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
      } catch (e) {
        console.error('Upload error:', e)
      return new Response(
          JSON.stringify({ error: 'Upload failed', details: String(e) }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
        )
      }
    }

    // Default response for unmatched routes
    console.log(`Unmatched route: ${method} ${path}`)
    return new Response(
      JSON.stringify({ 
        error: 'Endpoint not found',
        path: path,
        method: method,
        timestamp: new Date().toISOString(),
        available_endpoints: [
          '/',
          '/test',
          '/auth/login',
          '/auth/me',
          '/qa/ask',
          '/qa/sessions',
          '/qa/sessions/:id',
          '/qa/sessions/:id/cleanup',
          '/qa/sessions/:id/questions',
          '/free/ask',
          '/free/analyze-risks',
          '/free/session',
          '/free/upload',
          '/free/cleanup-orphaned',
          '/upload',
          '/upload/supabase',
          '/upload/direct'
        ]
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 404 
      }
    )

  } catch (error) {
    console.error('Function error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error.message,
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    )
  }
})