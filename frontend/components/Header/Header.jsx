"use client";

import React from 'react';
import styles from './Header.module.css';

export default function Header({ activeRole, setActiveRole }) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.badge}>FIFA 26</span>
        <span className={styles.title}>STADIUM OPERATIONS COMMAND</span>
      </div>
      
      {/* Role Selector Tabs (WAI-ARIA compliant tablist with 4 roles) */}
      <div className={styles.selector} role="tablist" aria-label="Interface Mode Selector">
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
      </div>
    </header>
  );
}
