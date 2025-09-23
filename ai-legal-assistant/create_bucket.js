#!/usr/bin/env node
/**
 * Create Supabase bucket using service role key
 */

const { createClient } = require('@supabase/supabase-js');

// Use service role key for admin operations - New Project
const supabaseUrl = 'https://iuxqomqbxfoetnieaorw.supabase.co';
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1eHFvbXFieGZvZXRuaWVhb3J3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODMxNzA1OSwiZXhwIjoyMDczODkzMDU5fQ.hB0ZH93Wv-KCwwTQZBfJ2xia-kH75s8xYLBx6q5SoT4';

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function createBucket() {
  console.log('🪣 Creating Supabase bucket...');
  
  try {
    // Create the bucket
    const { data, error } = await supabase.storage.createBucket('legal-documents', {
      public: true,
      allowedMimeTypes: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
      fileSizeLimit: 10485760 // 10MB
    });
    
    if (error) {
      console.error('❌ Error creating bucket:', error);
      return;
    }
    
    console.log('✅ Bucket created successfully!');
    console.log('📋 Bucket details:', data);
    
    // Test listing buckets
    const { data: buckets, error: listError } = await supabase.storage.listBuckets();
    
    if (listError) {
      console.error('❌ Error listing buckets:', listError);
      return;
    }
    
    console.log('📋 Available buckets:', buckets.map(b => b.name));
    
  } catch (error) {
    console.error('❌ Failed to create bucket:', error);
  }
}

createBucket();
