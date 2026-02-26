import './App.css'
import { useState, useEffect } from 'react' 
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { supabase } from './supabaseClient'
import AuthPage from './components/AuthPage'
import StoryLoader from './components/StoryLoader'
import StoryGenerator from './components/StoryGenerator'

function App() {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true) // 1. Add a loading state

  useEffect(() => {
    const timeout = setTimeout(() => setLoading(false), 5000);
    
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
      clearTimeout(timeout)
    }).catch(err => {
      console.error("Supabase connection failed:", err)
      setLoading(false)
    }
    )

    // Listen for login/logout changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setLoading(false)
    })

    return () => {
      if (subscription) subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, [])

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Connecting to Adventure Engine...</div>
  }

  return (
    <Router>
      <div className="app-container">
        {/* DEBUG HELLO WORLD */}
        <div style={{ background: 'yellow', color: 'black', textAlign: 'center', padding: '5px' }}>
          Hello World - The App is Rendering!
        </div>

        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem' }}>
          <h1>Interactive Story Generator</h1>
          {session && (
            <button 
              onClick={() => supabase.auth.signOut()} 
              className="logout-btn"
              style={{ padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}
            >
              Logout
            </button>
          )}
        </header>
        
        <main>
          {!session ? (
            <AuthPage />
          ) : (
            <Routes>
              <Route path="/story/:id" element={<StoryLoader />} />
              <Route path="/" element={<StoryGenerator session={session} />} />
            </Routes>
          )}
        </main>
      </div>
    </Router>
  )
}

export default App