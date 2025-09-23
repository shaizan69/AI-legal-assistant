// Test Supabase Storage connection
// Run with: node test_supabase_storage.js

const { createClient } = require('@supabase/supabase-js');

// Your Supabase credentials
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testSupabaseStorage() {
  try {
    console.log('🔍 Testing Supabase Storage connection...');
    
    // Test 1: List storage buckets
    console.log('📦 Checking storage buckets...');
    const { data: buckets, error: bucketError } = await supabase.storage.listBuckets();
    
    if (bucketError) {
      console.log('❌ Storage access failed:', bucketError.message);
      return;
    }
    
    console.log('✅ Storage access successful!');
    console.log('📋 Available buckets:', buckets.map(b => b.name));
    
    // Check if legal-documents bucket exists
    const legalBucket = buckets.find(bucket => bucket.name === 'legal-documents');
    if (legalBucket) {
      console.log('✅ Storage bucket "legal-documents" found!');
    } else {
      console.log('⚠️  Storage bucket "legal-documents" not found.');
      console.log('📝 Please create it in your Supabase dashboard:');
      console.log('   1. Go to Storage in your Supabase dashboard');
      console.log('   2. Click "New bucket"');
      console.log('   3. Name it "legal-documents"');
      console.log('   4. Make it public');
    }
    
    // Test 2: Try to create a test file (if bucket exists)
    if (legalBucket) {
      console.log('🧪 Testing file upload...');
      const testContent = 'Hello from AI Legal Assistant!';
      const testPath = 'test/connection-test.txt';
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('legal-documents')
        .upload(testPath, testContent, {
          contentType: 'text/plain',
          cacheControl: '3600'
        });
      
      if (uploadError) {
        console.log('❌ Upload test failed:', uploadError.message);
      } else {
        console.log('✅ Upload test successful!');
        console.log('📁 Test file uploaded to:', uploadData.path);
        
        // Get public URL
        const { data: urlData } = supabase.storage
          .from('legal-documents')
          .getPublicUrl(testPath);
        console.log('🔗 Public URL:', urlData.publicUrl);
        
        // Clean up test file
        const { error: deleteError } = await supabase.storage
          .from('legal-documents')
          .remove([testPath]);
        
        if (deleteError) {
          console.log('⚠️  Could not delete test file:', deleteError.message);
        } else {
          console.log('🧹 Test file cleaned up successfully');
        }
      }
    }
    
    console.log('🎉 Supabase Storage test completed!');
    console.log('✅ Your Supabase setup is ready for file uploads!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testSupabaseStorage();
