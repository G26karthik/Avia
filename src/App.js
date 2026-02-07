import React, { useState, useEffect, useRef, useCallback, createContext, useContext } from 'react';
import './App.css';

const API = '/api';
const ENTERPRISE_MAILTO = 'mailto:enterprise@avia-claims.ai?subject=Enterprise%20Inquiry';

/* ═══════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════ */

const riskColor = (s) => {
  if (s == null) return '#94a3b8';
  if (s >= 80) return '#dc2626';
  if (s >= 60) return '#d97706';
  return '#16a34a';
};

const riskBg = (s) => {
  if (s == null) return '#f1f5f9';
  if (s >= 80) return '#fef2f2';
  if (s >= 60) return '#fffbeb';
  return '#f0fdf4';
};

const statusBadge = (st) => {
  const m = {
    pending:  { bg: '#e6f5f5', color: '#0d6e6e', label: 'Pending' },
    reviewed: { bg: '#fff5f3', color: '#e8553d', label: 'Reviewed' },
    approved: { bg: '#dcfce7', color: '#16a34a', label: 'Approved' },
    denied:   { bg: '#fee2e2', color: '#dc2626', label: 'Denied' },
    escalated:{ bg: '#fef3c7', color: '#d97706', label: 'Escalated' },
    deferred: { bg: '#e6f5f5', color: '#0d6e6e', label: 'Deferred' },
  };
  const v = m[(st || '').toLowerCase()] || { bg: '#f1f5f9', color: '#64748b', label: st || 'Unknown' };
  return <span className="status-badge" style={{ background: v.bg, color: v.color }}>{v.label}</span>;
};

const formatCurrency = (v) => v != null ? `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '—';

const displayValue = (v, fallback = '—') => (v != null && v !== '' && v !== 'unknown') ? String(v) : fallback;

const sourceBadge = (s) =>
  s === 'uploaded'
    ? <span className="source-badge source-uploaded">Uploaded</span>
    : <span className="source-badge source-dataset">Dataset</span>;

/* ═══════════════════════════════════════════════════════════
   TOAST SYSTEM
   ═══════════════════════════════════════════════════════════ */

const ToastContext = createContext();

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const toastApi = useRef(null);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 250);
    }, toast.duration || 4000);
    return id;
  }, []);

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 250);
  }, []);

  toastApi.current = { addToast, dismiss };

  const icons = { success: '✓', error: '✕', info: 'i', warning: '!' };

  return (
    <ToastContext.Provider value={toastApi}>
      {children}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type || 'info'}${t.exiting ? ' toast-exit' : ''}`}>
            <div className="toast-icon">{icons[t.type] || 'i'}</div>
            <div className="toast-body">
              {t.title && <div className="toast-title">{t.title}</div>}
              <div className="toast-message">{t.message}</div>
            </div>
            <button className="toast-dismiss" onClick={() => dismiss(t.id)}>×</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function useToast() {
  const ref = useContext(ToastContext);
  return ref.current;
}

/* ═══════════════════════════════════════════════════════════
   LANDING PAGE
   ═══════════════════════════════════════════════════════════ */

function LandingPage({ onNavigate }) {
  return (
    <div className="landing-page">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="landing-brand">Avia</div>
          <div className="landing-nav-links">
            <button className="landing-nav-link" onClick={() => {}}>Platform</button>
            <button className="landing-nav-link" onClick={() => {}}>Features</button>
            <a className="landing-nav-link" href={ENTERPRISE_MAILTO}>Enterprise</a>
            <button className="landing-signin-btn" onClick={() => onNavigate('login')}>
              Sign In →
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero-inner">
          <div className="landing-hero-text">
            <span className="landing-eyebrow">AI-Powered Insurance Intelligence</span>
            <h1 className="landing-title">Detect Fraud Before It Costs You</h1>
            <p className="landing-subtitle">
              Avia combines advanced ML risk scoring, document OCR analysis, and GenAI
              reasoning to help claims teams investigate fraud faster and with greater confidence.
            </p>
            <div className="landing-cta-row">
              <button className="btn-primary btn-lg" onClick={() => onNavigate('login')}>
                Get Started Free →
              </button>
              <a className="btn-secondary btn-lg" href={ENTERPRISE_MAILTO}>
                Contact Sales
              </a>
            </div>
            <div className="landing-hero-stats">
              <div>
                <div className="hero-stat-number">94%</div>
                <div className="hero-stat-label">Fraud Detection</div>
              </div>
              <div>
                <div className="hero-stat-number">3x</div>
                <div className="hero-stat-label">Faster Review</div>
              </div>
              <div>
                <div className="hero-stat-number">$2.4M</div>
                <div className="hero-stat-label">Avg. Savings/Year</div>
              </div>
            </div>
          </div>
          <div className="landing-hero-visual">
            <div className="hero-glow">
              <div className="hero-badge">
                <div className="hero-badge-number">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <path d="M9 12l2 2 4-4"/>
                  </svg>
                </div>
                <div className="hero-badge-label">Protected by AI</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Bar */}
      <section className="landing-trust">
        <div className="landing-trust-inner">
          <div className="landing-trust-label">Trusted by leading insurance providers</div>
          <div className="landing-trust-logos">
            <span className="trust-logo">SAFEGUARD INS.</span>
            <span className="trust-logo">PREMIER COVER</span>
            <span className="trust-logo">ATLAS GROUP</span>
            <span className="trust-logo">SHIELD MUTUAL</span>
            <span className="trust-logo">HORIZON RE</span>
          </div>
        </div>
      </section>

      {/* Services / Features */}
      <section className="landing-services">
        <div className="landing-section-header">
          <div className="landing-section-eyebrow">What We Offer</div>
          <h2>Comprehensive Fraud Detection</h2>
          <p>Every tool your SIU team needs, powered by ML and GenAI</p>
        </div>
        <div className="landing-services-grid">
          {[
            {
              icon: (<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>),
              title: 'ML Risk Scoring',
              desc: 'Multi-dimensional fraud probability with behavioral & pattern analysis',
            },
            {
              icon: (<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>),
              title: 'Document OCR',
              desc: 'Extract & cross-reference data from uploaded documents automatically',
              active: true,
            },
            {
              icon: (<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>),
              title: 'GenAI Reasoning',
              desc: 'Natural language explanations of risk factors and fraud indicators',
            },
            {
              icon: (<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>),
              title: 'Decision Audit Trail',
              desc: 'Full traceability from intake through final adjudication decision',
            },
          ].map((s, i) => (
            <div key={i} className={`service-card${s.active ? ' active' : ''}`}>
              <div className="service-icon-wrap">{s.icon}</div>
              <div className="service-card-title">{s.title}</div>
              <div className="service-card-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* About / How It Works */}
      <section className="landing-about">
        <div className="landing-about-inner">
          <div className="landing-about-visual">
            <button className="about-play-btn" onClick={() => onNavigate('login')}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><polygon points="10,8 16,12 10,16"/></svg>
            </button>
          </div>
          <div className="landing-about-text">
            <div className="landing-about-eyebrow">How It Works</div>
            <h2>From Claim Intake to Investigation in Seconds</h2>
            <p>
              Upload a claim, attach documents and let Avia's AI engine do the rest.
              Our ML models score risk across multiple dimensions while GenAI provides
              human-readable reasoning for every flag. Claims that need attention are
              surfaced instantly with full escalation packages.
            </p>
            <button className="btn-about-learn" onClick={() => onNavigate('login')}>
              Try It Now →
            </button>
          </div>
        </div>
      </section>

      {/* Built For */}
      <section className="landing-who">
        <div className="landing-who-inner">
          <h2>Built For Insurance Professionals</h2>
          <div className="landing-who-grid">
            {[
              { title: 'Claims Adjusters', desc: 'Quickly assess risk, review AI reasoning, and make decisions with confidence.' },
              { title: 'SIU Investigators', desc: 'Receive pre-built escalation packages with evidence summaries and risk breakdowns.' },
              { title: 'Claims Managers', desc: 'Monitor team throughput, track decision patterns, and ensure compliance with audit trails.' },
              { title: 'Compliance Officers', desc: 'Full transparency into AI decisioning with explainable reasoning and document traceability.' },
            ].map((c, i) => (
              <div key={i} className="landing-who-card">
                <h3>{c.title}</h3>
                <p>{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="landing-cta-section">
        <div className="landing-cta-inner">
          <div className="landing-cta-text">
            <h2>Ready to stop fraud before it starts?</h2>
            <p>Join leading insurers using Avia to protect their bottom line.</p>
          </div>
          <button className="btn-cta-action" onClick={() => onNavigate('login')}>
            Start Free Trial →
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-top">
            <div>
              <div className="landing-footer-brand">Avia</div>
              <p className="landing-footer-desc">
                AI-powered insurance fraud detection platform helping claims teams
                investigate smarter and faster.
              </p>
            </div>
            <div>
              <div className="footer-col-title">Platform</div>
              <span className="footer-link">Risk Scoring</span>
              <span className="footer-link">Document OCR</span>
              <span className="footer-link">GenAI Analysis</span>
              <span className="footer-link">Escalation Packages</span>
            </div>
            <div>
              <div className="footer-col-title">Company</div>
              <span className="footer-link">About</span>
              <span className="footer-link">Careers</span>
              <span className="footer-link">Contact</span>
              <span className="footer-link">Blog</span>
            </div>
            <div>
              <div className="footer-col-title">Legal</div>
              <span className="footer-link">Privacy Policy</span>
              <span className="footer-link">Terms of Service</span>
              <span className="footer-link">Compliance</span>
            </div>
          </div>
          <div className="landing-footer-bottom">
            <span className="landing-footer-copy">© {new Date().getFullYear()} Avia. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   LOGIN SCREEN
   ═══════════════════════════════════════════════════════════ */

function LoginScreen({ onLogin, onBack }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-header">
          <div className="logo">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M9 12l2 2 4-4"/>
            </svg>
            <h1>Avia</h1>
          </div>
          <p className="login-subtitle">Claims Fraud Intelligence Platform</p>
        </div>
        {error && <div className="error-msg">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter your username" autoFocus />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" />
          </div>
          <button className="btn-primary" style={{ width: '100%' }} disabled={loading || !username || !password}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <button className="btn-back-to-landing" onClick={onBack}>← Back to Home</button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   RISK METER
   ═══════════════════════════════════════════════════════════ */

function RiskMeter({ label, value, large }) {
  const v = value ?? 0;
  return (
    <div className={`risk-meter${large ? ' large' : ''}`}>
      <div className="risk-meter-header">
        <span className="risk-meter-label">{label}</span>
        <span className="risk-meter-value" style={{ color: riskColor(v) }}>{v}%</span>
      </div>
      <div className="risk-meter-track">
        <div className="risk-meter-fill" style={{ width: `${v}%`, background: riskColor(v) }} />
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   CLAIMS LIST / DASHBOARD
   ═══════════════════════════════════════════════════════════ */

function ClaimsList({ user, onSelect, onUpload }) {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const toast = useToast();

  const fetchClaims = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/claims`, { headers: { Authorization: `Bearer ${user.token}` } });
      if (!res.ok) throw new Error('Failed to fetch claims');
      const data = await res.json();
      setClaims(data.claims || []);
    } catch (err) {
      toast.addToast({ type: 'error', title: 'Error', message: err.message });
    } finally {
      setLoading(false);
    }
  }, [user.token, toast]);

  useEffect(() => { fetchClaims(); }, [fetchClaims]);

  const filtered = claims.filter(c => {
    const term = search.toLowerCase();
    const matchesSearch = !term ||
      (c.claim_id || '').toLowerCase().includes(term) ||
      (c.policy_number || '').toLowerCase().includes(term) ||
      (c.incident_type || '').toLowerCase().includes(term);
    if (filter === 'high') return matchesSearch && c.risk_score >= 80;
    if (filter === 'medium') return matchesSearch && c.risk_score >= 60 && c.risk_score < 80;
    if (filter === 'low') return matchesSearch && c.risk_score < 60 && c.risk_score != null;
    if (filter === 'pending') return matchesSearch && (c.status || '').toLowerCase() === 'pending';
    return matchesSearch;
  });

  const stats = {
    total: claims.length,
    high: claims.filter(c => c.risk_score >= 80).length,
    medium: claims.filter(c => c.risk_score >= 60 && c.risk_score < 80).length,
    low: claims.filter(c => c.risk_score != null && c.risk_score < 60).length,
    pending: claims.filter(c => (c.status || '').toLowerCase() === 'pending').length,
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /><span>Loading claims…</span></div>;

  return (
    <div className="dashboard-page">
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <h1 className="dashboard-title">Claims Dashboard</h1>
          <p className="dashboard-subtitle">Manage, investigate, and adjudicate insurance claims across your portfolio</p>
        </div>
        <button className="btn-primary btn-upload-claim" onClick={onUpload}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Upload New Claim
        </button>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <div className={`stat-card${filter === 'all' ? ' stat-active' : ''}`} onClick={() => setFilter('all')}>
          <div className="stat-card-inner">
            <div className="stat-icon-wrap stat-icon-total">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
            </div>
            <div className="stat-text">
              <div className="stat-number">{stats.total}</div>
              <div className="stat-label">Total Claims</div>
            </div>
          </div>
        </div>
        <div className={`stat-card stat-high${filter === 'high' ? ' stat-active' : ''}`} onClick={() => setFilter('high')}>
          <div className="stat-card-inner">
            <div className="stat-icon-wrap stat-icon-high">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div className="stat-text">
              <div className="stat-number">{stats.high}</div>
              <div className="stat-label">High Risk</div>
            </div>
          </div>
        </div>
        <div className={`stat-card stat-medium${filter === 'medium' ? ' stat-active' : ''}`} onClick={() => setFilter('medium')}>
          <div className="stat-card-inner">
            <div className="stat-icon-wrap stat-icon-medium">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <div className="stat-text">
              <div className="stat-number">{stats.medium}</div>
              <div className="stat-label">Medium Risk</div>
            </div>
          </div>
        </div>
        <div className={`stat-card stat-low${filter === 'low' ? ' stat-active' : ''}`} onClick={() => setFilter('low')}>
          <div className="stat-card-inner">
            <div className="stat-icon-wrap stat-icon-low">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div className="stat-text">
              <div className="stat-number">{stats.low}</div>
              <div className="stat-label">Low Risk</div>
            </div>
          </div>
        </div>
        <div className={`stat-card stat-pending${filter === 'pending' ? ' stat-active' : ''}`} onClick={() => setFilter('pending')}>
          <div className="stat-card-inner">
            <div className="stat-icon-wrap stat-icon-pending">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </div>
            <div className="stat-text">
              <div className="stat-number">{stats.pending}</div>
              <div className="stat-label">Pending Review</div>
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="search-filter-bar">
        <div className="search-input-wrap">
          <span className="search-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </span>
          <input className="search-input" placeholder="Search by claim ID, policy number, or incident type…" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="filter-pills">
          {[
            { key: 'all', label: 'All' },
            { key: 'high', label: 'High Risk' },
            { key: 'medium', label: 'Medium' },
            { key: 'low', label: 'Low Risk' },
            { key: 'pending', label: 'Pending' },
          ].map(f => (
            <button key={f.key} className={`pill${filter === f.key ? ' active' : ''}`} onClick={() => setFilter(f.key)}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Claims Table */}
      <div className="claims-table-wrap">
        <div className="table-title-row">
          <span className="table-title">Claims Queue</span>
          <span className="table-count">{filtered.length} of {claims.length} claims</span>
        </div>
        <table className="claims-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Source</th>
              <th>Policy No.</th>
              <th>Incident Type</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Risk Level</th>
              <th>Score</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={10} className="empty-state">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5" style={{marginBottom:8}}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <div>No claims match your filter criteria</div>
              </td></tr>
            ) : filtered.map(c => (
              <tr key={c.claim_id} className="claim-row" onClick={() => onSelect(c.claim_id)}>
                <td>
                  <span className="claim-id-cell">{c.claim_id || '—'}</span>
                </td>
                <td>{sourceBadge(c.source)}</td>
                <td><span className="policy-cell">{displayValue(c.policy_number, '—')}</span></td>
                <td><span className="type-cell">{displayValue(c.incident_type)}</span></td>
                <td><span className="amount-cell">{formatCurrency(c.claim_amount)}</span></td>
                <td>{statusBadge(c.status)}</td>
                <td>
                  <span className="risk-pill" style={{ background: riskBg(c.risk_score), color: riskColor(c.risk_score) }}>
                    <span className="risk-dot" style={{ background: riskColor(c.risk_score) }}></span>
                    {c.risk_score != null ? (c.risk_score >= 80 ? 'High' : c.risk_score >= 60 ? 'Medium' : 'Low') : 'N/A'}
                  </span>
                </td>
                <td>
                  <span className="score-cell" style={{ color: riskColor(c.risk_score) }}>
                    {c.risk_score != null ? c.risk_score : '—'}
                  </span>
                </td>
                <td><span className="date-cell">{displayValue(c.incident_date)}</span></td>
                <td>
                  <span className={`action-btn ${c.risk_score == null ? 'action-analyze' : c.status === 'pending' ? 'action-review' : 'action-view'}`}>
                    {c.risk_score == null ? 'Analyze' : c.status === 'pending' ? 'Review' : 'View'}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   UPLOAD CLAIM SCREEN
   ═══════════════════════════════════════════════════════════ */

function UploadClaimScreen({ user, onDone }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef();
  const toast = useToast();

  const handleFiles = (fileList) => {
    const arr = Array.from(fileList).filter(f =>
      f.type === 'application/pdf' || f.type.startsWith('image/')
    );
    if (arr.length === 0) {
      toast.addToast({ type: 'warning', title: 'Invalid files', message: 'Only PDF and image files are supported.' });
      return;
    }
    setFiles(prev => [...prev, ...arr]);
  };

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx));

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      const form = new FormData();
      files.forEach(f => form.append('files', f));
      const res = await fetch(`${API}/claims/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${user.token}` },
        body: form,
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || 'Upload failed'); }
      const data = await res.json();
      toast.addToast({ type: 'success', title: 'Uploaded', message: `Claim ${data.claim_id} created successfully.` });
      onDone(data.claim_id);
    } catch (err) {
      toast.addToast({ type: 'error', title: 'Upload Error', message: err.message });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-claim-screen">
      <button className="btn-back" onClick={() => onDone(null)}>← Back to Dashboard</button>
      <h2>Upload New Claim</h2>
      <p className="upload-subtitle">Upload PDF or image documents. Avia will extract claim data via OCR and create a new claim record for analysis.</p>

      <div
        className={`upload-drop-zone${files.length ? ' has-files' : ''}`}
        onDragOver={e => { e.preventDefault(); e.currentTarget.classList.add('drag-over'); }}
        onDragLeave={e => { e.currentTarget.classList.remove('drag-over'); }}
        onDrop={e => { e.preventDefault(); e.currentTarget.classList.remove('drag-over'); handleFiles(e.dataTransfer.files); }}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" accept=".pdf,image/*" multiple style={{ display: 'none' }} onChange={e => { handleFiles(e.target.files); e.target.value = ''; }} />
        {files.length === 0 ? (
          <>
            <div className="upload-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <p><strong>Drop files here</strong> or click to browse</p>
            <p className="upload-hint">Supports PDF & image files</p>
          </>
        ) : (
          <div className="upload-file-list">
            {files.map((f, i) => (
              <div key={i} className="upload-file-item">
                <span>📄</span>
                <span className="upload-file-name">{f.name}</span>
                <span className="upload-file-size">{(f.size / 1024).toFixed(0)} KB</span>
                <button className="upload-file-remove" onClick={e => { e.stopPropagation(); removeFile(i); }}>×</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {uploading && (
        <div className="upload-progress">
          <div className="spinner" />
          Processing documents with OCR…
        </div>
      )}

      <div className="upload-actions">
        <button className="btn-primary" onClick={handleUpload} disabled={files.length === 0 || uploading}>
          {uploading ? 'Uploading…' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   INTAKE QUALITY CHECK
   ═══════════════════════════════════════════════════════════ */

function IntakeQualityCheck({ claimId, user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/claims/${claimId}/intake-check`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (!res.ok) throw new Error('Failed to fetch intake check');
        const d = await res.json();
        setData(d);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [claimId, user.token]);

  if (loading) return <div className="loading-screen"><div className="spinner" /><span>Running intake quality check…</span></div>;
  if (error) return <div className="error-msg">{error}</div>;
  if (!data) return null;

  const statusClass = data.ready_for_analysis ? 'ready' : (data.required_fields_present === data.total_required_fields ? 'needs-info' : 'incomplete');
  const statusLabel = data.ready_for_analysis ? 'Ready for Analysis' : (statusClass === 'needs-info' ? 'Needs Attention' : 'Incomplete');

  return (
    <div className="intake-check-card">
      <div className="intake-check-header">
        <span className={`intake-status-badge ${statusClass}`}>
          {statusClass === 'ready' ? '✓' : statusClass === 'needs-info' ? '!' : '✕'} {statusLabel}
        </span>
      </div>
      <p className="intake-check-message">{data.message}</p>

      {data.required_fields && data.required_fields.length > 0 && (
        <>
          <div className="intake-section-title">Required Fields ({data.required_fields_present}/{data.total_required_fields})</div>
          <div className="intake-fields-grid">
            {data.required_fields.map((f, i) => (
              <div key={i} className={`intake-field ${f.present ? 'present' : 'missing'}`}>
                <span className="intake-field-icon">{f.present ? '✓' : '✕'}</span>
                <span className="intake-field-label">{f.field_name}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {data.important_fields && data.important_fields.length > 0 && (
        <>
          <div className="intake-section-title">Important Fields ({data.important_fields_present}/{data.total_important_fields})</div>
          <div className="intake-fields-grid">
            {data.important_fields.map((f, i) => (
              <div key={i} className={`intake-field ${f.present ? 'present' : 'missing'}`}>
                <span className="intake-field-icon">{f.present ? '✓' : '!'}</span>
                <span className="intake-field-label">{f.field_name}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {data.inconsistencies && data.inconsistencies.length > 0 && (
        <div className="intake-inconsistencies">
          <h4>⚠ Data Inconsistencies</h4>
          <ul>{data.inconsistencies.map((inc, i) => <li key={i}>{inc}</li>)}</ul>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   ESCALATION PACKAGE MODAL
   ═══════════════════════════════════════════════════════════ */

function EscalationPackageModal({ claimId, user, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/claims/${claimId}/escalation-package`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (!res.ok) throw new Error('Failed to generate escalation package');
        const d = await res.json();
        setData(d);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [claimId, user.token]);

  const copyToClipboard = () => {
    if (!data) return;
    const sections = [];
    sections.push(`ESCALATION PACKAGE: ${data.claim_id}`);
    sections.push(`Generated: ${data.generated_at}\n`);

    if (data.summary) {
      const s = data.summary;
      sections.push('── CLAIM SUMMARY ──');
      sections.push(`Claim ID: ${s.claim_id}`);
      sections.push(`Policy: ${s.policy_number}`);
      sections.push(`Type: ${s.incident_type}`);
      sections.push(`Amount: ${formatCurrency(s.claim_amount)}`);
      sections.push(`Status: ${s.status}`);
      sections.push(`Date: ${s.incident_date}\n`);
    }

    if (data.risk_assessment) {
      const r = data.risk_assessment;
      sections.push('── RISK ASSESSMENT ──');
      sections.push(`Overall Score: ${r.overall_score}`);
      sections.push(`Risk Level: ${r.risk_level}`);
      if (r.explanation) sections.push(`Explanation: ${r.explanation}\n`);
    }

    if (data.reasoning_trace && data.reasoning_trace.length > 0) {
      sections.push('── REASONING TRACE ──');
      data.reasoning_trace.forEach((step, i) => sections.push(`${i + 1}. ${step}`));
      sections.push('');
    }

    if (data.adjuster_notes && data.adjuster_notes.length > 0) {
      sections.push('── ADJUSTER NOTES ──');
      data.adjuster_notes.forEach(n => sections.push(`[${n.decision} — ${n.decided_at}] ${n.notes}`));
    }

    navigator.clipboard.writeText(sections.join('\n'));
    toast.addToast({ type: 'success', title: 'Copied', message: 'Escalation package copied to clipboard.' });
  };

  const downloadText = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `escalation-${data.claim_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.addToast({ type: 'success', title: 'Downloaded', message: 'Escalation package saved.' });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📋 Escalation Package</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-actions">
          <button className="btn-teal" onClick={copyToClipboard} disabled={!data}>
            📋 Copy to Clipboard
          </button>
          <button className="btn-secondary" onClick={downloadText} disabled={!data}>
            ⬇ Download JSON
          </button>
        </div>

        <div className="modal-body">
          {loading && <div className="loading-screen"><div className="spinner" /><span>Generating escalation package…</span></div>}
          {error && <div className="error-msg">{error}</div>}

          {data && (
            <>
              {/* Summary Section */}
              {data.summary && (
                <div className="escalation-section">
                  <div className="escalation-section-title">Claim Summary</div>
                  <div className="escalation-grid">
                    <div className="escalation-field">
                      <div className="escalation-field-label">Claim ID</div>
                      <div className="escalation-field-value">{data.summary.claim_id}</div>
                    </div>
                    <div className="escalation-field">
                      <div className="escalation-field-label">Policy Number</div>
                      <div className="escalation-field-value">{displayValue(data.summary.policy_number)}</div>
                    </div>
                    <div className="escalation-field">
                      <div className="escalation-field-label">Incident Type</div>
                      <div className="escalation-field-value">{displayValue(data.summary.incident_type)}</div>
                    </div>
                    <div className="escalation-field">
                      <div className="escalation-field-label">Claim Amount</div>
                      <div className="escalation-field-value">{formatCurrency(data.summary.claim_amount)}</div>
                    </div>
                    <div className="escalation-field">
                      <div className="escalation-field-label">Status</div>
                      <div className="escalation-field-value">{displayValue(data.summary.status)}</div>
                    </div>
                    <div className="escalation-field">
                      <div className="escalation-field-label">Incident Date</div>
                      <div className="escalation-field-value">{displayValue(data.summary.incident_date)}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Risk Assessment */}
              {data.risk_assessment && (
                <div className="escalation-section">
                  <div className="escalation-section-title">Risk Assessment</div>
                  <div className="escalation-grid">
                    <div className="escalation-field">
                      <div className="escalation-field-label">Overall Risk Score</div>
                      <div className="escalation-field-value" style={{ color: riskColor(data.risk_assessment.overall_score), fontSize: 20 }}>
                        {data.risk_assessment.overall_score ?? '—'}
                      </div>
                    </div>
                    <div className="escalation-field">
                      <div className="escalation-field-label">Risk Level</div>
                      <div className="escalation-field-value">
                        <span className="risk-pill large" style={{ background: riskBg(data.risk_assessment.overall_score), color: riskColor(data.risk_assessment.overall_score) }}>
                          {displayValue(data.risk_assessment.risk_level)}
                        </span>
                      </div>
                    </div>
                  </div>
                  {data.risk_assessment.component_scores && (
                    <div className="escalation-risk-meters">
                      {Object.entries(data.risk_assessment.component_scores).map(([key, val]) => (
                        <RiskMeter key={key} label={key.replace(/_/g, ' ')} value={val} />
                      ))}
                    </div>
                  )}
                  {data.risk_assessment.explanation && (
                    <div className="escalation-explanation">{data.risk_assessment.explanation}</div>
                  )}
                </div>
              )}

              {/* Evidence / Reasoning */}
              {data.reasoning_trace && data.reasoning_trace.length > 0 && (
                <div className="escalation-section">
                  <div className="escalation-section-title">Reasoning Trace</div>
                  <div className="escalation-trace-list">
                    {data.reasoning_trace.map((step, i) => (
                      <div key={i} className="escalation-trace-item">
                        <span className="escalation-trace-num">{i + 1}</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Adjuster Notes */}
              <div className="escalation-section">
                <div className="escalation-section-title">Adjuster Notes & Decisions</div>
                {data.adjuster_notes && data.adjuster_notes.length > 0 ? (
                  data.adjuster_notes.map((n, i) => (
                    <div key={i} className="escalation-note-item">
                      <div className="escalation-note-meta">
                        {statusBadge(n.decision)} — {n.decided_at} by {n.decided_by}
                      </div>
                      <div className="escalation-note-text">{n.notes || 'No notes provided.'}</div>
                    </div>
                  ))
                ) : (
                  <div className="escalation-empty">No adjuster notes recorded yet.</div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   CLAIM DETAIL
   ═══════════════════════════════════════════════════════════ */

function ClaimDetail({ claimId, user, onBack }) {
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [notes, setNotes] = useState('');
  const [escalationOpen, setEscalationOpen] = useState(false);
  const [genaiError, setGenaiError] = useState(null);
  const fileRef = useRef();
  const toast = useToast();

  const fetchClaim = useCallback(async () => {
    try {
      const res = await fetch(`${API}/claims/${claimId}`, { headers: { Authorization: `Bearer ${user.token}` } });
      if (!res.ok) throw new Error('Failed to fetch claim');
      const data = await res.json();
      setClaim(data);
    } catch (err) {
      toast.addToast({ type: 'error', title: 'Error', message: err.message });
    } finally {
      setLoading(false);
    }
  }, [claimId, user.token, toast]);

  useEffect(() => { fetchClaim(); }, [fetchClaim]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setGenaiError(null);
    try {
      const res = await fetch(`${API}/claims/${claimId}/analyze`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${user.token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Analysis failed');
      if (data.genai_error) {
        setGenaiError(data.genai_error);
        toast.addToast({ type: 'warning', title: 'Partial Analysis', message: 'ML scoring complete but GenAI explanation unavailable.' });
      } else {
        toast.addToast({ type: 'success', title: 'Analysis Complete', message: `Risk score: ${data.risk_score}` });
      }
      await fetchClaim();
    } catch (err) {
      toast.addToast({ type: 'error', title: 'Analysis Failed', message: err.message });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDocUpload = async (fileList) => {
    const files = Array.from(fileList);
    if (files.length === 0) return;
    setUploading(true);
    try {
      const form = new FormData();
      files.forEach(f => form.append('files', f));
      const res = await fetch(`${API}/claims/${claimId}/documents`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${user.token}` },
        body: form,
      });
      if (!res.ok) throw new Error('Document upload failed');
      toast.addToast({ type: 'success', title: 'Documents Uploaded', message: `${files.length} document(s) attached.` });
      await fetchClaim();
    } catch (err) {
      toast.addToast({ type: 'error', title: 'Upload Error', message: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleDecision = async (decision) => {
    setDeciding(true);
    try {
      const res = await fetch(`${API}/claims/${claimId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.token}` },
        body: JSON.stringify({ decision, notes }),
      });
      if (!res.ok) throw new Error('Decision failed');
      toast.addToast({ type: 'success', title: 'Decision Recorded', message: `Claim marked as ${decision}.` });
      setNotes('');
      await fetchClaim();
    } catch (err) {
      toast.addToast({ type: 'error', title: 'Error', message: err.message });
    } finally {
      setDeciding(false);
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /><span>Loading claim details…</span></div>;
  if (!claim) return <div className="error-msg">Claim not found.</div>;

  const analysis = claim.analysis;
  const risk = analysis?.risk_scores || {};
  const docs = claim.documents || [];
  const decisions = claim.decisions || [];
  const hasAnalysis = analysis && analysis.risk_score != null;

  const nextAction = !hasAnalysis ? { text: '⚡ Run AI analysis to generate risk scores', bg: '#e6f5f5', border: '#0d6e6e' }
    : claim.status === 'pending' ? { text: '⏳ Claim analyzed — awaiting adjuster decision', bg: '#fffbeb', border: '#d97706' }
    : null;

  return (
    <div className="claim-detail-page">
      <button className="btn-back" onClick={onBack}>← Back to Dashboard</button>

      <div className="detail-header">
        <div className="detail-title-row">
          <div>
            <h2>{claim.claim_id}</h2>
            <div className="detail-policy">Policy {displayValue(claim.policy_number)} · {displayValue(claim.incident_type)}</div>
          </div>
          <div className="detail-header-actions">
            {sourceBadge(claim.source)}
            {statusBadge(claim.status)}
          </div>
        </div>
        {nextAction && <div className="next-action-banner" style={{ background: nextAction.bg, borderColor: nextAction.border }}>{nextAction.text}</div>}
      </div>

      {genaiError && (
        <div className="genai-error-banner genai-error-warn">
          <span className="genai-error-icon">⚠</span>
          <span><strong>GenAI Note:</strong> {genaiError}</span>
          <button className="genai-error-dismiss" onClick={() => setGenaiError(null)}>✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        {['overview', 'risk', 'trace', 'documents', 'actions', 'escalation'].map(t => (
          <button key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            {t === 'overview' ? '📋 Overview' : t === 'risk' ? '📊 Risk' : t === 'trace' ? '🔍 Trace' : t === 'documents' ? '📄 Documents' : t === 'actions' ? '⚖ Actions' : '📦 Escalation'}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {tab === 'overview' && (
        <div>
          <IntakeQualityCheck claimId={claimId} user={user} />
          <div className="info-grid">
            <InfoCard label="Claim Amount" value={formatCurrency(claim.claim_amount)} />
            <InfoCard label="Incident Date" value={displayValue(claim.incident_date)} />
            <InfoCard label="Report Date" value={displayValue(claim.report_date)} />
            <InfoCard label="Age" value={displayValue(claim.customer_age)} />
            <InfoCard label="Tenure (months)" value={displayValue(claim.months_as_customer)} />
            <InfoCard label="Past Claims" value={displayValue(claim.past_claims)} />
            <InfoCard label="Vehicle" value={`${displayValue(claim.vehicle_year)} ${displayValue(claim.vehicle_make)}`} />
            <InfoCard label="Police Report" value={displayValue(claim.police_report_filed)} />
            <InfoCard label="Witness" value={displayValue(claim.witness_present)} />
          </div>
          {!hasAnalysis && (
            <div className="analyze-prompt">
              <h3>Ready for AI Analysis</h3>
              <p>Run the AI engine to generate risk scores, reasoning trace, and fraud indicators for this claim.</p>
              <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                {analyzing ? 'Analyzing…' : '⚡ Run AI Analysis'}
              </button>
            </div>
          )}
          {hasAnalysis && analysis.explanation && (
            <div className="explanation-card">
              <h3>🤖 AI Explanation</h3>
              <p>{analysis.explanation}</p>
            </div>
          )}
        </div>
      )}

      {/* RISK TAB */}
      {tab === 'risk' && (
        <div>
          {hasAnalysis ? (
            <>
              <div className="risk-overview-card">
                <div className="risk-overall-score" style={{ color: riskColor(analysis.risk_score) }}>
                  {analysis.risk_score}
                </div>
                <div className="risk-overall-label">Overall Risk Score</div>
                <span className="risk-pill large" style={{ background: riskBg(analysis.risk_score), color: riskColor(analysis.risk_score) }}>
                  {analysis.risk_score >= 80 ? 'High Risk' : analysis.risk_score >= 60 ? 'Medium Risk' : 'Low Risk'}
                </span>
              </div>
              <div className="risk-buckets">
                <div className="bucket-card">
                  <h4>Claim Risk</h4>
                  <div className="bucket-desc">Amount, timing, and pattern indicators</div>
                  <RiskMeter label="Claim Score" value={risk.claim_risk} large />
                </div>
                <div className="bucket-card">
                  <h4>Customer Risk</h4>
                  <div className="bucket-desc">History, tenure, and behavioral signals</div>
                  <RiskMeter label="Customer Score" value={risk.customer_risk} large />
                </div>
                <div className="bucket-card">
                  <h4>Policy Risk</h4>
                  <div className="bucket-desc">Coverage alignment and policy anomalies</div>
                  <RiskMeter label="Policy Score" value={risk.policy_risk} large />
                </div>
              </div>
              {analysis.flags && analysis.flags.length > 0 && (
                <div className="features-card">
                  <h4>Fraud Indicators</h4>
                  <div className="features-list">
                    {analysis.flags.map((f, i) => <span key={i} className="feature-tag">{f}</span>)}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="analyze-prompt">
              <h3>No Risk Data Yet</h3>
              <p>Run AI analysis to generate risk scoring breakdown.</p>
              <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                {analyzing ? 'Analyzing…' : '⚡ Run AI Analysis'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* TRACE TAB */}
      {tab === 'trace' && (
        <div className="tab-trace">
          <h3>Reasoning Trace</h3>
          {hasAnalysis && analysis.reasoning_trace && analysis.reasoning_trace.length > 0 ? (
            <>
              <p className="trace-intro">Step-by-step AI reasoning process for this claim assessment</p>
              <div className="trace-steps">
                {analysis.reasoning_trace.map((step, i) => (
                  <div key={i} className="trace-step">
                    <div className="trace-step-number">{i + 1}</div>
                    <div className="trace-step-text">{step}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="analyze-prompt" style={{ marginTop: 16 }}>
              <h3>No Trace Available</h3>
              <p>Run AI analysis to generate the reasoning trace.</p>
              <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                {analyzing ? 'Analyzing…' : '⚡ Run AI Analysis'}
              </button>
            </div>
          )}

          {/* Document Insights */}
          {hasAnalysis && analysis.document_insights && analysis.document_insights.length > 0 && (
            <div className="doc-insights-section">
              <h3>Document Insights</h3>
              {analysis.document_insights.map((di, i) => (
                <div key={i} style={{ marginBottom: 16 }}>
                  <strong>{di.filename}</strong>
                  {di.summary && <div className="insight-summary">{di.summary}</div>}
                  {di.flags && di.flags.length > 0 && (
                    <div className="insight-flags">
                      <h4>Flags</h4>
                      {di.flags.map((fl, j) => <span key={j} className="flag-tag">{fl}</span>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* DOCUMENTS TAB */}
      {tab === 'documents' && (
        <div>
          {claim.source === 'uploaded' && (
            <div className="source-info-banner">
              <strong>📎 Source:</strong> This claim was created from uploaded documents via OCR extraction.
            </div>
          )}
          <div className="upload-section">
            <h3>Attach Documents</h3>
            <p>Upload additional evidence documents for this claim</p>
            <label className="upload-btn">
              {uploading ? 'Uploading…' : '+ Upload Files'}
              <input ref={fileRef} type="file" accept=".pdf,image/*" multiple style={{ display: 'none' }} onChange={e => { handleDocUpload(e.target.files); e.target.value = ''; }} disabled={uploading} />
            </label>
          </div>
          <div className="documents-list">
            <h3>Attached Documents ({docs.length})</h3>
            {docs.length === 0 ? (
              <p className="text-muted">No documents attached to this claim yet.</p>
            ) : docs.map((doc, i) => (
              <div key={i} className="document-card">
                <div className="doc-icon-svg">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0d6e6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  </svg>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="doc-name">{doc.filename}</div>
                  {doc.summary && <div className="doc-summary">{doc.summary}</div>}
                  {doc.upload_time && <div className="doc-upload-time">Uploaded: {doc.upload_time}</div>}
                  {doc.flags && doc.flags.length > 0 && (
                    <div className="doc-flags">{doc.flags.map((f, j) => <span key={j} className="flag-tag">{f}</span>)}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ACTIONS TAB */}
      {tab === 'actions' && (
        <div className="tab-actions">
          <h3>Adjudication Decision</h3>
          <div className="decision-form">
            <textarea rows={3} placeholder="Add notes about your decision rationale…" value={notes} onChange={e => setNotes(e.target.value)} />
            <div className="decision-buttons">
              <button className="btn-escalate" onClick={() => handleDecision('escalated')} disabled={deciding}>🚨 Escalate</button>
              <button className="btn-genuine" onClick={() => handleDecision('approved')} disabled={deciding}>✅ Approve</button>
              <button className="btn-defer" onClick={() => handleDecision('deferred')} disabled={deciding}>⏸ Defer</button>
            </div>
          </div>
          {decisions.length > 0 && (
            <div className="decision-history">
              <h4>Decision History</h4>
              {decisions.map((d, i) => (
                <div key={i} className="decision-entry">
                  {statusBadge(d.decision)}
                  <div className="decision-meta">by {d.decided_by} · {d.decided_at}</div>
                  {d.notes && <div className="decision-notes">{d.notes}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ESCALATION TAB */}
      {tab === 'escalation' && (
        <div>
          <div className="analyze-prompt">
            <h3>📦 Escalation Package</h3>
            <p>Generate a comprehensive investigation package with all claim data, risk assessment, reasoning trace, and adjuster notes — ready for SIU handoff.</p>
            <button className="btn-primary" onClick={() => setEscalationOpen(true)}>Generate Escalation Package</button>
          </div>
        </div>
      )}

      {/* Escalation Modal */}
      {escalationOpen && <EscalationPackageModal claimId={claimId} user={user} onClose={() => setEscalationOpen(false)} />}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   INFO CARD
   ═══════════════════════════════════════════════════════════ */

function InfoCard({ label, value }) {
  return (
    <div className="info-card">
      <div className="info-label">{label}</div>
      <div className="info-value">{value}</div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   TOP NAV
   ═══════════════════════════════════════════════════════════ */

function TopNav({ user, onLogout, onHome }) {
  return (
    <nav className="top-nav">
      <div className="nav-left">
        <div className="nav-logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
          <span className="nav-brand" onClick={onHome}>Avia</span>
        </div>
        <span className="nav-org">Claims Intelligence Platform</span>
      </div>
      <div className="nav-right">
        <span className="nav-user">{user.username}</span>
        <span className="nav-role">{user.role || 'Adjuster'}</span>
        <button className="btn-logout" onClick={onLogout}>Sign Out</button>
      </div>
    </nav>
  );
}

/* ═══════════════════════════════════════════════════════════
   APP INNER — Route Management
   ═══════════════════════════════════════════════════════════ */

function AppInner() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('landing');
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [restoring, setRestoring] = useState(true);

  // Session restore
  useEffect(() => {
    const saved = sessionStorage.getItem('avia_user');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setUser(parsed);
        setView('dashboard');
      } catch {}
    }
    setRestoring(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    sessionStorage.setItem('avia_user', JSON.stringify(userData));
    setView('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    sessionStorage.removeItem('avia_user');
    setView('landing');
    setSelectedClaim(null);
  };

  if (restoring) return <div className="loading-screen"><div className="spinner" /><span>Restoring session…</span></div>;

  if (view === 'landing') return <LandingPage onNavigate={setView} />;

  if (view === 'login') return <LoginScreen onLogin={handleLogin} onBack={() => setView('landing')} />;

  // Dashboard shell
  return (
    <div className="app-shell">
      <TopNav user={user} onLogout={handleLogout} onHome={() => { setView('dashboard'); setSelectedClaim(null); }} />
      <div className="main-content">
        {view === 'upload' && (
          <UploadClaimScreen user={user} onDone={(id) => { if (id) { setSelectedClaim(id); setView('detail'); } else { setView('dashboard'); } }} />
        )}
        {view === 'detail' && selectedClaim && (
          <ClaimDetail claimId={selectedClaim} user={user} onBack={() => { setView('dashboard'); setSelectedClaim(null); }} />
        )}
        {view === 'dashboard' && (
          <ClaimsList user={user} onSelect={(id) => { setSelectedClaim(id); setView('detail'); }} onUpload={() => setView('upload')} />
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   APP — Root
   ═══════════════════════════════════════════════════════════ */

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}
