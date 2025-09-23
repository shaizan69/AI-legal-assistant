-- Make Supabase bucket public for document viewing
-- Run this in your Supabase SQL editor

-- First, make sure the bucket exists and is public
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('legal-documents', 'legal-documents', true, 52428800, ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
ON CONFLICT (id) DO UPDATE SET public = true;

-- Create a policy to allow public read access to all files
CREATE POLICY "Public read access for all files" ON storage.objects
FOR SELECT USING (bucket_id = 'legal-documents');

-- Create a policy to allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload files" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'legal-documents' 
  AND auth.role() = 'authenticated'
);

-- Create a policy to allow users to delete their own files
CREATE POLICY "Users can delete their own files" ON storage.objects
FOR DELETE USING (
  bucket_id = 'legal-documents' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Verify the bucket is public
SELECT id, name, public FROM storage.buckets WHERE id = 'legal-documents';
