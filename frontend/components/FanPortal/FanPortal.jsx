"use client";

import React, { useState, useEffect } from 'react';
import { fetchSustainabilityNudge, fetchLiveMatch, fetchMatchFixtures } from '../../lib/api';
import styles from './FanPortal.module.css';

export default function FanPortal({ offlineMode, transitStatuses, incidentsList, handleSelectMouseDown, handleSelectChange }) {
  const [nudgeGate, setNudgeGate] = useState('Gate A');
  const [sustainabilityNudge, setSustainabilityNudge] = useState('Loading green suggestions for Gate A...');
  const [matchData, setMatchData] = useState(null);
  const [fixturesList, setFixturesList] = useState([]);

  // Dynamic API fetching & live telemetry ticker for match data & fixtures
  useEffect(() => {
    async function loadMatchInfo() {
      const live = await fetchLiveMatch(offlineMode);
      setMatchData(live);
      const fixtures = await fetchMatchFixtures(offlineMode);
      setFixturesList(fixtures);
    }
    loadMatchInfo();
    const timer = setInterval(loadMatchInfo, 5000);
    return () => clearInterval(timer);
  }, [offlineMode]);


  // Fetch sustainability nudge when gate changes
  useEffect(() => {
    async function loadNudge() {
      const nudge = await fetchSustainabilityNudge(nudgeGate, 'en', offlineMode);
      setSustainabilityNudge(nudge);
    }
    loadNudge();
  }, [nudgeGate, offlineMode]);

  return (
    <div id="fan-panel" className="dashboard-grid" role="tabpanel" aria-labelledby="fan-tab">
      {/* ── Main Left Column (Match Center Live + Upcoming Schedule) ───────── */}
      <section className="glass-panel col-8 highlight-secondary" aria-label="Live Match Center">
        <div className="panel-title">
          <span>🏆 Match Center Live</span>
          <span className="status-pill high" style={{background: 'rgba(0, 229, 255, 0.08)', color: 'var(--color-secondary)'}}>
            {matchData?.match_minute || "Live 76'"}
          </span>
        </div>

        {/* Dynamic Score Display Card */}
        <div style={{
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          background: 'rgba(0,0,0,0.3)', 
          padding: '2rem 1.5rem', 
          borderRadius: '12px',
          border: '1px solid var(--glass-border)',
          marginBottom: '1.75rem',
          textAlign: 'center'
        }}>
          <div style={{flex: 1}}>
            <div style={{fontSize: '2.5rem'}}>{matchData?.home_flag || "🇨🇦"}</div>
            <div style={{fontWeight: 800, fontSize: '1.25rem', marginTop: '0.5rem', color: '#fff'}}>{matchData?.home_team || "CANADA"}</div>
          </div>
          <div style={{flex: 1}}>
            <div style={{fontSize: '2.5rem', fontWeight: 800, color: 'var(--color-secondary)', letterSpacing: '0.2em'}}>
              {matchData ? `${matchData.home_score} - ${matchData.away_score}` : "2 - 1"}
            </div>
            <div style={{fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.5rem'}}>{matchData?.match_minute || "76th Minute"}</div>
          </div>
          <div style={{flex: 1}}>
            <div style={{fontSize: '2.5rem'}}>{matchData?.away_flag || "🇺🇸"}</div>
            <div style={{fontWeight: 800, fontSize: '1.25rem', marginTop: '0.5rem', color: '#fff'}}>{matchData?.away_team || "USA"}</div>
          </div>
        </div>

        {/* Dynamic Live Match Stats */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem', background: 'rgba(255,255,255,0.01)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--glass-border)'}}>
          <h3 style={{fontSize: '0.9rem', fontWeight: 700, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em'}}>Match Stats</h3>
          
          {/* Ball Possession — dynamic from live matchData */}
          <div>
            <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem'}}>
              <span>{matchData?.possession_home ?? 52}%</span>
              <span style={{color: 'var(--color-text-muted)'}}>Ball Possession</span>
              <span>{matchData?.possession_away ?? 48}%</span>
            </div>
            <div
              role="progressbar"
              aria-label="Ball possession"
              aria-valuenow={matchData?.possession_home ?? 52}
              aria-valuemin={0}
              aria-valuemax={100}
              style={{height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', display: 'flex', overflow: 'hidden'}}
            >
              <div style={{width: `${matchData?.possession_home ?? 52}%`, background: 'var(--color-secondary)'}} />
              <div style={{width: `${matchData?.possession_away ?? 48}%`, background: 'rgba(255,255,255,0.1)'}} />
            </div>
          </div>

          {/* Shots on Goal — dynamic widths computed from live data */}
          <div>
            {(() => {
              const sh = matchData?.shots_home ?? 12;
              const sa = matchData?.shots_away ?? 9;
              const total = sh + sa || 1;
              const homePct = Math.round((sh / total) * 100);
              const awayPct = 100 - homePct;
              return (
                <>
                  <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem'}}>
                    <span>{sh}</span>
                    <span style={{color: 'var(--color-text-muted)'}}>Shots on Goal</span>
                    <span>{sa}</span>
                  </div>
                  <div
                    role="progressbar"
                    aria-label={`Shots on goal: ${sh} home vs ${sa} away`}
                    aria-valuenow={homePct}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    style={{height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', display: 'flex', overflow: 'hidden'}}
                  >
                    <div style={{width: `${homePct}%`, background: 'var(--color-secondary)'}} />
                    <div style={{width: `${awayPct}%`, background: 'rgba(255,255,255,0.1)'}} />
                  </div>
                </>
              );
            })()}
          </div>

          {/* Pass Accuracy — dynamic widths computed from live data */}
          <div>
            {(() => {
              const ph = matchData?.pass_accuracy_home ?? 85;
              const pa = matchData?.pass_accuracy_away ?? 81;
              const total = ph + pa || 1;
              const homePct = Math.round((ph / total) * 100);
              const awayPct = 100 - homePct;
              return (
                <>
                  <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem'}}>
                    <span>{ph}%</span>
                    <span style={{color: 'var(--color-text-muted)'}}>Pass Accuracy</span>
                    <span>{pa}%</span>
                  </div>
                  <div
                    role="progressbar"
                    aria-label={`Pass accuracy: ${ph}% home vs ${pa}% away`}
                    aria-valuenow={homePct}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    style={{height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', display: 'flex', overflow: 'hidden'}}
                  >
                    <div style={{width: `${homePct}%`, background: 'var(--color-secondary)'}} />
                    <div style={{width: `${awayPct}%`, background: 'rgba(255,255,255,0.1)'}} />
                  </div>
                </>
              );
            })()}
          </div>
        </div>

        {/* Stadium Occupancy Diagnostic */}
        <div style={{marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
          <div style={{flex: 1, minWidth: '180px', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--glass-border)'}}>
            <div style={{fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase'}}>Attendance</div>
            <div style={{fontSize: '1.25rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem'}}>{matchData?.attendance || "68,243"}</div>
          </div>
          <div style={{flex: 1, minWidth: '180px', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--glass-border)'}}>
            <div style={{fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase'}}>Stadium Capacity</div>
            <div style={{fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-primary)', marginTop: '0.25rem'}}>
              {matchData?.stadium_capacity_pct ?? 92.4}% Occupied
            </div>
          </div>
        </div>

        {/* Dynamic Match Fixtures List */}
        <div style={{marginTop: '1.75rem'}}>
          <h2 className="panel-title">📅 Upcoming Matches (Stadium Schedule)</h2>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem'}}>
            {fixturesList.map((fix) => (
              <div key={fix.id} className="list-item" style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem'}}>
                <span className="status-pill draft" style={{fontSize: '0.65rem'}}>{fix.date_label}</span>
                <div style={{fontWeight: 700, fontSize: '1.05rem', color: '#fff'}}>{fix.teams}</div>
                <div className="list-item-meta">{fix.stage}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Right Column (Sustainability + Transit + Safety Broadcast Channel) ── */}
      <div className="col-4" style={{display: 'flex', flexDirection: 'column', gap: '1.75rem'}}>
        {/* Sustainability Nudge Card */}
        <section className="glass-panel highlight-primary" aria-label="Stadium Green Initiative">
          <h2 className="panel-title">🌱 Sustainability Nudges</h2>
          <div className="form-group">
            <label htmlFor="nudge-gate-select" className="form-label">Inspect Near Gate:</label>
            <select 
              id="nudge-gate-select" 
              className="select-input"
              value={nudgeGate}
              onChange={handleSelectChange(setNudgeGate)}
              onMouseDown={handleSelectMouseDown}
            >
              <option value="Gate A">Gate A</option>
              <option value="Gate B">Gate B</option>
              <option value="Gate C">Gate C</option>
              <option value="Transit Plaza">Transit Plaza</option>
              <option value="Concourse West">Concourse West</option>
            </select>
          </div>
          <div className={styles.nudgeHighlight}>
            {sustainabilityNudge}
          </div>
        </section>

        {/* Transit Alerts */}
        <section className="glass-panel highlight-warning" aria-label="Transit Delay Advisories">
          <h2 className="panel-title">🚌 Live Transit Connections</h2>
          <div className="scrollable-y">
            {transitStatuses.length === 0 ? (
              <p style={{color: 'var(--color-text-muted)', fontSize: '0.9rem'}}>No delays reported on transit lanes.</p>
            ) : (
              transitStatuses.map((t) => (
                <div key={t.route} className="list-item">
                  <div>
                    <div style={{fontWeight: 600}}>{t.route}</div>
                    <div className="list-item-meta">Delay: <strong>{t.delay_minutes}</strong> min</div>
                  </div>
                  <span className={`status-pill ${t.status}`} aria-label={`Status: ${t.status}`}>{t.status}</span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* 📢 ACTIVE SAFETY BROADCAST CHANNEL (Repositioned to Right Column below Live Transit) */}
        <section className={styles.dangerContainer} aria-label="Emergency Alerts Channel">
          <div className={styles.dangerHeader}>
            <h2 style={{fontFamily: 'Outfit', fontSize: '1.15rem', color: 'var(--color-danger)', fontWeight: 800}}>
              📢 ACTIVE SAFETY BROADCAST
            </h2>
            <span className="status-pill high">LIVE TELEMETRY</span>
          </div>
          <div>
            {incidentsList.filter(i => i.status === 'active').length === 0 ? (
              <p style={{color: 'var(--color-text-muted)', fontSize: '0.85rem'}}>No active emergency alerts. Stadium running normally.</p>
            ) : (
              incidentsList.filter(i => i.status === 'active').map((inc) => (
                <div 
                  key={inc.id} 
                  className={styles.incidentCard} 
                  style={{borderLeft: '4px solid var(--color-danger)', background: 'rgba(255,23,68,0.02)'}}
                >
                  <div className={styles.incidentHeader}>
                    <strong className={styles.incidentTitle}>{inc.title} ({inc.gate})</strong>
                    <span className="status-pill high">HIGH ALERT</span>
                  </div>
                  <p className={styles.incidentDesc}>{inc.description}</p>
                  <div className={styles.sopBox}>
                    <div className={styles.sopTitle}>
                      🛡️ Safe Rerouting Instruction:
                    </div>
                    <div className={styles.sopText}>{inc.suggested_action}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
