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
    
    // Normalize path
    let path = rawPath
      .replace(/^\/(functions\/v\d+)?\/?api(\/|$)/, '/')
      .replace(/^\/(functions\/v\d+)(\/|$)/, '/')
      .replace(/\/+/g, '/')
    if (path.length > 1 && path.endsWith('/')) {
      path = path.slice(0, -1)
    }

    console.log(`Request: ${method} ${path} (raw: ${rawPath})`)

    // Test endpoint
    if (path === '/test' && method === 'GET') {
      return new Response(
        JSON.stringify({ 
          message: 'Edge Function is working!',
          timestamp: new Date().toISOString(),
          path: path,
          method: method
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
        
        console.log(`Login attempt: ${username}, password: ${password}`)
        
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
      } catch (error) {
        console.error('Login error:', error)
        return new Response(
          JSON.stringify({ error: 'Login failed', details: error.message }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 500 
          }
        )
      }
    }

    // User info endpoint
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

    // Default response
    return new Response(
      JSON.stringify({ 
        error: 'Endpoint not found',
        path: path,
        method: method,
        available_endpoints: ['/test', '/auth/login', '/auth/me']
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