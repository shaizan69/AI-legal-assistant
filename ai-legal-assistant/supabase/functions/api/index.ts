import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
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
        
        console.log(`Q&A question: ${question}`)
        
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

        // Simple response for now
        const answer = `I received your question: "${question}". This is a test response from the Edge Function.`
        
        return new Response(
          JSON.stringify({ 
            answer,
            question_id: Date.now(),
            session_id: session_id || 1,
            timestamp: new Date().toISOString()
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      } catch (error) {
        console.error('Q&A error:', error)
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
        
        console.log(`Free Q&A question: ${question}`)
        
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

        // Simple response for now
        const answer = `I received your free question: "${question}". This is a test response from the Edge Function.`
        
        return new Response(
          JSON.stringify({ 
            answer,
            question_id: Date.now(),
            session_id: session_id || 1,
            timestamp: new Date().toISOString()
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      } catch (error) {
        console.error('Free Q&A error:', error)
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
        
        console.log(`Risk analysis request`)
        
        const risks = `This is a test risk analysis response. The document appears to have standard legal risks that should be reviewed by a qualified attorney.`
        
        return new Response(
          JSON.stringify({ 
            risks,
            session_id: session_id || 1,
            timestamp: new Date().toISOString()
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      } catch (error) {
        console.error('Risk analysis error:', error)
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
    if (path === '/free/session' && (method === 'GET' || method === 'POST')) {
      const sessionId = Date.now()
      console.log(`Creating session: ${sessionId}`)
      
      return new Response(
        JSON.stringify({ 
          session_id: sessionId,
          message: 'Session created successfully',
          timestamp: new Date().toISOString()
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      )
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

    // Documents list
    if ((path === '/upload' || path === '/upload/') && method === 'GET') {
      console.log('Fetching documents list')
      
      return new Response(
        JSON.stringify({ 
          documents: [], 
          pages: 1, 
          total: 0,
          message: 'No documents found',
          timestamp: new Date().toISOString()
        }), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }, 
          status: 200 
        }
      )
    }

    // Free upload - simple working logic
    if (path === '/free/upload' && method === 'POST') {
      try {
        if (!req.headers.get('content-type')?.includes('multipart/form-data')) {
          return new Response(
            JSON.stringify({ error: 'multipart/form-data required' }), 
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
          )
        }
        
        const form = await req.formData()
        const file = form.get('file') as File | null
        
        if (!file) {
          return new Response(
            JSON.stringify({ error: 'file is required' }), 
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
          )
        }
        
        // Simple response - just return document_id like the working backend
        const document_id = Date.now()
        
        return new Response(
          JSON.stringify({ 
            document_id: document_id,
            filename: (file as File).name,
            message: 'Document uploaded successfully'
          }), 
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        )
      } catch (e) {
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