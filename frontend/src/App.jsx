import React, { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';
import { Send, Undo2, Redo2 } from 'lucide-react';
import './index.css';

const API_BASE = 'http://localhost:8000';
const DEFAULT_PROMPT = 'A beautiful sunset over the mountains, digital art';

const PHASES = [
  { key: 'story',     name: 'Story',     match: ['generating_story'] },
  { key: 'cast',      name: 'Cast',      match: ['casting_characters'] },
  { key: 'audio',     name: 'Audio',     match: ['generating_audio'] },
  { key: 'video',     name: 'Footage',   match: ['generating_video', 'lip_syncing'] },
  { key: 'composite', name: 'Print',     match: ['compositing', 'saving_state'] },
];

function getPhaseIndex(status) {
  if (!status) return -1;
  if (status === 'completed') return PHASES.length;
  const s = status.toLowerCase();
  for (let i = 0; i < PHASES.length; i++) {
    if (PHASES[i].match.some(m => s.includes(m))) return i;
  }
  return -1;
}

function prettyStatus(status) {
  if (!status) return '';
  return status.replace(/_/g, ' ').replace(/\s+/g, ' ').trim().toUpperCase();
}

function pad(n, w = 2) { return String(n).padStart(w, '0'); }

function App() {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [portraits, setPortraits] = useState({});

  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Continuity desk ready. Mark up scene revisions or undo to revert a take.' }
  ]);

  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'night';
    const stored = window.localStorage.getItem('ai-studio:theme');
    if (stored === 'day' || stored === 'night') return stored;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'day' : 'night';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { window.localStorage.setItem('ai-studio:theme', theme); } catch {}
  }, [theme]);

  const videoRef = useRef(null);
  const logRef = useRef(null);

  // Cinema timecode tick (HH:MM:SS:FF @ 24fps)
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000 / 24);
    return () => clearInterval(id);
  }, []);
  const tc = useMemo(() => {
    const totalFrames = tick;
    const ff = totalFrames % 24;
    const totalSec = Math.floor(totalFrames / 24);
    const ss = totalSec % 60;
    const mm = Math.floor(totalSec / 60) % 60;
    const hh = Math.floor(totalSec / 3600);
    return { hh: pad(hh), mm: pad(mm), ss: pad(ss), ff: pad(ff) };
  }, [tick]);

  // Scroll to latest entry
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages]);

  const startPolling = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/status/${jobId}`);
        setProgress(res.data.progress || 0);
        setStatusText(res.data.status || 'processing');
        if (res.data.portraits) setPortraits(res.data.portraits);

        if (res.data.status === 'completed') {
          clearInterval(interval);
          setLoading(false);
          setVideoUrl(`${API_BASE}/outputs/final_output.mp4?t=${new Date().getTime()}`);
        } else if (res.data.status && res.data.status.includes('error')) {
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
      const it = res.data && res.data.intent;
      if (it && it.target === 'video_frame') {
        setMessages(prev => [...prev, { sender: 'bot', text: `Applied to Scene ${it.scene_id}: "${it.value}". Reusing original seed for visual continuity.` }]);
      } else if (it && it.target === 'global') {
        setMessages(prev => [...prev, { sender: 'bot', text: `Applied globally: "${it.value}". Regenerating every scene with the original seeds.` }]);
      }
      startPolling(res.data.job_id);
    } catch (err) {
      console.error(err);
      setLoading(false);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Could not parse the revision.' }]);
    }
  };

  const handleUndo = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/api/undo`);
      setVideoUrl(`${API_BASE}/outputs/final_output.mp4?t=${new Date().getTime()}`);
      setMessages(prev => [...prev, { sender: 'bot', text: res.data.message }]);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert(err.response?.data?.detail || 'Failed to undo');
    }
  };

  const handleRedo = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/api/redo`);
      setVideoUrl(`${API_BASE}/outputs/final_output.mp4?t=${new Date().getTime()}`);
      setMessages(prev => [...prev, { sender: 'bot', text: res.data.message }]);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert(err.response?.data?.detail || 'Failed to redo');
    }
  };

  const phaseIdx = useMemo(() => getPhaseIndex(statusText), [statusText]);
  const promptCount = prompt.length;
  const showProgress = loading || (progress > 0 && progress < 100);
  const portraitEntries = Object.entries(portraits);
  const today = useMemo(() => {
    const d = new Date();
    const m = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()];
    return `${m} ${pad(d.getDate())} · ${d.getFullYear()}`;
  }, []);

  return (
    <>
      <div className="stage" />
      <div className="stage-grain" />
      <div className="stage-vignette" />

      <div className="studio">
        {/* ===================== MAIN ===================== */}
        <main className="studio-main">

          <header className="masthead r r-1">
            <div className="masthead-eyebrow">AI Studio · Reel No. 01</div>
            <h1 className="masthead-title">A continuity desk for <em>generated</em> film</h1>
            <div className="masthead-meta">
              <div><span className="rec" />System ready</div>
              <div><b>{today}</b></div>
              <div>v1.0 — local</div>
              <div className="theme-toggle" role="group" aria-label="Theme">
                <button
                  type="button"
                  className={theme === 'day' ? 'is-active' : ''}
                  onClick={() => setTheme('day')}
                  aria-pressed={theme === 'day'}
                  aria-label="Day mode"
                >
                  <span className="glyph" aria-hidden="true" />Day
                </button>
                <button
                  type="button"
                  className={theme === 'night' ? 'is-active' : ''}
                  onClick={() => setTheme('night')}
                  aria-pressed={theme === 'night'}
                  aria-label="Night mode"
                >
                  <span className="glyph" aria-hidden="true" />Night
                </button>
              </div>
            </div>
          </header>

          {/* ===== Section 01 — Composer ===== */}
          <section className="section r r-2">
            <div className="section-head">
              <span className="section-num">§ 01</span>
              <h2 className="section-title">Scene composer</h2>
              <span className="section-rule" />
              <span className="section-aside">Phase 1 — Screenplay</span>
            </div>

            <div className="field">
              <textarea
                id="prompt-input"
                className="field-input"
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="A beautiful sunset over the mountains, digital art…"
                aria-label="Scene prompt"
              />
              <div className="field-meta">
                <span><b>3 scenes</b> · auto cast</span>
                <span></span>
                <span className="field-counter">{pad(promptCount, 3)} / 800</span>
              </div>
            </div>

            <button
              className="cta cta--primary"
              onClick={handleGenerate}
              disabled={loading || !prompt.trim()}
              aria-label="Generate video"
            >
              <span className="lhs">Roll →</span>
              <span>{loading ? 'Generating Take' : 'Action — Generate'}</span>
              <span className="rhs">↩ ⏎</span>
            </button>

            {/* Timeline + progress */}
            {(showProgress || phaseIdx >= 0) && (
              <>
                <div className="timeline" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
                  {PHASES.map((p, i) => {
                    const isDone = phaseIdx === PHASES.length || i < phaseIdx;
                    const isActive = phaseIdx !== PHASES.length && i === phaseIdx;
                    const stepCls = isActive ? 'timeline-step--active' : isDone ? 'timeline-step--done' : '';
                    const linkFilled = (phaseIdx === PHASES.length || i < phaseIdx);
                    return (
                      <React.Fragment key={p.key}>
                        <div className={`timeline-step ${stepCls}`}>
                          <span className="timeline-mark">0{i + 1}</span>
                          <span className="timeline-name">{p.name}</span>
                        </div>
                        {i < PHASES.length - 1 && (
                          <span className={`timeline-link ${linkFilled ? 'timeline-link--filled' : ''}`} />
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>

                <div className="progress">
                  <div className="progress-fill" style={{ width: `${Math.max(progress, loading ? 4 : 0)}%` }} />
                </div>
                <div className="progress-meta">
                  <span><b>Status</b> &nbsp; {prettyStatus(statusText) || 'INITIALIZING'}</span>
                  <span className="pct">{pad(progress, 2)}<sup>%</sup></span>
                </div>
              </>
            )}

            {/* Cast */}
            {portraitEntries.length > 0 && (
              <div className="cast">
                <div className="cast-head">
                  <span className="label">Cast — sheet</span>
                  <span className="rule" />
                </div>
                <div className="cast-row">
                  {portraitEntries.map(([name, path], i) => (
                    <div
                      key={name}
                      className="cast-item"
                      style={{ animationDelay: `${i * 70}ms` }}
                    >
                      <div className="avatar">
                        <img src={`${API_BASE}/${path}`} alt={name} />
                      </div>
                      <span className="cast-name">{name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* ===== Section 02 — Viewport ===== */}
          <section className="section r r-3">
            <div className="section-head">
              <span className="section-num">§ 02</span>
              <h2 className="section-title">Monitor</h2>
              <span className="section-rule" />
              <span className="section-aside">{videoUrl ? 'Take ready' : 'Stand-by'}</span>
            </div>

            <div className="viewport">
              {videoUrl ? (
                <video src={videoUrl} controls autoPlay loop ref={videoRef} />
              ) : (
                <>
                  <div className="slate-marks" aria-hidden="true">
                    <span /><span /><span /><span />
                  </div>
                  <div className="slate-scan" aria-hidden="true" />
                  <div className="slate">
                    <div className="slate-row">
                      <div>
                        <span className="k">Take</span>
                        <span className="v">01</span>
                      </div>
                      <div className="center">
                        <span className="k">Slate</span>
                        <span className="v">A · 0001</span>
                      </div>
                      <div className="right">
                        <span className="slate-rec">REC · standby</span>
                      </div>
                    </div>

                    <div className="slate-center">
                      <div className="slate-tc">
                        <span>{tc.hh}</span><span className="sep">:</span>
                        <span>{tc.mm}</span><span className="sep">:</span>
                        <span>{tc.ss}</span><span className="sep">:</span>
                        <span className="ms">{tc.ff}</span>
                      </div>
                      <div className="slate-cap">awaiting capture</div>
                    </div>

                    <div className="slate-row bottom">
                      <div>
                        <span className="k">Aspect</span>
                        <span className="v">16 : 9</span>
                      </div>
                      <div className="center">
                        <span className="k">Frame rate</span>
                        <span className="v">24 fps</span>
                      </div>
                      <div className="right">
                        <span className="k">Codec</span>
                        <span className="v">H.264 · MoviePy</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </section>
        </main>

        {/* ===================== SIDEBAR ===================== */}
        <aside className="studio-side r r-4">
          <header className="script-head">
            <div>
              <div className="script-eyebrow">Script Notes</div>
              <h2 className="script-title">Continuity</h2>
            </div>
            <div className="script-actions">
              <button
                className="cta cta--icon"
                onClick={handleUndo}
                title="Revert one take"
                disabled={loading}
                aria-label="Undo"
              >
                <Undo2 size={15} strokeWidth={1.6} />
              </button>
              <button
                className="cta cta--icon"
                onClick={handleRedo}
                title="Restore one take"
                disabled={loading}
                aria-label="Redo"
              >
                <Redo2 size={15} strokeWidth={1.6} />
              </button>
            </div>
          </header>

          <div className="log" ref={logRef}>
            {messages.map((m, i) => (
              <div
                key={i}
                className={`entry ${m.sender === 'user' ? 'entry--user' : ''}`}
                data-mark={m.sender === 'user' ? `Note · ${pad(i)}` : `Desk · ${pad(i)}`}
              >
                <div className="entry-text">{m.text}</div>
              </div>
            ))}
          </div>

          <form className="composer" onSubmit={handleEditSubmit}>
            <div className="composer-input-wrap">
              <span className="composer-prefix">Note</span>
              <input
                type="text"
                className="composer-input"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Update scene 1: a dark stormy night…"
                disabled={loading}
                aria-label="Edit instruction"
              />
            </div>
            <button
              type="submit"
              className="cta cta--send"
              disabled={loading || !chatInput.trim()}
              aria-label="Send revision"
            >
              <Send size={16} strokeWidth={1.8} />
            </button>
          </form>
        </aside>
      </div>
    </>
  );
}

export default App;
