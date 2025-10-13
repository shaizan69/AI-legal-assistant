# Vercel Deployment Guide for AI Legal Assistant

## 🚀 Quick Deployment Steps

### 1. **Deploy Frontend to Vercel**

1. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub
2. **Click "New Project"**
3. **Import your repository** (the one containing this project)
4. **Set the following settings:**
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend` (important!)
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

### 2. **Set Environment Variables in Vercel**

In your Vercel project dashboard, go to **Settings > Environment Variables** and add:

```
REACT_APP_API_URL = https://your-backend-url.vercel.app
REACT_APP_SUPABASE_URL = https://iuxqomqbxfoetnieaorw.supabase.co
REACT_APP_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1eHFvbXFieGZvZXRuaWVhb3J3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgzMTcwNTksImV4cCI6MjA3Mzg5MzA1OX0.srnZNdTn781Ay7F-rJO7xvD8mHMXsSQjMRXf0jKeX7E
```

### 3. **Deploy Backend (Optional - for full functionality)**

Since your backend uses Python/FastAPI, you have several options:

#### Option A: Deploy Backend to Vercel (Recommended)
1. Create a separate Vercel project for the backend
2. Use Vercel's Python runtime
3. Set up environment variables for database connections

#### Option B: Use External Backend Service
- Deploy backend to Railway, Render, or Heroku
- Update `REACT_APP_API_URL` to point to your deployed backend

#### Option C: Use Supabase Edge Functions
- Convert backend API to Supabase Edge Functions
- This keeps everything in one platform

## 🔧 Configuration Files Created

### `vercel.json`
```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "installCommand": "npm install",
  "framework": "create-react-app",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### `.env.production`
Contains production environment variables for the frontend.

### `.vercelignore`
Excludes unnecessary files from deployment.

## 🐛 Common Issues & Solutions

### Issue 1: 404 NOT_FOUND Error
**Cause**: Wrong root directory or missing configuration
**Solution**: 
- Set Root Directory to `frontend`
- Ensure `vercel.json` is in the frontend folder
- Check that `package.json` exists in frontend folder

### Issue 2: Build Failures
**Cause**: Missing dependencies or environment variables
**Solution**:
- Check that all dependencies are in `package.json`
- Ensure environment variables are set in Vercel dashboard
- Check build logs for specific errors

### Issue 3: API Connection Issues
**Cause**: Backend not deployed or wrong API URL
**Solution**:
- Deploy backend separately
- Update `REACT_APP_API_URL` environment variable
- Check CORS settings in backend

## 📋 Pre-Deployment Checklist

- [ ] `vercel.json` file created in frontend directory
- [ ] `.env.production` file created with correct values
- [ ] `.vercelignore` file created
- [ ] Environment variables set in Vercel dashboard
- [ ] Root directory set to `frontend`
- [ ] Backend deployed (if using full-stack functionality)
- [ ] API URL updated in environment variables

## 🎯 Deployment Commands

### Local Testing
```bash
cd frontend
npm install
npm run build
npm start
```

### Vercel CLI (Alternative)
```bash
npm i -g vercel
cd frontend
vercel
```

## 🔗 Important URLs

- **Frontend**: `https://your-project-name.vercel.app`
- **Backend**: `https://your-backend-name.vercel.app` (if deployed separately)
- **Supabase**: `https://iuxqomqbxfoetnieaorw.supabase.co`

## 📞 Support

If you encounter issues:
1. Check Vercel build logs
2. Verify environment variables
3. Test locally first
4. Check browser console for errors

---

**Note**: This deployment guide assumes you're deploying only the frontend. For full-stack deployment, you'll need to deploy the backend separately or use a different platform that supports Python/FastAPI.
