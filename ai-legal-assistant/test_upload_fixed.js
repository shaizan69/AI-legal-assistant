#!/usr/bin/env node
/**
 * Test upload with service role key
 */

const { createClient } = require('@supabase/supabase-js');

// Use service role key for uploads
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODIyMzU1NSwiZXhwIjoyMDczNzk5NTU1fQ.UkQYHsWqhxDNT3XKu04UxfXDOZ1lX-uPqZuhtYTJhdQ';

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function testUpload() {
  console.log('🧪 Testing Fixed Upload...');
  
  try {
    // Test upload
    const testContent = 'This is a test document for the fixed upload.';
    const testFileName = `test-fixed-${Date.now()}.txt`;
    const testPath = `test-user/${testFileName}`;
    
    console.log('📤 Uploading file...');
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(testPath, testContent, {
        cacheControl: '3600',
        upsert: false
      });
    
    if (uploadError) {
      console.error('❌ Upload failed:', uploadError);
      return;
    }
    
    console.log('✅ Upload successful!');
    console.log('📁 Path:', uploadData.path);
    
    // Get public URL
    const { data: urlData } = supabase.storage
      .from('legal-documents')
      .getPublicUrl(testPath);
    
    console.log('🔗 Public URL:', urlData.publicUrl);
    
    // Clean up
    console.log('🧹 Cleaning up...');
    const { error: deleteError } = await supabase.storage
      .from('legal-documents')
      .remove([testPath]);
    
    if (deleteError) {
      console.warn('⚠️ Could not delete test file:', deleteError);
    } else {
      console.log('✅ Test file cleaned up');
    }
    
    console.log('🎉 Upload is working! The frontend should now work.');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testUpload();
