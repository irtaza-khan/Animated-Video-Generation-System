import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Undo2, Play, Loader2, Sparkles } from 'lucide-react';
import './index.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [prompt, setPrompt] = useState('A beautiful sunset over the mountains, digital art');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [portraits, setPortraits] = useState({});
  
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! I am your Edit Agent. How would you like to modify the scene?' }
  ]);
  
  const videoRef = useRef(null);

  const startPolling = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/status/${jobId}`);
        setProgress(res.data.progress || 0);
        setStatusText(res.data.status || 'processing');
        if (res.data.portraits) {
          setPortraits(res.data.portraits);
        }
        
        if (res.data.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          // Append timestamp to bust cache
          setVideoUrl(`${API_BASE}/outputs/final_output.mp4?t=${new Date().getTime()}`);
        } else if (res.data.status.includes('error')) {
          clearInterval(interval);
          setLoading(false);
          alert('Generation failed: ' + res.data.status);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 1000);
  };

  const handleGenerate = async () => {
    if (!prompt) return;
    setLoading(true);
    setProgress(0);
    setStatusText('initializing');
    setVideoUrl('');
    setPortraits({});
    
    try {
      const res = await axios.post(`${API_BASE}/api/generate`, {
        prompt: prompt,
        num_scenes: 3,
      });
      startPolling(res.data.job_id);
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert('Failed to start generation');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatInput('');
    setLoading(true);
    setProgress(0);
    setStatusText('processing edit');
    
    try {
      const res = await axios.post(`${API_BASE}/api/edit`, { query: userMsg });
      startPolling(res.data.job_id);
    } catch (err) {
      console.error(err);
      setLoading(false);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I could not process that edit.' }]);
    }
  };

  const handleUndo = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE}/api/undo`);
      setVideoUrl(`${API_BASE}/outputs/final_output.mp4?t=${new Date().getTime()}`);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Successfully reverted to previous version.' }]);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert('Failed to undo');
    }
  };

  return (
    <div className="dashboard">
      <div className="main-panel">
        <div>
          <h1>AI Studio</h1>
          <p style={{ color: 'var(--text-muted)' }}>Generate and orchestrate animated videos</p>
        </div>
        
        <div className="glass-card">
          <div className="input-group">
            <label>Scene Prompt</label>
            <textarea 
              rows={3} 
              value={prompt} 
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your scene..."
            />
          </div>
          <button 
            style={{ marginTop: '1rem', width: '100%' }} 
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? <Loader2 className="spin" /> : <Sparkles />}
            {loading ? 'Generating...' : 'Generate Video'}
          </button>
          
          {loading && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <span>{statusText.toUpperCase()}</span>
                <span>{progress}%</span>
              </div>
              <div className="progress-container">
                <div className="progress-bar" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          )}

          {Object.keys(portraits).length > 0 && (
            <div className="portraits-gallery" style={{ marginTop: '2rem' }}>
              <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Cast</h3>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                {Object.entries(portraits).map(([name, path]) => (
                  <div key={name} className="portrait-item">
                    <img 
                      src={`${API_BASE}/${path}`} 
                      alt={name} 
                      style={{ width: '60px', height: '60px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--accent)' }}
                    />
                    <span style={{ display: 'block', textAlign: 'center', fontSize: '0.7rem', marginTop: '0.2rem' }}>{name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="video-container">
          {videoUrl ? (
            <video src={videoUrl} controls autoPlay loop ref={videoRef}></video>
          ) : (
            <div style={{ color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <Play size={48} opacity={0.5} />
              <p>Your generated video will appear here</p>
            </div>
          )}
        </div>
      </div>
      
      <div className="sidebar">
        <div className="chat-header">
          <h2>Edit Agent</h2>
          <button className="undo-btn" onClick={handleUndo} title="Undo last edit">
            <Undo2 size={18} /> Undo
          </button>
        </div>
        
        <div className="chat-messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.sender}`}>
              {m.text}
            </div>
          ))}
        </div>
        
        <form className="chat-input-area" onSubmit={handleEditSubmit}>
          <input 
            type="text" 
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="E.g., Update scene 1 prompt to..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !chatInput.trim()}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
