"use client";

import React, { useState, useEffect } from 'react';
import styles from './Header.module.css';

/**
 * RBAC Role Permission Map:
 * Defines which interface tabs are accessible for each authenticated user role.
 * - 'fan': Fan Portal, AI Assistant
 * - 'volunteer': Fan Portal, AI Assistant, Volunteer Console
 * - 'organizer' / 'admin': Fan Portal, AI Assistant, Volunteer Console, Organizer Dashboard
 */
const ROLE_PERMISSIONS = {
  fan: ['fan', 'assistant'],
  volunteer: ['fan', 'assistant', 'volunteer'],
  organizer: ['fan', 'assistant', 'volunteer', 'organizer'],
  admin: ['fan', 'assistant', 'volunteer', 'organizer'],
};

export default function Header({ activeRole, setActiveRole }) {
  const [userRole, setUserRole] = useState('fan');

  // Load active RBAC role from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('fifa_user_role') || 'fan';
    setUserRole(saved);
  }, []);

  const handleRoleChange = (e) => {
    const newRole = e.target.value;
    setUserRole(newRole);
    localStorage.setItem('fifa_user_role', newRole);

    // If active tab is not permitted under new role, switch back to Fan Portal
    const permittedTabs = ROLE_PERMISSIONS[newRole] || ['fan', 'assistant'];
    if (!permittedTabs.includes(activeRole)) {
      setActiveRole('fan');
    }
  };

  const isTabAllowed = (tabId) => {
    const allowed = ROLE_PERMISSIONS[userRole] || ['fan', 'assistant'];
    return allowed.includes(tabId);
  };

  return (
    <header className={styles.header}>
      {/* Brand Title */}
      <div className={styles.brand}>
        <span className={styles.badge}>FIFA 26</span>
        <span className={styles.title}>STADIUM OPERATIONS COMMAND</span>
      </div>
      
      {/* Role-Based Access Controlled Navigation (RBAC Filtered Tabs) */}
      <div className={styles.rightGroup}>
        <nav className={styles.selector} role="tablist" aria-label="RBAC Interface Mode Selector">
          {/* Fan Portal (All Roles) */}
          <button 
            id="fan-tab"
            className={`${styles.btn} ${activeRole === 'fan' ? styles.btnActive : ''}`}
            onClick={() => setActiveRole('fan')}
            role="tab"
            aria-selected={activeRole === 'fan'}
            aria-controls="fan-panel"
          >
            Fan Portal
          </button>

          {/* AI Assistant (All Roles) */}
          <button 
            id="assistant-tab"
            className={`${styles.btn} ${activeRole === 'assistant' ? styles.btnActive : ''}`}
            onClick={() => setActiveRole('assistant')}
            role="tab"
            aria-selected={activeRole === 'assistant'}
            aria-controls="assistant-panel"
          >
            AI Assistant
          </button>

          {/* Volunteer Console (Volunteer, Organizer, Admin) */}
          {isTabAllowed('volunteer') && (
            <button 
              id="volunteer-tab"
              className={`${styles.btn} ${activeRole === 'volunteer' ? styles.btnActive : ''}`}
              onClick={() => setActiveRole('volunteer')}
              role="tab"
              aria-selected={activeRole === 'volunteer'}
              aria-controls="volunteer-panel"
            >
              Volunteer Console
            </button>
          )}

          {/* Organizer Dashboard (Organizer, Admin Only) */}
          {isTabAllowed('organizer') && (
            <button 
              id="organizer-tab"
              className={`${styles.btn} ${activeRole === 'organizer' ? styles.btnActive : ''}`}
              onClick={() => setActiveRole('organizer')}
              role="tab"
              aria-selected={activeRole === 'organizer'}
              aria-controls="organizer-panel"
            >
              Organizer Dashboard
            </button>
          )}
        </nav>

        {/* RBAC Role Switcher & Security Badge */}
        <div className={styles.rbacControl}>
          <span className={styles.rbacLabel}>RBAC Auth:</span>
          <select 
            className={styles.rbacSelect}
            value={userRole}
            onChange={handleRoleChange}
            aria-label="RBAC Role Switcher"
          >
            <option value="fan">👤 Fan (Public)</option>
            <option value="volunteer">👷 Volunteer Staff</option>
            <option value="organizer">🛡️ Organizer Command</option>
            <option value="admin">⚡ Admin (Full Access)</option>
          </select>
        </div>
      </div>
    </header>
  );
}
