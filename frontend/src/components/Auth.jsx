import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { supabase } from '../supabaseClient'; // Make sure you have a supabaseClient file!

const Authentication = () => (
  <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', background: '#1a1a1a', borderRadius: '12px' }}>
    <h2 style={{ textAlign: 'center', color: 'white' }}>Join the Adventure</h2>
    <Auth
      supabaseClient={supabase}
      appearance={{ theme: ThemeSupa }}
      providers={['google', 'github']} // You can add these later!
      theme="dark"
    />
  </div>
);

export default Authentication;