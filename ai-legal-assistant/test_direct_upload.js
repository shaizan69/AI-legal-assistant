// Direct upload test - bypasses bucket listing
// Run with: node test_direct_upload.js

const { createClient } = require('@supabase/supabase-js');

// Your Supabase credentials
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testDirectUpload() {
  try {
    console.log('🚀 Testing direct file upload to legal-documents bucket...');
    
    // Create a simple test file
    const testContent = `Test Legal Document
This is a test document for the AI Legal Assistant.
Created at: ${new Date().toISOString()}

This document contains sample legal text that would typically be found in contracts, agreements, or other legal documents.`;
    
    const testPath = `test-direct-${Date.now()}.txt`;
    
    console.log('📄 Creating test file...');
    console.log('📁 File path:', testPath);
    
    // Try to upload directly to the bucket
    console.log('⬆️  Uploading to legal-documents bucket...');
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(testPath, testContent, {
        contentType: 'text/plain',
        cacheControl: '3600'
      });
    
    if (uploadError) {
      console.log('❌ Upload failed:', uploadError.message);
      
      if (uploadError.message.includes('new row violates row-level security policy')) {
        console.log('💡 This is an RLS (Row Level Security) issue.');
        console.log('📋 Solutions:');
        console.log('   1. Go to Supabase Dashboard → Storage → Policies');
        console.log('   2. Disable RLS for legal-documents bucket temporarily');
        console.log('   3. Or run the SQL policies in setup_storage_policies.sql');
      }
      return;
    }
    
    console.log('✅ Upload successful!');
    console.log('📁 Uploaded to:', uploadData.path);
    
    // Get public URL
    console.log('🔗 Getting public URL...');
    const { data: urlData } = supabase.storage
      .from('legal-documents')
      .getPublicUrl(uploadData.path);
    
    console.log('✅ Public URL:', urlData.publicUrl);
    
    // Test file access
    console.log('🌐 Testing file access...');
    try {
      const response = await fetch(urlData.publicUrl);
      if (response.ok) {
        const content = await response.text();
        console.log('✅ File is accessible!');
        console.log('📄 File content preview:', content.substring(0, 100) + '...');
      } else {
        console.log('❌ File not accessible. Status:', response.status);
      }
    } catch (error) {
      console.log('❌ File access test failed:', error.message);
    }
    
    // Clean up
    console.log('🧹 Cleaning up...');
    const { error: deleteError } = await supabase.storage
      .from('legal-documents')
      .remove([uploadData.path]);
    
    if (deleteError) {
      console.log('⚠️  Could not delete test file:', deleteError.message);
    } else {
      console.log('✅ Test file cleaned up');
    }
    
    console.log('🎉 Direct upload test completed!');
    console.log('✅ Your Supabase storage is working!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testDirectUpload();
