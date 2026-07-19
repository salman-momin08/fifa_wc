"use client";

import React from 'react';
import styles from './A11yFooter.module.css';

export default function A11yFooter({ a11yHighContrast, setA11yHighContrast, offlineMode, setOfflineMode }) {
  return (
    <footer className={styles.bar} role="contentinfo">
      <span>WCAG 2.2 AA Compliant Command Center</span>
      <div className={styles.actions}>
        <button 
          className={styles.btn} 
          onClick={() => setA11yHighContrast(!a11yHighContrast)}
          aria-pressed={a11yHighContrast}
        >
          {a11yHighContrast ? 'Disable High Contrast' : 'Enable High Contrast'}
        </button>
        <button 
          className={styles.btn} 
          onClick={() => setOfflineMode(!offlineMode)}
          aria-pressed={offlineMode}
        >
          {offlineMode ? 'Go Online' : 'Simulate Offline Mode'}
        </button>
      </div>
    </footer>
  );
}
