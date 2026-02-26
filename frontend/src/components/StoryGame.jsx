import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from "../utils.js";

export default function StoryGame({ story, onNewStory }) {
    const [currentNodeId, setCurrentNodeId] = useState(null);
    const [currentNode, setCurrentNode] = useState(null);
    const [options, setOptions] = useState([]);
    const [isEnding, setIsEnding] = useState(false);
    const [isWinningEnding, setIsWinningEnding] = useState(false);
    const [imageUrl, setImageUrl] = useState(null);
    const [imageLoading, setImageLoading] = useState(false);

    useEffect(() => {
        if (story && story.root_node) {
            setCurrentNodeId(story.root_node.id);
        }
    }, [story]);

    useEffect(() => {
        if (currentNodeId && story && story.all_nodes) {
            const node = story.all_nodes[currentNodeId];
            setCurrentNode(node);
            setIsEnding(node.is_ending);
            setIsWinningEnding(node.is_winning_ending);

            if (!node.is_ending && node.options && node.options.length > 0) {
                setOptions(node.options);
            } else {
                setOptions([]);
            }
        }
    }, [currentNodeId, story]);

    const handleGenerateImage = async (sceneText) => {
        setImageLoading(true);
        setImageUrl(null);
        try {
            const response = await axios.post(`${API_BASE_URL}/stories/generate-scene-image`, {
                scene_description: sceneText
            });
            setImageUrl(response.data.image_url);
        } catch (err) {
            console.error("Image error:", err);
            alert("Could not generate image. Check your OpenAI credits!");
        } finally {
            setImageLoading(false);
        }
    };

    const chooseOption = (nodeId) => {
        setImageUrl(null);
        setCurrentNodeId(nodeId);
    }

    const restartStory = () => {
        setImageUrl(null);
        if (story && story.root_node) {
            setCurrentNodeId(story.root_node.id);
        }
    }

    return (
        <div className="story-game">
            <header className="story-header">
                <h2>{story?.title || "Loading Title..."}</h2>
            </header>

            <div className="story-content">
                {currentNode && (
                    <div className="story-node">
                        
                        {/* 3. Added Image Display Area */}
                        <div className="image-section" style={{ marginBottom: '20px', textAlign: 'center' }}>
                            {imageLoading && <p>🎨 Painting the scene...</p>}
                            {imageUrl && (
                                <img 
                                    src={imageUrl} 
                                    alt="Scene" 
                                    style={{ width: '100%', borderRadius: '12px', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }} 
                                />
                            )}
                            {!imageUrl && !imageLoading && (
                                <button 
                                    onClick={() => handleGenerateImage(currentNode.content)}
                                    className="visualize-btn"
                                    style={{ padding: '8px 16px', cursor: 'pointer', borderRadius: '20px', border: '1px solid #ddd' }}
                                >
                                    ✨ Visualize Scene
                                </button>
                            )}
                        </div>

                        <p className="story-text">{currentNode.content}</p>

                        {isEnding ? (
                            <div className="story-ending">
                                <h3>{isWinningEnding ? "Congratulations!" : "The End"}</h3>
                                <p>{isWinningEnding ? "You reached a winning ending!" : "Your adventure has ended."}</p>
                            </div>
                        ) : (
                            <div className="story-options">
                                <h3>What will you do?</h3>
                                <div className="options-list">
                                    {options.map((option, index) => (
                                        <button
                                            key={index}
                                            onClick={() => chooseOption(option.node_id)}
                                            className="option-btn"
                                        >
                                            {option.text}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <div className="story-controls" style={{ marginTop: '30px', display: 'flex', gap: '10px' }}>
                    <button onClick={restartStory} className="reset-btn">Restart Story</button>
                    {onNewStory && <button onClick={onNewStory} className="new-story-btn">New Story</button>}
                </div>
            </div>
        </div>
    );
}