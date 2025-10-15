import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
}

// Gemini API configuration
const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY') ?? ''
const GEMINI_MODEL = Deno.env.get('GEMINI_MODEL') ?? 'gemini-2.5-flash'
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const STORAGE_BUCKET = 'legal-documents'

// Supabase Admin client for privileged operations (storage uploads)
const supabaseAdmin = SUPABASE_URL && SUPABASE_SERVICE_ROLE_KEY
  ? createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
  : null

// Helper function to call Gemini API
async function callGeminiAPI(prompt: string, context: string = '') {
  try {
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: `${context}\n\nQuestion: ${prompt}\n\nAnswer:`
          }]
        }],
        generationConfig: {
          temperature: 0.7,
          topK: 40,
          topP: 0.95,
          maxOutputTokens: 2048,
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`)
    }

    const data = await response.json()
    return data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated'
  } catch (error) {
    console.error('Gemini API error:', error)
    return 'Sorry, I encountered an error while processing your question.'
  }
}

// Helper: read payload from POST/GET (query fallback for public endpoints)
async function readPayload(req: Request, method: string, urlObj: URL): Promise<Record<string, unknown>> {
  if (method === 'GET') {
    const params = Object.fromEntries(urlObj.searchParams.entries())
    return params
  }
  try {
    return await req.json()
  } catch {
    return {}
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
    // normalize so both /api/xyz and /xyz work
    const path = rawPath.replace(/^\/api(\/|$)/, '/');

    console.log(`Request: ${method} ${path}`)

    // Test endpoint - always works
    if (path === '/test' && method === 'GET') {
      return new Response(
        JSON.stringify({ 
          message: 'Edge Function is working!',
          timestamp: new Date().toISOString(),
          path: path,
          method: method,
          gemini_key_set: GEMINI_API_KEY ? 'YES' : 'NO'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Login endpoint - accept POST body or GET query (?username=&password=)
    if (path === '/auth/login') {
      const payload = await readPayload(req, method, urlObj)
      const username = String(payload.username ?? '')
      const password = String(payload.password ?? '')
      
      console.log(`Login attempt: ${username}`)
      
      // Simple hardcoded user
      if (username === 'test@example.com' && password === 'testpass') {
        const token = btoa(JSON.stringify({ 
          email: username, 
          exp: Date.now() + 3600000 
        }))
        
        return new Response(
          JSON.stringify({ 
            access_token: token,
            token_type: 'bearer',
            expires_in: 3600 
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      } else {
        return new Response(
          JSON.stringify({ error: 'Invalid credentials' }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 401 
          }
        )
      }
    }

    // User info endpoint - allow GET/POST for public convenience
    if (path === '/auth/me') {
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

    // Q&A endpoint - accept POST body or GET query (?question=&session_id=)
    if (path === '/qa/ask') {
      const payload = await readPayload(req, method, urlObj)
      const question = String(payload.question ?? '')
      const session_id = payload.session_id ? Number(payload.session_id) : undefined
      
      console.log(`Q&A question: ${question}`)
      
      if (!question) {
        return new Response(
          JSON.stringify({ error: 'Question is required' }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400 
          }
        )
      }

      // Call Gemini API
      const answer = await callGeminiAPI(question)
      
      return new Response(
        JSON.stringify({ 
          answer,
          question_id: Date.now(),
          session_id: session_id || 1
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
      const payload = await readPayload(req, method, urlObj)
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

    // QA Question feedback
    const qaFeedbackMatch = path.match(/^\/qa\/questions\/(\d+)\/feedback$/)
    if (qaFeedbackMatch) {
      if (method !== 'PUT') {
        return new Response(JSON.stringify({ error: 'Method Not Allowed' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 405 })
      }
      return new Response(JSON.stringify({ message: 'Feedback recorded' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }

    // Documents upload metadata (after client uploads to Supabase storage)
    if (path === '/upload/supabase' && method === 'POST') {
      const payload = await readPayload(req, method, urlObj)
      const document_id = Date.now()
      return new Response(
        JSON.stringify({ id: document_id, ...payload, message: 'Document metadata recorded' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
      )
    }

    // Documents list
    if (path === '/upload/' && method === 'GET') {
      return new Response(JSON.stringify([]), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }

    // Document detail/delete
    const uploadDetailMatch = path.match(/^\/upload\/(\d+)$/)
    if (uploadDetailMatch) {
      const docId = Number(uploadDetailMatch[1])
      if (method === 'GET') {
        return new Response(JSON.stringify({ id: docId, title: 'Document', description: '' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      if (method === 'DELETE') {
        return new Response(JSON.stringify({ message: 'Document deleted' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      return new Response(JSON.stringify({ error: 'Method Not Allowed' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 405 })
    }

    // Summarize endpoints
    if (path === '/summarize/' && method === 'POST') {
      const payload = await readPayload(req, method, urlObj)
      return new Response(JSON.stringify({ summary: 'Summary generation is stubbed for now.', document_id: payload.document_id ?? null }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }
    const summarizeDetailMatch = path.match(/^\/summarize\/(\d+)$/)
    if (summarizeDetailMatch && method === 'GET') {
      return new Response(JSON.stringify({ summary: 'No summary available yet.' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }

    // Risks endpoints
    if (path === '/risks/' && method === 'POST') {
      const payload = await readPayload(req, method, urlObj)
      const analysis = await callGeminiAPI('Provide a concise risk summary for the provided document context.')
      return new Response(JSON.stringify({ risks: analysis, document_id: payload.document_id ?? null }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }
    const risksDetailMatch = path.match(/^\/risks\/(\d+)$/)
    if (risksDetailMatch && method === 'GET') {
      return new Response(JSON.stringify({ risks: 'No risks calculated yet.' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }

    // Compare endpoints
    if (path === '/compare/' && method === 'POST') {
      const payload = await readPayload(req, method, urlObj)
      return new Response(JSON.stringify({ comparison_id: Date.now(), result: 'Comparison is stubbed.', document1_id: payload.document1_id, document2_id: payload.document2_id }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }
    if (path === '/compare/' && method === 'GET') {
      return new Response(JSON.stringify([]), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
    }
    const compareDetailMatch = path.match(/^\/compare\/(\d+)$/)
    if (compareDetailMatch) {
      if (method === 'GET') {
        return new Response(JSON.stringify({ id: Number(compareDetailMatch[1]), result: 'Comparison details are stubbed.' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      if (method === 'DELETE') {
        return new Response(JSON.stringify({ message: 'Comparison deleted' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      }
      return new Response(JSON.stringify({ error: 'Method Not Allowed' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 405 })
    }

    // Free upload - accept multipart form or JSON
    if (path === '/free/upload') {
      try {
        if (req.headers.get('content-type')?.includes('multipart/form-data')) {
          const form = await req.formData()
          const file = form.get('file')
          if (!file) {
            return new Response(JSON.stringify({ error: 'file is required' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 })
          }
          // We are not persisting the file on the server; return a fake document id
          return new Response(JSON.stringify({ document_id: Date.now(), filename: (file as File).name }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
        } else {
          const payload = await readPayload(req, method, urlObj)
          return new Response(JSON.stringify({ document_id: Date.now(), payload }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
        }
      } catch (e) {
        return new Response(JSON.stringify({ error: 'Upload failed', details: String(e) }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 })
      }
    }

    // Direct upload via Edge Function using service role (bypass RLS)
    if (path === '/upload/direct') {
      if (!supabaseAdmin) {
        return new Response(JSON.stringify({ error: 'Server storage client not configured' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 })
      }
      try {
        if (!req.headers.get('content-type')?.includes('multipart/form-data')) {
          return new Response(JSON.stringify({ error: 'multipart/form-data required' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 })
        }
        const form = await req.formData()
        const file = form.get('file') as File | null
        let pathParam = (form.get('path') as string | null) ?? ''
        if (!file) {
          return new Response(JSON.stringify({ error: 'file is required' }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 })
        }
        if (!pathParam) {
          const ts = new Date().toISOString().replace(/[:.]/g, '-')
          const fname = (file as File).name || 'upload.bin'
          pathParam = `anonymous/${ts}_${fname}`
        }
        const { data, error } = await supabaseAdmin.storage
          .from(STORAGE_BUCKET)
          .upload(pathParam, file, { upsert: false, cacheControl: '3600' })
        if (error) {
          return new Response(JSON.stringify({ error: error.message }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 })
        }
        const { data: pub } = supabaseAdmin.storage.from(STORAGE_BUCKET).getPublicUrl(pathParam)
        return new Response(JSON.stringify({ path: data?.path ?? pathParam, publicUrl: pub.publicUrl }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 })
      } catch (e) {
        return new Response(JSON.stringify({ error: 'Direct upload failed', details: String(e) }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 })
      }
    }

    // Free Q&A endpoint - accept POST body or GET query
    if (path === '/free/ask') {
      const payload = await readPayload(req, method, urlObj)
      const question = String(payload.question ?? '')
      const session_id = payload.session_id ? Number(payload.session_id) : undefined
      
      console.log(`Free Q&A question: ${question}`)
      
      if (!question) {
        return new Response(
          JSON.stringify({ error: 'Question is required' }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400 
          }
        )
      }

      // Call Gemini API
      const answer = await callGeminiAPI(question)
      
      return new Response(
        JSON.stringify({ 
          answer,
          question_id: Date.now(),
          session_id: session_id || 1
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Risk analysis endpoint - accept POST body or GET query
    if (path === '/free/analyze-risks') {
      const payload = await readPayload(req, method, urlObj)
      const session_id = payload.session_id ? Number(payload.session_id) : undefined
      
      console.log(`Risk analysis request`)
      
      const riskPrompt = `Analyze the following document for potential legal risks, compliance issues, and areas of concern. Provide a comprehensive risk assessment.`
      
      const answer = await callGeminiAPI(riskPrompt)
      
      return new Response(
        JSON.stringify({ 
          risks: answer,
          session_id: session_id || 1
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Session creation - allow GET or POST
    if (path === '/free/session') {
      const sessionId = Date.now()
      return new Response(
        JSON.stringify({ 
          session_id: sessionId,
          message: 'Session created successfully'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Session deletion - always works
    if (path.startsWith('/free/session/')) {
      return new Response(
        JSON.stringify({ 
          message: 'Session deleted successfully'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
    }

    // Default response
    return new Response(
      JSON.stringify({ 
        error: 'Endpoint not found',
        path: path,
        method: method,
        available_endpoints: [
          '/test',
          '/auth/login',
          '/auth/me',
          '/qa/ask',
          '/free/ask',
          '/free/analyze-risks',
          '/free/session'
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
        error: error.message,
        details: 'Internal server error'
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    )
  }
})