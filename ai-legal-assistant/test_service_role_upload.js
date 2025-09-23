// Test upload with service role key
// Run with: node test_service_role_upload.js

const { createClient } = require('@supabase/supabase-js');

// Your Supabase credentials
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const serviceRoleKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODIyMzU1NSwiZXhwIjoyMDczNzk5NTU1fQ.UkQYHsWqhxDNT3XKu04UxfXDOZ1lX-uPqZuhtYTJhdQ';

const supabase = createClient(supabaseUrl, serviceRoleKey);

async function testServiceRoleUpload() {
  try {
    console.log('🚀 Testing upload with service role key...');
    
    // Test 1: List buckets (should work with service role)
    console.log('📦 Listing storage buckets...');
    const { data: buckets, error: bucketError } = await supabase.storage.listBuckets();
    
    if (bucketError) {
      console.log('❌ Error listing buckets:', bucketError.message);
      return;
    }
    
    console.log('✅ Buckets listed successfully!');
    console.log('📋 Available buckets:', buckets.map(b => `${b.name} (${b.public ? 'public' : 'private'})`));
    
    // Check if legal-documents bucket exists
    const legalBucket = buckets.find(bucket => bucket.name === 'legal-documents');
    if (!legalBucket) {
      console.log('❌ legal-documents bucket not found!');
      return;
    }
    
    console.log('✅ legal-documents bucket found!');
    console.log(`   Public: ${legalBucket.public ? 'Yes' : 'No'}`);
    
    // Test 2: Create a test PDF file
    console.log('📄 Creating test PDF document...');
    const testPdfContent = `%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 16 Tf
72 720 Td
(AI Legal Assistant Test Document) Tj
0 -30 Td
/F1 12 Tf
(This is a test document for file upload functionality.) Tj
0 -20 Td
(Created: ${new Date().toISOString()}) Tj
0 -20 Td
(File Type: PDF) Tj
0 -20 Td
(Status: Upload Test) Tj
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
450
%%EOF`;
    
    const testPath = `test-uploads/service-role-test-${Date.now()}.pdf`;
    
    // Test 3: Upload file
    console.log('⬆️  Uploading test PDF...');
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(testPath, testPdfContent, {
        contentType: 'application/pdf',
        cacheControl: '3600'
      });
    
    if (uploadError) {
      console.log('❌ Upload failed:', uploadError.message);
      return;
    }
    
    console.log('✅ Upload successful!');
    console.log('📁 File uploaded to:', uploadData.path);
    
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
        console.log('📊 Response status:', response.status);
        console.log('📏 Content length:', response.headers.get('content-length'));
      } else {
        console.log('❌ File not accessible. Status:', response.status);
      }
    } catch (error) {
      console.log('❌ File access test failed:', error.message);
    }
    
    // Test 6: List files in bucket
    console.log('📋 Listing files in bucket...');
    const { data: files, error: listError } = await supabase.storage
      .from('legal-documents')
      .list('test-uploads', {
        limit: 10,
        sortBy: { column: 'created_at', order: 'desc' }
      });
    
    if (listError) {
      console.log('⚠️  Could not list files:', listError.message);
    } else {
      console.log('✅ Files in bucket:', files.map(f => f.name));
    }
    
    // Test 7: Clean up
    console.log('🧹 Cleaning up test file...');
    const { error: deleteError } = await supabase.storage
      .from('legal-documents')
      .remove([uploadData.path]);
    
    if (deleteError) {
      console.log('⚠️  Could not delete test file:', deleteError.message);
    } else {
      console.log('✅ Test file cleaned up successfully');
    }
    
    console.log('🎉 Service role upload test completed!');
    console.log('✅ Your Supabase storage is fully functional!');
    console.log('');
    console.log('🚀 Ready to start your application:');
    console.log('   Backend: cd backend && python -m uvicorn app.main:app --reload');
    console.log('   Frontend: cd frontend && npm start');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testServiceRoleUpload();
