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
const QUICK    = ['Newton ka 3rd law samjhao','Photosynthesis explain karo','Kal exam hai — help karo','Quiz mode on karo']

const bounceStyle = document.createElement('style')
bounceStyle.textContent = `
  textarea:focus { border-color: var(--accent) !important; outline: none; }
  .hint:hover { background: var(--surface2) !important; color: var(--text) !important; }
  .subj:hover { background: var(--accent-soft) !important; color: var(--accent) !important; }
  @keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40% { transform: translateY(-6px); opacity: 1; }
  }
`
document.head.appendChild(bounceStyle)

export default function App() {
  const [messages,    setMessages]    = useState([])
  const [input,       setInput]       = useState('')
  const [loading,     setLoading]     = useState(false)
  const [listening,   setListening]   = useState(false)
  const [sessionInfo, setSessionInfo] = useState({})
  const [activeSubj,  setActiveSubj]  = useState(null)
  const [activeCls,   setActiveCls]   = useState(null)
  const [backendOk,   setBackendOk]   = useState(false)

  const bottomRef = useRef(null)
  const taRef     = useRef(null)
  const recognRef = useRef(null)
  const audioRef  = useRef(null)

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(() => setBackendOk(true)).catch(() => {})
  }, [])

  useEffect(() => {
    const greeting = 'Namaste! Main hoon AI-BOT, tumhara study companion. Pehle batao — tumhara naam kya hai aur tum konsi class mein ho?'
    setMessages([{ id: 0, role: 'assistant', text: greeting }])
    apiChat('__init__', true).then(d => { if (d.audio_b64) playAudio(d.audio_b64) }).catch(() => {})
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const sendMessage = useCallback(async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', text: msg }])
    setLoading(true)
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    try {
      const data = await apiChat(msg, true)
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: data.reply }])
      if (data.session_info) setSessionInfo(data.session_info)
      if (data.audio_b64)   audioRef.current = playAudio(data.audio_b64)
    } catch {
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: 'Ek second — kuch technical issue aa gayi. Dobara try karo.' }])
    } finally {
      setLoading(false)
      taRef.current?.focus()
    }
  }, [input, loading])

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

  const C = {
    app:      { display:'flex', height:'100vh', width:'100vw', overflow:'hidden' },
    sidebar:  { width:220, minWidth:220, background:'var(--surface)', borderRight:'1px solid var(--border)', display:'flex', flexDirection:'column', padding:'18px 14px', gap:18 },
    logo:     { display:'flex', alignItems:'center', gap:10, paddingBottom:14, borderBottom:'1px solid var(--border)' },
    av:       { width:34, height:34, borderRadius:'50%', background:'var(--accent)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:15, fontWeight:600, color:'#fff', flexShrink:0 },
    slabel:   { fontSize:10, fontWeight:600, color:'var(--text-muted)', letterSpacing:'0.1em', textTransform:'uppercase', marginBottom:6 },
    clsGrid:  { display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:5 },
    clsBtn:   (a) => ({ padding:'5px 0', borderRadius:7, border:'1px solid', borderColor:a?'var(--accent)':'var(--border)', background:a?'var(--accent-soft)':'transparent', color:a?'var(--accent)':'var(--text-muted)', fontSize:11, fontWeight:500, cursor:'pointer' }),
    subjList: { display:'flex', flexDirection:'column', gap:3, overflowY:'auto', flex:1 },
    subjBtn:  (a) => ({ padding:'6px 9px', borderRadius:7, border:'1px solid', borderColor:a?'var(--accent)':'transparent', background:a?'var(--accent-soft)':'transparent', color:a?'var(--accent)':'var(--text-muted)', fontSize:12, fontWeight:500, cursor:'pointer', textAlign:'left' }),
    infoBox:  { padding:'9px 11px', borderRadius:9, background:'var(--accent-soft)', border:'1px solid var(--border)', fontSize:11, color:'var(--text-muted)', lineHeight:1.8 },
    logBtn:   { padding:'7px 11px', borderRadius:7, border:'1px solid var(--border)', background:'transparent', color:'var(--text-muted)', fontSize:11, cursor:'pointer', width:'100%', textDecoration:'none', display:'block', textAlign:'center' },
    main:     { flex:1, display:'flex', flexDirection:'column', overflow:'hidden' },
    header:   { padding:'12px 18px', borderBottom:'1px solid var(--border)', background:'var(--surface)', display:'flex', alignItems:'center', justifyContent:'space-between' },
    dot:      (ok) => ({ width:7, height:7, borderRadius:'50%', background:ok?'var(--green)':'var(--text-muted)', display:'inline-block', marginRight:6 }),
    msgs:     { flex:1, overflowY:'auto', padding:'18px 22px', display:'flex', flexDirection:'column', gap:10 },
    row:      (u) => ({ display:'flex', flexDirection:u?'row-reverse':'row', alignItems:'flex-end', gap:7 }),
    botAv:    { width:26, height:26, borderRadius:'50%', background:'var(--accent)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:11, fontWeight:600, color:'#fff', flexShrink:0 },
    bubble:   (u) => ({ maxWidth:'72%', padding:'9px 13px', borderRadius:u?'16px 16px 3px 16px':'16px 16px 16px 3px', background:u?'var(--bubble-user)':'var(--bubble-bot)', border:'1px solid var(--border)', fontSize:13, lineHeight:1.6, color:'var(--text)' }),
    typing:   { display:'flex', gap:4, alignItems:'center', padding:'9px 13px', background:'var(--bubble-bot)', borderRadius:'16px 16px 16px 3px', border:'1px solid var(--border)', alignSelf:'flex-start' },
    tdot:     (d) => ({ width:6, height:6, borderRadius:'50%', background:'var(--text-muted)', animation:'bounce 1.2s infinite', animationDelay:d }),
    inputArea:{ padding:'14px 18px', borderTop:'1px solid var(--border)', background:'var(--surface)', display:'flex', flexDirection:'column', gap:9 },
    hints:    { display:'flex', gap:7, flexWrap:'wrap' },
    hint:     { padding:'3px 9px', borderRadius:20, border:'1px solid var(--border)', background:'transparent', color:'var(--text-muted)', fontSize:11, cursor:'pointer' },
    inputRow: { display:'flex', gap:8, alignItems:'flex-end' },
    ta:       { flex:1, padding:'9px 13px', borderRadius:11, border:'1px solid var(--border)', background:'var(--surface2)', color:'var(--text)', fontSize:13, resize:'none', fontFamily:'var(--font)', lineHeight:1.5, maxHeight:110, minHeight:40 },
    micBtn:   (l) => ({ width:40, height:40, borderRadius:11, border:'1px solid', borderColor:l?'var(--green)':'var(--border)', background:l?'var(--green-soft)':'var(--surface2)', color:l?'var(--green)':'var(--text-muted)', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', fontSize:17, flexShrink:0 }),
    sendBtn:  (d) => ({ width:40, height:40, borderRadius:11, border:'none', background:d?'var(--border)':'var(--accent)', color:'#fff', cursor:d?'not-allowed':'pointer', display:'flex', alignItems:'center', justifyContent:'center', fontSize:17, flexShrink:0 }),
  }

  return (
    <div style={C.app}>
      <aside style={C.sidebar}>
        <div style={C.logo}>
          <div style={C.av}>AI</div>
          <div>
            <div style={{ fontSize:14, fontWeight:600 }}>AI-BOT</div>
            <div style={{ fontSize:10, color:'var(--text-muted)' }}>VidyaGyan</div>
          </div>
        </div>
        <div>
          <div style={C.slabel}>Class</div>
          <div style={C.clsGrid}>
            {CLASSES.map(c => <button key={c} style={C.clsBtn(activeCls===c)} onClick={() => handleClass(c)}>{c}th</button>)}
          </div>
        </div>
        <div style={{ flex:1, overflow:'hidden', display:'flex', flexDirection:'column' }}>
          <div style={C.slabel}>Subject</div>
          <div style={C.subjList}>
            {SUBJECTS.map(s => <button key={s} className="subj" style={C.subjBtn(activeSubj===s)} onClick={() => handleSubject(s)}>{s}</button>)}
          </div>
        </div>
        {(sessionInfo.name || sessionInfo.class) && (
          <div style={C.infoBox}>
            {sessionInfo.name    && <div>Student: {sessionInfo.name}</div>}
            {sessionInfo.class   && <div>Class: {sessionInfo.class}</div>}
            {sessionInfo.subject && <div>Subject: {sessionInfo.subject}</div>}
          </div>
        )}
        <a href={`/api/log/${SESSION_ID}`} target="_blank" rel="noreferrer" style={C.logBtn}>
          Download Session Log
        </a>
      </aside>
      <main style={C.main}>
        <header style={C.header}>
          <div>
            <div style={{ fontSize:13, fontWeight:600 }}><span style={C.dot(backendOk)} />AI-BOT Study Companion</div>
            <div style={{ fontSize:11, color:'var(--text-muted)', marginTop:2 }}>{backendOk ? 'Online · Llama 3.3 70B · Groq' : 'Connecting to backend...'}</div>
          </div>
          <div style={{ fontSize:11, color:'var(--text-muted)' }}>VidyaGyan · Shiv Nadar Foundation</div>
        </header>
        <div style={C.msgs}>
          {messages.map(m => (
            <div key={m.id} style={C.row(m.role==='user')}>
              {m.role==='assistant' && <div style={C.botAv}>AI</div>}
              <div style={C.bubble(m.role==='user')}>{m.text}</div>
            </div>
          ))}
          {loading && (
            <div style={C.row(false)}>
              <div style={C.botAv}>AI</div>
              <div style={C.typing}>
                <div style={C.tdot('0s')} /><div style={C.tdot('0.2s')} /><div style={C.tdot('0.4s')} />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <div style={C.inputArea}>
          <div style={C.hints}>
            {QUICK.map(q => <button key={q} className="hint" style={C.hint} onClick={() => sendMessage(q)}>{q}</button>)}
          </div>
          <div style={C.inputRow}>
            <button style={C.micBtn(listening)} onClick={toggleVoice} title={listening?'Stop':'Speak'}>
              {listening ? 'Stop' : 'Mic'}
            </button>
            <textarea ref={taRef} style={C.ta} value={input}
              onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
              rows={1} disabled={loading||listening}
              placeholder={listening ? 'Listening...' : 'Type your doubt or click Mic to speak...'} />
            <button style={C.sendBtn(!input.trim()||loading)} onClick={() => sendMessage()} disabled={!input.trim()||loading}>Send</button>
          </div>
        </div>
      </main>
    </div>
  )
}
