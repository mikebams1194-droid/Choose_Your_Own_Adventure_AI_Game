import './App.css'
import { useState, useEffect } from 'react' 
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { supabase } from './supabaseClient'
import AuthPage from './components/AuthPage'
import StoryLoader from './components/StoryLoader'
import StoryGenerator from './components/StoryGenerator'
import StoryList from './components/StoryList'

function App() {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  // FIX #1: Define the view state
  const [view, setView] = useState('generator') 

  useEffect(() => {
    const timeout = setTimeout(() => setLoading(false), 5000);
    
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
      clearTimeout(timeout)
    }).catch(err => {
      console.error("Supabase connection failed:", err)
      setLoading(false)
    })

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
        {/* Header Section */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', background: '#222', color: 'white', flexWrap: 'wrap', minHeight: '70px' }}>
          <h1>Adventure AI</h1>
          {session && (
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {/* FIX #2: Navigation buttons inside the session check */}
              <button onClick={() => setView('generator')}>New Game</button>
              <button onClick={() => setView('library')}>My Stories</button>
              <button onClick={() => supabase.auth.signOut()} className="logout-btn">Logout</button>
            </div>
          )}
        </header>

        {/* Main Content Area */}
        <main style={{ padding: '2rem' }}>
          {!session ? (
            <AuthPage />
          ) : (
            <>
              {/* FIX #3: Unified View Logic */}
              {view === 'library' ? (
                <StoryList session={session} setView={setView} />
              ) : (
                <Routes>
                  {/* If a user clicks an old story in StoryList, navigate here */}
                  <Route path="/story/:id" element={<StoryLoader />} />
                  {/* Default view is the Generator */}
                  <Route path="/" element={<StoryGenerator session={session} />} />
                </Routes>
              )}
            </>
          )}
        </main>
      </div>
    </Router>
  )
}

export default App