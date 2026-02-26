import './App.css'
import { useState, useEffect } from 'react' // 1. Added Hooks
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { supabase } from './supabaseClient' // 2. Added Supabase Client
import AuthPage from './components/AuthPage' // 3. Added Auth Component
import StoryLoader from './components/StoryLoader'
import StoryGenerator from './components/StoryGenerator'

function App() {
  const [session, setSession] = useState(null)

  useEffect(() => {
    // Check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    // Listen for login/logout changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  return (
    <Router>
      <div className="app-container">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem' }}>
          <h1>Interactive Story Generator</h1>
          {/* Show Logout only if logged in */}
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
          {/* 4. The Gatekeeper Logic */}
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