"use client";

import React, { useState, useEffect, useRef } from 'react';
import { queryAssistantAPI } from '../../lib/api';
import styles from './AIAssistant.module.css';

export default function AIAssistant({ offlineMode, handleSelectMouseDown, handleSelectChange }) {
  const [fanLang, setFanLang] = useState('en');
  const [queryInput, setQueryInput] = useState('');
  const [sessions, setSessions] = useState([
    {
      id: 'session-1',
      title: 'Stadium Wayfinding Guide',
      age: '2m ago',
      history: [
        { sender: 'bot', text: 'Welcome to the FIFA World Cup 2026 Operations Assistant. How can I help you navigate the stadium today?', timestamp: '10:30 AM' },
        { sender: 'user', text: 'Where is the nearest wheelchair ramp from Gate A?', timestamp: '10:31 AM' },
        { sender: 'bot', text: 'The nearest wheelchair ramp from Gate A is located 15 meters to the left of the main gate entrance. Follow the blue line markings on the pavement.', timestamp: '10:31 AM' }
      ]
    },
    {
      id: 'session-2',
      title: 'Transit Route to Gate B',
      age: '1h ago',
      history: [
        { sender: 'bot', text: 'Welcome to the FIFA World Cup 2026 Operations Assistant. How can I help you navigate the stadium today?', timestamp: '09:30 AM' },
        { sender: 'user', text: 'What is the fastest way to Gate B from the transit plaza?', timestamp: '09:31 AM' },
        { sender: 'bot', text: 'The fastest way to Gate B from the transit plaza is via the East Walkway. It is currently at Low Density (15%) and takes approximately 4 minutes to walk.', timestamp: '09:32 AM' }
      ]
    },
    {
      id: 'session-3',
      title: 'Concourse Restrooms',
      age: '3h ago',
      history: [
        { sender: 'bot', text: 'Welcome to the FIFA World Cup 2026 Operations Assistant. How can I help you navigate the stadium today?', timestamp: '07:30 AM' },
        { sender: 'user', text: 'Are there any accessible restrooms on Concourse level 2?', timestamp: '07:31 AM' },
        { sender: 'bot', text: 'Yes, there are two accessible family restrooms on Concourse Level 2: one near Section 204 and another near Section 228.', timestamp: '07:32 AM' }
      ]
    }
  ]);
  const [activeSessionId, setActiveSessionId] = useState('session-1');

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const chatHistory = activeSession.history;
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const chatEndRef = useRef(null);

  // Responsive Drawer States for Mobile/Tablet
  const [showLeftSidebar, setShowLeftSidebar] = useState(false);
  const [sidebarHidden, setSidebarHidden] = useState(false);

  // Context Menu & Rename States
  const [activeMenuSessionId, setActiveMenuSessionId] = useState(null);
  const [renamingSessionId, setRenamingSessionId] = useState(null);
  const [renameInputVal, setRenameInputVal] = useState('');
  
  // Feedback action labels
  const [activeFeedback, setActiveFeedback] = useState(null);
  const [likeStatus, setLikeStatus] = useState(null); // 'liked', 'disliked', or null

  // Reset likes status when loading another session
  useEffect(() => {
    setLikeStatus(null);
  }, [activeSessionId]);

  // Outside click listener to dismiss floating menus
  useEffect(() => {
    const handleGlobalClick = () => {
      setActiveMenuSessionId(null);
    };
    window.addEventListener('click', handleGlobalClick);
    return () => window.removeEventListener('click', handleGlobalClick);
  }, []);


  useEffect(() => {
    if (chatHistory.length > 1) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!queryInput.trim()) return;

    const userText = queryInput;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setQueryInput('');
    
    // Update local session state with user's message
    setSessions(prev => prev.map(s => {
      if (s.id === activeSessionId) {
        const updatedHistory = [...s.history, { sender: 'user', text: userText, timestamp: timeStr }];
        const updatedTitle = s.title === 'New Chat' ? (userText.length > 25 ? userText.substring(0, 22) + '...' : userText) : s.title;
        return { ...s, title: updatedTitle, history: updatedHistory };
      }
      return s;
    }));
    
    setIsLoadingChat(true);

    try {
      const reply = await queryAssistantAPI(userText, fanLang, offlineMode);
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, history: [...s.history, { sender: 'bot', text: reply, timestamp: timeStr }] };
        }
        return s;
      }));
    } catch {
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, history: [...s.history, { sender: 'bot', text: 'Offline backup: Proceed to Concourse West to access main restrooms.', timestamp: timeStr }] };
        }
        return s;
      }));
    } finally {
      setIsLoadingChat(false);
    }
  };

  // Structured response parsers
  const parseRouteText = (text) => {
    if (!text.includes("route from") || !text.includes("transit:")) {
      return null;
    }
    try {
      const cleanText = text.replace("[Offline Safe Mode] ", "");
      const startMatch = cleanText.match(/from (.*?) to/);
      const endMatch = cleanText.match(/to (.*?):/);
      const routeMatch = cleanText.match(/:\s*(.*?)\.\s*(?:Estimated|transit)/i);
      const timeMatch = cleanText.match(/(?:Estimated transit:|transit:)\s*(.*?)\./i);
      const accessMatch = cleanText.match(/(?:Accessibility features:|features:)\s*(.*?)\./i);

      return {
        start: startMatch ? startMatch[1].trim() : "Start Point",
        end: endMatch ? endMatch[1].trim() : "Destination",
        route: routeMatch ? routeMatch[1].trim() : "Direct Concourse Path",
        time: timeMatch ? timeMatch[1].trim() : "5 Minutes",
        access: accessMatch ? accessMatch[1].trim() : "Standard Access"
      };
    } catch (e) {
      return null;
    }
  };

  const parseCoordinatesText = (text) => {
    if (!text.includes("coordinates:") || !text.includes("LatLng")) {
      return null;
    }
    try {
      const cleanText = text.replace("[Offline Safe Mode] ", "");
      const gateMatch = cleanText.match(/^(.*?)\s+verified/);
      const coordsMatch = cleanText.match(/LatLng\s*(.*?)\./);
      const featuresMatch = cleanText.match(/(?:features:|equipment:)\s*(.*?)\./);

      return {
        gate: gateMatch ? gateMatch[1].trim() : "Gate Zone",
        coords: coordsMatch ? coordsMatch[1].trim() : "Verified",
        features: featuresMatch ? featuresMatch[1].trim() : "Standard Equipment"
      };
    } catch (e) {
      return null;
    }
  };

  const renderFormattedBotMessage = (text) => {
    const routeObj = parseRouteText(text);
    if (routeObj) {
      const isWheelchair = routeObj.access.toLowerCase().includes("ramp") || routeObj.access.toLowerCase().includes("elevator");
      return (
        <div>
          <p>Here is the verified wayfinding route generated by the Ops database:</p>
          <div className={styles.structuredCard}>
            <div className={styles.cardTitle}>🧭 Route Navigation Overview</div>
            
            <div className={styles.metricsGrid}>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Start Point</span>
                <span className={styles.metricVal} style={{fontSize: '0.95rem'}}>{routeObj.start}</span>
              </div>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Destination</span>
                <span className={styles.metricVal} style={{fontSize: '0.95rem'}}>{routeObj.end}</span>
              </div>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Est. Time</span>
                <span className={styles.metricVal} style={{color: 'var(--color-secondary)'}}>{routeObj.time}</span>
              </div>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Access Mode</span>
                <span className={styles.metricVal} style={{color: isWheelchair ? 'var(--color-primary)' : 'var(--color-warning)', fontSize: '0.85rem'}}>
                  {isWheelchair ? '♿ ACCESSIBLE' : '⚠️ STANDARD'}
                </span>
              </div>
            </div>

            <div className={styles.featuresSection}>
              <span className={styles.sectionTitle}>Routing Guideline</span>
              <ul className={styles.featuresList}>
                <li>{routeObj.route}</li>
              </ul>
            </div>

            <div className={styles.featuresSection}>
              <span className={styles.sectionTitle}>Equipment & Landmarks Enroute</span>
              <ul className={styles.featuresList}>
                {routeObj.access.split(',').map((feat, i) => (
                  <li key={i}>{feat.trim()}</li>
                ))}
              </ul>
            </div>

            <span className={styles.sectionTitle}>Route Comparisons</span>
            <table className={styles.comparisonTable}>
              <thead>
                <tr>
                  <th>Option</th>
                  <th>Transit Time</th>
                  <th>Accessibility</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Primary {routeObj.start} to {routeObj.end}</td>
                  <td>{routeObj.time}</td>
                  <td>{isWheelchair ? 'Full Ramps' : 'Standard'}</td>
                </tr>
                <tr>
                  <td>Alternative Outer Ring</td>
                  <td>+4 mins</td>
                  <td>Full Elevator Access</td>
                </tr>
              </tbody>
            </table>

            <div className={styles.sourcesRow}>
              <span className={styles.sourcesTitle}>Sources:</span>
              <span className={styles.sourcePill}>Stadium Database</span>
              <span className={styles.sourcePill}>GIS Coordinates</span>
              <span className={styles.sourcePill}>WCAG AA Checklist</span>
            </div>
          </div>
        </div>
      );
    }

    const coordsObj = parseCoordinatesText(text);
    if (coordsObj) {
      return (
        <div>
          <p>Here are the verified zone coordinates fetched from the SQLite database:</p>
          <div className={styles.structuredCard}>
            <div className={styles.cardTitle}>📡 Stadium Node Diagnostic</div>
            
            <div className={styles.metricsGrid}>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Gate Zone</span>
                <span className={styles.metricVal} style={{fontSize: '0.95rem'}}>{coordsObj.gate}</span>
              </div>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Coordinates</span>
                <span className={styles.metricVal} style={{color: 'var(--color-secondary)', fontSize: '0.85rem'}}>{coordsObj.coords}</span>
              </div>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>Sync Status</span>
                <span className={styles.metricVal} style={{color: 'var(--color-primary)', fontSize: '0.85rem'}}>✓ ANCHORED</span>
              </div>
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>SOP Protocol</span>
                <span className={styles.metricVal} style={{fontSize: '0.85rem'}}>FIFA-2026</span>
              </div>
            </div>

            <div className={styles.featuresSection}>
              <span className={styles.sectionTitle}>Nearby Accessibility Landmarks</span>
              <ul className={styles.featuresList}>
                {coordsObj.features.split(',').map((feat, i) => (
                  <li key={i}>{feat.trim()}</li>
                ))}
              </ul>
            </div>

            <div className={styles.sourcesRow}>
              <span className={styles.sourcesTitle}>Sources:</span>
              <span className={styles.sourcePill}>SQLite database</span>
              <span className={styles.sourcePill}>Gate Topology</span>
            </div>
          </div>
        </div>
      );
    }

    return <p>{text}</p>;
  };

  const handleResetChat = () => {
    const newId = `session-${Date.now()}`;
    const newSess = {
      id: newId,
      title: 'New Chat',
      age: 'Just now',
      history: [
        { sender: 'bot', text: 'Welcome to the FIFA World Cup 2026 Operations Assistant. How can I help you navigate the stadium today?', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
      ]
    };
    setSessions(prev => [newSess, ...prev]);
    setActiveSessionId(newId);
  };

  const handleDeleteSession = (id) => {
    const remaining = sessions.filter(s => s.id !== id);
    if (remaining.length === 0) {
      const fallbackId = `session-${Date.now()}`;
      const fallbackSess = {
        id: fallbackId,
        title: 'New Chat',
        age: 'Just now',
        history: [
          { sender: 'bot', text: 'Welcome to the FIFA World Cup 2026 Operations Assistant. How can I help you navigate the stadium today?', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
        ]
      };
      setSessions([fallbackSess]);
      setActiveSessionId(fallbackId);
    } else {
      setSessions(remaining);
      if (activeSessionId === id) {
        setActiveSessionId(remaining[0].id);
      }
    }
  };

  const handleRenameSession = (id, newVal) => {
    if (newVal.trim()) {
      setSessions(prev => prev.map(s => {
        if (s.id === id) {
          return { ...s, title: newVal.trim() };
        }
        return s;
      }));
    }
    setRenamingSessionId(null);
  };

  return (
    <div className={`${styles.dashboardContainer} ${sidebarHidden ? styles.sidebarHiddenLayout : ''}`}>
      
      {/* Drawer Overlay for Mobile viewports */}
      {showLeftSidebar && (
        <div 
          className={styles.sidebarOverlay} 
          onClick={() => setShowLeftSidebar(false)}
        />
      )}

      {/* LEFT SIDEBAR: Brand, Actions & Account info */}
      <aside className={`${styles.sidebarLeft} ${showLeftSidebar ? styles.active : ''} ${sidebarHidden ? styles.hiddenSidebar : ''}`}>
        <div className={styles.brandRow} style={{marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '0.8rem'}}>
            <div className={styles.brandIcon}>F</div>
            <span className={styles.brandName}>FIFA-Copilot</span>
          </div>
          <button 
            className={styles.desktopToggleBtn} 
            onClick={() => setSidebarHidden(true)} 
            title="Hide sidebar"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: '0.4rem',
              fontSize: '1.2rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '0.4rem',
              transition: 'var(--transition-smooth)'
            }}
          >
            ◀
          </button>
        </div>

        <button className={styles.newSessionBtn} onClick={handleResetChat} style={{marginBottom: '1.5rem'}}>
          <span>New Session</span>
        </button>

        <div className={styles.sectionHeading} style={{marginBottom: '0.8rem'}}>Recent Chats</div>
        <div className={styles.recentChatsList} style={{flex: 1, overflowY: 'auto'}}>
          {sessions.map(sess => (
            <div 
              key={sess.id} 
              className={`${styles.recentChatItem} ${sess.id === activeSessionId ? styles.activeRecentChat : ''}`}
              onClick={() => {
                if (renamingSessionId !== sess.id) {
                  setActiveSessionId(sess.id);
                  setShowLeftSidebar(false); // Auto close drawer on mobile when clicking
                }
              }}
              style={{
                background: sess.id === activeSessionId ? 'rgba(0, 229, 255, 0.08)' : 'transparent',
                borderLeft: sess.id === activeSessionId ? '0.2rem solid var(--color-secondary)' : '0.2rem solid transparent',
                paddingLeft: sess.id === activeSessionId ? '0.65rem' : '0.85rem',
                cursor: renamingSessionId === sess.id ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.5rem'
              }}
            >
              <div style={{display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0}}>
                {renamingSessionId === sess.id ? (
                  <input 
                    type="text"
                    value={renameInputVal}
                    onChange={(e) => setRenameInputVal(e.target.value)}
                    onBlur={() => handleRenameSession(sess.id, renameInputVal)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleRenameSession(sess.id, renameInputVal);
                      } else if (e.key === 'Escape') {
                        setRenamingSessionId(null);
                      }
                    }}
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      background: 'rgba(0,0,0,0.5)',
                      border: '0.1rem solid var(--color-secondary)',
                      color: '#fff',
                      fontSize: '1.0rem',
                      padding: '0.2rem 0.4rem',
                      borderRadius: '0.3rem',
                      width: '100%',
                      outline: 'none'
                    }}
                  />
                ) : (
                  <>
                    <span className={styles.chatTitle}>{sess.title}</span>
                    <span className={styles.chatAge}>{sess.age}</span>
                  </>
                )}
              </div>
              
              {renamingSessionId !== sess.id && (
                <button 
                  className={styles.moreOptionsBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMenuSessionId(activeMenuSessionId === sess.id ? null : sess.id);
                  }}
                  title="More options"
                >
                  •••
                </button>
              )}

              {/* Floating Context Menu */}
              {activeMenuSessionId === sess.id && (
                <div 
                  className={styles.contextMenu}
                  onClick={(e) => e.stopPropagation()}
                >
                  <button 
                    className={styles.contextMenuItem}
                    onClick={() => {
                      setRenamingSessionId(sess.id);
                      setRenameInputVal(sess.title);
                      setActiveMenuSessionId(null);
                    }}
                  >
                    Rename
                  </button>
                  <button 
                    className={`${styles.contextMenuItem} ${styles.contextMenuItemDelete}`}
                    onClick={() => {
                      handleDeleteSession(sess.id);
                      setActiveMenuSessionId(null);
                    }}
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* User Account Row */}
        <div className={styles.profileRow} style={{borderTop: '0.1rem solid var(--glass-border)', borderBottom: 'none', paddingTop: '1.0rem', paddingBottom: 0, marginTop: '1.5rem', marginBottom: 0}}>
          <div className={styles.profileAvatar}>KM</div>
          <div className={styles.profileDetails}>
            <span className={styles.profileName}>Operations Lead</span>
            <span className={styles.profileEmail}>stadium.ops@fifa.com</span>
          </div>
        </div>
      </aside>

      {/* CENTER PANEL: Chat Workspace */}
      <section className={styles.centerPanel}>
        
        {/* Chat window Header */}
        <div className={styles.chatHeader}>
          <div className={styles.chatHeaderLeft} style={{flexDirection: 'row', alignItems: 'center', gap: '0.75rem'}}>
             <button className={styles.drawerToggleBtn} onClick={() => setShowLeftSidebar(!showLeftSidebar)} title="Open side menu">
              ☰
            </button>
            {sidebarHidden && (
              <button 
                className={styles.desktopToggleBtn}
                onClick={() => setSidebarHidden(false)} 
                title="Show sidebar"
                style={{
                  background: 'transparent',
                  border: '0.1rem solid var(--glass-border)',
                  color: 'var(--color-text-muted)',
                  padding: '0.4rem 0.65rem',
                  borderRadius: '0.4rem',
                  cursor: 'pointer',
                  fontSize: '1.0rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: '0.5rem',
                  transition: 'var(--transition-smooth)'
                }}
              >
                ▶
              </button>
            )}
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span className={styles.chatHeaderTitle}>Stadium Wayfinding & Operations</span>
            </div>
          </div>
          <div className={styles.chatHeaderRight} style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
            <select 
              id="lang-select" 
              className="select-input" 
              value={fanLang}
              onChange={handleSelectChange(setFanLang)}
              onMouseDown={handleSelectMouseDown}
              style={{
                padding: '0.35rem 2rem 0.35rem 0.65rem', 
                fontSize: '1.0rem', 
                borderRadius: '0.4rem', 
                width: 'auto', 
                minWidth: '12.0rem', 
                backgroundColor: 'rgba(0,0,0,0.3)', 
                borderColor: 'rgba(255,255,255,0.08)', 
                backgroundPosition: 'right 0.6rem center', 
                backgroundSize: '1.0rem', 
                margin: 0
              }}
              aria-label="Assistant accent language select"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="ar">العربية</option>
              <option value="pt">Português</option>
            </select>
          </div>
        </div>

        {/* Chat Messages */}
        <div className={styles.chatMessages}>
          {chatHistory.map((ch, idx) => (
            <div key={idx} className={`${styles.msgRow} ${ch.sender === 'user' ? styles.userRow : ''}`}>
              <div className={`${styles.msgContentBlock} ${ch.sender === 'user' ? styles.userBlock : ''}`}>
                <div className={`${styles.chatBubble} ${ch.sender === 'user' ? styles.user : styles.bot}`}>
                  {ch.sender === 'user' ? <p>{ch.text}</p> : renderFormattedBotMessage(ch.text)}
                </div>
                {ch.sender === 'bot' && idx === chatHistory.length - 1 && (
                  <div className={styles.bubbleActions} style={{display: 'flex', alignItems: 'center', gap: '1.0rem', marginTop: '0.75rem', paddingBottom: '1.25rem'}}>
                    
                    <div style={{position: 'relative', display: 'inline-flex', flexDirection: 'column', alignItems: 'center'}}>
                      <button 
                        className={styles.actionBtn} 
                        title="Copy response" 
                        onClick={() => {
                          navigator.clipboard.writeText(ch.text);
                          setActiveFeedback('copied');
                          setTimeout(() => setActiveFeedback(null), 1500);
                        }} 
                        style={{display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.25rem'}}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                        </svg>
                      </button>
                      {activeFeedback === 'copied' && (
                        <span style={{
                          position: 'absolute',
                          top: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          fontSize: '0.65rem',
                          color: 'var(--color-secondary)',
                          whiteSpace: 'nowrap',
                          marginTop: '0.2rem',
                          fontWeight: '600'
                        }}>Copied!</span>
                      )}
                    </div>

                    <div style={{position: 'relative', display: 'inline-flex', flexDirection: 'column', alignItems: 'center'}}>
                      <button 
                        className={styles.actionBtn} 
                        title="Good response" 
                        onClick={() => {
                          const newVal = likeStatus === 'liked' ? null : 'liked';
                          setLikeStatus(newVal);
                          setActiveFeedback(newVal);
                          if (newVal) {
                            setTimeout(() => setActiveFeedback(null), 1500);
                          }
                        }}
                        style={{display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.25rem'}}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={likeStatus === 'liked' ? 'var(--color-primary)' : 'none'} stroke={likeStatus === 'liked' ? 'var(--color-primary)' : 'currentColor'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                        </svg>
                      </button>
                      {activeFeedback === 'liked' && (
                        <span style={{
                          position: 'absolute',
                          top: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          fontSize: '0.65rem',
                          color: 'var(--color-primary)',
                          whiteSpace: 'nowrap',
                          marginTop: '0.2rem',
                          fontWeight: '600'
                        }}>Liked!</span>
                      )}
                    </div>

                    <div style={{position: 'relative', display: 'inline-flex', flexDirection: 'column', alignItems: 'center'}}>
                      <button 
                        className={styles.actionBtn} 
                        title="Bad response" 
                        onClick={() => {
                          const newVal = likeStatus === 'disliked' ? null : 'disliked';
                          setLikeStatus(newVal);
                          setActiveFeedback(newVal);
                          if (newVal) {
                            setTimeout(() => setActiveFeedback(null), 1500);
                          }
                        }}
                        style={{display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.25rem'}}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={likeStatus === 'disliked' ? 'var(--color-danger)' : 'none'} stroke={likeStatus === 'disliked' ? 'var(--color-danger)' : 'currentColor'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transform: 'rotate(180deg)' }}>
                          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                        </svg>
                      </button>
                      {activeFeedback === 'disliked' && (
                        <span style={{
                          position: 'absolute',
                          top: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          fontSize: '0.65rem',
                          color: 'var(--color-danger)',
                          whiteSpace: 'nowrap',
                          marginTop: '0.2rem',
                          fontWeight: '600'
                        }}>Disliked!</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoadingChat && (
            <div className={styles.msgRow}>
              <div className={styles.msgContentBlock}>
                <div className={`${styles.chatBubble} ${styles.bot}`}>
                  <span className="loading-dots">FIFA-Copilot is formulating verified route...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Chat Input Bar */}
        <div className={styles.inputAreaContainer}>
          <form onSubmit={handleSendChat}>
            <div className={styles.premiumInputBox}>
              <input 
                type="text" 
                className={styles.chatTextarea} 
                placeholder="Ask anything..."
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                aria-label="Ask assistant query"
              />
              <button type="submit" className={styles.sendCircularBtn} title="Send message">➔</button>
            </div>
            <div className={styles.disclaimerText}>
              FIFA-Copilot can make mistakes. Verify critical coordinates & safety alerts.
            </div>
          </form>
        </div>

      </section>

    </div>
  );
}
