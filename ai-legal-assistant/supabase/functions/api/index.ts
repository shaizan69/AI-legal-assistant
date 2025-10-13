import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
}

// Gemini API configuration
const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY') ?? ''
const GEMINI_MODEL = Deno.env.get('GEMINI_MODEL') ?? 'gemini-2.5-flash'

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