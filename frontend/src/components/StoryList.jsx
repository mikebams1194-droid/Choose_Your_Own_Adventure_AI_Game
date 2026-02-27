import { useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from "../utils.js";
import { useNavigate } from "react-router-dom";

function StoryList({ session }) {
    const [stories, setStories] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchStories = async () => {
            try {
                // Notice the URL matches the backend route /stories/user/ID
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

    if (loading) return <p>Loading your adventures...</p>;

    return (
        <div style={{ padding: '20px' }}>
            <h2>Your Library</h2>
            {stories.length === 0 ? (
                <p>You haven't created any stories yet.</p>
            ) : (
                <div style={{ display: 'grid', gap: '10px' }}>
                    {stories.map((story) => (
                        <div 
                            key={story.id} 
                            onClick={() => navigate(`/story/${story.id}`)}
                            style={{ 
                                border: '1px solid #ccc', 
                                padding: '15px', 
                                cursor: 'pointer',
                                borderRadius: '8px'
                            }}
                        >
                            <h3 style={{ margin: 0 }}>{story.title}</h3>
                            <small>Created: {story.created_at ? new Date(story.created_at).toLocaleDateString() : 'Unknown'}</small>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default StoryList;