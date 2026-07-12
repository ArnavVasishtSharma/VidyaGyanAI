import { useState, useEffect, useRef, useCallback } from 'react'

const SESSION_ID = 'session_' + Math.random().toString(36).slice(2, 9)

async function apiChat(message, tts = true) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: SESSION_ID, message, tts }),
  })
  if (!res.ok) throw new Error('API error ' + res.status)
  return res.json()
}

function playAudio(b64) {
  if (!b64) return
  const audio = new Audio('data:audio/mp3;base64,' + b64)
  audio.playbackRate = 1.1
  audio.play().catch(() => {})
  return audio
}

const SUBJECTS = ['Maths','Physics','Chemistry','Biology','History','Geography','English','Hindi','Computer']
const CLASSES  = ['7','8','9','10','11','12']

// Quick actions — matching v0 style
const QUICK = [
  { icon: 'book',   label: 'Newton ka 3rd law samjhao' },
  { icon: 'leaf',   label: 'Photosynthesis explain karo' },
  { icon: 'clock',  label: 'Kal exam hai — help karo' },
  { icon: 'zap',    label: 'Quiz mode on karo' },
  { icon: 'user',   label: 'Revision notes banao' },
]

/* ═══════════════════════════════════════════════════════════════════
   SVG ICONS — inline, no dependencies
   ═══════════════════════════════════════════════════════════════════ */

function IconSparkle({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
    </svg>
  )
}

function IconPaperclip({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
    </svg>
  )
}

function IconMic({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" x2="12" y1="19" y2="22"/>
    </svg>
  )
}

function IconMicOff({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="2" x2="22" y1="2" y2="22"/>
      <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/>
      <path d="M5 10v2a7 7 0 0 0 12 5"/>
      <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/>
      <path d="M9 9v3a3 3 0 0 0 5.12 2.12"/>
      <line x1="12" x2="12" y1="19" y2="22"/>
    </svg>
  )
}

function IconArrowUp({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m5 12 7-7 7 7"/>
      <path d="M12 19V5"/>
    </svg>
  )
}

function IconPlus({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14"/>
      <path d="M12 5v14"/>
    </svg>
  )
}

function IconDownload({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" x2="12" y1="15" y2="3"/>
    </svg>
  )
}

function IconMenu({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" x2="20" y1="12" y2="12"/>
      <line x1="4" x2="20" y1="6" y2="6"/>
      <line x1="4" x2="20" y1="18" y2="18"/>
    </svg>
  )
}

function IconBook({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/>
    </svg>
  )
}

function IconLeaf({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 20A7 7 0 0 1 9.8 6.9C15.5 4.9 20 .5 20 .5s-3.5 11-12 19.5"/>
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
    </svg>
  )
}

function IconClock({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  )
}

function IconZap({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  )
}

function IconUser({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="5"/>
      <path d="M20 21a8 8 0 0 0-16 0"/>
    </svg>
  )
}

function IconV({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 4l7 16 7-16" />
    </svg>
  )
}

const ICON_MAP = { book: IconBook, leaf: IconLeaf, clock: IconClock, zap: IconZap, user: IconUser }

const TYPEWRITER_SENTENCES = ["VidhyaGyan AI", "How can I help you today ?"];

function AnimatedHeading() {
  const [index, setIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [phase, setPhase] = useState('typing'); 

  useEffect(() => {
    if (phase === 'typing') {
      if (charIndex < TYPEWRITER_SENTENCES[index].length) {
        const timeout = setTimeout(() => setCharIndex(c => c + 1), 60); 
        return () => clearTimeout(timeout);
      } else {
        const timeout = setTimeout(() => setPhase('idle'), 500);
        return () => clearTimeout(timeout);
      }
    } else if (phase === 'idle') {
      const timeout = setTimeout(() => setPhase('fading'), 2500);
      return () => clearTimeout(timeout);
    } else if (phase === 'fading') {
      const timeout = setTimeout(() => {
        setIndex(i => (i + 1) % TYPEWRITER_SENTENCES.length);
        setCharIndex(0);
        setPhase('typing');
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [charIndex, phase, index]);

  return (
    <h1 className={`welcome-heading ${phase === 'fading' ? 'fade-out' : 'fade-in'}`}>
      {TYPEWRITER_SENTENCES[index].substring(0, charIndex)}
      <span className="tw-cursor"></span>
    </h1>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   AUTO-RESIZE TEXTAREA HOOK
   ═══════════════════════════════════════════════════════════════════ */

function useAutoResizeTextarea({ minHeight, maxHeight }) {
  const textareaRef = useRef(null)

  const adjustHeight = useCallback((reset) => {
    const ta = textareaRef.current
    if (!ta) return
    if (reset) { ta.style.height = `${minHeight}px`; return }
    ta.style.height = `${minHeight}px`
    ta.style.height = `${Math.max(minHeight, Math.min(ta.scrollHeight, maxHeight ?? Infinity))}px`
  }, [minHeight, maxHeight])

  useEffect(() => {
    if (textareaRef.current) textareaRef.current.style.height = `${minHeight}px`
  }, [minHeight])

  useEffect(() => {
    const h = () => adjustHeight()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [adjustHeight])

  return { textareaRef, adjustHeight }
}

/* ═══════════════════════════════════════════════════════════════════
   APP
   ═══════════════════════════════════════════════════════════════════ */

export default function App() {
  const [messages,    setMessages]    = useState([])
  const [input,       setInput]       = useState('')
  const [loading,     setLoading]     = useState(false)
  const [listening,   setListening]   = useState(false)
  const [sessionInfo, setSessionInfo] = useState({})
  const [activeSubj,  setActiveSubj]  = useState(null)
  const [activeCls,   setActiveCls]   = useState(null)
  const [backendOk,   setBackendOk]   = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const bottomRef = useRef(null)
  const recognRef = useRef(null)
  const audioRef  = useRef(null)

  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 52,
    maxHeight: 180,
  })

  // Health
  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(() => setBackendOk(true)).catch(() => {})
  }, [])

  // Greeting
  useEffect(() => {
    const greeting = 'Namaste! Main hoon VidhyaGyan AI, tumhara study companion. Pehle batao — tumhara naam kya hai aur tum konsi class mein ho?'
    setMessages([{ id: 0, role: 'assistant', text: greeting }])
    apiChat('__init__', true).then(d => { if (d.audio_b64) playAudio(d.audio_b64) }).catch(() => {})
  }, [])

  // Scroll
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  // Send
  const sendMessage = useCallback(async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    adjustHeight(true)
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', text: msg }])
    setLoading(true)
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    try {
      const data = await apiChat(msg, true)
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: data.reply }])
      if (data.session_info) setSessionInfo(data.session_info)
      if (data.audio_b64) audioRef.current = playAudio(data.audio_b64)
    } catch {
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: 'Ek second — kuch technical issue aa gayi. Dobara try karo.' }])
    } finally {
      setLoading(false)
      textareaRef.current?.focus()
    }
  }, [input, loading, adjustHeight, textareaRef])

  // Voice
  const toggleVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) { alert('Voice needs Chrome browser.'); return }
    if (listening) { recognRef.current?.stop(); setListening(false); return }
    const r = new SR()
    r.lang = 'hi-IN'; r.continuous = false; r.interimResults = false
    r.onstart  = () => setListening(true)
    r.onend    = () => setListening(false)
    r.onerror  = () => setListening(false)
    r.onresult = (e) => { const t = e.results[0][0].transcript.trim(); if (t) sendMessage(t) }
    recognRef.current = r
    r.start()
  }, [listening, sendMessage])

  const handleSubject = (s) => { setActiveSubj(s); sendMessage(s + ' padhna hai') }
  const handleClass   = (c) => { setActiveCls(c);  sendMessage('Main Class ' + c + ' mein hoon') }
  const handleKey     = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }

  const hasMessages = messages.length > 1

  // ─── The Input Box (shared between welcome & conversation) ──────────────
  const renderInputBox = () => (
    <div className="input-wrapper">
      {listening && (
        <div className="listening-pill">
          <span className="pulse-dot" />
          Listening... speak now
        </div>
      )}

      <div className="input-box">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => { setInput(e.target.value); adjustHeight() }}
          onKeyDown={handleKey}
          rows={1}
          disabled={loading || listening}
          placeholder={listening ? 'Listening...' : 'Ask VidhyaGyan AI a question...'}
          style={{ overflow: 'hidden' }}
        />

        {/* Toolbar — exactly like v0 */}
        <div className="input-toolbar">
          <div className="toolbar-left">
            {/* Mic */}
            <button
              className={`tb-icon-btn ${listening ? 'mic-on' : ''}`}
              onClick={toggleVoice}
            >
              {listening ? <IconMicOff size={16} /> : <IconMic size={16} />}
              <span className="hover-label">{listening ? 'Stop' : 'Voice'}</span>
            </button>

            {/* Paperclip — decorative like v0 */}
            <button className="tb-icon-btn">
              <IconPaperclip size={16} />
              <span className="hover-label">Attach</span>
            </button>
          </div>

          <div className="toolbar-right">
            {/* Project / Subject badge */}
            <button className="tb-badge">
              <IconPlus size={14} />
              {activeSubj || 'Subject'}
            </button>

            {/* Send */}
            <button
              className={`send-btn ${input.trim() ? 'ready' : ''}`}
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
            >
              <IconArrowUp size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Action pills */}
      <div className="action-row">
        {QUICK.map(q => {
          const Icon = ICON_MAP[q.icon]
          return (
            <button key={q.label} className="action-btn" onClick={() => sendMessage(q.label)}>
              {Icon && <Icon size={14} />}
              <span>{q.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )

  return (
    <div className="app-shell">
      {/* ════════ TOP NAV ════════ */}
      <nav className="top-nav">
        <div className="nav-left">
          <button className="tb-icon-btn" onClick={() => setSidebarOpen(o => !o)} style={{ padding: 6 }}>
            <IconMenu size={18} />
          </button>
          <div className="nav-brand">
            <div className="nav-logo">
              <IconV size={16} />
            </div>
            <span className="nav-title">VidhyaGyan AI</span>
          </div>
        </div>

        <div className="nav-right">
          <div className="nav-status">
            <span className={`status-dot ${backendOk ? 'online' : 'offline'}`} />
            {backendOk ? 'Llama 3.3 70B · Groq' : 'Connecting...'}
          </div>
          <a href={`/api/log/${SESSION_ID}`} target="_blank" rel="noreferrer" className="nav-btn">
            <IconDownload size={12} />
            Log
          </a>
        </div>
      </nav>

      <div className="layout-body">
        {/* ════════ SIDEBAR ════════ */}
        <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
          <div>
            <div className="section-label">Class</div>
            <div className="class-grid">
              {CLASSES.map(c => (
                <button key={c} className={`class-btn ${activeCls === c ? 'active' : ''}`} onClick={() => handleClass(c)}>
                  {c}th
                </button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div className="section-label">Subject</div>
            <div className="subject-list">
              {SUBJECTS.map(s => (
                <button key={s} className={`subject-btn ${activeSubj === s ? 'active' : ''}`} onClick={() => handleSubject(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          {(sessionInfo.name || sessionInfo.class) && (
            <div className="session-info">
              {sessionInfo.name    && <div><strong>Student:</strong> {sessionInfo.name}</div>}
              {sessionInfo.class   && <div><strong>Class:</strong> {sessionInfo.class}</div>}
              {sessionInfo.subject && <div><strong>Subject:</strong> {sessionInfo.subject}</div>}
            </div>
          )}
        </aside>

        {/* ════════ CHAT AREA ════════ */}
        <div className="chat-area">
          {!hasMessages ? (
            /* ── Welcome state — centered like v0 ── */
            <div className="chat-welcome">
              <AnimatedHeading />
              {renderInputBox()}
            </div>
          ) : (
            /* ── Conversation state ── */
            <div className="chat-conversation">
              <div className="messages-scroll">
                <div className="messages-inner">
                  {messages.map(m => (
                    <div key={m.id} className={`msg-row ${m.role === 'user' ? 'user' : ''}`}>
                      {m.role === 'assistant' && (
                        <div className="bot-avatar">
                          <IconSparkle size={12} />
                        </div>
                      )}
                      <div className={`msg-bubble ${m.role === 'user' ? 'user' : 'bot'}`}>
                        {m.text}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="typing-row">
                      <div className="bot-avatar">
                        <IconSparkle size={12} />
                      </div>
                      <div className="typing-bubble">
                        <div className="t-dot" />
                        <div className="t-dot" />
                        <div className="t-dot" />
                      </div>
                    </div>
                  )}

                  <div ref={bottomRef} />
                </div>
              </div>

              {renderInputBox()}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
