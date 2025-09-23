import { createClient } from '@supabase/supabase-js';

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'https://your-project.supabase.co';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'your-anon-key';
const supabaseServiceKey = process.env.REACT_APP_SUPABASE_SERVICE_KEY || 'your-service-key';

// Create Supabase clients
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey);

// Storage bucket name
export const STORAGE_BUCKET = 'legal-documents';

// File upload helper
export const uploadFile = async (file, path, options = {}) => {
  try {
    // Use admin client for uploads to bypass RLS
    const { data, error } = await supabaseAdmin.storage
      .from(STORAGE_BUCKET)
      .upload(path, file, {
        cacheControl: '3600',
        upsert: false,
        ...options
      });

    if (error) {
      throw error;
    }

    return data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

// Get file URL helper
export const getFileUrl = (path) => {
  const { data } = supabase.storage
    .from(STORAGE_BUCKET)
    .getPublicUrl(path);
  
  return data.publicUrl;
};

// Delete file helper
export const deleteFile = async (path) => {
  try {
    const { error } = await supabaseAdmin.storage
      .from(STORAGE_BUCKET)
      .remove([path]);

    if (error) {
      throw error;
    }

    return true;
  } catch (error) {
    console.error('Error deleting file:', error);
    throw error;
  }
};

// Generate unique file path
export const generateFilePath = (userId, originalName) => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const extension = originalName.split('.').pop();
  const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '');
  const sanitizedName = nameWithoutExt.replace(/[^a-zA-Z0-9-_]/g, '_');
  
  return `${userId}/${timestamp}_${sanitizedName}.${extension}`;
};
