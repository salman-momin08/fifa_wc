"use client";

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../lib/useAuth';
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
  const { user, login, logout, isLoading, error } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');

  // Default role is 'fan' if unauthenticated
  const userRole = user?.role || 'fan';

  // If active tab becomes restricted when user logs out, reset to Fan Portal
  useEffect(() => {
    const permitted = ROLE_PERMISSIONS[userRole] || ['fan', 'assistant'];
    if (!permitted.includes(activeRole)) {
      setActiveRole('fan');
    }
  }, [userRole, activeRole, setActiveRole]);

  const handleTabClick = (tabId) => {
    const permitted = ROLE_PERMISSIONS[userRole] || ['fan', 'assistant'];
    if (permitted.includes(tabId)) {
      setActiveRole(tabId);
    } else {
      // Prompt login modal if trying to access restricted tab
      setShowLoginModal(true);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!usernameInput.trim() || !passwordInput.trim()) return;
    await login(usernameInput, passwordInput);
    setShowLoginModal(false);
    setUsernameInput('');
    setPasswordInput('');
  };

  const handleQuickLogin = async (roleName, pass) => {
    await login(roleName, pass);
    setShowLoginModal(false);
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
            onClick={() => handleTabClick('fan')}
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
            onClick={() => handleTabClick('assistant')}
            role="tab"
            aria-selected={activeRole === 'assistant'}
            aria-controls="assistant-panel"
          >
            AI Assistant
          </button>

          {/* Volunteer Console (Volunteer, Organizer, Admin) */}
          <button 
            id="volunteer-tab"
            className={`${styles.btn} ${activeRole === 'volunteer' ? styles.btnActive : ''} ${!ROLE_PERMISSIONS[userRole]?.includes('volunteer') ? styles.btnRestricted : ''}`}
            onClick={() => handleTabClick('volunteer')}
            role="tab"
            aria-selected={activeRole === 'volunteer'}
            aria-controls="volunteer-panel"
            title={!ROLE_PERMISSIONS[userRole]?.includes('volunteer') ? "Login as Volunteer or Organizer required" : ""}
          >
            Volunteer Console {!ROLE_PERMISSIONS[userRole]?.includes('volunteer') && '🔒'}
          </button>

          {/* Organizer Dashboard (Organizer, Admin Only) */}
          <button 
            id="organizer-tab"
            className={`${styles.btn} ${activeRole === 'organizer' ? styles.btnActive : ''} ${!ROLE_PERMISSIONS[userRole]?.includes('organizer') ? styles.btnRestricted : ''}`}
            onClick={() => handleTabClick('organizer')}
            role="tab"
            aria-selected={activeRole === 'organizer'}
            aria-controls="organizer-panel"
            title={!ROLE_PERMISSIONS[userRole]?.includes('organizer') ? "Login as Organizer or Admin required" : ""}
          >
            Organizer Dashboard {!ROLE_PERMISSIONS[userRole]?.includes('organizer') && '🔒'}
          </button>
        </nav>

        {/* Auth Profile / Login Button */}
        <div className={styles.authContainer}>
          {user ? (
            <div className={styles.userProfileBadge}>
              <span className={styles.roleTag}>
                {user.role === 'organizer' || user.role === 'admin' ? '🛡️' : '👷'} {user.role.toUpperCase()}
              </span>
              <span className={styles.usernameText}>{user.username}</span>
              <button className={styles.logoutBtn} onClick={logout} title="Sign out">Sign Out</button>
            </div>
          ) : (
            <button className={styles.loginTriggerBtn} onClick={() => setShowLoginModal(true)}>
              🔐 Sign In
            </button>
          )}
        </div>
      </div>

      {/* JWT Login Modal */}
      {showLoginModal && (
        <div className={styles.modalOverlay} onClick={() => setShowLoginModal(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>🔐 Authenticate via OAuth2 JWT</h3>
              <button className={styles.closeBtn} onClick={() => setShowLoginModal(false)}>✕</button>
            </div>

            <form onSubmit={handleFormSubmit} className={styles.loginForm}>
              {error && <div className={styles.errorBanner}>{error}</div>}

              <div className={styles.formField}>
                <label>Username</label>
                <input 
                  type="text" 
                  value={usernameInput} 
                  onChange={(e) => setUsernameInput(e.target.value)} 
                  placeholder="organizer, volunteer, or admin"
                  required
                />
              </div>

              <div className={styles.formField}>
                <label>Password</label>
                <input 
                  type="password" 
                  value={passwordInput} 
                  onChange={(e) => setPasswordInput(e.target.value)} 
                  placeholder="Enter password"
                  required
                />
              </div>

              <button type="submit" className={styles.submitBtn} disabled={isLoading}>
                {isLoading ? 'Authenticating...' : 'Sign In & Verify RBAC Token'}
              </button>
            </form>

            {/* Quick-login shortcuts for test credentials */}
            <div className={styles.quickLoginSection}>
              <span>Quick Demo Accounts:</span>
              <div className={styles.quickButtonsRow}>
                <button type="button" onClick={() => handleQuickLogin('organizer', 'organizerpassword')}>
                  🛡️ Organizer
                </button>
                <button type="button" onClick={() => handleQuickLogin('volunteer', 'volunteerpassword')}>
                  👷 Volunteer
                </button>
                <button type="button" onClick={() => handleQuickLogin('admin', 'adminpassword')}>
                  ⚡ Admin
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
