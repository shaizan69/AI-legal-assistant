// Test Supabase URL generation
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testUrlGeneration() {
  console.log('🔍 Testing Supabase URL generation...');
  
  // Test with a sample path
  const testPath = 'user123/sample-document.pdf';
  
  try {
    const { data, error } = supabase.storage
      .from('legal-documents')
      .getPublicUrl(testPath);
    
    if (error) {
      console.error('❌ Error getting public URL:', error);
      return;
    }
    
    console.log('📋 Raw response:', data);
    console.log('🔗 Public URL:', data.publicUrl);
    
    // Test if the URL is accessible
    try {
      const response = await fetch(data.publicUrl, { method: 'HEAD' });
      console.log('✅ URL is accessible:', response.status);
    } catch (fetchError) {
      console.log('❌ URL not accessible:', fetchError.message);
    }
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

testUrlGeneration();
