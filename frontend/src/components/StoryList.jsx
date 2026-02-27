import { useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from "../utils.js";
import { useNavigate } from "react-router-dom";

function StoryList({ session, setView }) { // Receiving setView as a prop
    const [stories, setStories] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchStories = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/stories/user/${session?.user?.id}`);
                setStories(response.data);
            } catch (err) {
                console.error("Failed to fetch stories:", err);
            } finally {
                setLoading(false);
            }
        };

        if (session?.user?.id) {
            fetchStories();
        }
    }, [session]);

    // This is the magic function that fixes the click behavior
    const handleStoryClick = (storyId) => {
        // 1. Update the URL so StoryLoader knows which ID to fetch
        navigate(`/story/${storyId}`);
        
        // 2. Flip the switch in App.js to hide the Library and show the Routes
        if (setView) {
            setView('generator'); 
        }
    };

    if (loading) return <p style={{ textAlign: 'center', marginTop: '50px' }}>Loading your adventures...</p>;

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <h2 style={{ borderBottom: '2px solid #eee', paddingBottom: '10px' }}>Your Library</h2>
            
            {stories.length === 0 ? (
                <div style={{ textAlign: 'center', marginTop: '40px', color: '#666' }}>
                    <p>You haven't created any stories yet.</p>
                    <button onClick={() => setView('generator')}>Start a New Adventure</button>
                </div>
            ) : (
                <div style={{ display: 'grid', gap: '15px', marginTop: '20px' }}>
                    {stories.map((story) => (
                        <div 
                            key={story.id} 
                            onClick={() => handleStoryClick(story.id)} // Use the new handler here
                            style={{ 
                                border: '1px solid #ddd', 
                                padding: '20px', 
                                cursor: 'pointer',
                                borderRadius: '12px',
                                background: '#fff',
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
                            }}
                        >
                            <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50' }}>{story.title}</h3>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <small style={{ color: '#7f8c8d' }}>
                                    📅 {story.created_at ? new Date(story.created_at).toLocaleDateString() : 'Unknown Date'}
                                </small>
                                <span style={{ color: '#3498db', fontSize: '0.9rem', fontWeight: 'bold' }}>Resume →</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default StoryList;