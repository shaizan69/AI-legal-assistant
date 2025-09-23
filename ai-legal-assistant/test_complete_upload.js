// Complete upload test after bucket creation
// Run with: node test_complete_upload.js

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Your Supabase credentials
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testCompleteUpload() {
  try {
    console.log('🚀 Testing complete file upload flow...');
    
    // Test 1: Check if bucket exists
    console.log('📦 Checking for legal-documents bucket...');
    const { data: buckets, error: bucketError } = await supabase.storage.listBuckets();
    
    if (bucketError) {
      console.log('❌ Storage access failed:', bucketError.message);
      return;
    }
    
    const legalBucket = buckets.find(bucket => bucket.name === 'legal-documents');
    if (!legalBucket) {
      console.log('❌ legal-documents bucket not found. Please create it first!');
      return;
    }
    
    console.log('✅ legal-documents bucket found!');
    
    // Test 2: Create a test PDF file
    console.log('📄 Creating test document...');
    const testContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Legal Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF`;
    
    const testFilePath = 'test-upload.pdf';
    fs.writeFileSync(testFilePath, testContent);
    
    // Test 3: Upload file
    console.log('⬆️  Uploading test file...');
    const fileBuffer = fs.readFileSync(testFilePath);
    const uploadPath = `test/${Date.now()}-test-upload.pdf`;
    
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(uploadPath, fileBuffer, {
        contentType: 'application/pdf',
        cacheControl: '3600'
      });
    
    if (uploadError) {
      console.log('❌ Upload failed:', uploadError.message);
      return;
    }
    
    console.log('✅ File uploaded successfully!');
    console.log('📁 Upload path:', uploadData.path);
    
    // Test 4: Get public URL
    console.log('🔗 Getting public URL...');
    const { data: urlData } = supabase.storage
      .from('legal-documents')
      .getPublicUrl(uploadData.path);
    
    console.log('✅ Public URL generated:', urlData.publicUrl);
    
    // Test 5: Test file access
    console.log('🌐 Testing file access...');
    try {
      const response = await fetch(urlData.publicUrl);
      if (response.ok) {
        console.log('✅ File is accessible via public URL!');
      } else {
        console.log('❌ File not accessible:', response.status);
      }
    } catch (error) {
      console.log('❌ File access test failed:', error.message);
    }
    
    // Test 6: Clean up
    console.log('🧹 Cleaning up test files...');
    const { error: deleteError } = await supabase.storage
      .from('legal-documents')
      .remove([uploadData.path]);
    
    if (deleteError) {
      console.log('⚠️  Could not delete test file:', deleteError.message);
    } else {
      console.log('✅ Test file cleaned up');
    }
    
    // Clean up local file
    fs.unlinkSync(testFilePath);
    
    console.log('🎉 Complete upload test successful!');
    console.log('✅ Your file upload system is ready to use!');
    console.log('');
    console.log('📋 Next steps:');
    console.log('1. Start your backend: cd backend && python -m uvicorn app.main:app --reload');
    console.log('2. Start your frontend: cd frontend && npm start');
    console.log('3. Go to http://localhost:3000/upload to test the upload page!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testCompleteUpload();
