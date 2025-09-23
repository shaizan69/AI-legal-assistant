#!/usr/bin/env node
/**
 * Check bucket with service role key
 */

const { createClient } = require('@supabase/supabase-js');

// Use service role key for admin operations
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODIyMzU1NSwiZXhwIjoyMDczNzk5NTU1fQ.UkQYHsWqhxDNT3XKu04UxfXDOZ1lX-uPqZuhtYTJhdQ';

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function checkBucket() {
  console.log('🔍 Checking bucket with service role key...');
  
  try {
    // List buckets
    const { data: buckets, error: listError } = await supabase.storage.listBuckets();
    
    if (listError) {
      console.error('❌ Error listing buckets:', listError);
      return;
    }
    
    console.log('✅ Buckets found:', buckets.map(b => b.name));
    
    const legalBucket = buckets.find(b => b.name === 'legal-documents');
    if (legalBucket) {
      console.log('✅ legal-documents bucket exists');
      console.log('📋 Bucket details:', legalBucket);
      
      // Try to list files in the bucket
      const { data: files, error: filesError } = await supabase.storage
        .from('legal-documents')
        .list('', { limit: 10 });
      
      if (filesError) {
        console.error('❌ Error listing files:', filesError);
      } else {
        console.log('📁 Files in bucket:', files.length);
        if (files.length > 0) {
          console.log('📄 Sample files:', files.slice(0, 3).map(f => f.name));
        }
      }
      
      // Test upload with service role
      console.log('🧪 Testing upload with service role...');
      const testContent = 'Test file for service role upload';
      const testPath = `test-service-role-${Date.now()}.txt`;
      
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('legal-documents')
        .upload(testPath, testContent);
      
      if (uploadError) {
        console.error('❌ Service role upload failed:', uploadError);
      } else {
        console.log('✅ Service role upload successful:', uploadData.path);
        
        // Clean up
        await supabase.storage.from('legal-documents').remove([testPath]);
        console.log('🧹 Test file cleaned up');
      }
      
    } else {
      console.error('❌ legal-documents bucket not found');
    }
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

checkBucket();
