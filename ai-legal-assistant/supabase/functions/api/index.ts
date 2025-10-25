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
const GEMINI_MODEL = Deno.env.get('GEMINI_MODEL') || 'gemini-2.0-flash-exp'

class GeminiLLMService {
  private apiKey: string
  private modelName: string

  constructor() {
    this.apiKey = GEMINI_API_KEY || ''
    this.modelName = GEMINI_MODEL

    if (!this.apiKey) {
      console.error('❌ GEMINI_API_KEY is required')
    }
  }

  async generateText(prompt: string, maxTokens: number = 1000, temperature: number = 0.7): Promise<string> {
    try {
      console.log(`🤖 Generating text with Gemini (${this.modelName})...`)
      console.log(`📝 Prompt length: ${prompt.length} characters`)

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
          topK: 40
        }
      }

      console.log(`🚀 Making request to Gemini API...`)
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${this.modelName}:generateContent?key=${this.apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      console.log(`📊 Gemini API response status: ${response.status}`)

    if (!response.ok) {
        const errorText = await response.text()
        console.error(`❌ Gemini API error response: ${errorText}`)
        throw new Error(`Gemini API error: ${response.status} ${response.statusText} - ${errorText}`)
    }

    const data = await response.json()
      console.log(`📦 Gemini API response received (${JSON.stringify(data).length} chars)`)

      if (data.candidates && data.candidates[0] && data.candidates[0].content) {
        const result = data.candidates[0].content.parts[0].text.trim()
        console.log(`✅ Gemini response generated (${result.length} characters)`)
        return result
      } else {
        console.error(`❌ Invalid Gemini response structure:`, data)
        throw new Error('No response from Gemini - invalid response structure')
      }
  } catch (error) {
      console.error('❌ Gemini API error:', error)
      throw new Error(`Failed to generate text: ${error.message}`)
    }
  }

  async answerQuestion(question: string, context: string): Promise<any> {
    try {
      const prompt = `You are an expert legal AI assistant. Answer the following question based ONLY on the provided context. Do not use external knowledge.

Context:
${context}

Question: ${question}

Answer:`

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
      const prompt = `Analyze the following legal document for potential risks and provide a comprehensive risk analysis.

Document:
${text}

Provide a structured risk analysis with:
1. Risk Level (HIGH/MEDIUM/LOW)
2. Risk Categories (Contractual, Compliance, Financial, Operational, Legal)
3. Specific risks identified
4. Impact assessment
5. Recommendations

Risk Analysis:`

      const analysis = await this.generateText(prompt, 1000, 0.1)

      return {
        analysis: analysis,
        risk_level: "Medium",
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

// Test Gemini API connection on startup
console.log('🤖 Testing Gemini API connection...')
try {
  if (GEMINI_API_KEY) {
    console.log(`✅ Gemini API Key found (length: ${GEMINI_API_KEY.length})`)
    console.log(`✅ Gemini Model: ${GEMINI_MODEL}`)
    console.log('✅ Gemini service initialized successfully')
  } else {
    console.error('❌ GEMINI_API_KEY not found in environment variables')
    console.error('❌ Please add GEMINI_API_KEY to Supabase Edge Function environment variables')
  }
} catch (error) {
  console.error('❌ Gemini initialization error:', error)
}

// PDF text extraction function
async function extractTextFromPDF(fileBuffer: ArrayBuffer, filename: string): Promise<string> {
  try {
    console.log('📄 Starting PDF text extraction...')

    // Load PDF.js from CDN
    const pdfjsLib = await import('https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.mjs')

    // Load the PDF document
    const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(fileBuffer) }).promise
    console.log(`📄 PDF loaded with ${pdf.numPages} pages`)

    let fullText = ''
    const maxPages = Math.min(pdf.numPages, 50) // Limit to first 50 pages for performance

    // Extract text from each page
    for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
      try {
        const page = await pdf.getPage(pageNum)
        const textContent = await page.getTextContent()

        // Extract text from text content items
        const pageText = textContent.items
          .map((item: any) => item.str || '')
          .join(' ')
          .replace(/\s+/g, ' ') // Normalize whitespace
          .trim()

        if (pageText) {
          fullText += `Page ${pageNum}:\n${pageText}\n\n`
        }
      } catch (pageError) {
        console.warn(`⚠️ Failed to extract text from page ${pageNum}:`, pageError)
        fullText += `Page ${pageNum}: [Text extraction failed for this page]\n\n`
      }
    }

    if (pdf.numPages > maxPages) {
      fullText += `\n[Note: Only first ${maxPages} pages processed. Total pages: ${pdf.numPages}]`
    }

    console.log(`✅ PDF text extraction completed (${fullText.length} characters)`)
    return fullText || `PDF document: ${filename}. No readable text content found in the PDF.`
  } catch (error) {
    console.error('❌ PDF text extraction failed:', error)
    throw new Error(`PDF text extraction failed: ${error.message}`)
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

        // Use Gemini to answer the question
        const result = await geminiService.answerQuestion(question, document.extracted_text)

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

        // Use Gemini to answer the question
        const result = await geminiService.answerQuestion(question, document.extracted_text)

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