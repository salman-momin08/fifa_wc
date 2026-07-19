"use client";

import React, { useState } from 'react';
import { submitIncidentReport } from '../../lib/api';
import styles from './VolunteerConsole.module.css';

const SEVERITY_OPTIONS = [
  {
    value: 'low',
    label: 'Low',
    sub: 'Alert only',
    color: '#00e676',
    btnClass: styles.severityBtnLow,
  },
  {
    value: 'medium',
    label: 'Medium',
    sub: 'Slowing traffic',
    color: '#ffb300',
    btnClass: styles.severityBtnMedium,
  },
  {
    value: 'high',
    label: 'High',
    sub: 'Safety stop',
    color: '#ff5252',
    btnClass: styles.severityBtnHigh,
  },
];

const GATE_OPTIONS = ['Gate A', 'Gate B', 'Gate C', 'Transit Plaza', 'Concourse West'];

const DUTY_CHECKLIST = [
  'Always verify visitor accessibility queries against approved verified routes.',
  'In the event of overcrowding, direct spectators outward — never inward.',
  'Monitor active safety broadcasts and relay changes to your sector lead.',
];

function getStatusStyle(msg) {
  if (!msg) return null;
  if (msg.startsWith('✅')) return styles.statusSuccess;
  if (msg.startsWith('⚠️')) return styles.statusWarning;
  return styles.statusError;
}

function getStatusIcon(msg) {
  if (msg.startsWith('✅')) return '✅';
  if (msg.startsWith('⚠️')) return '⚠️';
  return '❌';
}

export default function VolunteerConsole({
  offlineMode,
  incidentsList,
  handleSelectMouseDown,
  handleSelectChange,
  fetchIncidentsData,
}) {
  const [reportTitle, setReportTitle]   = useState('');
  const [reportDesc, setReportDesc]     = useState('');
  const [reportGate, setReportGate]     = useState('Gate A');
  const [reportSeverity, setReportSeverity] = useState('medium');
  const [statusMsg, setStatusMsg]       = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reportTitle.trim() || !reportDesc.trim()) return;
    setIsSubmitting(true);

    if (offlineMode) {
      setStatusMsg('⚠️ Offline: Incident cached locally. Will sync when network is restored.');
      setReportTitle('');
      setReportDesc('');
      setIsSubmitting(false);
      return;
    }

    try {
      await submitIncidentReport({ title: reportTitle, description: reportDesc, gate: reportGate, severity: reportSeverity });
      setStatusMsg('✅ Incident logged. SOP draft queued for Organizer approval.');
      setReportTitle('');
      setReportDesc('');
      fetchIncidentsData();
    } catch {
      setStatusMsg('❌ Network failure. Incident could not be submitted.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeIncidents = incidentsList.filter((i) => i.status === 'active');

  return (
    <div
      id="volunteer-panel"
      className={styles.consoleGrid}
      role="tabpanel"
      aria-labelledby="volunteer-tab"
    >
      {/* ── LEFT: Incident Reporter ── */}
      <section className={`${styles.panel} ${styles.panelWarning}`} aria-label="Incident Reporter Form">
        <div className={styles.panelHeader}>
          <div className={`${styles.panelIcon} ${styles.panelIconWarning}`}>📋</div>
          <div className={styles.panelHeading}>
            <span className={styles.panelTitle}>Report Incident</span>
            <span className={styles.panelSubtitle}>Log stadium bottlenecks &amp; safety events</span>
          </div>
        </div>

        <div className={styles.panelBody}>
          {/* Status banner */}
          {statusMsg && (
            <div className={`${styles.statusBanner} ${getStatusStyle(statusMsg)}`} role="alert">
              <span className={styles.statusIcon}>{getStatusIcon(statusMsg)}</span>
              <span>{statusMsg.replace(/^[✅⚠️❌]\s*/, '')}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className={styles.formGrid}>
              {/* Title */}
              <div className={styles.formFieldFull}>
                <label htmlFor="report-title" className={styles.fieldLabel}>Incident Title</label>
                <input
                  type="text"
                  id="report-title"
                  className="text-input"
                  placeholder="e.g. Gate A Turnstile Jammed"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  required
                />
              </div>

              {/* Gate */}
              <div>
                <label htmlFor="report-gate-select" className={styles.fieldLabel}>Location / Gate</label>
                <select
                  id="report-gate-select"
                  className="select-input"
                  value={reportGate}
                  onChange={handleSelectChange(setReportGate)}
                  onMouseDown={handleSelectMouseDown}
                >
                  {GATE_OPTIONS.map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>

              {/* Severity tile-picker */}
              <div>
                <label className={styles.fieldLabel}>Severity Level</label>
                <div className={styles.severityRow} role="group" aria-label="Severity Level">
                  {SEVERITY_OPTIONS.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      aria-pressed={reportSeverity === s.value}
                      onClick={() => setReportSeverity(s.value)}
                      className={`${styles.severityBtn} ${s.btnClass} ${reportSeverity === s.value ? styles.severityActive : ''}`}
                    >
                      <span
                        className={styles.severityDot}
                        style={{ background: s.color }}
                      />
                      <span className={styles.severityLabel}>{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div className={styles.formFieldFull}>
                <label htmlFor="report-desc" className={styles.fieldLabel}>Details / Observations</label>
                <textarea
                  id="report-desc"
                  className="text-input"
                  rows={4}
                  placeholder="Describe the situation. e.g. Gate A scanner failed, queue extending past barricades…"
                  value={reportDesc}
                  onChange={(e) => setReportDesc(e.target.value)}
                  style={{ resize: 'none' }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isSubmitting}
              style={{ marginTop: '1.25rem', opacity: isSubmitting ? 0.6 : 1 }}
            >
              {isSubmitting ? 'Submitting…' : '⚡ Log Incident Draft'}
            </button>
          </form>
        </div>
      </section>

      {/* ── RIGHT: Guidelines + Live Alerts ── */}
      <section className={`${styles.panel} ${styles.panelPrimary}`} aria-label="Volunteer Operational Briefs">
        <div className={styles.panelHeader}>
          <div className={`${styles.panelIcon} ${styles.panelIconPrimary}`}>🛡️</div>
          <div className={styles.panelHeading}>
            <span className={styles.panelTitle}>Volunteer Briefing</span>
            <span className={styles.panelSubtitle}>Active guidelines &amp; live safety alerts</span>
          </div>
        </div>

        <div className={styles.panelBody}>
          {/* Duty checklist */}
          <div className={styles.checklist}>
            <div className={styles.checklistTitle}>Duty Checklist</div>
            {DUTY_CHECKLIST.map((item, i) => (
              <div key={i} className={styles.checklistItem}>
                <div className={styles.checklistBullet}>✓</div>
                <span>{item}</span>
              </div>
            ))}
          </div>

          {/* Live incident feed */}
          <div className={styles.incidentFeedTitle}>
            <span className={styles.liveDot} aria-hidden="true" />
            Live Safety Broadcasts
            {activeIncidents.length > 0 && (
              <span
                className="status-pill high"
                style={{ marginLeft: 'auto' }}
              >
                {activeIncidents.length} Active
              </span>
            )}
          </div>

          <div className={styles.incidentFeed} aria-live="polite" aria-label="Active safety incidents">
            {activeIncidents.length === 0 ? (
              <div className={styles.allClearBox}>
                <span className={styles.allClearIcon}>✅</span>
                <span className={styles.allClearText}>All Clear</span>
                <span className={styles.allClearSub}>No active safety broadcasts at this time</span>
              </div>
            ) : (
              activeIncidents.map((inc) => (
                <div key={inc.id} className={styles.incidentItem}>
                  <div className={styles.incidentItemBody}>
                    <div className={styles.incidentItemTitle}>{inc.title}</div>
                    <div className={styles.incidentItemGate}>📍 {inc.gate}</div>
                    <div className={styles.incidentItemAction}>{inc.suggested_action}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
