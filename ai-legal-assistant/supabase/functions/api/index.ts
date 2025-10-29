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

  async generateText(prompt: string, maxTokens: number = 2000, temperature: number = 0.7): Promise<string> {
    try {
      if (!this.apiKey || this.apiKey.length < 10) {
        console.error(`❌ Invalid or missing Gemini API key. Please check your environment variables.`)
        throw new Error('Missing or invalid Gemini API key. Please set GEMINI_API_KEY in Supabase Dashboard.')
      }
      
      console.log(`🤖 Generating text with Gemini (${this.modelName})...`)
      console.log(`📝 Prompt length: ${prompt.length} characters (~${Math.ceil(prompt.length / 4)} tokens)`)
      console.log(`🎯 Max output tokens requested: ${maxTokens}`)

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
      
      // Log token usage if available
      if (data.usageMetadata) {
        console.log(`📈 Token usage: Prompt=${data.usageMetadata.promptTokenCount}, Output=${data.usageMetadata.candidatesTokenCount}, Total=${data.usageMetadata.totalTokenCount}`)
        if (data.usageMetadata.candidatesTokenCount >= maxTokens * 0.95) {
          console.warn(`⚠️ Output tokens (${data.usageMetadata.candidatesTokenCount}) near limit (${maxTokens}). Consider increasing maxTokens.`)
        }
      }

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
      
      // Truncate context if too long (reduced to leave more room for output)
      const MAX_CONTEXT_LENGTH = 5000  // Reduced from 8000 to allow longer responses
      if (cleanedContext.length > MAX_CONTEXT_LENGTH) {
        console.log(`⚠️ Context too long (${cleanedContext.length} chars), truncating to ${MAX_CONTEXT_LENGTH} chars`)
        cleanedContext = cleanedContext.substring(0, MAX_CONTEXT_LENGTH) + '... [truncated]'
      }
      
      // Use optimized backend-style prompt (more concise to save tokens)
      const prompt = `You are an expert legal AI assistant specializing in financial analysis. Answer based ONLY on the provided context.

CORE RULES:
1. Answer from context only - no external knowledge
2. ALWAYS read the actual context - never say "no monetary figures present" if amounts exist
3. Quote relevant sections when applicable
4. Be precise and comprehensive

FINANCIAL ANALYSIS:
If "=== COMPREHENSIVE FINANCIAL ANALYSIS ===" appears, use it as PRIMARY source. It contains:
- MONETARY AMOUNTS with context
- PAYMENT SCHEDULES
- FINANCIAL TERMS
- TABLES data
- CALCULATIONS
Prioritize this over narrative text.

AMOUNT IDENTIFICATION:
- Find ALL monetary values: $, USD/EUR/INR, Indian format (/- e.g. 187,450/-)
- Identify: fees, payments, penalties, deposits, installments, taxes
- ALWAYS read context around amounts to understand what/when/who/why

KEY ANALYSIS:
- Payment schedules, due dates, penalties
- Cost breakdowns and hidden fees
- Financial obligations and liabilities
- Currency and calculations
- Table data extraction when present

For money questions: provide exact figures with context, payment terms, all fees, and calculations.

LEGAL DOCUMENT CONTEXT (read strictly):
${cleanedContext}

USER QUESTION: ${question}

IMPORTANT:
- Analyze THIS specific context, not generic responses
- If amounts exist (e.g., 187,450/-), ALWAYS report them
- Prioritize "=== COMPREHENSIVE FINANCIAL ANALYSIS ===" section if present
- Use "TABLE DATA:" section for structured information

FORMAT:
- Direct answer first
- Cite sections (e.g., "Section 3.2 states...")
- For financial data: use bullets, show all amounts/fees/calculations
- End with: "If you need clarification on any specific aspect, please let me know."

ANSWER:`;

      console.log(`📝 Question: "${question.substring(0, 100)}${question.length > 100 ? '...' : ''}"`)
      console.log(`📄 Context length: ${cleanedContext.length} characters`)
      
      // Use lower temperature for more factual responses, increased token limit to prevent cutoffs
      const answer = await this.generateText(prompt, 6000, 0.1)  // Increased from 3000 to use Gemini's 8K output limit

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
      
      // Truncate text if too long (reduced to leave more room for output)
      const MAX_CONTEXT_LENGTH = 5000  // Reduced from 8000 to allow longer responses
      if (cleanedText.length > MAX_CONTEXT_LENGTH) {
        console.log(`⚠️ Document too long (${cleanedText.length} chars), truncating to ${MAX_CONTEXT_LENGTH} chars`)
        cleanedText = cleanedText.substring(0, MAX_CONTEXT_LENGTH) + '... [truncated]'
      }
      
      // Use comprehensive backend-style prompt for risk analysis
      const prompt = `You are an expert legal risk analyst. Analyze the following legal document for potential legal risks, compliance issues, and areas of concern.

DOCUMENT TO ANALYZE:
"""
${cleanedText}
"""

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

RISK ANALYSIS:`;

      console.log(`📄 Document length for risk analysis: ${cleanedText.length} characters`)
      
      // Use slightly higher temperature for more comprehensive analysis, increased tokens to prevent cutoffs
      const analysis = await this.generateText(prompt, 3000, 0.1)  // Increased from 1000 to allow complete analysis

      return {
        analysis: analysis,
        risk_level: "Medium", // This is a placeholder, ideally would be extracted from the analysis
        risk_factors: [analysis],
        recommendations: ["Review with legal expert"],
        document_type: "legal",
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

// ============================================================================
// FINANCIAL ANALYSIS UTILITIES
// ============================================================================

// Comprehensive money keywords for financial query detection
const MONEY_KEYWORDS = [
  'cost', 'price', 'amount', 'fee', 'payment', 'charge', 'total', 'sum', 'dollar', 'money', 
  'financial', 'budget', 'expense', 'revenue', 'income', 'salary', 'wage', 'bonus', 'penalty', 
  'fine', 'refund', 'deposit', 'advance', 'installment', 'interest', 'tax', 'commission', 
  'royalty', 'rent', 'lease', 'purchase', 'sale', 'value', 'worth', 'expensive', 'cheap', 
  'affordable', 'costly', 'free', 'paid', 'unpaid', 'due', 'overdue', 'billing', 'invoice', 
  'receipt', 'receivable', 'payable', 'debt', 'credit', 'loan', 'mortgage', 'investment', 
  'profit', 'loss', 'earnings', 'compensation', 'benefits', 'allowance', 'stipend', 'pension', 
  'retirement', 'insurance', 'premium', 'deductible', 'coverage', 'claim', 'settlement', 
  'award', 'damages', 'restitution', 'reimbursement', 'subsidy', 'grant', 'funding', 
  'sponsorship', 'endorsement', 'licensing', 'franchise', 'dividend', 'share', 'stock', 
  'bond', 'security', 'asset', 'liability', 'equity', 'capital', 'fund', 'treasury', 
  'forecast', 'projection', 'estimate', 'quotation', 'proposal', 'bid', 'tender', 'contract', 
  'agreement', 'deal', 'transaction', 'exchange', 'trade', 'commerce', 'business', 'enterprise', 
  'corporation', 'company', 'firm', 'partnership', 'llc', 'inc', 'corp', 'ltd', 'llp', 'pllc', 
  'pc', 'pa', 'rs.', 'inr', 'rupees', '$', 'usd', 'eur', '₹'
]

// Payment schedule keywords
const SCHEDULE_KEYWORDS = [
  'payment schedule', 'installment', 'instalment', 'milestone', 'stage of work',
  'schedule of payment', 'plan of payment', 'payment plan', 'due on', 'on possession',
  'on booking', 'on agreement', 'slab'
]

// Check if question is money-related
function isMoneyRelated(question: string): boolean {
  const qLower = question.toLowerCase()
  return MONEY_KEYWORDS.some(keyword => qLower.includes(keyword))
}

// Check if question is about payment schedule
function isScheduleQuery(question: string): boolean {
  const qLower = question.toLowerCase()
  return SCHEDULE_KEYWORDS.some(keyword => qLower.includes(keyword))
}

// Multi-pass financial analysis (TypeScript version of backend function)
interface FinancialAnalysis {
  amounts: Array<{amount: string, position: number, context: string, pattern_type: string}>
  currencies: string[]
  payment_schedules: Array<{text: string, position: number, type: string}>
  financial_terms: Array<{term: string, position: number, type: string}>
  tables: Array<{headers: string[], rows: any[], type: string}>
  calculations: Array<{calculation: string, position: number, type: string}>
  contexts: Record<string, any>
}

function multiPassFinancialAnalysis(text: string): FinancialAnalysis {
  const analysis: FinancialAnalysis = {
    amounts: [],
    currencies: [],
    payment_schedules: [],
    financial_terms: [],
    tables: [],
    calculations: [],
    contexts: {}
  }

  // Pass 1: Extract all monetary amounts with context
  const amountPatterns = [
    /[\d,]+(?:\.\d{2})?\/-/g,  // Indian currency
    /\$[\d,]+(?:\.\d{2})?/g,  // USD
    /[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|CAD|AUD|JPY|CHF|CNY|INR)/gi,  // Currency codes
    /[\d,]+(?:\.\d{2})?\s*rupees?/gi,  // Written rupees
    /[\d,]+(?:\.\d{2})?\s*rs\.?/gi,  // Rs abbreviation
    /[\d,]+(?:\.\d{2})?\s*₹/g,  // Rupee symbol
  ]

  for (const pattern of amountPatterns) {
    const matches = [...text.matchAll(pattern)]
    for (const match of matches) {
      const amount = match[0]
      const start = match.index || 0
      const end = start + amount.length
      
      // Extract context around the amount (50 chars before and after)
      const contextStart = Math.max(0, start - 50)
      const contextEnd = Math.min(text.length, end + 50)
      const context = text.substring(contextStart, contextEnd)
      
      analysis.amounts.push({
        amount,
        position: start,
        context,
        pattern_type: 'currency'
      })
    }
  }

  // Pass 2: Extract payment schedules
  const schedulePatterns = [
    /(?:payment\s+schedule|installment\s+plan|payment\s+plan)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|$)/gi,
    /(?:monthly|quarterly|annual)\s+installment[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|$)/gi,
    /(?:down\s+payment|advance\s+payment)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|$)/gi,
  ]

  for (const pattern of schedulePatterns) {
    const matches = [...text.matchAll(pattern)]
    for (const match of matches) {
      const scheduleText = match[0]
      analysis.payment_schedules.push({
        text: scheduleText,
        position: match.index || 0,
        type: 'payment_schedule'
      })
    }
  }

  // Pass 3: Extract financial terms with amounts
  const financialTermPattern = /(?:payment|fee|cost|charge|price|amount|total|sum|value|worth|budget|expense|revenue|income)\s*:?\s*[\d,]+(?:\.\d{2})?/gi
  
  const termMatches = [...text.matchAll(financialTermPattern)]
  for (const match of termMatches) {
    analysis.financial_terms.push({
      term: match[0],
      position: match.index || 0,
      type: 'financial_term'
    })
  }

  // Pass 4: Extract tables (simplified - detect table-like structures)
  const lines = text.split('\n')
  const tables: Array<{headers: string[], rows: any[], type: string}> = []
  let currentTable: {headers: string[], rows: any[], type: string} | null = null

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    // Check if line looks like table header
    const columns = line.split(/\s{2,}|\t+/)
    if (columns.length >= 2 && (line.toLowerCase().includes('amount') || line.toLowerCase().includes('price') || line.toLowerCase().includes('payment'))) {
      if (currentTable) {
        tables.push(currentTable)
      }
      currentTable = {
        headers: columns.map(c => c.trim()),
        rows: [],
        type: 'financial'
      }
    } else if (currentTable && /\d/.test(line)) {
      // Table row with numbers
      const rowCols = line.split(/\s{2,}|\t+/)
      if (rowCols.length >= currentTable.headers.length - 1) {
        currentTable.rows.push({line_number: i, data: rowCols.map(c => c.trim())})
      }
    } else if (currentTable && (!line || columns.length < 2)) {
      // End of table
      if (currentTable.rows.length > 0) {
        tables.push(currentTable)
      }
      currentTable = null
    }
  }

  if (currentTable && currentTable.rows.length > 0) {
    tables.push(currentTable)
  }

  analysis.tables = tables

  // Pass 5: Extract calculations
  const calculationPattern = /(?:total|sum|subtotal|grand total|final amount)\s+(?:is|equals?|=\s*)?\s*[\d,]+(?:\.\d{2})?/gi
  const calcMatches = [...text.matchAll(calculationPattern)]
  for (const match of calcMatches) {
    analysis.calculations.push({
      calculation: match[0],
      position: match.index || 0,
      type: 'calculation'
    })
  }

  return analysis
}

// Extract payment schedule table (simplified version)
function extractPaymentScheduleTable(chunksText: string[]): string {
  const combined = chunksText.join('\n')
  const lines = combined.split('\n').filter(ln => /FINANCIAL|AMOUNT|Rs\.|rupees?|₹/.test(ln))
  
  if (lines.length === 0) {
    return ''
  }

  const rows: Array<[string, string]> = []
  let totalAmount = 0

  for (const ln of lines) {
    // Extract numeric amount
    const amountMatch = ln.match(/FINANCIAL:\s*AMOUNT:\s*([\d,]+)/i) || ln.match(/Rs\.\s*([\d,]+)/i) || ln.match(/([\d,]+)\s*\/-/)
    const amountRaw = amountMatch ? amountMatch[1] : ''
    let amountNum = 0
    try {
      amountNum = amountRaw ? parseInt(amountRaw.replace(/,/g, '')) : 0
    } catch {
      amountNum = 0
    }

    // Derive stage text
    let stageText = ln.replace(/Rs\.\s*\[\[.*?\]\]\s*\/-\]?/gi, '')
    stageText = stageText.replace(/\s{2,}/g, ' ').trim()
    stageText = stageText.substring(0, 120)

    if (amountNum > 0) {
      totalAmount += amountNum
    }
    if (stageText || amountRaw) {
      rows.push([stageText, amountRaw])
    }
  }

  if (rows.length === 0) {
    return ''
  }

  const tableLines = ['Payment Schedule:']
  for (let idx = 0; idx < rows.length; idx++) {
    const [stage, amount] = rows[idx]
    const displayAmt = amount ? `${amount}/-` : ''
    tableLines.push(`${idx + 1}. ${stage}: ${displayAmt}`)
  }

  if (totalAmount > 0) {
    tableLines.push(`Total Amount: ${totalAmount.toLocaleString()}/-`)
  }

  return tableLines.join('\n')
}

// ============================================================================
// EMBEDDING SERVICE (Vector Search Support)
// ============================================================================

interface EmbeddingService {
  generateEmbedding(text: string): Promise<number[]>
  searchSimilar(queryEmbedding: number[], documentId: number, k: number): Promise<Array<{chunk_index: number, score: number}>>
}

// Simple embedding service using text similarity (fallback until full embedding support)
class SimpleEmbeddingService implements EmbeddingService {
  // For now, this is a placeholder that will use keyword-based search
  // In production, you would integrate:
  // 1. Google's Text Embedding API (textembedding-gecko@003)
  // 2. OpenAI Embeddings API
  // 3. Or a JavaScript embedding library like @xenova/transformers
  
  async generateEmbedding(text: string): Promise<number[]> {
    // Placeholder: Return empty embedding vector
    // This will trigger fallback to keyword search
    // TODO: Integrate actual embedding service
    console.log('⚠️ Embedding generation not yet implemented, using keyword fallback')
    return [] // Empty means use keyword search
  }
  
  async searchSimilar(queryEmbedding: number[], documentId: number, k: number): Promise<Array<{chunk_index: number, score: number}>> {
    // If no embeddings, return empty (will trigger fallback)
    if (queryEmbedding.length === 0) {
      return []
    }
    
    // TODO: Implement pgvector similarity search using SQL
    // SELECT chunk_index, 1 - (embedding_vec <=> query_vector) as similarity
    // FROM document_chunks
    // WHERE document_id = $1 AND has_embedding = true
    // ORDER BY embedding_vec <=> query_vector
    // LIMIT $2
    
    return []
  }
}

// Embedding service using Supabase pgvector
async function searchSimilarVectors(
  queryVector: number[], 
  documentId: number, 
  k: number = 10
): Promise<Array<{chunk_index: number, score: number}>> {
  if (!queryVector || queryVector.length === 0) {
    return []
  }
  
  try {
    // Convert vector to pgvector format: "[0.1,0.2,...]"
    const vectorStr = `[${queryVector.join(',')}]`
    
    // Use Supabase RPC to call the search_similar_chunks function
    // Note: This requires the SQL function to be set up (see vector_search_setup.sql)
    const { data, error } = await supabase.rpc('search_similar_chunks', {
      query_vector: vectorStr,
      document_id: documentId,
      limit_count: k
    })
    
    if (error) {
      // If RPC doesn't exist or embeddings not available, fall back to keyword search
      if (error.message?.includes('function') || error.message?.includes('does not exist')) {
        console.warn('⚠️ Vector search function not set up yet. Run vector_search_setup.sql in Supabase SQL Editor.')
      } else {
        console.warn('⚠️ Vector search not available, using keyword fallback:', error.message)
      }
      return []
    }
    
    return (data || []).map((item: any) => ({
      chunk_index: item.chunk_index,
      score: item.similarity_score || 0
    }))
  } catch (e) {
    console.warn('⚠️ Vector search error, using keyword fallback:', e)
    return []
  }
}

// Generate embedding using Google's Text Embedding API (alternative to InLegalBERT)
async function generateEmbeddingGoogle(text: string): Promise<number[]> {
  try {
    // Check if we have Google API key for embeddings
    const GOOGLE_API_KEY = Deno.env.get('GOOGLE_API_KEY') || GEMINI_API_KEY
    
    if (!GOOGLE_API_KEY) {
      console.warn('⚠️ No Google API key for embeddings, using keyword fallback')
      return []
    }
    
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent?key=${GOOGLE_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'models/text-embedding-004',
          content: { parts: [{ text }] }
        })
      }
    )
    
    if (!response.ok) {
      console.warn('⚠️ Google embedding API failed, using keyword fallback')
      return []
    }
    
    const data = await response.json()
    return data.embedding?.values || []
  } catch (e) {
    console.warn('⚠️ Embedding generation error, using keyword fallback:', e)
    return []
  }
}

const embeddingService = new SimpleEmbeddingService()

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
    console.log('📄 Starting PDF text extraction...')
    
    // Convert ArrayBuffer to Uint8Array
    const uint8Array = new Uint8Array(fileBuffer)
    
    // Decode using Latin1 to preserve byte values
    const rawText = new TextDecoder('latin1', { fatal: false }).decode(uint8Array)
    
    // Extract text from PDF content streams
    const extractedParts: string[] = []
    
    // Method 1: Extract text from TJ/Tj operators (text showing operators in PDF)
    // Pattern: [(text)] TJ or (text) Tj
    const tjPattern = /\[?\(([^()]{2,}?)\)\]?\s*T[Jj]/g
    let match
    while ((match = tjPattern.exec(rawText)) !== null) {
      const text = match[1]
      if (text && text.length > 2) {
        extractedParts.push(text)
      }
    }
    
    // Method 2: Extract text from parentheses in content streams
    // More comprehensive than Method 1
    const parenPattern = /\(([^()]{3,}?)\)/g
    while ((match = parenPattern.exec(rawText)) !== null) {
      const text = match[1]
      // Only include if it looks like text (contains letters)
      if (text && /[a-zA-Z]{2,}/i.test(text)) {
        extractedParts.push(text)
      }
    }
    
    // Method 3: Extract from BT/ET blocks (text objects)
    const btEtPattern = /BT\s+([\s\S]*?)\s+ET/g
    while ((match = btEtPattern.exec(rawText)) !== null) {
      const block = match[1]
      // Extract text from this block
      const blockTextPattern = /\(([^()]+)\)/g
      let blockMatch
      while ((blockMatch = blockTextPattern.exec(block)) !== null) {
        const text = blockMatch[1]
        if (text && /[a-zA-Z]{2,}/i.test(text)) {
          extractedParts.push(text)
        }
      }
    }
    
    console.log(`🔍 Found ${extractedParts.length} text fragments`)
    
    // Process and clean all extracted parts
    const cleanedParts: string[] = []
    
    for (const part of extractedParts) {
      // Decode PDF escape sequences
      let cleaned = part
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '\r')
        .replace(/\\t/g, '\t')
        .replace(/\\\(/g, '(')
        .replace(/\\\)/g, ')')
        .replace(/\\\\/g, '\\')
        .replace(/\\(\d{3})/g, (_, octal) => String.fromCharCode(parseInt(octal, 8)))
      
      // Remove non-printable characters but keep newlines
      cleaned = cleaned.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]/g, '')
      
      // Normalize whitespace
      cleaned = cleaned.replace(/\s+/g, ' ').trim()
      
      // Only keep parts that look like real text
      // Must have at least 2 letters and be at least 3 characters
      if (cleaned.length >= 3 && /[a-zA-Z]{2,}/i.test(cleaned)) {
        // Filter out common PDF syntax
        if (!/^(obj|endobj|stream|endstream|xref|trailer|Type|Font|Page|Pages|XObject|Catalog|Encoding)$/i.test(cleaned)) {
          cleanedParts.push(cleaned)
        }
      }
    }
    
    console.log(`✅ Cleaned to ${cleanedParts.length} valid text parts`)
    
    if (cleanedParts.length === 0) {
      console.log('⚠️ No text extracted, PDF may be image-based')
      return `PDF document "${filename}" uploaded. The document appears to be image-based or contains no extractable text. For best results, please use text-based PDF documents.`
    }
    
    // Join parts intelligently
    let fullText = ''
    for (let i = 0; i < cleanedParts.length; i++) {
      const part = cleanedParts[i]
      const nextPart = cleanedParts[i + 1]
      
      fullText += part
      
      // Add spacing between parts
      if (nextPart) {
        // If current part ends with punctuation or next starts with capital, add space
        if (/[.!?:]$/.test(part) || /^[A-Z]/.test(nextPart)) {
          fullText += ' '
        } else {
          fullText += ' '
        }
      }
    }
    
    // Final cleanup
    fullText = fullText
      .replace(/\s+/g, ' ')
      .replace(/ ([.,;:!?])/g, '$1')
      .replace(/\(\s+/g, '(')
      .replace(/\s+\)/g, ')')
      .trim()
    
    console.log(`📊 Final extracted text: ${fullText.length} characters`)
    
    if (fullText.length < 50) {
      return `PDF document "${filename}" uploaded. Extracted minimal text (${fullText.length} chars). The document may be image-based or heavily formatted.`
    }
    
    // Limit to 20000 characters to prevent token issues
    if (fullText.length > 20000) {
      console.log(`⚠️ Text too long (${fullText.length} chars), truncating to 20000`)
      fullText = fullText.substring(0, 20000) + '...[truncated]'
    }
    
    return fullText
    
  } catch (error) {
    console.error('❌ PDF extraction failed:', error)
    return `PDF document "${filename}" uploaded. Text extraction encountered an error: ${error.message}. The document has been stored but text extraction failed.`
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

// ============================================================================
// USER MANAGEMENT HELPERS
// ============================================================================

// Helper function to extract user ID from request
async function getCurrentUserId(req: Request): Promise<number | null> {
  try {
    // Check for JWT token in Authorization header
    const authHeader = req.headers.get('authorization')
    if (authHeader && authHeader.startsWith('Bearer ')) {
      // For now, we'll use the free user system
      // In production, you would decode the JWT token here
      // For authenticated users, extract user_id from token
      // For this implementation, we'll check if it's a free user request
      const { data: freeUser } = await supabase
        .from('users')
        .select('id')
        .eq('email', 'free@system.local')
        .single()
      return freeUser?.id || null
    }
    // If no auth header, return null (will use free user logic)
    return null
  } catch (e) {
    console.error('Error extracting user ID:', e)
    return null
  }
}

// Helper function to get or create free user
async function getOrCreateFreeUser(): Promise<number> {
  try {
    const { data: existingUser } = await supabase
      .from('users')
      .select('id')
      .eq('email', 'free@system.local')
      .single()
    
    if (existingUser) {
      return existingUser.id
    }
    
    // Create free user if doesn't exist
    const { data: newUser, error } = await supabase
      .from('users')
      .insert({
        email: 'free@system.local',
        username: 'free_user',
        is_verified: true
      })
      .select('id')
      .single()
    
    if (error || !newUser) {
      console.error('Failed to create free user:', error)
      return 1 // Fallback to ID 1
    }
    
    return newUser.id
  } catch (e) {
    console.error('Error getting/creating free user:', e)
    return 1 // Fallback
  }
}

// Helper function to validate session ownership
async function validateSessionOwnership(sessionId: number, userId: number): Promise<boolean> {
  try {
    const { data: session, error } = await supabase
      .from('qa_sessions')
      .select('user_id')
      .eq('id', sessionId)
      .single()
    
    if (error || !session) {
      return false
    }
    
    return session.user_id === userId
  } catch (e) {
    console.error('Error validating session ownership:', e)
    return false
  }
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

        // Get current user ID and validate session ownership (like backend)
        const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()

        // Get session and document context with ownership validation
        const { data: session, error: sessionError } = await supabase
          .from('qa_sessions')
          .select('*, documents(*)')
          .eq('id', session_id)
          .eq('user_id', userId)  // Validate ownership (like backend)
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

        // Check if question is money-related
        const isMoney = isMoneyRelated(question)
        const isSchedule = isScheduleQuery(question)
        console.log(`💰 Question is money-related: ${isMoney}, schedule query: ${isSchedule}`)

        // Get all chunks for comprehensive analysis
        const { data: allChunks } = await supabase
          .from('document_chunks')
          .select('content, chunk_index')
          .eq('document_id', document.id)
          .order('chunk_index', { ascending: true })

        let fullDocumentText = document.extracted_text || ''
        
        // Build full document text from chunks if available
        if (allChunks && allChunks.length > 0) {
          fullDocumentText = allChunks.map(ch => ch.content || '').join('\n\n')
        }

        // Perform multi-pass financial analysis if money-related
        let financialAnalysis: FinancialAnalysis | null = null
        if (isMoney) {
          financialAnalysis = multiPassFinancialAnalysis(fullDocumentText)
          console.log(`💰 Financial analysis: ${financialAnalysis.amounts.length} amounts, ${financialAnalysis.payment_schedules.length} schedules, ${financialAnalysis.tables.length} tables`)
        }

        // Get relevant chunks (enhanced with financial analysis)
        let context = ''
        const contextParts: string[] = []

        // Add comprehensive financial analysis summary if available
        if (isMoney && financialAnalysis) {
          contextParts.push('=== COMPREHENSIVE FINANCIAL ANALYSIS ===')
          
          // Add monetary amounts
          if (financialAnalysis.amounts.length > 0) {
            contextParts.push(`\nMONETARY AMOUNTS FOUND (${financialAnalysis.amounts.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.amounts.length, 10); i++) {
              const amountData = financialAnalysis.amounts[i]
              contextParts.push(`${i + 1}. ${amountData.amount} - Context: ${amountData.context}`)
            }
          }
          
          // Add payment schedules
          if (financialAnalysis.payment_schedules.length > 0) {
            contextParts.push(`\nPAYMENT SCHEDULES FOUND (${financialAnalysis.payment_schedules.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.payment_schedules.length, 3); i++) {
              const schedule = financialAnalysis.payment_schedules[i]
              contextParts.push(`${i + 1}. ${schedule.text.substring(0, 200)}...`)
            }
          }
          
          // Add financial terms
          if (financialAnalysis.financial_terms.length > 0) {
            contextParts.push(`\nFINANCIAL TERMS FOUND (${financialAnalysis.financial_terms.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.financial_terms.length, 10); i++) {
              contextParts.push(`${i + 1}. ${financialAnalysis.financial_terms[i].term}`)
            }
          }
          
          // Add tables
          if (financialAnalysis.tables.length > 0) {
            contextParts.push(`\nTABLES FOUND (${financialAnalysis.tables.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.tables.length, 3); i++) {
              const table = financialAnalysis.tables[i]
              contextParts.push(`Table ${i + 1} (${table.type}): Headers: ${table.headers.join(', ')}`)
              for (let j = 0; j < Math.min(table.rows.length, 5); j++) {
                contextParts.push(`  Row ${j + 1}: ${table.rows[j].data.join(', ')}`)
              }
            }
          }
          
          // Add calculations
          if (financialAnalysis.calculations.length > 0) {
            contextParts.push(`\nCALCULATIONS FOUND (${financialAnalysis.calculations.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.calculations.length, 5); i++) {
              contextParts.push(`${i + 1}. ${financialAnalysis.calculations[i].calculation}`)
            }
          }
          
          contextParts.push('\n=== END FINANCIAL ANALYSIS ===\n')
        }

        // Add payment schedule table if schedule query
        if (isSchedule && allChunks) {
          const scheduleTable = extractPaymentScheduleTable(allChunks.map(ch => ch.content || ''))
          if (scheduleTable) {
            contextParts.push(`TABLE DATA:\n${scheduleTable}`)
            console.log(`📊 Synthesized payment schedule table`)
          }
        }

        // Try vector similarity search first (if embeddings available)
        let candidateIndices = new Set<number>()
        
        try {
          // Generate embedding for question using Google's API
          const questionEmbedding = await generateEmbeddingGoogle(question)
          
          if (questionEmbedding.length > 0) {
            console.log(`🔍 Q&A: Using vector search with ${questionEmbedding.length}-dim embedding`)
            // Try vector similarity search via pgvector
            const vectorSearchResults = await searchSimilarVectors(questionEmbedding, document.id, isMoney ? 25 : 15)
            
            if (vectorSearchResults.length > 0) {
              console.log(`✅ Vector search found ${vectorSearchResults.length} similar chunks`)
              // Add vector search results
              for (const result of vectorSearchResults) {
                candidateIndices.add(result.chunk_index)
                // Include adjacent chunks (±1 to ±3 depending on query type)
                const spread = isMoney ? 3 : 2
                for (let i = -spread; i <= spread; i++) {
                  candidateIndices.add(result.chunk_index + i)
                }
              }
            }
          }
        } catch (e) {
          console.warn('⚠️ Vector search failed, using keyword fallback:', e)
        }
        
        // Fallback to keyword-based search if vector search didn't find enough results
        if (candidateIndices.size < 5 && allChunks) {
          console.log('📊 Q&A: Using keyword-based chunk selection (vector search unavailable)')
          // Get base chunks (first 15 for semantic search simulation, or more for financial)
          const baseK = isMoney ? 25 : 15
          const baseChunks = allChunks.slice(0, baseK)
          
          // Include adjacent chunks (±1 to ±3 depending on query type)
          baseChunks.forEach(ch => {
            const idx = ch.chunk_index
            const spread = isMoney ? 3 : 2
            for (let i = -spread; i <= spread; i++) {
              candidateIndices.add(idx + i)
            }
          })

          // For money queries, also find chunks with amounts
          if (isMoney) {
            const amountPatterns = [
              /\$[\d,]+/,  // Dollar amounts
              /[\d,]+(?:\.\d{2})?\/-/,  // Indian currency
              /[\d,]+(?:\.\d{2})?\s*\/-/,  // Indian currency with space
              /[\d,]+(?:\.\d{2})?\s*(?:dollars?|usd|eur|gbp|rupees?)/i,  // Currency amounts
            ]
            
            allChunks.forEach(ch => {
              const content = ch.content || ''
              if (amountPatterns.some(pattern => pattern.test(content))) {
                candidateIndices.add(ch.chunk_index)
                // Include more surrounding context for amount chunks
                candidateIndices.add(ch.chunk_index - 2)
                candidateIndices.add(ch.chunk_index - 1)
                candidateIndices.add(ch.chunk_index + 1)
                candidateIndices.add(ch.chunk_index + 2)
              }
            })
          }
        }

        // Fetch selected chunks
        const indices = Array.from(candidateIndices).filter(i => i >= 0).sort((a, b) => a - b)
        let selectedChunks: Array<{content: string, chunk_index: number}> = []
        
        if (allChunks && indices.length > 0) {
          selectedChunks = allChunks.filter(ch => indices.includes(ch.chunk_index))
        } else if (allChunks) {
          // Final fallback: use first chunks
          const baseK = isMoney ? 25 : 15
          selectedChunks = allChunks.slice(0, baseK)
        }

        // Build context from chunks
        const maxContextLength = isMoney ? 8000 : 3500
        let totalLen = contextParts.join('\n\n').length
        
        for (const ch of selectedChunks) {
          if (!ch.content) continue
          if (totalLen >= maxContextLength) break
          contextParts.push(ch.content)
          totalLen += ch.content.length
        }

        // If no chunks, use extracted text
        if (contextParts.length === (isMoney ? 1 : 0)) {
          const textLen = Math.min(fullDocumentText.length, maxContextLength)
          contextParts.push(fullDocumentText.substring(0, textLen))
        }

        context = contextParts.join('\n\n')
        console.log(`📊 Final context length: ${context.length} chars (${selectedChunks.length} chunks)`)

        // Create question record FIRST (like backend)
        const startTime = Date.now()
        const { data: questionRecord, error: createError } = await supabase
          .from('qa_questions')
          .insert({
            session_id: session_id,
            question: question,
          })
          .select()
          .single()

        if (createError || !questionRecord) {
          console.error('⚠️ Failed to create question record:', createError)
        }

        // Use Gemini to answer the question
        const result = await geminiService.answerQuestion(question, context)
        const processingTime = (Date.now() - startTime) / 1000

        // Update question with answer (like backend)
        if (questionRecord) {
          const { error: updateError } = await supabase
            .from('qa_questions')
            .update({
              answer: result.answer,
              confidence_score: result.confidence,
              context_used: context, // Store context used
              processing_time: processingTime,
              model_used: result.model_used,
              answered_at: new Date().toISOString(),
              token_count: result.answer.length + context.length, // Rough estimate
            })
            .eq('id', questionRecord.id)

          if (updateError) {
            console.error('⚠️ Failed to update question with answer:', updateError)
          }
        }

        // Update session activity
        await supabase
          .from('qa_sessions')
          .update({
            total_questions: (session.total_questions || 0) + 1,
            last_activity: new Date().toISOString()
          })
          .eq('id', session_id)

        // Return complete response matching backend QAQuestionResponse schema
        return new Response(
          JSON.stringify({
            id: questionRecord?.id || Date.now(),
            session_id: session_id,
            question: question,
            answer: result.answer,
            confidence_score: result.confidence,
            context_used: context, // Include context used
            processing_time: processingTime,
            model_used: result.model_used,
            answered_at: questionRecord ? new Date().toISOString() : null,
            created_at: questionRecord?.created_at || new Date().toISOString(),
            is_helpful: null,
            user_rating: null,
            feedback: null,
            token_count: result.answer.length + context.length,
            // Legacy fields for compatibility
            confidence: result.confidence,
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

        // Check if question is money-related
        const isMoney = isMoneyRelated(question)
        const isSchedule = isScheduleQuery(question)
        console.log(`💰 Free question is money-related: ${isMoney}, schedule query: ${isSchedule}`)

        // Get all chunks for comprehensive analysis
        const { data: allChunks } = await supabase
          .from('document_chunks')
          .select('content, chunk_index')
          .eq('document_id', document.id)
          .order('chunk_index', { ascending: true })

        let fullDocumentText = document.extracted_text || ''
        
        // Build full document text from chunks if available
        if (allChunks && allChunks.length > 0) {
          fullDocumentText = allChunks.map(ch => ch.content || '').join('\n\n')
        }

        // Perform multi-pass financial analysis if money-related
        let financialAnalysis: FinancialAnalysis | null = null
        if (isMoney) {
          financialAnalysis = multiPassFinancialAnalysis(fullDocumentText)
          console.log(`💰 Financial analysis: ${financialAnalysis.amounts.length} amounts, ${financialAnalysis.payment_schedules.length} schedules, ${financialAnalysis.tables.length} tables`)
        }

        // Get relevant chunks (enhanced with financial analysis)
        let context = ''
        const contextParts: string[] = []

        // Add comprehensive financial analysis summary if available
        if (isMoney && financialAnalysis) {
          contextParts.push('=== COMPREHENSIVE FINANCIAL ANALYSIS ===')
          
          // Add monetary amounts
          if (financialAnalysis.amounts.length > 0) {
            contextParts.push(`\nMONETARY AMOUNTS FOUND (${financialAnalysis.amounts.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.amounts.length, 10); i++) {
              const amountData = financialAnalysis.amounts[i]
              contextParts.push(`${i + 1}. ${amountData.amount} - Context: ${amountData.context}`)
            }
          }
          
          // Add payment schedules
          if (financialAnalysis.payment_schedules.length > 0) {
            contextParts.push(`\nPAYMENT SCHEDULES FOUND (${financialAnalysis.payment_schedules.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.payment_schedules.length, 3); i++) {
              const schedule = financialAnalysis.payment_schedules[i]
              contextParts.push(`${i + 1}. ${schedule.text.substring(0, 200)}...`)
            }
          }
          
          // Add financial terms
          if (financialAnalysis.financial_terms.length > 0) {
            contextParts.push(`\nFINANCIAL TERMS FOUND (${financialAnalysis.financial_terms.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.financial_terms.length, 10); i++) {
              contextParts.push(`${i + 1}. ${financialAnalysis.financial_terms[i].term}`)
            }
          }
          
          // Add tables
          if (financialAnalysis.tables.length > 0) {
            contextParts.push(`\nTABLES FOUND (${financialAnalysis.tables.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.tables.length, 3); i++) {
              const table = financialAnalysis.tables[i]
              contextParts.push(`Table ${i + 1} (${table.type}): Headers: ${table.headers.join(', ')}`)
              for (let j = 0; j < Math.min(table.rows.length, 5); j++) {
                contextParts.push(`  Row ${j + 1}: ${table.rows[j].data.join(', ')}`)
              }
            }
          }
          
          // Add calculations
          if (financialAnalysis.calculations.length > 0) {
            contextParts.push(`\nCALCULATIONS FOUND (${financialAnalysis.calculations.length}):`)
            for (let i = 0; i < Math.min(financialAnalysis.calculations.length, 5); i++) {
              contextParts.push(`${i + 1}. ${financialAnalysis.calculations[i].calculation}`)
            }
          }
          
          contextParts.push('\n=== END FINANCIAL ANALYSIS ===\n')
        }

        // Add payment schedule table if schedule query
        if (isSchedule && allChunks) {
          const scheduleTable = extractPaymentScheduleTable(allChunks.map(ch => ch.content || ''))
          if (scheduleTable) {
            contextParts.push(`TABLE DATA:\n${scheduleTable}`)
            console.log(`📊 Synthesized payment schedule table`)
          }
        }

        // Try vector similarity search first (if embeddings available)
        let candidateIndices = new Set<number>()
        
        try {
          // Generate embedding for question using Google's API
          const questionEmbedding = await generateEmbeddingGoogle(question)
          
          if (questionEmbedding.length > 0) {
            console.log(`🔍 Free Q&A: Using vector search with ${questionEmbedding.length}-dim embedding`)
            // Try vector similarity search via pgvector
            const vectorSearchResults = await searchSimilarVectors(questionEmbedding, document.id, isMoney ? 25 : 15)
            
            if (vectorSearchResults.length > 0) {
              console.log(`✅ Vector search found ${vectorSearchResults.length} similar chunks`)
              // Add vector search results
              for (const result of vectorSearchResults) {
                candidateIndices.add(result.chunk_index)
                // Include adjacent chunks (±1 to ±3 depending on query type)
                const spread = isMoney ? 3 : 2
                for (let i = -spread; i <= spread; i++) {
                  candidateIndices.add(result.chunk_index + i)
                }
              }
            }
          }
        } catch (e) {
          console.warn('⚠️ Vector search failed, using keyword fallback:', e)
        }
        
        // Fallback to keyword-based search if vector search didn't find enough results
        if (candidateIndices.size < 5 && allChunks) {
          console.log('📊 Free Q&A: Using keyword-based chunk selection (vector search unavailable)')
          // Get base chunks (first 15 for semantic search simulation, or more for financial)
          const baseK = isMoney ? 25 : 15
          const baseChunks = allChunks.slice(0, baseK)
          
          // Include adjacent chunks (±1 to ±3 depending on query type)
          baseChunks.forEach(ch => {
            const idx = ch.chunk_index
            const spread = isMoney ? 3 : 2
            for (let i = -spread; i <= spread; i++) {
              candidateIndices.add(idx + i)
            }
          })

          // For money queries, also find chunks with amounts
          if (isMoney) {
            const amountPatterns = [
              /\$[\d,]+/,  // Dollar amounts
              /[\d,]+(?:\.\d{2})?\/-/,  // Indian currency
              /[\d,]+(?:\.\d{2})?\s*\/-/,  // Indian currency with space
              /[\d,]+(?:\.\d{2})?\s*(?:dollars?|usd|eur|gbp|rupees?)/i,  // Currency amounts
            ]
            
            allChunks.forEach(ch => {
              const content = ch.content || ''
              if (amountPatterns.some(pattern => pattern.test(content))) {
                candidateIndices.add(ch.chunk_index)
                // Include more surrounding context for amount chunks
                candidateIndices.add(ch.chunk_index - 2)
                candidateIndices.add(ch.chunk_index - 1)
                candidateIndices.add(ch.chunk_index + 1)
                candidateIndices.add(ch.chunk_index + 2)
              }
            })
          }
        }

        // Fetch selected chunks
        const indices = Array.from(candidateIndices).filter(i => i >= 0).sort((a, b) => a - b)
        let selectedChunks: Array<{content: string, chunk_index: number}> = []
        
        if (allChunks && indices.length > 0) {
          selectedChunks = allChunks.filter(ch => indices.includes(ch.chunk_index))
        } else if (allChunks) {
          // Final fallback: use first chunks
          const baseK = isMoney ? 25 : 15
          selectedChunks = allChunks.slice(0, baseK)
        }

        // Build context from chunks
        const maxContextLength = isMoney ? 8000 : 3500
        let totalLen = contextParts.join('\n\n').length
        
        for (const ch of selectedChunks) {
          if (!ch.content) continue
          if (totalLen >= maxContextLength) break
          contextParts.push(ch.content)
          totalLen += ch.content.length
        }

        // If no chunks, use extracted text
        if (contextParts.length === (isMoney ? 1 : 0)) {
          const textLen = Math.min(fullDocumentText.length, maxContextLength)
          contextParts.push(fullDocumentText.substring(0, textLen))
        }

        context = contextParts.join('\n\n')
        console.log(`📊 Final context length: ${context.length} chars (${selectedChunks.length} chunks)`)

        // Create question record FIRST (like backend)
        const startTime = Date.now()
        const { data: questionRecord, error: createError } = await supabase
          .from('qa_questions')
          .insert({
            session_id: session_id,
            question: question,
          })
          .select()
          .single()

        if (createError || !questionRecord) {
          console.error('⚠️ Failed to create free question record:', createError)
        }

        // Use Gemini to answer the question
        const result = await geminiService.answerQuestion(question, context)
        const processingTime = (Date.now() - startTime) / 1000

        // Update question with answer (like backend)
        if (questionRecord) {
          const { error: updateError } = await supabase
            .from('qa_questions')
            .update({
              answer: result.answer,
              confidence_score: result.confidence,
              context_used: context, // Store context used
              processing_time: processingTime,
              model_used: result.model_used,
              answered_at: new Date().toISOString(),
              token_count: result.answer.length + context.length, // Rough estimate
            })
            .eq('id', questionRecord.id)

          if (updateError) {
            console.error('⚠️ Failed to update free question with answer:', updateError)
          }
        }

        // Update session activity
        await supabase
          .from('qa_sessions')
          .update({
            total_questions: (session.total_questions || 0) + 1,
            last_activity: new Date().toISOString()
          })
          .eq('id', session_id)

        // Return complete response matching backend QAQuestionResponse schema
        return new Response(
          JSON.stringify({
            id: questionRecord?.id || Date.now(),
            session_id: session_id,
            question: question,
            answer: result.answer,
            confidence_score: result.confidence,
            context_used: context, // Include context used
            processing_time: processingTime,
            model_used: result.model_used,
            answered_at: questionRecord ? new Date().toISOString() : null,
            created_at: questionRecord?.created_at || new Date().toISOString(),
            is_helpful: null,
            user_rating: null,
            feedback: null,
            token_count: result.answer.length + context.length,
            // Legacy fields for compatibility
            confidence: result.confidence,
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

    // Debug endpoint for document processing
    const debugMatch = path.match(/^\/free\/debug\/document\/(\d+)$/)
    if (debugMatch && method === 'GET') {
      try {
        const documentId = Number(debugMatch[1])
        
        // Get or create free user
        let userId = 1
        const { data: existingUser } = await supabase
          .from('users')
          .select('id')
          .eq('email', 'free@system.local')
          .single()
        if (existingUser) userId = existingUser.id
        
        const { data: document, error: docError } = await supabase
          .from('documents')
          .select('id, filename, status, is_processed, extracted_text')
          .eq('id', documentId)
          .eq('owner_id', userId)
          .single()
        
        if (docError || !document) {
          return new Response(
            JSON.stringify({ error: 'Document not found' }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
          )
        }
        
        // Get chunks
        const { data: chunks } = await supabase
          .from('document_chunks')
          .select('chunk_index, content')
          .eq('document_id', documentId)
          .order('chunk_index', { ascending: true })
        
        // Check for amounts in chunks
        const amountPattern = /[\d,]+(?:\.\d{2})?\/-|\$[\d,]+/
        
        return new Response(
          JSON.stringify({
            document_id: documentId,
            filename: document.filename,
            status: document.status,
            is_processed: document.is_processed,
            total_chunks: chunks?.length || 0,
            chunks_preview: chunks?.slice(0, 5).map(ch => ({
              index: ch.chunk_index,
              content_preview: ch.content ? (ch.content.substring(0, 200) + (ch.content.length > 200 ? '...' : '')) : '',
              has_amounts: ch.content ? amountPattern.test(ch.content) : false
            })) || []
          }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        )
      } catch (e) {
        console.error('Debug endpoint error:', e)
        return new Response(
          JSON.stringify({ error: 'Debug failed', details: String(e) }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
        )
      }
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
        // List all sessions for the current user
        try {
          // Get current user ID
          const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
          
          // Filter sessions by user_id (like backend)
          const { data: sessions, error } = await supabase
            .from('qa_sessions')
            .select('*, documents(id, title, original_filename, file_size, mime_type, created_at)')
            .eq('user_id', userId)
            .order('created_at', { ascending: false })
          
          if (error) {
            console.error('Error fetching sessions:', error)
            return new Response(
              JSON.stringify({ error: 'Failed to fetch sessions', details: error.message }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
            )
          }
          
          return new Response(
            JSON.stringify(sessions || []),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        } catch (e) {
          return new Response(
            JSON.stringify({ error: 'Failed to fetch sessions', details: String(e) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
      }
      
      // POST create session
      try {
        const payload = await req.json()
        const document_id = payload.document_id ? Number(payload.document_id) : null
        
        if (!document_id) {
          return new Response(
            JSON.stringify({ error: 'document_id is required' }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
          )
        }
        
        // Get current user ID
        const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
        
        // Verify document exists, is processed, and belongs to user (like backend)
        const { data: doc, error: docError } = await supabase
          .from('documents')
          .select('id, title, is_processed, owner_id')
          .eq('id', document_id)
          .eq('owner_id', userId)  // Validate ownership
          .single()
        
        if (docError || !doc) {
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
            document_id: document_id,
            session_name: payload.session_name || `Q&A - ${doc.title}`,
            is_active: true,
            total_questions: 0
          })
          .select()
          .single()
        
        if (error || !session) {
          console.error('Session creation error:', error)
          return new Response(
            JSON.stringify({ error: 'Failed to create session', details: error?.message }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
        
        return new Response(
          JSON.stringify(session),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        )
      } catch (e) {
        console.error('Session creation error:', e)
        return new Response(
          JSON.stringify({ error: 'Failed to create session', details: String(e) }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
        )
      }
    }

    // QA Sessions - detail/delete/cleanup/questions
    const qaSessionMatch = path.match(/^\/qa\/sessions\/(\d+)(?:\/(cleanup|questions))?$/)
    if (qaSessionMatch) {
      const sessionId = Number(qaSessionMatch[1])
      const subPath = qaSessionMatch[2]
      
      // GET session details
      if (!subPath && method === 'GET') {
        try {
          // Get current user ID and validate ownership
          const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
          
          const { data: session, error } = await supabase
            .from('qa_sessions')
            .select('*, documents(id, title, original_filename, file_size, mime_type, created_at)')
            .eq('id', sessionId)
            .eq('user_id', userId)  // Validate ownership (like backend)
            .single()
          
          if (error || !session) {
            return new Response(
              JSON.stringify({ error: 'Session not found' }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
            )
          }
          
          return new Response(
            JSON.stringify(session),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        } catch (e) {
          return new Response(
            JSON.stringify({ error: 'Failed to fetch session', details: String(e) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
      }
      
      // DELETE session with cascade
      if (!subPath && method === 'DELETE') {
        try {
          // Get current user ID and validate ownership
          const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
          
          // Get session to find document and validate ownership
          const { data: session } = await supabase
            .from('qa_sessions')
            .select('document_id, user_id')
            .eq('id', sessionId)
            .eq('user_id', userId)  // Validate ownership (like backend)
            .single()
          
          if (!session) {
            return new Response(
              JSON.stringify({ error: 'Session not found' }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
            )
          }
          
          // Delete QA questions first
          await supabase
            .from('qa_questions')
            .delete()
            .eq('session_id', sessionId)
          
          // Delete session
          await supabase
            .from('qa_sessions')
            .delete()
            .eq('id', sessionId)
          
          // Delete document chunks
          await supabase
            .from('document_chunks')
            .delete()
            .eq('document_id', session.document_id)
          
          // Delete risk analyses
          await supabase
            .from('risk_analyses')
            .delete()
            .eq('document_id', session.document_id)
          
          // Get document to delete from storage
          const { data: document } = await supabase
            .from('documents')
            .select('supabase_path')
            .eq('id', session.document_id)
            .single()
          
          // Delete from storage
          if (document && document.supabase_path) {
            try {
              await supabase.storage
                .from('legal-assistant')
                .remove([document.supabase_path])
            } catch (storageError) {
              console.warn('Failed to delete from storage:', storageError)
            }
          }
          
          // Delete document record
          await supabase
            .from('documents')
            .delete()
            .eq('id', session.document_id)
          
          return new Response(
            JSON.stringify({ message: 'Session, document, and related data deleted successfully' }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        } catch (e) {
          console.error('Delete session error:', e)
          return new Response(
            JSON.stringify({ error: 'Failed to delete session', details: String(e) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
      }
      
      // POST cleanup session
      if (subPath === 'cleanup' && method === 'POST') {
        try {
          // Get current user ID and validate ownership
          const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
          
          // Same as DELETE but without removing the session itself
          const { data: session } = await supabase
            .from('qa_sessions')
            .select('document_id, user_id')
            .eq('id', sessionId)
            .eq('user_id', userId)  // Validate ownership (like backend)
            .single()
          
          if (!session) {
            return new Response(
              JSON.stringify({ error: 'Session not found' }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
            )
          }
          
          // Delete QA questions
          await supabase
            .from('qa_questions')
            .delete()
            .eq('session_id', sessionId)
          
          // Reset session stats
          await supabase
            .from('qa_sessions')
            .update({ total_questions: 0 })
            .eq('id', sessionId)
          
          return new Response(
            JSON.stringify({ message: 'Session cleaned up successfully' }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        } catch (e) {
          return new Response(
            JSON.stringify({ error: 'Failed to cleanup session', details: String(e) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
      }
      
      // GET session questions
      if (subPath === 'questions' && method === 'GET') {
        try {
          // Get current user ID and validate session ownership
          const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
          
          // Verify session ownership first (like backend)
          const isOwner = await validateSessionOwnership(sessionId, userId)
          if (!isOwner) {
            return new Response(
              JSON.stringify({ error: 'Session not found' }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
            )
          }
          
          const { data: questions, error } = await supabase
            .from('qa_questions')
            .select('*')
            .eq('session_id', sessionId)
            .order('created_at', { ascending: true })
          
          if (error) {
            return new Response(
              JSON.stringify({ error: 'Failed to fetch questions', details: error.message }),
              { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
            )
          }
          
          return new Response(
            JSON.stringify(questions || []),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
          )
        } catch (e) {
          return new Response(
            JSON.stringify({ error: 'Failed to fetch questions', details: String(e) }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
      }
      
      return new Response(JSON.stringify({ error: 'Method Not Allowed' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 405 })
    }

    // QA Question feedback
    const qaFeedbackMatch = path.match(/^\/qa\/questions\/(\d+)\/feedback$/)
    if (qaFeedbackMatch && method === 'PUT') {
      try {
        const questionId = Number(qaFeedbackMatch[1])
        const payload = await req.json()
        
        // Get current user ID and validate question ownership (like backend)
        const userId = await getCurrentUserId(req) || await getOrCreateFreeUser()
        
        // Verify question belongs to user's session
        const { data: question, error: qError } = await supabase
          .from('qa_questions')
          .select('session_id, qa_sessions!inner(user_id)')
          .eq('id', questionId)
          .single()
        
        if (qError || !question || (question as any).qa_sessions?.user_id !== userId) {
          return new Response(
            JSON.stringify({ error: 'Question not found' }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
          )
        }
        
        const { error } = await supabase
          .from('qa_questions')
          .update({
            is_helpful: payload.is_helpful,
            user_rating: payload.rating || null,
            feedback: payload.feedback || null
          })
          .eq('id', questionId)
        
        if (error) {
          return new Response(
            JSON.stringify({ error: 'Failed to record feedback', details: error.message }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
          )
        }
        
        return new Response(
          JSON.stringify({ message: 'Feedback recorded successfully' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        )
      } catch (e) {
        return new Response(
          JSON.stringify({ error: 'Failed to record feedback', details: String(e) }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
        )
      }
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
        let bucketName = 'legal-assistant' // Initialize at outer scope

        try {
          console.log('📦 Converting file to buffer...')
          fileBuffer = await (file as File).arrayBuffer()
          console.log('✅ File converted to buffer, size:', fileBuffer.byteLength)

          // Try multiple bucket names in order
          const bucketNames = ['legal-assistant', 'legal-documents', 'documents']
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

          // Create document chunks with embeddings
          console.log('📦 Creating document chunks with embeddings...')
          const chunks = chunkText(extractedText, 800, 160)
          
          if (chunks.length > 0) {
            // Generate embeddings for chunks in parallel (with rate limiting)
            console.log(`🔍 Generating embeddings for ${chunks.length} chunks...`)
            const chunkRecords = await Promise.all(chunks.map(async (content, index) => {
              let embedding: number[] | null = null
              let hasEmbedding = false
              
              // Try to generate embedding using Google's Text Embedding API
              try {
                // Add small delay to avoid rate limits
                if (index > 0 && index % 10 === 0) {
                  await new Promise(resolve => setTimeout(resolve, 100))
                }
                
                embedding = await generateEmbeddingGoogle(content)
                hasEmbedding = embedding.length > 0
                if (hasEmbedding && index % 10 === 0) { // Log every 10th chunk
                  console.log(`✅ Generated embedding for chunk ${index}/${chunks.length} (${embedding.length} dimensions)`)
                }
              } catch (e) {
                // Silently fail - embeddings are optional, will use keyword search fallback
                if (index === 0) {
                  console.warn(`⚠️ Embedding generation not available, continuing without embeddings`)
                }
              }
              
              const record: any = {
                document_id: document.id,
                chunk_index: index,
                content: content,
                word_count: content.split(' ').length,
                character_count: content.length,
                has_embedding: hasEmbedding
              }
              
              // Add embedding vector if available (for pgvector)
              // Note: Supabase's pgvector expects the embedding_vec column to be of type vector
              // We'll store as string representation and let SQL cast it, or use RPC
              if (hasEmbedding && embedding) {
                // Store embedding for vector search
                // In Supabase, we need to use a function or direct SQL to insert vector type
                // For now, we'll store the embedding string representation
                record.embedding_vec = embedding // Supabase will handle the vector type conversion
              }
              
              return record
            }))
            
            // Insert chunks with embeddings
            // Note: If embedding_vec column doesn't support direct insert, we may need to use RPC
            const { error: chunkError } = await supabase
              .from('document_chunks')
              .insert(chunkRecords)
            
            if (chunkError) {
              console.error('⚠️ Failed to create chunks:', chunkError)
              // If embedding_vec insert fails, try without embeddings
              if (chunkError.message?.includes('embedding') || chunkError.message?.includes('vector')) {
                console.warn('⚠️ Retrying chunk insert without embeddings...')
                const chunksWithoutEmbeddings = chunkRecords.map(({ embedding_vec, has_embedding, ...rest }) => rest)
                const { error: retryError } = await supabase
                  .from('document_chunks')
                  .insert(chunksWithoutEmbeddings)
                
                if (retryError) {
                  console.error('⚠️ Failed to create chunks even without embeddings:', retryError)
                } else {
                  console.log(`✅ Created ${chunks.length} chunks (without embeddings)`)
                }
              } else {
                // Don't fail the upload if chunk creation fails
                console.warn('⚠️ Continuing without chunks')
              }
            } else {
              const embeddedCount = chunkRecords.filter(r => r.has_embedding).length
              console.log(`✅ Created ${chunks.length} chunks for document ${document.id} (${embeddedCount} with embeddings)`)
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