#!/usr/bin/env node
/**
 * Debug file upload process
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Supabase configuration
const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMjM1NTUsImV4cCI6MjA3Mzc5OTU1NX0.hSyovFYu7-G0AXWnGCnLq_yxeTLJzWUhdTbb3AFgWJc';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testUpload() {
  console.log('🧪 Testing Supabase Upload...');
  
  try {
    // Test 1: Check if we can connect to Supabase
    console.log('1. Testing Supabase connection...');
    const { data: buckets, error: bucketsError } = await supabase.storage.listBuckets();
    
    if (bucketsError) {
      console.error('❌ Error listing buckets:', bucketsError);
      return;
    }
    
    console.log('✅ Supabase connection successful');
    console.log('📋 Available buckets:', buckets.map(b => b.name));
    
    // Test 2: Check if legal-documents bucket exists
    const legalBucket = buckets.find(b => b.name === 'legal-documents');
    if (!legalBucket) {
      console.error('❌ legal-documents bucket not found!');
      console.log('Available buckets:', buckets.map(b => b.name));
      return;
    }
    
    console.log('✅ legal-documents bucket found');
    
    // Test 3: Try to upload a test file
    console.log('2. Testing file upload...');
    
    // Create a test file
    const testContent = 'This is a test document for upload testing.';
    const testFileName = `test_${Date.now()}.txt`;
    const testPath = `test-user/${testFileName}`;
    
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(testPath, testContent, {
        cacheControl: '3600',
        upsert: false
      });
    
    if (uploadError) {
      console.error('❌ Upload failed:', uploadError);
      console.error('Error details:', JSON.stringify(uploadError, null, 2));
      return;
    }
    
    console.log('✅ File uploaded successfully!');
    console.log('📁 Upload path:', uploadData.path);
    
    // Test 4: Get public URL
    console.log('3. Testing public URL generation...');
    const { data: urlData } = supabase.storage
      .from('legal-documents')
      .getPublicUrl(testPath);
    
    console.log('✅ Public URL generated:', urlData.publicUrl);
    
    // Test 5: Clean up - delete the test file
    console.log('4. Cleaning up test file...');
    const { error: deleteError } = await supabase.storage
      .from('legal-documents')
      .remove([testPath]);
    
    if (deleteError) {
      console.warn('⚠️ Could not delete test file:', deleteError);
    } else {
      console.log('✅ Test file cleaned up');
    }
    
    console.log('🎉 All tests passed! Upload should work.');
    
  } catch (error) {
    console.error('❌ Test failed with error:', error);
  }
}

testUpload();
