"use client";

import React, { useState } from 'react';
import { submitSensorUpdate, approveIncidentBroadcast, queryAssistantAPI, submitIncidentReport } from '../../lib/api';
import styles from './OrganizerDashboard.module.css';

export default function OrganizerDashboard({ 
  offlineMode, 
  incidentsList, 
  handleSelectMouseDown, 
  handleSelectChange, 
  fetchIncidentsData, 
  fetchSensorsData 
}) {
  const [sensorGate, setSensorGate] = useState('Gate A');
  const [sensorDensity, setSensorDensity] = useState(50);
  const [sensorAdvisory, setSensorAdvisory] = useState('');
  const [organizerStatusMsg, setOrganizerStatusMsg] = useState('');
  const [editingActionId, setEditingActionId] = useState(null);
  const [editingActionText, setEditingActionText] = useState('');
  const [opsBrief, setOpsBrief] = useState('');
  const [isLoadingBrief, setIsLoadingBrief] = useState(false);

  // Mock Incident Injector state
  const [injectGate, setInjectGate] = useState('Gate A');
  const [injectType, setInjectType] = useState('Scanner Issue');

  const handleInjectIncidentSubmit = async (e) => {
    e.preventDefault();
    
    let title = '';
    let description = '';
    let severity = 'medium';

    if (injectType === 'Scanner Issue') {
      title = 'Scanner Failure';
      description = `RFID Gate Reader 4 at ${injectGate} failed to boot. High backlog forming.`;
      severity = 'high';
    } else if (injectType === 'Queue Congestion') {
      title = 'Crowd Bottleneck';
      description = `Density sensor registers over 90% at ${injectGate} entrance funnel. Flow stagnant.`;
      severity = 'high';
    } else if (injectType === 'Restroom Spill') {
      title = 'Sanitation Required';
      description = `Water spill reported in Section G restrooms near ${injectGate}. Slipping hazard.`;
      severity = 'low';
    } else {
      title = 'First Aid Request';
      description = `Fan reports feeling faint near ${injectGate} medical kiosk. Medic team dispatch requested.`;
      severity = 'medium';
    }

    const payload = {
      title,
      description,
      gate: injectGate,
      severity
    };

    if (offlineMode) {
      setOrganizerStatusMsg('⚠️ Cannot inject incident while offline.');
      return;
    }

    try {
      await submitIncidentReport(payload);
      setOrganizerStatusMsg('✅ Incident simulation injected successfully.');
      fetchIncidentsData();
    } catch {
      setOrganizerStatusMsg('❌ Failed to inject simulation incident.');
    }
  };

  const handleUpdateSensorSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      zone: sensorGate,
      density_percentage: parseInt(sensorDensity),
      advisory: sensorAdvisory
    };

    if (offlineMode) {
      setOrganizerStatusMsg('⚠️ Sensor cached offline locally.');
      return;
    }

    try {
      await submitSensorUpdate(payload);
      setOrganizerStatusMsg('✅ Sensor feedback processed.');
      setSensorAdvisory('');
      fetchSensorsData();
    } catch {
      setOrganizerStatusMsg('❌ Failed to update sensors.');
    }
  };

  const handleApproveIncidentClick = async (id, customAction) => {
    if (offlineMode) {
      setOrganizerStatusMsg('⚠️ Cannot approve incident while offline.');
      return;
    }
    try {
      await approveIncidentBroadcast(id, customAction);
      setOrganizerStatusMsg('✅ Broadcast approved! Active alert pushed to fans.');
      setEditingActionId(null);
      fetchIncidentsData();
    } catch {
      setOrganizerStatusMsg('❌ Broadcast action failed.');
    }
  };

  const generateOpsBriefText = async () => {
    setIsLoadingBrief(true);
    try {
      const brief = await queryAssistantAPI(
        "Provide a formal 3-sentence operational brief summarizing overall stadium flow, security events, and transit bottlenecks for senior coordinators.",
        "en",
        offlineMode
      );
      setOpsBrief(brief);
    } catch {
      setOpsBrief("Ops Brief: System offline. Static sensors list indicates normal stadium flows.");
    } finally {
      setIsLoadingBrief(false);
    }
  };

  return (
    <div 
      id="organizer-panel" 
      className="dashboard-grid" 
      role="tabpanel" 
      aria-labelledby="organizer-tab"
      style={{
        height: '100%', 
        overflow: 'hidden', 
        padding: '1.5rem 2.0rem', 
        boxSizing: 'border-box'
      }}
    >
      {/* Incident Controller (Human-in-the-loop AI review) */}
      <section className="glass-panel col-8 highlight-danger" style={{height: '100%', display: 'flex', flexDirection: 'column'}} aria-label="Incident Operations Center">
        <h2 className="panel-title">AI Incident Copilot (SOP Validation)</h2>
        {organizerStatusMsg && (
          <p style={{background: 'rgba(255,255,255,0.05)', padding: '0.8rem 1.1rem', borderRadius: '8px', fontSize: '0.9rem', marginBottom: '1.25rem'}}>
            {organizerStatusMsg}
          </p>
        )}
        
        <div className="scrollable-y" style={{flex: 1, minHeight: 0}}>
          {incidentsList.length === 0 ? (
            <p style={{color: 'var(--color-text-muted)'}}>No logged incidents or reports.</p>
          ) : (
            incidentsList.map((inc) => (
              <div key={inc.id} className={`${styles.incidentCard} ${inc.status === 'draft' ? styles.draft : ''}`}>
                <div className="incident-header">
                  <div>
                    <span className={styles.incidentTitle}>{inc.title}</span>
                    <span style={{marginLeft: '0.75rem'}} className="status-pill low">{inc.gate}</span>
                    <span style={{marginLeft: '0.5rem'}} className={`status-pill ${inc.severity}`}>{inc.severity} severity</span>
                  </div>
                  <span className={`status-pill ${inc.status}`}>{inc.status}</span>
                </div>
                
                <p className={styles.incidentDesc}>{inc.description}</p>
                
                {/* Show AI suggested Action */}
                <div className={styles.sopBox}>
                  <div className={styles.sopTitle}>
                    AI Suggested SOP Action Plan:
                  </div>
                  
                  {editingActionId === inc.id ? (
                    <div>
                      <textarea 
                        className="text-input" 
                        rows="3" 
                        value={editingActionText}
                        onChange={(e) => setEditingActionText(e.target.value)}
                        style={{resize: 'none', marginBottom: '0.75rem'}}
                      />
                      <div className={styles.sopActions}>
                        <button 
                          className="cta-button" 
                          style={{padding: '0.5rem 1rem', fontSize: '0.85rem'}}
                          onClick={() => handleApproveIncidentClick(inc.id, editingActionText)}
                        >
                          Save & Broadcast
                        </button>
                        <button 
                          className="cta-button" 
                          style={{background: 'rgba(255,255,255,0.1)', color: '#fff', padding: '0.5rem 1rem', fontSize: '0.85rem'}}
                          onClick={() => setEditingActionId(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className={styles.sopText}>{inc.suggested_action}</div>
                      {inc.status === 'draft' && (
                        <div className={styles.sopActions}>
                          <button 
                            className="cta-button" 
                            style={{padding: '0.5rem 1rem', fontSize: '0.85rem'}}
                            onClick={() => handleApproveIncidentClick(inc.id, inc.suggested_action)}
                          >
                            Approve As Is
                          </button>
                          <button 
                            className="cta-button" 
                            style={{background: 'rgba(255,255,255,0.08)', color: '#fff', padding: '0.5rem 1rem', fontSize: '0.85rem'}}
                            onClick={() => {
                              setEditingActionId(inc.id);
                              setEditingActionText(inc.suggested_action);
                            }}
                          >
                            Modify SOP Plan
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Operations Control and Aggregation */}
      <div className="col-4" style={{display: 'flex', flexDirection: 'column', gap: '1.0rem', height: '100%', overflowY: 'auto', scrollbarWidth: 'none', msOverflowStyle: 'none'}}>
        {/* Sensor mock controller */}
        <section className="glass-panel highlight-primary" aria-label="Mock Sensor Input Controller">
          <h2 className="panel-title">Simulate Crowd Sensor</h2>
          <form onSubmit={handleUpdateSensorSubmit}>
            <div className="form-group">
              <label htmlFor="sensor-gate-select" className="form-label">Select Zone</label>
              <select 
                id="sensor-gate-select" 
                className="select-input"
                value={sensorGate}
                onChange={handleSelectChange(setSensorGate)}
                onMouseDown={handleSelectMouseDown}
              >
                <option value="Gate A">Gate A</option>
                <option value="Gate B">Gate B</option>
                <option value="Gate C">Gate C</option>
                <option value="Transit Plaza">Transit Plaza</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="sensor-density-range" className="form-label">Simulate Density: {sensorDensity}%</label>
              <input 
                type="range" 
                id="sensor-density-range"
                min="0" 
                max="100" 
                value={sensorDensity}
                onChange={(e) => setSensorDensity(e.target.value)}
                className={styles.densitySlider}
                style={{
                  background: `linear-gradient(to right, var(--color-primary) 0%, var(--color-primary) ${sensorDensity}%, #2b3040 ${sensorDensity}%, #2b3040 100%)`
                }}
              />
              {/* Tap-presets for finger-tips organizer ease */}
              <div style={{display: 'flex', gap: '0.4rem', marginTop: '0.6rem'}}>
                {[10, 30, 50, 70, 90, 100].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setSensorDensity(val)}
                    style={{
                      flex: 1,
                      background: parseInt(sensorDensity) === val ? 'rgba(0, 229, 255, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                      border: parseInt(sensorDensity) === val ? '0.1rem solid var(--color-secondary)' : '0.1rem solid var(--glass-border)',
                      color: parseInt(sensorDensity) === val ? 'var(--color-secondary)' : 'var(--color-text-muted)',
                      borderRadius: '0.4rem',
                      padding: '0.35rem 0',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      fontWeight: '700',
                      transition: 'var(--transition-smooth)'
                    }}
                  >
                    {val}%
                  </button>
                ))}
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="sensor-advisory-input" className="form-label">Alert context (Optional)</label>
              <input 
                type="text" 
                id="sensor-advisory-input"
                className="text-input" 
                placeholder="e.g. Scanner slow" 
                value={sensorAdvisory}
                onChange={(e) => setSensorAdvisory(e.target.value)}
              />
            </div>
            <button type="submit" className="cta-button" style={{width: '100%'}}>Push Sensor Update</button>
          </form>
        </section>

        {/* GenAI Operations Summary Brief */}
        <section className="glass-panel highlight-secondary" aria-label="AI Intelligence Brief">
          <h2 className="panel-title">GenAI Executive Ops Brief</h2>
          <button 
            className="cta-button" 
            onClick={generateOpsBriefText} 
            disabled={isLoadingBrief}
            style={{width: '100%'}}
          >
            {isLoadingBrief ? 'Generating Brief...' : 'Generate Operational Brief'}
          </button>
          {opsBrief && (
            <p style={{marginTop: '1rem', fontSize: '0.9rem', color: '#e0e4eb', background: 'rgba(0,229,255,0.05)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid var(--color-secondary)', lineHeight: 1.5}}>
              {opsBrief}
            </p>
          )}
        </section>

        {/* Mock Incident Injector (Ease of access operations simulation) */}
        <section className="glass-panel highlight-danger" aria-label="Mock Incident Injector">
          <h2 className="panel-title">Inject Simulation Incident</h2>
          <form onSubmit={handleInjectIncidentSubmit}>
            <div className="form-group">
              <label htmlFor="inject-gate-select" className="form-label">Select Gate</label>
              <select 
                id="inject-gate-select" 
                className="select-input"
                value={injectGate}
                onChange={handleSelectChange(setInjectGate)}
                onMouseDown={handleSelectMouseDown}
              >
                <option value="Gate A">Gate A</option>
                <option value="Gate B">Gate B</option>
                <option value="Gate C">Gate C</option>
                <option value="Transit Plaza">Transit Plaza</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="inject-type-select" className="form-label">Select Incident Type</label>
              <select 
                id="inject-type-select" 
                className="select-input"
                value={injectType}
                onChange={handleSelectChange(setInjectType)}
                onMouseDown={handleSelectMouseDown}
              >
                <option value="Scanner Issue">Scanner Failure</option>
                <option value="Queue Congestion">Crowd Bottleneck</option>
                <option value="Restroom Spill">Sanitation Required</option>
                <option value="First Aid Needed">First Aid Request</option>
              </select>
            </div>
            <button type="submit" className="cta-button" style={{width: '100%', marginTop: '0.5rem'}}>Inject Incident</button>
          </form>
        </section>
      </div>
    </div>
  );
}
