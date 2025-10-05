import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Send, Bot, User, Loader2, Paperclip, AlertTriangle, Shield } from 'lucide-react';
import api from '../api';
import { freeAPI } from '../api/free';

const LandingChat = () => {
  // const [documentId, setDocumentId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [waitingSession, setWaitingSession] = useState(false);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [isAnalyzingRisks, setIsAnalyzingRisks] = useState(false);
  const fileInputRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleUpload = async (file) => {
    if (!file) return;
    setIsUploading(true);
    try {
      const res = await freeAPI.uploadDocument(file);
      // poll for session creation until document is processed
      setWaitingSession(true);
      const start = Date.now();
      while (Date.now() - start < 60000) { // up to 60s
        try {
          const sessionRes = await freeAPI.createSession(res.data.id);
          setSessionId(sessionRes.data.id);
          setWaitingSession(false);
          break;
        } catch (e) {
          await new Promise(r => setTimeout(r, 1500));
        }
      }
      setWaitingSession(false);
    } catch (e) {
      console.error('Upload failed', e);
      alert('Upload failed. Please try a smaller PDF or DOCX.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleAnalyzeRisks = async () => {
    if (!sessionId || isAnalyzingRisks) return;
    setIsAnalyzingRisks(true);
    try {
      const res = await freeAPI.analyzeRisks(sessionId);
      setRiskAnalysis(res.data);
      setMessages((m) => [...m, { 
        type: 'ai', 
        content: `🔍 **Risk Analysis Complete**\n\n**Risk Level:** ${res.data.risk_level}\n\n**Analysis:**\n${res.data.risk_analysis}\n\n**Recommendations:**\n${res.data.recommendations.join('\n')}`, 
        id: Date.now() 
      }]);
    } catch (e) {
      console.error('Risk analysis failed', e);
      setMessages((m) => [...m, { 
        type: 'ai', 
        content: 'Error analyzing risks. Please try again.', 
        id: Date.now() 
      }]);
    } finally {
      setIsAnalyzingRisks(false);
    }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!sessionId || !question.trim() || isLoading) return;
    const text = question.trim();
    setQuestion('');
    setMessages((m) => [...m, { type: 'user', content: text, id: Date.now() }]);
    setIsLoading(true);
    try {
      const res = await freeAPI.askQuestion(sessionId, text);
      setMessages((m) => [...m, { type: 'ai', content: res.data.answer || 'No answer returned.', id: Date.now() + 1 }]);
    } catch (e) {
      console.error('Ask failed', e);
      setMessages((m) => [...m, { type: 'ai', content: 'Error answering. Please try again.', id: Date.now() + 1 }]);
    } finally {
      setIsLoading(false);
    }
  };

  // const endSession = async () => {
  //   try {
  //     if (sessionId) await api.delete(`/api/free/sessions/${sessionId}`);
  //     setSessionId(null);
  //     setMessages([]);
  //   } catch (e) {
  //     console.error('Failed to end session', e);
  //   }
  // };

  return (
    <div style={{
      minHeight:'100vh', 
      background:'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color:'#ffffff', 
      fontFamily:'-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position:'relative',
      overflow:'hidden'
    }}>
      {/* Background Pattern */}
      <div style={{
        position:'absolute',
        top:0,
        left:0,
        right:0,
        bottom:0,
        backgroundImage:'radial-gradient(circle at 25% 25%, rgba(16, 163, 127, 0.1) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)',
        pointerEvents:'none'
      }}></div>

      {/* Header with Sign up/Sign in buttons */}
      <div style={{
        display:'flex', 
        justifyContent:'space-between', 
        alignItems:'center', 
        padding:'1.5rem 2rem',
        position:'relative',
        zIndex:1
      }}>
        <div style={{display:'flex', alignItems:'center', gap:'12px'}}>
          <div style={{
            width:'40px',
            height:'40px',
            background:'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            borderRadius:'12px',
            display:'flex',
            alignItems:'center',
            justifyContent:'center',
            boxShadow:'0 4px 12px rgba(59, 130, 246, 0.3)'
          }}>
            <Bot size={20} color="#ffffff"/>
          </div>
          <h1 style={{fontSize:'20px', fontWeight:'700', margin:0, background:'linear-gradient(135deg, #ffffff, #3b82f6)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent'}}>
            Legal Assistant
          </h1>
        </div>
        <div style={{display:'flex', gap:16}}>
          <Link to="/login" style={{
            color:'#ffffff', 
            textDecoration:'none', 
            fontSize:'14px', 
            fontWeight:'500',
            padding:'8px 16px',
            borderRadius:'8px',
            transition:'all 0.2s ease',
            background:'rgba(255, 255, 255, 0.1)',
            border:'1px solid rgba(255, 255, 255, 0.2)'
          }}>Log in</Link>
          <Link to="/signup" style={{
            background:'linear-gradient(135deg, #10a37f, #059669)', 
            color:'#ffffff', 
            textDecoration:'none', 
            padding:'8px 20px', 
            borderRadius:'8px', 
            fontSize:'14px', 
            fontWeight:'600',
            boxShadow:'0 4px 12px rgba(16, 163, 127, 0.3)',
            transition:'all 0.2s ease'
          }}>Sign up</Link>
        </div>
      </div>

      {/* Main chat area - Full width */}
      <div style={{
        display:'flex', 
        flexDirection:'column', 
        height:'calc(100vh - 100px)', 
        width:'100%',
        padding:'0 2rem',
        position:'relative',
        zIndex:2
      }}>
        
        {/* Chat messages area */}
        <div style={{
          flex:1, 
          overflowY:'auto', 
          padding:'1rem 0', 
          display:'flex', 
          flexDirection:'column', 
          justifyContent: messages.length === 0 ? 'center' : 'flex-start',
          maxWidth:'1200px',
          margin:'0 auto',
          width:'100%',
          marginTop:'1rem',
          minHeight:'400px',
          maxHeight:'calc(100vh - 300px)'
        }}>
          {messages.length === 0 && !isLoading ? (
            <div style={{textAlign:'center', marginBottom:'2rem'}}>
              <div style={{
                width:'80px',
                height:'80px',
                background:'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                borderRadius:'20px',
                display:'flex',
                alignItems:'center',
                justifyContent:'center',
                margin:'0 auto 24px',
                boxShadow:'0 8px 32px rgba(59, 130, 246, 0.3)'
              }}>
                <Bot size={32} color="#ffffff"/>
              </div>
              <h1 style={{
                fontSize:'48px', 
                fontWeight:'700', 
                marginBottom:'16px', 
                background:'linear-gradient(135deg, #ffffff, #3b82f6)', 
                WebkitBackgroundClip:'text', 
                WebkitTextFillColor:'transparent',
                letterSpacing:'-0.02em'
              }}>What can I help with?</h1>
              <p style={{
                fontSize:'18px',
                color:'rgba(255, 255, 255, 0.7)',
                marginBottom:'32px',
                maxWidth:'600px',
                margin:'0 auto 32px',
                lineHeight:'1.6'
              }}>
                Upload your legal documents and get instant answers to your questions. 
                Powered by advanced AI technology.
              </p>
            </div>
          ) : (
            <div style={{flex:1, display:'flex', flexDirection:'column', justifyContent:'flex-start', maxWidth:'1200px', margin:'0 auto', width:'100%', padding:'0 20px'}}>
              {messages.map((m) => (
                <div key={m.id} style={{
                  display:'flex', 
                  gap:'16px', 
                  marginBottom:'24px',
                  padding:'20px',
                  alignItems:'flex-start',
                  background:'rgba(255, 255, 255, 0.02)',
                  borderRadius:'16px',
                  border:'1px solid rgba(255, 255, 255, 0.05)',
                  backdropFilter:'blur(10px)',
                  width:'100%',
                  boxSizing:'border-box'
                }}>
                  <div style={{
                    width:'40px', 
                    height:'40px', 
                    borderRadius:'50%', 
                    background: m.type === 'user' ? 'linear-gradient(135deg, #10a37f, #059669)' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                    display:'flex', 
                    alignItems:'center', 
                    justifyContent:'center',
                    flexShrink:0,
                    boxShadow:'0 4px 12px rgba(0, 0, 0, 0.2)'
                  }}>
                    {m.type === 'user' ? <User size={18} color="#ffffff"/> : <Bot size={18} color="#ffffff"/>}                
                  </div>
                  <div style={{
                    flex:1,
                    fontSize:'16px',
                    lineHeight:'1.7',
                    color:'#ffffff',
                    whiteSpace:'pre-wrap',
                    wordBreak:'break-word',
                    fontWeight:'400'
                  }}>
                    {m.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div style={{display:'flex', gap:'16px', marginBottom:'24px', padding:'20px', background:'rgba(255, 255, 255, 0.02)', borderRadius:'16px', border:'1px solid rgba(255, 255, 255, 0.05)', backdropFilter:'blur(10px)', width:'100%', boxSizing:'border-box'}}>
                  <div style={{
                    width:'40px', 
                    height:'40px', 
                    borderRadius:'50%', 
                    background:'linear-gradient(135deg, #6366f1, #4f46e5)',
                    display:'flex', 
                    alignItems:'center', 
                    justifyContent:'center',
                    flexShrink:0,
                    boxShadow:'0 4px 12px rgba(0, 0, 0, 0.2)'
                  }}>
                    <Bot size={18} color="#ffffff"/>
                  </div>
                  <div style={{flex:1, display:'flex', alignItems:'center', gap:'8px'}}>
                    <Loader2 size={20} className="animate-spin" color="#6366f1"/>
                    <span style={{color:'rgba(255, 255, 255, 0.7)', fontSize:'14px'}}>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={endRef}/>
            </div>
          )}
        </div>

        {/* Input area */}
        <div style={{
          padding:'24px 2rem',
          position:'relative',
          marginBottom:'1rem'
        }}>
          <div style={{
            maxWidth:'1200px',
            margin:'0 auto',
            width:'100%',
            backdropFilter:'blur(20px)',
            background:'rgba(255, 255, 255, 0.02)',
            border:'1px solid rgba(255, 255, 255, 0.05)',
            borderRadius:'16px',
            padding:'20px',
            boxShadow:'0 8px 32px rgba(0, 0, 0, 0.2)'
          }}>
            <div style={{
              display:'flex',
              alignItems:'center',
              background:'rgba(255, 255, 255, 0.05)',
              border:'1px solid rgba(255, 255, 255, 0.1)',
              borderRadius:'12px',
              padding:'12px 16px',
              gap:'12px',
              position:'relative',
              backdropFilter:'blur(10px)',
              transition:'all 0.2s ease'
            }}>
            <button 
              type="button" 
              onClick={()=>!isUploading && fileInputRef.current?.click()} 
              style={{
                background:'rgba(255, 255, 255, 0.1)',
                border:'1px solid rgba(255, 255, 255, 0.2)',
                color:'#ffffff',
                cursor: isUploading ? 'not-allowed' : 'pointer',
                padding:'8px',
                borderRadius:'8px',
                opacity: isUploading ? 0.5 : 1,
                transition:'all 0.2s ease',
                display:'flex',
                alignItems:'center',
                justifyContent:'center'
              }}
              title="Attach document" 
              disabled={isUploading}
            >
              <Paperclip size={18}/>
            </button>
            <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx" onChange={(e)=>handleUpload(e.target.files?.[0])} style={{display:'none'}}/>
            
            {sessionId && (
              <button 
                type="button" 
                onClick={handleAnalyzeRisks}
                disabled={isAnalyzingRisks}
                style={{
                  background:'rgba(255, 193, 7, 0.2)',
                  border:'1px solid rgba(255, 193, 7, 0.4)',
                  color:'#ffc107',
                  cursor: isAnalyzingRisks ? 'not-allowed' : 'pointer',
                  padding:'8px',
                  borderRadius:'8px',
                  opacity: isAnalyzingRisks ? 0.5 : 1,
                  transition:'all 0.2s ease',
                  display:'flex',
                  alignItems:'center',
                  justifyContent:'center'
                }}
                title="Analyze risks in document"
              >
                {isAnalyzingRisks ? <Loader2 size={18} className="animate-spin"/> : <Shield size={18}/>}
              </button>
            )}
              
              <input
                type="text"
                value={question}
                onChange={(e)=>setQuestion(e.target.value)}
                placeholder={waitingSession ? 'Processing your document…' : (sessionId ? 'Ask anything about your legal document...' : 'Attach a document to start asking questions')}
                disabled={!sessionId || isLoading || waitingSession}
                style={{
                  flex:1,
                  background:'transparent',
                  border:'none',
                  outline:'none',
                  color:'#ffffff',
                  fontSize:'16px',
                  padding:'8px 0',
                  fontWeight:'400'
                }}
              />
              
              <button 
                onClick={handleAsk} 
                style={{
                  background: (!sessionId || !question.trim() || isLoading || waitingSession) ? 'rgba(255, 255, 255, 0.1)' : 'linear-gradient(135deg, #10a37f, #059669)',
                  border:'none',
                  borderRadius:'12px',
                  padding:'12px 16px',
                  cursor: (!sessionId || !question.trim() || isLoading || waitingSession) ? 'not-allowed' : 'pointer',
                  color:'#ffffff',
                  display:'flex',
                  alignItems:'center',
                  justifyContent:'center',
                  boxShadow: (!sessionId || !question.trim() || isLoading || waitingSession) ? 'none' : '0 4px 12px rgba(16, 163, 127, 0.3)',
                  transition:'all 0.2s ease'
                }}
                disabled={!sessionId || !question.trim() || isLoading || waitingSession}
              >
                <Send size={18}/>
              </button>
            </div>
            
            <div style={{
              textAlign:'center',
              marginTop:'16px',
              fontSize:'13px',
              color:'rgba(255, 255, 255, 0.6)',
              display:'flex',
              alignItems:'center',
              justifyContent:'center',
              gap:'8px'
            }}>
              <div style={{width:'4px', height:'4px', background:'#10a37f', borderRadius:'50%'}}></div>
              AI Legal Assistant can make mistakes. Check important info.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingChat;


