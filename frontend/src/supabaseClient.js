import { createClient } from '@supabase/supabase-js'

// Use fallback empty strings so createClient doesn't receive 'undefined'
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ""
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ""

// If the strings are empty, we log a helpful warning instead of crashing
if (!supabaseUrl || !supabaseAnonKey) {
  console.warn("⚠️ Supabase credentials not found. Check Vercel Env Variables.")
}

export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co', 
  supabaseAnonKey || 'placeholder'
)