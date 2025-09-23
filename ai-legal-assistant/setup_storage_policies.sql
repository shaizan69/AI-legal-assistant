-- Supabase Storage RLS Policies for legal-documents bucket
-- Run this in your Supabase SQL Editor

-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy for public read access to legal-documents bucket
CREATE POLICY "Public read access for legal-documents" ON storage.objects
FOR SELECT USING (bucket_id = 'legal-documents');

-- Policy for authenticated users to upload to legal-documents bucket
CREATE POLICY "Authenticated users can upload to legal-documents" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'legal-documents' 
  AND auth.role() = 'authenticated'
);

-- Policy for users to update their own files
CREATE POLICY "Users can update their own files" ON storage.objects
FOR UPDATE USING (
  bucket_id = 'legal-documents' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy for users to delete their own files
CREATE POLICY "Users can delete their own files" ON storage.objects
FOR DELETE USING (
  bucket_id = 'legal-documents' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Alternative: Allow all operations for development (less secure)
-- Uncomment the following lines if you want to allow all operations for testing

-- CREATE POLICY "Allow all operations on legal-documents" ON storage.objects
-- FOR ALL USING (bucket_id = 'legal-documents');
