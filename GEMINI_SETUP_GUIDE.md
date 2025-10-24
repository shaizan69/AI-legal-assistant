# 🚨 URGENT: Gemini API Setup Required

## **Critical Issue: Missing Gemini API Key**

The system is failing because the **Gemini API key is not configured** in your Supabase Edge Function. Here's how to fix it:

## **Step 1: Get Gemini API Key**

1. **Go to Google AI Studio**: https://aistudio.google.com/
2. **Sign in** with your Google account
3. **Click "Create API Key"** in the left sidebar
4. **Copy the generated API key** (it looks like `AIza...`)

## **Step 2: Add API Key to Supabase**

1. **Go to Supabase Dashboard**:
   - URL: https://supabase.com/dashboard/project/iuxqomqbxfoetnieaorw/functions

2. **Edit the `api` function**:
   - Click on the `api` function in the Functions list
   - Click "Edit function"

3. **Add Environment Variables**:
   ```
   GEMINI_API_KEY=AIzaSyYourActualApiKeyHere123456789
   GEMINI_MODEL=gemini-2.0-flash-exp
   ```

4. **Deploy the function** (it redeploys automatically)

## **Step 3: Verify Setup**

1. **Check Edge Function Logs**:
   - Go to: https://supabase.com/dashboard/project/iuxqomqbxfoetnieaorw/functions/api/logs
   - Look for: `✅ Gemini API Key found` and `✅ Gemini service initialized successfully`

2. **Test the API**:
   - Go to: https://iuxqomqbxfoetnieaorw.supabase.co/functions/v1/api/test
   - Should show successful response

## **Step 4: Test Complete System**

1. **Upload a PDF document** in your app
2. **Create a Q&A session**
3. **Ask a question** - should get real AI response based on document content
4. **Try risk analysis** - should analyze document content

## **Common Issues & Solutions**

### **❌ "GEMINI_API_KEY not found"**
- **Solution**: Add the environment variable in Supabase dashboard

### **❌ "Gemini API error: 400"**
- **Solution**: Check that your API key is correct and has proper permissions

### **❌ "No response from Gemini"**
- **Solution**: Verify the model name `gemini-2.0-flash-exp` is correct

### **❌ Document upload works but Q&A fails**
- **Solution**: The Gemini API key is missing from environment variables

## **Current Configuration Status**

✅ **Edge Function**: Deployed with PDF text extraction
✅ **Database**: Tables created and connected
✅ **Storage**: Bucket configured
❌ **Gemini API**: **MISSING API KEY** ← **THIS IS THE ISSUE**

## **Quick Test**

Run this in your browser console after uploading a document:
```javascript
// Test if Gemini is working
fetch('https://iuxqomqbxfoetnieaorw.supabase.co/functions/v1/api/test')
  .then(r => r.json())
  .then(console.log)
```

**The system will NOT work for Q&A until you add the Gemini API key!** 🚨

Once you add the API key, the legal assistant will have full AI capabilities for:
- ✅ Answering questions based on document content
- ✅ Providing risk analysis
- ✅ Understanding context from uploaded documents
