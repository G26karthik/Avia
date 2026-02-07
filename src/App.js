import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';

const API = '/api';

/* ───────────────────────── helpers ───────────────────────── */

function riskColor(level) {
  if (level === 'High') return '#e74c3c';
  if (level === 'Medium') return '#f39c12';
  return '#27ae60';
}

function riskBg(level) {
  if (level === 'High') return '#fdecea';
  if (level === 'Medium') return '#fef5e7';
  return '#eafaf1';
}

function statusBadge(status) {
  const map = {
    pending: { bg: '#eef2ff', color: '#4f46e5', label: 'Pending' },
    analyzed: { bg: '#fef3c7', color: '#d97706', label: 'Analyzed' },
    escalate: { bg: '#fee2e2', color: '#dc2626', label: 'Escalated' },
    escalated: { bg: '#fee2e2', color: '#dc2626', label: 'Escalated' },
    genuine: { bg: '#d1fae5', color: '#059669', label: 'Genuine' },
    cleared: { bg: '#d1fae5', color: '#059669', label: 'Cleared' },
    defer: { bg: '#e0e7ff', color: '#4338ca', label: 'Deferred' },
    deferred: { bg: '#e0e7ff', color: '#4338ca', label: 'Deferred' },
  };
  const s = map[status] || map.pending;
  return (
    <span className="status-badge" style={{ background: s.bg, color: s.color }}>
      {s.label}
    </span>
  );
}

function formatCurrency(n) {
  if (n == null || n === '' || n === 'Not specified') return 'Not specified';
  const num = Number(n);
  if (isNaN(num)) return 'Not specified';
  return '$' + num.toLocaleString();
}

function displayValue(val, fallback = 'Not specified') {
  if (val === null || val === undefined || val === '') return fallback;
  if (typeof val === 'string') {
    const lower = val.toLowerCase().trim();
    if (['unknown', 'n/a', 'none', '\u2014', '-', 'not available', 'not mentioned'].includes(lower)) return fallback;
  }
  return val;
}

function sourceBadge(source) {
  if (source === 'dataset') {
    return (
      <span className="source-badge source-dataset">
        Historical Dataset
      </span>
    );
  }
  return (
    <span className="source-badge source-uploaded">
      Uploaded Document
    </span>
  );
}

/* ───────────────────────── LandingPage ───────────────────────── */

const ENTERPRISE_MAILTO = "mailto:karthikofficialmain@gmail.com?subject=Avia%20%E2%80%93%20Enterprise%20Access%20Request&body=Organization%20Name%3A%0AContact%20Person%3A%0ARole%3A%0AUse%20Case%3A";

function LandingPage({ onSignIn }) {
  return (
    <div className="landing-page">
      <header className="landing-nav">
        <div className="landing-nav-inner">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="#4f46e5" />
              <path d="M12 28L20 12L28 28H12Z" fill="white" opacity="0.9" />
              <circle cx="20" cy="22" r="3" fill="#4f46e5" />
            </svg>
            <span className="landing-brand">Avia</span>
          </div>
          <button className="btn-primary landing-signin-btn" onClick={onSignIn}>Sign In</button>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-inner">
          <h1 className="landing-title">Avia</h1>
          <p className="landing-subtitle">
            AI-powered claim investigation for insurance teams
          </p>
          <div className="landing-cta-row">
            <button className="btn-primary btn-lg" onClick={onSignIn}>Sign In</button>
            <a className="btn-secondary btn-lg" href={ENTERPRISE_MAILTO}>Request Enterprise Access</a>
          </div>
        </div>
      </section>

      <section className="landing-features">
        <div className="landing-section-header">
          <h2>How Avia works</h2>
          <p>Purpose-built tools for insurance investigation workflows</p>
        </div>
        <div className="landing-features-inner">
          <div className="landing-feature-card">
            <div className="landing-feature-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            </div>
            <h3>Document-first claim intake</h3>
            <p>Upload claim documents \u2014 PDFs, images, forms. Multimodal AI reads them directly and auto-extracts structured claim data.</p>
          </div>
          <div className="landing-feature-card">
            <div className="landing-feature-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <h3>Risk assessment &amp; prioritization</h3>
            <p>Three-bucket scoring \u2014 claim details, customer history, behavioral patterns \u2014 ranks every claim by urgency.</p>
          </div>
          <div className="landing-feature-card">
            <div className="landing-feature-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            </div>
            <h3>Explainable decision trace</h3>
            <p>Every risk assessment comes with a step-by-step rationale written in plain English \u2014 no black boxes.</p>
          </div>
          <div className="landing-feature-card">
            <div className="landing-feature-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <h3>Investigator-controlled workflow</h3>
            <p>AI provides signals and explains. Investigators make the final call \u2014 escalate, clear, or defer. Full audit trail.</p>
          </div>
        </div>
      </section>

      <section className="landing-who">
        <div className="landing-who-inner">
          <h2>Built for</h2>
          <div className="landing-who-grid">
            <div className="landing-who-card">
              <h3>Insurance companies</h3>
              <p>Streamline claims triage across large portfolios. Reduce manual review time while maintaining investigator control.</p>
            </div>
            <div className="landing-who-card">
              <h3>Fraud investigation teams</h3>
              <p>Surface high-risk claims faster with AI-powered risk scoring and document intelligence. Focus effort where it matters.</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <span className="landing-footer-brand">Avia</span>
          <a href={ENTERPRISE_MAILTO} className="landing-footer-link">Contact</a>
        </div>
      </footer>
    </div>
  );
}

/* ───────────────────────── LoginScreen ───────────────────────── */

function LoginScreen({ onLogin, onBack }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Login failed');
      }
      const user = await res.json();
      onLogin(user);
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
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="#4f46e5" />
              <path d="M12 28L20 12L28 28H12Z" fill="white" opacity="0.9" />
              <circle cx="20" cy="22" r="3" fill="#4f46e5" />
            </svg>
            <h1>Avia</h1>
          </div>
          <p className="login-subtitle">Fraud Investigation Platform</p>
        </div>
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Username</label>
            <input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" autoFocus required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required />
          </div>
          {error && <div className="error-msg">{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <button className="btn-back-to-landing" onClick={onBack}>\u2190 Back to home</button>
      </div>
    </div>
  );
}

/* ───────────────────────── RiskMeter ───────────────────────── */

function RiskMeter({ label, score, size = 'normal' }) {
  const pct = Math.min(100, Math.max(0, score || 0));
  let color = '#27ae60';
  if (pct >= 65) color = '#e74c3c';
  else if (pct >= 35) color = '#f39c12';

  return (
    <div className={`risk-meter ${size}`}>
      <div className="risk-meter-header">
        <span className="risk-meter-label">{label}</span>
        <span className="risk-meter-value" style={{ color }}>{pct.toFixed(0)}</span>
      </div>
      <div className="risk-meter-track">
        <div className="risk-meter-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

/* ───────────────────────── ClaimsList ───────────────────────── */

function ClaimsList({ user, onSelect, onUploadClaim }) {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetch(`${API}/claims`, {
      headers: { 'Authorization': `Bearer ${user.token}` }
    })
      .then(r => { if (!r.ok) throw new Error('Auth failed'); return r.json(); })
      .then(d => { setClaims(d.claims || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [user.token]);

  const filtered = claims.filter(c => {
    if (filter === 'high') return c.risk_level === 'High';
    if (filter === 'medium') return c.risk_level === 'Medium';
    if (filter === 'low') return c.risk_level === 'Low';
    if (filter === 'pending') return c.status === 'pending';
    if (filter === 'analyzed') return c.status === 'analyzed';
    if (filter === 'dataset') return c.source === 'dataset';
    if (filter === 'uploaded') return c.source === 'uploaded';
    return true;
  }).filter(c => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      c.policy_number?.toLowerCase().includes(q) ||
      c.incident_type?.toLowerCase().includes(q) ||
      c.id?.toLowerCase().includes(q) ||
      c.source?.toLowerCase().includes(q)
    );
  });

  const stats = {
    total: claims.length,
    high: claims.filter(c => c.risk_level === 'High').length,
    medium: claims.filter(c => c.risk_level === 'Medium').length,
    low: claims.filter(c => c.risk_level === 'Low').length,
    pending: claims.filter(c => c.status === 'pending').length,
  };

  if (loading) return <div className="loading-screen"><div className="spinner" />Loading claims…</div>;

  return (
    <div className="claims-list-page">
      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stat-card" onClick={() => setFilter('all')}>
          <div className="stat-number">{stats.total}</div>
          <div className="stat-label">Total Claims</div>
        </div>
        <div className="stat-card stat-high" onClick={() => setFilter('high')}>
          <div className="stat-number">{stats.high}</div>
          <div className="stat-label">High Risk</div>
        </div>
        <div className="stat-card stat-medium" onClick={() => setFilter('medium')}>
          <div className="stat-number">{stats.medium}</div>
          <div className="stat-label">Medium Risk</div>
        </div>
        <div className="stat-card stat-low" onClick={() => setFilter('low')}>
          <div className="stat-number">{stats.low}</div>
          <div className="stat-label">Low Risk</div>
        </div>
        <div className="stat-card stat-pending" onClick={() => setFilter('pending')}>
          <div className="stat-number">{stats.pending}</div>
          <div className="stat-label">Pending</div>
        </div>
      </div>

      {/* Search & Filter Row */}
      <div className="search-filter-row">
        <input
          className="search-input"
          placeholder="Search by policy #, type, or claim ID…"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
        <button className="btn-primary btn-upload-claim" onClick={onUploadClaim}>
          + Upload New Claim
        </button>
        <div className="filter-pills">
          {['all', 'high', 'medium', 'low', 'pending', 'analyzed', 'dataset', 'uploaded'].map(f => (
            <button
              key={f}
              className={`pill ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Claims Table */}
      <div className="claims-table-wrap">
        <table className="claims-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Policy Number</th>
              <th>Source</th>
              <th>Incident Type</th>
              <th>Severity</th>
              <th>Claim Amount</th>
              <th>Risk Level</th>
              <th>Score</th>
              <th>Status</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr key={c.id} onClick={() => onSelect(c.id)} className="claim-row">
                <td className="mono">{c.id?.slice(0, 12)}</td>
                <td>{c.policy_number}</td>
                <td>{sourceBadge(c.source)}</td>
                <td>{displayValue(c.incident_type)}</td>
                <td>{displayValue(c.incident_severity)}</td>
                <td className="amount">{formatCurrency(c.total_claim_amount)}</td>
                <td>
                  {c.risk_level ? (
                    <span className="risk-pill" style={{ background: riskBg(c.risk_level), color: riskColor(c.risk_level) }}>
                      {c.risk_level}
                    </span>
                  ) : <span className="text-muted">Pending</span>}
                </td>
                <td className="score-cell">
                  {c.overall_risk_score != null ? (
                    <span style={{ color: riskColor(c.risk_level), fontWeight: 600 }}>
                      {c.overall_risk_score}
                    </span>
                  ) : <span className="text-muted">Pending</span>}
                </td>
                <td>{statusBadge(c.status)}</td>
                <td className="next-action">{c.risk_level ? c.next_action : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="empty-state">No claims match the current filters.</div>
        )}
      </div>
    </div>
  );
}

/* ───────────────────────── UploadClaimScreen ───────────────────────── */

function UploadClaimScreen({ user, onDone, onCancel }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState('');
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const addFiles = (newFiles) => {
    const allowed = ['.pdf', '.png', '.jpg', '.jpeg'];
    const valid = Array.from(newFiles).filter(f => {
      const ext = '.' + f.name.split('.').pop().toLowerCase();
      return allowed.includes(ext);
    });
    if (valid.length + files.length > 10) {
      setError('Maximum 10 files allowed.');
      return;
    }
    setFiles(prev => [...prev, ...valid]);
    setError(null);
  };

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files);
  };

  const handleSubmit = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError(null);
    setProgress('Extracting claim details from document with AI…');

    const fd = new FormData();
    files.forEach(f => fd.append('files', f));

    try {
      const res = await fetch(`${API}/claims/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` },
        body: fd,
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Upload failed');
      }
      const result = await res.json();
      setProgress('');
      onDone(result.claim_id);
    } catch (err) {
      setError(err.message);
      setProgress('');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-claim-screen">
      <button className="btn-back" onClick={onCancel}>← Back to Claims</button>
      <h2>Upload New Claim</h2>
      <p className="upload-subtitle">
        Drop claim documents below. Avia will use AI to extract claim details directly
        from the document and create a new claim for review.
      </p>

      <div
        className={`upload-drop-zone ${dragOver ? 'drag-over' : ''} ${files.length > 0 ? 'has-files' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          hidden
          multiple
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }}
        />
        <svg className="upload-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <p><strong>Click or drag files here</strong></p>
        <p className="upload-hint">PDF, PNG, or JPG — up to 20 MB each, 10 files max</p>
      </div>

      {files.length > 0 && (
        <div className="upload-file-list">
          {files.map((f, i) => (
            <div key={i} className="upload-file-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span className="upload-file-name">{f.name}</span>
              <span className="upload-file-size">{(f.size / 1024).toFixed(0)} KB</span>
              <button className="upload-file-remove" onClick={(e) => { e.stopPropagation(); removeFile(i); }}>×</button>
            </div>
          ))}
        </div>
      )}

      {error && <div className="error-msg" style={{ marginTop: 16 }}>{error}</div>}

      {progress && (
        <div className="upload-progress">
          <div className="spinner" />
          <span>{progress}</span>
        </div>
      )}

      <div className="upload-actions">
        <button
          className="btn-primary btn-lg"
          onClick={handleSubmit}
          disabled={files.length === 0 || uploading}
        >
          {uploading ? 'Extracting…' : `Upload & Extract Claim (${files.length} file${files.length !== 1 ? 's' : ''})`}
        </button>
      </div>
    </div>
  );
}

/* ───────────────────────── ClaimDetail ───────────────────────── */

function ClaimDetail({ claimId, onBack, user }) {
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [analyzeError, setAnalyzeError] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const loadClaim = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/claims/${claimId}`, {
        headers: { 'Authorization': `Bearer ${user.token}` }
      });
      if (!res.ok) throw new Error('Failed to load claim');
      const data = await res.json();
      setClaim(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [claimId, user.token]);

  useEffect(() => { loadClaim(); }, [loadClaim]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const res = await fetch(`${API}/claims/${claimId}/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` }
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setAnalyzeError(errData.detail || 'Analysis failed');
      } else {
        await loadClaim();
        setActiveTab('risk');
      }
    } catch (err) {
      setAnalyzeError('Unable to reach the server. Please check your connection.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch(`${API}/claims/${claimId}/documents`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` },
        body: fd
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setUploadError(errData.detail || 'Upload failed');
      } else {
        const data = await res.json();
        if (data.genai_error) {
          setUploadError('Document saved. AI insights unavailable: ' + data.genai_error);
        }
        await loadClaim();
      }
    } catch (err) {
      setUploadError('Unable to reach the server. Please check your connection.');
    } finally {
      setUploading(false);
    }
  };

  const handleDecision = async (action) => {
    setDeciding(true);
    try {
      await fetch(`${API}/claims/${claimId}/decide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ action, notes: decisionNotes }),
      });
      await loadClaim();
      setDecisionNotes('');
    } catch (err) {
      console.error(err);
    } finally {
      setDeciding(false);
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" />Loading claim…</div>;
  if (!claim) return <div className="loading-screen">Claim not found.</div>;

  const cd = claim.claim_data || {};
  const isAnalyzed = claim.risk_level != null;
  const hasDocuments = claim.documents && claim.documents.length > 0;
  const isDatasetClaim = claim.source === 'dataset';
  const isUploadedClaim = claim.source === 'uploaded';

  return (
    <div className="claim-detail-page">
      {/* Header */}
      <div className="detail-header">
        <button className="btn-back" onClick={onBack}>← Claims</button>
        <div className="detail-title-row">
          <div>
            <h2>Claim {claim.id?.slice(0, 12)}</h2>
            <span className="detail-policy">Policy: {claim.policy_number}</span>
            <div style={{ marginTop: 6 }}>{sourceBadge(claim.source)}</div>
          </div>
          <div className="detail-header-actions">
            {statusBadge(claim.status)}
            {isAnalyzed && (
              <span className="risk-pill large" style={{ background: riskBg(claim.risk_level), color: riskColor(claim.risk_level) }}>
                {claim.risk_level} Risk — {claim.overall_risk_score}
              </span>
            )}
          </div>
        </div>
        {isAnalyzed && claim.next_action && (
          <div className="next-action-banner" style={{ background: riskBg(claim.risk_level), borderLeftColor: riskColor(claim.risk_level) }}>
            <strong>Recommended Action:</strong> {claim.next_action}
          </div>
        )}
      </div>

      {/* Error Banners */}
      {analyzeError && (
        <div className="genai-error-banner">
          <span className="genai-error-icon">&#9888;</span>
          <span>{analyzeError}</span>
          <button className="genai-error-dismiss" onClick={() => setAnalyzeError(null)}>&times;</button>
        </div>
      )}
      {uploadError && (
        <div className="genai-error-banner genai-error-warn">
          <span className="genai-error-icon">&#9888;</span>
          <span>{uploadError}</span>
          <button className="genai-error-dismiss" onClick={() => setUploadError(null)}>&times;</button>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        {[['overview', 'Overview'], ['risk', 'Risk Assessment'], ['trace', 'Review Rationale'], ['documents', 'Documents'], ['actions', 'Decision']].map(([tab, label]) => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="tab-overview">
            <div className="info-grid">
              <InfoCard label="Incident Type" value={displayValue(cd.incident_type)} />
              <InfoCard label="Severity" value={displayValue(cd.incident_severity)} />
              <InfoCard label="Claim Amount" value={formatCurrency(cd.total_claim_amount)} />
              <InfoCard label="Customer Tenure" value={
                cd.customer_tenure_months != null
                  ? `${cd.customer_tenure_months} months`
                  : cd.months_as_customer != null
                    ? `${cd.months_as_customer} months`
                    : 'Not available'
              } />
              <InfoCard label="Vehicles Involved" value={displayValue(cd.number_of_vehicles_involved)} />
              <InfoCard label="Bodily Injuries" value={displayValue(cd.bodily_injuries)} />
              <InfoCard label="Witnesses" value={displayValue(cd.witnesses)} />
              <InfoCard label="Police Report" value={displayValue(cd.police_report_available)} />
              <InfoCard label="Authorities" value={displayValue(cd.authorities_contacted)} />
              <InfoCard label="Property Damage" value={displayValue(cd.property_damage)} />
              <InfoCard label="Vehicle" value={
                [cd.vehicle_year, cd.vehicle_make, cd.vehicle_model, cd.auto_year, cd.auto_make, cd.auto_model]
                  .filter(Boolean).length > 0
                  ? [cd.vehicle_year || cd.auto_year, cd.vehicle_make || cd.auto_make, cd.vehicle_model || cd.auto_model].filter(Boolean).join(' ')
                  : 'Not present in document'
              } />
              <InfoCard label="Policy State" value={cd.policy_state || 'Not present in document'} />
            </div>

            {!isAnalyzed && (
              <div className="analyze-prompt">
                <h3>Pending Review</h3>
                {isDatasetClaim ? (
                  <>
                    <p>This is a historical dataset claim. It can be analyzed using the existing claim data without requiring document upload.</p>
                    <button className="btn-primary btn-lg" onClick={handleAnalyze} disabled={analyzing}>
                      {analyzing ? 'Reviewing…' : 'Run Claim Review'}
                    </button>
                  </>
                ) : hasDocuments ? (
                  <>
                    <p>Claim details have been extracted from the uploaded document. Click below to run risk analysis across three dimensions: claim details, customer history, and behavioral patterns.</p>
                    <button className="btn-primary btn-lg" onClick={handleAnalyze} disabled={analyzing}>
                      {analyzing ? 'Analyzing…' : 'Analyze Claim'}
                    </button>
                  </>
                ) : (
                  <p>Upload at least one supporting document in the Documents tab before running a review.</p>
                )}
              </div>
            )}

            {isAnalyzed && claim.ai_explanation && (
              <div className="explanation-card">
                <h3>Assessment Summary</h3>
                <p>{claim.ai_explanation}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="tab-risk">
            {!isAnalyzed ? (
              <div className="analyze-prompt">
                {isDatasetClaim ? (
                  <p>Run a claim review to see the risk breakdown (no documents required for historical claims).</p>
                ) : hasDocuments ? (
                  <p>Click "Analyze Claim" to run risk scoring and see the breakdown.</p>
                ) : (
                  <p>Upload at least one supporting document before running a review.</p>
                )}
                <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing || (!isDatasetClaim && !hasDocuments)}>
                  {analyzing ? 'Analyzing…' : (isUploadedClaim ? 'Analyze Claim' : 'Run Claim Review')}
                </button>
              </div>
            ) : (
              <>
                <div className="risk-overview-card">
                  <div className="risk-overall">
                    <div className="risk-overall-score" style={{ color: riskColor(claim.risk_level) }}>
                      {claim.overall_risk_score}
                    </div>
                    <div className="risk-overall-label">Overall Risk Score</div>
                    <span className="risk-pill large" style={{ background: riskBg(claim.risk_level), color: riskColor(claim.risk_level) }}>
                      {claim.risk_level}
                    </span>
                  </div>
                </div>

                <div className="risk-buckets">
                  <div className="bucket-card">
                    <h4>Claim Details</h4>
                    <p className="bucket-desc">Based on incident details, claimed amounts, and damage description</p>
                    <RiskMeter label="Claim Score" score={claim.claim_risk_score} size="large" />
                  </div>
                  <div className="bucket-card">
                    <h4>Customer History</h4>
                    <p className="bucket-desc">Based on tenure, prior claims, and policy characteristics</p>
                    <RiskMeter label="Customer Score" score={claim.customer_risk_score} size="large" />
                  </div>
                  <div className="bucket-card">
                    <h4>Behavioral Patterns</h4>
                    <p className="bucket-desc">Based on statistical patterns and anomaly indicators</p>
                    <RiskMeter label="Pattern Score" score={claim.pattern_risk_score} size="large" />
                  </div>
                </div>

                {claim.top_features && claim.top_features.length > 0 && (
                  <div className="features-card">
                    <h4>Key Risk Indicators</h4>
                    <div className="features-list">
                      {(claim.top_features || []).map((f, i) => (
                        <span key={i} className="feature-tag">{f}</span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'trace' && (
          <div className="tab-trace">
            {!isAnalyzed ? (
              <div className="analyze-prompt">
                {isDatasetClaim ? (
                  <p>Run a claim review to see the assessment rationale (no documents required for historical claims).</p>
                ) : hasDocuments ? (
                  <p>Click "Analyze Claim" to generate the assessment rationale.</p>
                ) : (
                  <p>Upload at least one supporting document before running a review.</p>
                )}
                <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing || (!isDatasetClaim && !hasDocuments)}>
                  {analyzing ? 'Analyzing\u2026' : (isUploadedClaim ? 'Analyze Claim' : 'Run Claim Review')}
                </button>
              </div>
            ) : (
              <>
                <h3>Review Rationale</h3>
                <p className="trace-intro">Step-by-step reasoning used to assess this claim:</p>
                <div className="trace-steps">
                  {(claim.decision_trace || []).map((step, i) => (
                    <div key={i} className="trace-step">
                      <div className="trace-step-number">{i + 1}</div>
                      <div className="trace-step-text">{typeof step === 'string' ? step : step.detail || step.title || JSON.stringify(step)}</div>
                    </div>
                  ))}
                </div>

                {claim.document_insights && (
                  (claim.document_insights.flags?.length > 0 || claim.document_insights.summaries?.length > 0) && (
                    <div className="doc-insights-section">
                      <h3>Document Insights</h3>
                      {claim.document_insights.summaries?.map((s, i) => (
                        <div key={i} className="insight-summary">{s}</div>
                      ))}
                      {claim.document_insights.flags?.length > 0 && (
                        <div className="insight-flags">
                          <h4>Flags</h4>
                          {claim.document_insights.flags.map((f, i) => (
                            <span key={i} className="flag-tag">⚠ {f}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="tab-documents">
            {/* Source info banner */}
            <div className="source-info-banner">
              <strong>Claim Source:</strong> {isDatasetClaim ? 'Historical Dataset' : 'Uploaded Document'}
            </div>

            {/* Upload section — always available */}
            <div className="upload-section">
              <h3>Attach Documents</h3>
              <p>Upload claim-related documents such as police reports, repair estimates, or photos (PDF, PNG, JPG — up to 20 MB).</p>
              <label className="upload-btn">
                {uploading ? 'Uploading\u2026' : 'Choose File'}
                <input type="file" hidden accept=".pdf,.png,.jpg,.jpeg" onChange={handleUpload} disabled={uploading} />
              </label>
            </div>

            {claim.documents && claim.documents.length > 0 && (
              <div className="documents-list">
                <h3>Attached Documents ({claim.documents.length})</h3>
                {claim.documents.map(doc => (
                  <div key={doc.id} className="document-card">
                    <div className="doc-icon doc-icon-svg">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    </div>
                    <div className="doc-info">
                      <div className="doc-name">{doc.filename}</div>
                      {doc.uploaded_at && <div className="doc-upload-time">Uploaded: {doc.uploaded_at}</div>}
                      {doc.ai_summary && <div className="doc-summary">{doc.ai_summary}</div>}
                      {doc.ai_flags && doc.ai_flags.length > 0 && (
                        <div className="doc-flags">
                          {doc.ai_flags.map((f, i) => (
                            <span key={i} className="flag-tag">⚠ {f}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {(!claim.documents || claim.documents.length === 0) && (
              <div className="empty-state">
                {isDatasetClaim
                  ? 'No documents available for historical claims. This claim was imported from a dataset and can be analyzed using existing claim data.'
                  : 'No documents attached to this claim yet. Upload documents to proceed with analysis.'}
              </div>
            )}
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="tab-actions">
            <h3>Record Decision</h3>
            {!isAnalyzed && (
              <div className="analyze-prompt">
                {isDatasetClaim ? (
                  <p>Run a claim review before recording a decision (no documents required for historical claims).</p>
                ) : hasDocuments ? (
                  <p>Analyze the claim before recording a decision.</p>
                ) : (
                  <p>Upload at least one supporting document and run a review before recording a decision.</p>
                )}
                <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing || (!isDatasetClaim && !hasDocuments)}>
                  {analyzing ? 'Analyzing…' : (isUploadedClaim ? 'Analyze Claim' : 'Run Claim Review')}
                </button>
              </div>
            )}
            {isAnalyzed && (
              <>
                <div className="decision-form">
                  <textarea
                    placeholder="Investigation notes (optional) — these will be recorded in the audit trail…"
                    value={decisionNotes}
                    onChange={e => setDecisionNotes(e.target.value)}
                    rows={3}
                  />
                  <div className="decision-buttons">
                    <button className="btn-escalate" onClick={() => handleDecision('escalate')} disabled={deciding}>
                      Escalate to SIU
                    </button>
                    <button className="btn-genuine" onClick={() => handleDecision('genuine')} disabled={deciding}>
                      Clear as Genuine
                    </button>
                    <button className="btn-defer" onClick={() => handleDecision('defer')} disabled={deciding}>
                      Defer for Review
                    </button>
                  </div>
                </div>

                {claim.decisions && claim.decisions.length > 0 && (
                  <div className="decision-history">
                    <h4>Audit Trail</h4>
                    {claim.decisions.map((d, i) => (
                      <div key={i} className="decision-entry">
                        <div className="decision-action">{statusBadge(d.action)}</div>
                        <div className="decision-meta">
                          by {d.investigator_name || d.display_name || d.user_id} &middot; {d.decided_at}
                        </div>
                        {d.notes && <div className="decision-notes">{d.notes}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoCard({ label, value }) {
  return (
    <div className="info-card">
      <div className="info-label">{label}</div>
      <div className="info-value">{value}</div>
    </div>
  );
}

/* ───────────────────────── App Shell ───────────────────────── */

function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('landing'); // 'landing' | 'login' | 'dashboard' | 'upload' | 'detail'
  const [selectedClaimId, setSelectedClaimId] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('avia_session');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        fetch(`${API}/auth/me`, {
          headers: { 'Authorization': `Bearer ${parsed.token}` }
        })
          .then(r => { if (!r.ok) throw new Error('expired'); return r.json(); })
          .then(data => {
            setUser({ ...data, token: parsed.token });
            setView('dashboard');
            setAuthChecking(false);
          })
          .catch(() => { localStorage.removeItem('avia_session'); setAuthChecking(false); });
      } catch { localStorage.removeItem('avia_session'); setAuthChecking(false); }
    } else {
      setAuthChecking(false);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('avia_session', JSON.stringify({ token: userData.token }));
    setView('dashboard');
  };

  const handleLogout = () => {
    if (user?.token) {
      fetch(`${API}/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` }
      }).catch(() => {});
    }
    localStorage.removeItem('avia_session');
    setUser(null);
    setSelectedClaimId(null);
    setView('landing');
  };

  if (authChecking) return <div className="loading-screen"><div className="spinner" />Verifying session…</div>;

  // Landing page (not logged in, default view)
  if (!user && view !== 'login') {
    return <LandingPage onSignIn={() => setView('login')} />;
  }

  // Login screen
  if (!user) {
    return <LoginScreen onLogin={handleLogin} onBack={() => setView('landing')} />;
  }

  // Upload claim screen
  if (view === 'upload') {
    return (
      <div className="app-shell">
        <header className="top-nav">
          <div className="nav-left">
            <div className="nav-logo">
              <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
                <rect width="40" height="40" rx="10" fill="#4f46e5" />
                <path d="M12 28L20 12L28 28H12Z" fill="white" opacity="0.9" />
                <circle cx="20" cy="22" r="3" fill="#4f46e5" />
              </svg>
              <span className="nav-brand" onClick={() => setView('dashboard')} style={{ cursor: 'pointer' }}>
                Avia
              </span>
            </div>
            <span className="nav-org">{user.org_name}</span>
          </div>
          <div className="nav-right">
            <span className="nav-user">{user.display_name}</span>
            <span className="nav-role">{user.role}</span>
            <button className="btn-logout" onClick={handleLogout}>Sign Out</button>
          </div>
        </header>
        <main className="main-content">
          <UploadClaimScreen
            user={user}
            onDone={(claimId) => { setSelectedClaimId(claimId); setView('detail'); }}
            onCancel={() => setView('dashboard')}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {/* Top Nav */}
      <header className="top-nav">
        <div className="nav-left">
          <div className="nav-logo">
            <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="#4f46e5" />
              <path d="M12 28L20 12L28 28H12Z" fill="white" opacity="0.9" />
              <circle cx="20" cy="22" r="3" fill="#4f46e5" />
            </svg>
            <span className="nav-brand" onClick={() => { setSelectedClaimId(null); setView('dashboard'); }} style={{ cursor: 'pointer' }}>
              Avia
            </span>
          </div>
          <span className="nav-org">{user.org_name}</span>
        </div>
        <div className="nav-right">
          <span className="nav-user">{user.display_name}</span>
          <span className="nav-role">{user.role}</span>
          <button className="btn-logout" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {selectedClaimId ? (
          <ClaimDetail
            claimId={selectedClaimId}
            onBack={() => { setSelectedClaimId(null); setView('dashboard'); }}
            user={user}
          />
        ) : (
          <ClaimsList
            user={user}
            onSelect={(id) => { setSelectedClaimId(id); setView('detail'); }}
            onUploadClaim={() => setView('upload')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
