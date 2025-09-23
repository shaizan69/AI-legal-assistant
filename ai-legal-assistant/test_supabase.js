// Test Supabase connection
// Run with: node test_supabase.js

const { createClient } = require('@supabase/supabase-js');

// Your Supabase credentials
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testSupabase() {
  try {
    console.log('🔍 Testing Supabase connection...');
    
    // Test 1: Check if we can connect
    const { data, error } = await supabase
      .from('_supabase_migrations')
      .select('*')
      .limit(1);
    
    if (error) {
      console.log('❌ Connection failed:', error.message);
      return;
    }
    
    console.log('✅ Supabase connection successful!');
    
    // Test 2: Check storage bucket
    console.log('🔍 Testing storage bucket...');
    const { data: buckets, error: bucketError } = await supabase.storage.listBuckets();
    
    if (bucketError) {
      console.log('❌ Storage access failed:', bucketError.message);
      return;
    }
    
    const legalBucket = buckets.find(bucket => bucket.name === 'legal-documents');
    if (legalBucket) {
      console.log('✅ Storage bucket "legal-documents" found!');
    } else {
      console.log('⚠️  Storage bucket "legal-documents" not found. Please create it in your Supabase dashboard.');
    }
    
    console.log('🎉 Supabase setup test completed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testSupabase();
