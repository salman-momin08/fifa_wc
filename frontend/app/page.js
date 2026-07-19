"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from '../components/Header/Header';
import A11yFooter from '../components/A11yFooter/A11yFooter';
import FanPortal from '../components/FanPortal/FanPortal';
import AIAssistant from '../components/AIAssistant/AIAssistant';
import VolunteerConsole from '../components/VolunteerConsole/VolunteerConsole';
import OrganizerDashboard from '../components/OrganizerDashboard/OrganizerDashboard';
import { fetchTransitStatus, fetchSensorsStatus, fetchIncidents } from '../lib/api';
import { useWebSocket } from '../lib/useWebSocket';

export default function Home() {
  const [activeRole, setActiveRole] = useState('fan'); // fan, assistant, volunteer, organizer
  const [offlineMode, setOfflineMode] = useState(false);
  const [a11yHighContrast, setA11yHighContrast] = useState(false);

  // Live announcement for screen readers (ARIA live region)
  const [liveAnnouncement, setLiveAnnouncement] = useState('');
  const announcementTimer = useRef(null);

  const announce = useCallback((msg) => {
    setLiveAnnouncement(msg);
    clearTimeout(announcementTimer.current);
    announcementTimer.current = setTimeout(() => setLiveAnnouncement(''), 6000);
  }, []);

  // Restore saved role from localStorage on mount
  useEffect(() => {
    const savedRole = localStorage.getItem('activeRole');
    if (savedRole) setActiveRole(savedRole);
  }, []);

  useEffect(() => {
    localStorage.setItem('activeRole', activeRole);
  }, [activeRole]);

  // Shared States
  const [transitStatuses, setTransitStatuses] = useState([]);
  const [sensorsList, setSensorsList] = useState([]);
  const [incidentsList, setIncidentsList] = useState([]);

  const loadAllData = useCallback(async () => {
    const [transit, sensors, incidents] = await Promise.all([
      fetchTransitStatus(offlineMode),
      fetchSensorsStatus(offlineMode),
      fetchIncidents(offlineMode),
    ]);
    setTransitStatuses(transit);
    setSensorsList(sensors);
    setIncidentsList(incidents);
  }, [offlineMode]);

  // Initial data load — no polling; live updates come via WebSocket
  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // ── WebSocket handler — receives server-pushed updates ──────────────────────
  const handleWsMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'crowd_update':
        setSensorsList((prev) => {
          const next = [...prev];
          const idx = next.findIndex((s) => s.zone === msg.zone);
          if (idx >= 0) {
            next[idx] = { ...next[idx], ...msg };
          } else {
            next.push(msg);
          }
          return next;
        });
        announce(`Live update: ${msg.zone} crowd density is now ${msg.density_percentage}%.`);
        break;

      case 'transit_update':
        setTransitStatuses((prev) => {
          const next = [...prev];
          const idx = next.findIndex((t) => t.route === msg.route);
          if (idx >= 0) {
            next[idx] = { route: msg.route, status: msg.status, delay_minutes: msg.delay_minutes };
          } else {
            next.push({ route: msg.route, status: msg.status, delay_minutes: msg.delay_minutes });
          }
          return next;
        });
        if (msg.status !== 'normal') {
          announce(`Transit alert: ${msg.route} is ${msg.status} (${msg.delay_minutes} minute delay).`);
        }
        break;

      case 'incident_approved':
        // Refresh incidents list on new approval broadcast
        loadAllData();
        announce(`Safety broadcast: Incident at ${msg.gate} approved. ${msg.action_plan}`);
        break;

      default:
        break;
    }
  }, [announce, loadAllData]);

  const { isConnected } = useWebSocket(handleWsMessage, offlineMode);

  // Reusable Dropdown UX handlers
  const handleSelectMouseDown = (e) => {
    if (document.activeElement === e.target) {
      e.preventDefault();
      e.target.blur();
    }
  };

  const handleSelectChange = (setter) => (e) => {
    setter(e.target.value);
    e.target.blur();
  };

  return (
    <div className={`app-container ${(activeRole === 'assistant' || activeRole === 'organizer' || activeRole === 'volunteer') ? 'fullscreen-mode' : ''} ${a11yHighContrast ? 'a11y-high-contrast' : ''}`}>

      {/* ── Skip Navigation (WCAG 2.2) ─────────────────────────────────────── */}
      <a href="#main-content" className="skip-nav" tabIndex={0}>
        Skip to main content
      </a>

      {/* ── ARIA Live Region for screen readers ─────────────────────────────── */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {liveAnnouncement}
      </div>

      {/* ── Offline Mode Banner ──────────────────────────────────────────────── */}
      {offlineMode && (
        <div className="offline-banner" role="alert" aria-live="assertive">
          <span className="offline-badge">OFFLINE MODE</span>
          <span>Stadium connection degraded. Local caching is active. All coordinates are verified offline.</span>
        </div>
      )}

      {/* ── WebSocket live indicator (screen readers only) ───────────────────── */}
      <span className="sr-only" aria-live="polite">
        {isConnected ? 'Live stadium data connected.' : 'Live data disconnected. Attempting reconnection.'}
      </span>

      {/* ── Main Header Tablist ──────────────────────────────────────────────── */}
      <Header activeRole={activeRole} setActiveRole={setActiveRole} />

      {/* ── Main Workspace ───────────────────────────────────────────────────── */}
      <main
        id="main-content"
        className={(activeRole === 'assistant' || activeRole === 'organizer' || activeRole === 'volunteer') ? 'content-wrapper-fullscreen' : 'content-wrapper'}
        tabIndex={-1}
      >
        {activeRole === 'fan' && (
          <FanPortal
            offlineMode={offlineMode}
            transitStatuses={transitStatuses}
            incidentsList={incidentsList}
            handleSelectMouseDown={handleSelectMouseDown}
            handleSelectChange={handleSelectChange}
          />
        )}

        {activeRole === 'assistant' && (
          <AIAssistant
            offlineMode={offlineMode}
            handleSelectMouseDown={handleSelectMouseDown}
            handleSelectChange={handleSelectChange}
          />
        )}

        {activeRole === 'volunteer' && (
          <VolunteerConsole
            offlineMode={offlineMode}
            incidentsList={incidentsList}
            handleSelectMouseDown={handleSelectMouseDown}
            handleSelectChange={handleSelectChange}
            fetchIncidentsData={loadAllData}
          />
        )}

        {activeRole === 'organizer' && (
          <OrganizerDashboard
            offlineMode={offlineMode}
            incidentsList={incidentsList}
            sensorsList={sensorsList}
            handleSelectMouseDown={handleSelectMouseDown}
            handleSelectChange={handleSelectChange}
            fetchIncidentsData={loadAllData}
            fetchSensorsData={loadAllData}
          />
        )}
      </main>

      {/* ── Accessibility Footer ─────────────────────────────────────────────── */}
      {activeRole !== 'assistant' && activeRole !== 'volunteer' && (
        <A11yFooter
          a11yHighContrast={a11yHighContrast}
          setA11yHighContrast={setA11yHighContrast}
          offlineMode={offlineMode}
          setOfflineMode={setOfflineMode}
        />
      )}
    </div>
  );
}
