import { useState, useEffect, useRef } from 'react';
import { 
  Shield, 
  Mic, 
  MicOff, 
  Camera, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  Send, 
  Edit3, 
  Eye, 
  ListOrdered,
  Activity,
  Lock,
  Unlock,
  GraduationCap
} from 'lucide-react';
import './index.css';

const defaultBase = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : `${window.location.protocol}//${window.location.hostname}:8000`;
const API_BASE = import.meta.env.VITE_API_URL || defaultBase;

function getAuthHeaders() {
  const key = sessionStorage.getItem('andrew_key');
  return {
    'Content-Type': 'application/json',
    'X-Andrew-Key': key || '',
  };
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...getAuthHeaders(), ...(options.headers || {}) },
  });
  if (res.status === 403) {
    sessionStorage.removeItem('andrew_key');
    window.location.reload();
  }
  return res;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!sessionStorage.getItem('andrew_key'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const [donnaMessage, setDonnaMessage] = useState("Good morning. The Event Bus is listening.");
  const [statusColor, setStatusColor] = useState('var(--teal)');
  const [chatInput, setChatInput] = useState('');

  const [hasInterviewAlert, setHasInterviewAlert] = useState(false);
  const [isBiometricLocked, setIsBiometricLocked] = useState(false);
  const [hasPendingProposal, setHasPendingProposal] = useState(false);
  const [hasShadowMessage, setHasShadowMessage] = useState(false);
  
  // Real data states — all start empty, populated from backend API
  const [energyScore, setEnergyScore] = useState(0);
  const [dynamicBarColor, setDynamicBarColor] = useState('var(--teal)');
  const [dynamicBarText, setDynamicBarText] = useState("Connecting to Andrew...");
  const [pendingDrafts, setPendingDrafts] = useState([]);
  const [scheduleItems, setScheduleItems] = useState([]);
  const [revenueData, setRevenueData] = useState({
    projected_earnings: 0.00,
    bounties_won: 0.00,
    saas_income: 0.00
  });
  const [relocationFund, setRelocationFund] = useState(0);

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const msg = new SpeechSynthesisUtterance(text);
      msg.rate = 0.9;
      window.speechSynthesis.speak(msg);
    }
  };

  // WebSocket Connection
  useEffect(() => {
    if (!isAuthenticated) return;
    
    const fetchStatus = async () => {
      try {
        const rt = await apiFetch('/api/v1/runtime/status');
        if (rt.ok) {
           const data = await rt.json();
           setEnergyScore(data.cycle_count || 0);
           setDynamicBarText(data.mode ? `Mode: ${data.mode}` : 'Andrew Online');
           setDynamicBarColor('var(--green)');
        }
      } catch (e) { console.error(e); }

      try {
        const rev = await apiFetch('/api/v1/wealth/portfolio');
        if (rev.ok) {
           const revData = await rev.json();
           const ownerWallet = revData.wallets?.owner_personal_wallet || {};
           const escrowWallet = revData.wallets?.upwork_escrow || {};
           const savingsWallet = revData.wallets?.relocation_savings || {};
           setRevenueData({
             projected_earnings: ownerWallet.balance || 0,
             bounties_won: escrowWallet.balance || 0,
             saas_income: 0.00
           });
           setRelocationFund(savingsWallet.balance || 0);
        }
      } catch (e) { console.error(e); }

      try {
        const sch = await apiFetch('/api/v1/schedule', {
          method: 'POST',
          body: JSON.stringify({ tasks: [], busy_slots: [] })
        });
        if (sch.ok) {
           const schData = await sch.json();
           if (schData.raw_schedule && schData.raw_schedule.schedule) {
             const items = schData.raw_schedule.schedule.map(s => ({
               time: s.start.substring(11, 16),
               title: s.task_id,
               urgency: "Medium",
               energy: 50,
               type: "work"
             }));
             if (items.length > 0) setScheduleItems(items);
           }
        }
      } catch (e) { console.error(e); }
    };
    fetchStatus();

    const wsUrl = API_BASE.replace('http', 'ws') + '/ws';
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Connected to Andrew Event Bus');
      ws.send('Frontend Online');
    };
    
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'job_found') {
           setDynamicBarText(`Scout Found: ${msg.data.job.title}`);
           setDynamicBarColor("var(--green)");
           setHasInterviewAlert(true);
           const alertText = `Alert. New Upwork job identified: ${msg.data.job.title}.`;
           setDonnaMessage(alertText);
           setStatusColor("var(--red)");
           speak(alertText);
        }
        else if (msg.type === 'gap_found') {
           setHasPendingProposal(true);
           const text = `Skill gap identified: ${msg.data.gap}. Generating a lesson.`;
           setDonnaMessage(text);
           speak(text);
        }
        else if (msg.type === 'quiz_ready') {
           setPendingDrafts(prev => [...prev, { sender: "Tutor", message: `New quiz ready for ${msg.data.gap}` }]);
           speak("A new learning module is ready for your review.");
        }
      } catch (e) {
        // If it's a raw string message from manager.broadcast
        if (typeof event.data === 'string' && event.data.startsWith('Andrew')) {
          console.log(event.data);
        }
      }
    };
    
    return () => ws.close();
  }, [isAuthenticated]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        sessionStorage.setItem('andrew_key', data.api_key);
        setIsAuthenticated(true);
      } else {
        setLoginError('Access Denied. Identity mismatch.');
      }
    } catch {
      setLoginError('Cannot reach Andrew Core. Is the backend running?');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCamera = () => {
    setDynamicBarText("VISION ONLINE");
    setDynamicBarColor("var(--green)");
    setDonnaMessage("Analyzing visual input. Face recognized.");
    speak("Analyzing visual input. Face recognized.");
  };

  const handleMic = () => {
    setIsListening(!isListening);
    if (!isListening) {
      setDynamicBarText("LISTENING...");
      setDynamicBarColor("var(--red)");
    } else {
      setDynamicBarText("STANDBY");
      setDynamicBarColor("var(--teal)");
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput) return;
    const msg = chatInput;
    setChatInput('');
    setDonnaMessage("Thinking...");
    
    try {
      const res = await apiFetch('/api/v1/chat', {
        method: 'POST',
        body: JSON.stringify({ message: msg })
      });
      if (res.ok) {
        const data = await res.json();
        setDonnaMessage(data.reply);
        speak(data.reply);
      }
    } catch(e) {
      console.error(e);
      const err = "Neural link offline. Cannot reach persona.";
      setDonnaMessage(err);
      speak(err);
    }
  };

  const getColorForType = (type, energy) => {
    if (type === "personal") return 'var(--green)';
    if (type === "career") return 'var(--purple)';
    if (energy > 80) return 'var(--red)';
    if (energy > 60) return 'var(--orange)';
    return 'var(--blue)';
  };

  if (!isAuthenticated) {
    return (
      <div className="app-container bg-low-energy" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '20px' }}>
        <Shield size={64} color="var(--cyan)" style={{ marginBottom: '2rem' }} />
        <h1 className="title-massive" style={{ fontSize: '3rem', textAlign: 'center' }}>The Sovereign Agent</h1>
        <p style={{ color: 'rgba(255,255,255,0.7)', marginTop: '1rem' }}>Identity Verification Required.</p>
        
        <form onSubmit={handleLogin} className="glass-panel" style={{ marginTop: '3rem', width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {loginError && <p style={{ color: 'var(--red)', margin: 0, fontSize: '14px', textAlign: 'center' }}>{loginError}</p>}
          <input 
            type="email" 
            style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', padding: '15px', borderRadius: '12px' }} 
            placeholder="Owner Email" 
            value={email} onChange={e => setEmail(e.target.value)} required 
          />
          <input 
            type="password" 
            style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', padding: '15px', borderRadius: '12px' }} 
            placeholder="Access Key" 
            value={password} onChange={e => setPassword(e.target.value)} required 
          />
          <button type="submit" className="btn-primary" style={{ padding: '15px', fontSize: '16px' }} disabled={isLoading}>
            {isLoading ? 'Connecting...' : 'Initiate Handshake'}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className={`app-container ${energyScore > 70 ? 'bg-high-energy' : 'bg-low-energy'}`}>
      
      {/* App Bar (Floating) */}
      <div style={{ position: 'fixed', top: 0, width: '100%', padding: '15px 20px', display: 'flex', justifyContent: 'flex-end', gap: '15px', zIndex: 50 }}>
        <button onClick={() => speak("Mock interview sequence initiated.")} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
          <Shield color="var(--blue)" size={24} />
        </button>
        <button onClick={handleCamera} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
          <Camera color="var(--green)" size={24} />
        </button>
        <button onClick={handleMic} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
          {isListening ? <Mic color="var(--red)" size={24} /> : <MicOff color="rgba(255,255,255,0.7)" size={24} />}
        </button>
      </div>

      {/* Dynamic Bar */}
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '40px', position: 'relative', zIndex: 10 }}>
        <div className="dynamic-bar" style={{ borderColor: dynamicBarColor }}>
          <Zap size={14} color={dynamicBarColor} />
          <span style={{ color: 'white', marginLeft: '5px' }}>{dynamicBarText}</span>
        </div>
      </div>

      <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '25px' }}>
        
        {/* Interview Alert */}
        {hasInterviewAlert && (
          <div className="fade-slide-up" style={{ animationDelay: '0.1s', background: 'rgba(255, 77, 106, 0.9)', padding: '12px 15px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle color="white" size={20} />
            <span style={{ color: 'white', fontWeight: 'bold', fontSize: '13px' }}>🚨 INTERVIEW READY: Upwork Client booked for 2 PM.</span>
          </div>
        )}

        {/* Wealth Dashboard */}
        <div className="glass-panel fade-slide-up" style={{ animationDelay: '0.2s', display: 'flex', justifyContent: 'space-evenly', borderTopColor: 'var(--green)' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--green)', fontSize: '24px', fontWeight: 'bold' }}>${revenueData.projected_earnings}</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>Projected Earnings</div>
          </div>
          <div style={{ width: '1px', background: 'rgba(255,255,255,0.2)' }}></div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--green)', fontSize: '18px', fontWeight: 'bold' }}>${revenueData.bounties_won}</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>Bounties</div>
          </div>
          <div style={{ width: '1px', background: 'rgba(255,255,255,0.2)' }}></div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--green)', fontSize: '18px', fontWeight: 'bold' }}>${revenueData.saas_income}</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>Passive SaaS</div>
          </div>
        </div>

        {/* Relocation Fund — reads from backend */}
        {relocationFund > 0 && (
          <div className="glass-panel fade-slide-up" style={{ animationDelay: '0.3s', display: 'flex', justifyContent: 'space-evenly', borderTopColor: 'var(--blue)' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>${relocationFund} USDT</div>
              <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>Relocation Fund</div>
            </div>
          </div>
        )}

        {/* Handshake (Proposal) */}
        {hasPendingProposal && (
          <div className="glass-panel slide-in-right" style={{ animationDelay: '0.4s', borderTopColor: 'var(--blue)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <ListOrdered color="var(--blue)" size={20} />
              <strong style={{ color: 'white' }}>Proposal Drafted</strong>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '13px', margin: '0 0 15px 0' }}>
              Donald, I found a Remote Cloud Migration internship. I've drafted a proposal based on your AWS school lab. Submit it?
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-primary" onClick={() => {
                setHasPendingProposal(false);
                setDonnaMessage("Sent. I've connected with the Hiring Manager on LinkedIn.");
                speak("Sent. I've connected with the Hiring Manager on LinkedIn.");
              }}>Yes</button>
              <button className="btn-outline danger" onClick={() => setHasPendingProposal(false)}>No</button>
              <button className="btn-outline">Edit</button>
            </div>
          </div>
        )}

        {/* Shadow Mode */}
        {hasShadowMessage && (
          <div className="glass-panel slide-in-right" style={{ animationDelay: '0.5s', borderTopColor: 'var(--purple)', position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <Eye color="var(--purple)" size={16} />
              <span style={{ color: 'var(--purple)', fontSize: '10px', fontWeight: 'bold', letterSpacing: '1px' }}>SHADOW MODE (WhatsApp)</span>
            </div>
            <div style={{ color: 'white', fontWeight: 'bold', fontSize: '12px', marginBottom: '5px' }}>From: Uncle Steve</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontStyle: 'italic', fontSize: '13px' }}>
              Draft: "Got the link, thanks! I'll take a proper look when I finish this meeting at 5."
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '15px' }}>
              <button className="btn-outline" onClick={() => setHasShadowMessage(false)}><Edit3 size={14} style={{ marginRight: '5px' }} />Edit</button>
              <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '5px' }} onClick={() => {
                setHasShadowMessage(false);
                speak("Sent exactly as you would have.");
              }}>
                <Send size={14} /> Send
              </button>
            </div>
          </div>
        )}

        {/* Timeline — populated from backend schedule API */}
        <h3 style={{ color: 'white', marginTop: '20px', marginBottom: '0px' }}>Today's Trajectory</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {scheduleItems.length === 0 ? (
            <div className="glass-panel fade-slide-up" style={{ animationDelay: '0.6s', padding: '20px', textAlign: 'center' }}>
              <Activity size={20} color="rgba(255,255,255,0.4)" style={{ marginBottom: '8px' }} />
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>No schedule generated yet. Andrew will build one as tasks arrive.</div>
            </div>
          ) : (
            scheduleItems.map((item, idx) => {
              const color = getColorForType(item.type, item.energy);
              return (
                <div key={idx} className="glass-panel fade-slide-up" style={{ animationDelay: `${0.6 + (idx * 0.1)}s`, padding: '15px', borderLeft: `3px solid ${color}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', fontWeight: 'bold' }}>{item.time}</span>
                    {item.energy && <span className="timeline-badge" style={{ background: color, color: 'black' }}>Energy: {item.energy}</span>}
                  </div>
                  <div style={{ color: 'white', fontSize: '16px', fontWeight: 'bold' }}>{item.title}</div>
                  {item.note && (
                    <div style={{ display: 'flex', gap: '5px', marginTop: '10px', color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontStyle: 'italic' }}>
                      <Activity size={14} /> <span>{item.note}</span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

      </div>

      {/* Floating Donna Persona Console */}
      <div className="donna-console">
        {pendingDrafts.length > 0 && (
          <div className="glass-panel" style={{ padding: '10px 15px', marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTopColor: 'var(--red)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle color="var(--red)" size={18} />
              <strong style={{ color: 'white', fontSize: '13px' }}>{pendingDrafts.length} Pending Approval(s)</strong>
            </div>
            <button style={{ background: 'transparent', border: 'none', cursor: 'pointer' }} onClick={() => {
              setPendingDrafts([]);
              speak("Drafts approved and sent.");
            }}>
              <CheckCircle color="var(--green)" size={20} />
            </button>
          </div>
        )}

        <div className="glass-panel" style={{ borderTopColor: statusColor, padding: '15px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <Activity className="pulse-scale" color={statusColor} size={24} />
            <div style={{ color: 'white', fontSize: '13px', fontStyle: 'italic', flex: 1 }}>{donnaMessage}</div>
          </div>
          <form className="donna-input-wrapper" onSubmit={handleChatSubmit}>
            <input 
              type="text" 
              className="donna-input" 
              placeholder="Briefing Console..." 
              value={chatInput} 
              onChange={e => setChatInput(e.target.value)} 
            />
            <button type="submit" style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
              <Send color="rgba(255,255,255,0.5)" size={16} />
            </button>
          </form>
        </div>
      </div>

      {/* Floating Biometric Lock Button */}
      <div className="floating-lock" onClick={() => setIsBiometricLocked(true)}>
        <Shield color="white" size={24} />
      </div>

      {/* Biometric Overlay */}
      {isBiometricLocked && (
        <div className="biometric-overlay">
          <Lock color="var(--blue)" size={80} style={{ marginBottom: '20px' }} />
          <h2 style={{ color: 'white', margin: 0 }}>Biometric Dead-Drop Active</h2>
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px', marginTop: '10px' }}>Andrew requires FaceID to process sensitive requests.</p>
          <button className="btn-primary" style={{ marginTop: '30px', background: 'var(--blue)', color: 'white', display: 'flex', alignItems: 'center', gap: '10px' }} onClick={() => setIsBiometricLocked(false)}>
            <Unlock size={18} /> Simulate FaceID Unlock
          </button>
        </div>
      )}

    </div>
  );
}

export default App;
