# Add Gemini API Key to Supabase Edge Function

Your Gemini API key is: `AIzaSyC_iQf6dNwLi6VlPJEp4FlRokDCJ6091vc`

## IMPORTANT: This needs to be added to Supabase Dashboard

Even though you have it in `.env`, the **Supabase Edge Function** needs it in the **Supabase Dashboard environment variables**.

## Steps to Add the Key:

### 1. Go to Your Supabase Dashboard
- URL: https://supabase.com/dashboard/project/iuxqomqbxfoetnieaorw
- Click on **"Edge Functions"** in the left sidebar
- Click on **"api"** function

### 2. Go to Settings
- Look for **"Settings"** or **"Configuration"** tab
- Find **"Environment Variables"** section

### 3. Add the Environment Variables

Add these two variables:

**Variable 1:**
- Key: `GEMINI_API_KEY`
- Value: `AIzaSyC_iQf6dNwLi6VlPJEp4FlRokDCJ6091vc`

**Variable 2:**
- Key: `GEMINI_MODEL`
- Value: `gemini-2.5-flash` (already in your .env)

### 4. Save and Redeploy

The function should automatically redeploy. If not, click the **"Deploy"** button.

## Alternative: Using Supabase CLI

You can also use the Supabase CLI to add secrets:

```bash
supabase secrets set GEMINI_API_KEY=AIzaSyC_iQf6dNwLi6VlPJEp4FlRokDCJ6091vc --project-ref iuxqomqbxfoetnieaorw
supabase secrets set GEMINI_MODEL=gemini-2.5-flash --project-ref iuxqomqbxfoetnieaorw
```

## Verify It Works

After adding the key, wait a minute for the function to redeploy, then test:

```powershell
# Test if the function is working
Invoke-WebRequest -Uri "https://iuxqomqbxfoetnieaorw.supabase.co/functions/v1/api/" -Headers @{"apikey"="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1eHFvbXFieGZvZXRuaWVhb3J3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgzMTcwNTksImV4cCI6MjA3Mzg5MzA1OX0.srnZNdTn781Ay7F-rJO7xvD8mHMXsSQjMRXf0jKeX7E"} -Method GET
```

## Why This Is Needed

- `.env` file is for local development
- Supabase Edge Functions need environment variables set in the **cloud dashboard**
- Edge Functions run in a separate environment that doesn't read your local `.env` file

## Once Done

After adding the key, your entire system will work:
- ✅ Document upload
- ✅ PDF text extraction
- ✅ Q&A with Gemini
- ✅ Risk analysis with Gemini
