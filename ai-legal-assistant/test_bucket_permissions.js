// Test bucket permissions and create if needed
// Run with: node test_bucket_permissions.js

const { createClient } = require('@supabase/supabase-js');

// Your Supabase credentials
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testBucketPermissions() {
  try {
    console.log('🔍 Testing bucket permissions...');
    
    // Test 1: List all buckets
    console.log('📦 Listing all buckets...');
    const { data: buckets, error: bucketError } = await supabase.storage.listBuckets();
    
    if (bucketError) {
      console.log('❌ Error listing buckets:', bucketError.message);
      console.log('💡 This might be a permissions issue with the anon key');
      return;
    }
    
    console.log('✅ Buckets listed successfully');
    console.log('📋 Available buckets:', buckets.map(b => `${b.name} (${b.public ? 'public' : 'private'})`));
    
    // Test 2: Try to create the bucket if it doesn't exist
    const legalBucket = buckets.find(bucket => bucket.name === 'legal-documents');
    if (!legalBucket) {
      console.log('📝 legal-documents bucket not found. Attempting to create...');
      
      const { data: createData, error: createError } = await supabase.storage.createBucket('legal-documents', {
        public: true,
        fileSizeLimit: 52428800, // 50MB
        allowedMimeTypes: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
      });
      
      if (createError) {
        console.log('❌ Could not create bucket:', createError.message);
        console.log('💡 You may need to create it manually in the dashboard');
        return;
      }
      
      console.log('✅ Bucket created successfully!');
    } else {
      console.log('✅ legal-documents bucket found!');
      console.log(`   Public: ${legalBucket.public ? 'Yes' : 'No'}`);
      console.log(`   Created: ${new Date(legalBucket.created_at).toLocaleString()}`);
    }
    
    // Test 3: Try to upload a test file
    console.log('🧪 Testing file upload...');
    const testContent = 'Test file content';
    const testPath = `test-${Date.now()}.txt`;
    
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(testPath, testContent, {
        contentType: 'text/plain',
        cacheControl: '3600'
      });
    
    if (uploadError) {
      console.log('❌ Upload failed:', uploadError.message);
      console.log('💡 This might be a permissions issue. Check RLS policies.');
    } else {
      console.log('✅ Upload successful!');
      console.log('📁 File path:', uploadData.path);
      
      // Get public URL
      const { data: urlData } = supabase.storage
        .from('legal-documents')
        .getPublicUrl(uploadData.path);
      console.log('🔗 Public URL:', urlData.publicUrl);
      
      // Clean up
      const { error: deleteError } = await supabase.storage
        .from('legal-documents')
        .remove([uploadData.path]);
      
      if (deleteError) {
        console.log('⚠️  Could not delete test file:', deleteError.message);
      } else {
        console.log('🧹 Test file cleaned up');
      }
    }
    
    console.log('🎉 Bucket permissions test completed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testBucketPermissions();
