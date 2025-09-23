// Check if Supabase bucket is public and make it public if needed
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://mnadbvirdkzgrlzgbrai.supabase.co';
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uYWRidmlyZGt6Z3JsemdicmFpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODIyMzU1NSwiZXhwIjoyMDczNzk5NTU1fQ.UkQYHsWqhxDNT3XKu04UxfXDOZ1lX-uPqZuhtYTJhdQ';

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function checkAndFixBucket() {
  console.log('🔍 Checking Supabase bucket configuration...');
  
  try {
    // List buckets
    const { data: buckets, error: bucketsError } = await supabase.storage.listBuckets();
    
    if (bucketsError) {
      console.error('❌ Error listing buckets:', bucketsError);
      return;
    }
    
    console.log('📋 Available buckets:', buckets);
    
    // Check if legal-documents bucket exists
    const legalBucket = buckets.find(bucket => bucket.name === 'legal-documents');
    
    if (!legalBucket) {
      console.log('❌ legal-documents bucket not found');
      return;
    }
    
    console.log('📋 legal-documents bucket:', legalBucket);
    console.log('🔒 Public:', legalBucket.public);
    
    if (!legalBucket.public) {
      console.log('⚠️  Bucket is not public. Making it public...');
      
      // Make bucket public
      const { data: updateData, error: updateError } = await supabase.storage.updateBucket('legal-documents', {
        public: true
      });
      
      if (updateError) {
        console.error('❌ Error making bucket public:', updateError);
      } else {
        console.log('✅ Bucket made public successfully');
      }
    } else {
      console.log('✅ Bucket is already public');
    }
    
    // Test file upload and URL generation
    console.log('\n🧪 Testing file upload and URL generation...');
    
    const testFile = new File(['Test content'], 'test.txt', { type: 'text/plain' });
    const testPath = 'test/test.txt';
    
    // Upload test file
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('legal-documents')
      .upload(testPath, testFile);
    
    if (uploadError) {
      console.error('❌ Error uploading test file:', uploadError);
      return;
    }
    
    console.log('✅ Test file uploaded:', uploadData);
    
    // Get public URL
    const { data: urlData } = supabase.storage
      .from('legal-documents')
      .getPublicUrl(testPath);
    
    console.log('🔗 Public URL:', urlData.publicUrl);
    
    // Test URL accessibility
    try {
      const response = await fetch(urlData.publicUrl);
      console.log('✅ URL is accessible:', response.status);
      
      if (response.ok) {
        const content = await response.text();
        console.log('📄 Content:', content);
      }
    } catch (fetchError) {
      console.log('❌ URL not accessible:', fetchError.message);
    }
    
    // Clean up test file
    await supabase.storage
      .from('legal-documents')
      .remove([testPath]);
    
    console.log('🧹 Test file cleaned up');
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

checkAndFixBucket();
