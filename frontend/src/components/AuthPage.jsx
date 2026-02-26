import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { supabase } from '../supabaseClient';

export default function AuthPage() {
  return (
    <div className="auth-container" style={{ padding: '50px', maxWidth: '400px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center' }}>Adventure AI</h1>
      <p style={{ textAlign: 'center', color: '#888' }}>Login to save your stories and generate art.</p>
      <Auth
        supabaseClient={supabase}
        appearance={{ theme: ThemeSupa }}
        theme="dark"
        providers={['google', 'github']} // Optional: Add these in Supabase dashboard later
      />
    </div>
  );
}