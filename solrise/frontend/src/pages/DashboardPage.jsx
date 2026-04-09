import React, { useState } from 'react';
import AnalyzePanel    from '../dashboard/AnalyzePanel';
import ResultsPanel    from '../dashboard/ResultsPanel';
import GeneratePanel   from '../dashboard/GeneratePanel';
import GEOPanel        from '../dashboard/GEOPanel';
import ValidationPanel from '../dashboard/ValidationPanel';
import ProjectsPanel   from '../dashboard/ProjectsPanel';
import SettingsPanel   from '../dashboard/SettingsPanel';

const SR = {
    orange:      '#F7A14F',
    coral:       '#F07A63',
    dark:        '#1A1A2E',
    white:       '#FFFFFF',
    btnGradient: 'linear-gradient(135deg, #F7A14F 0%, #F07A63 100%)',
    font:        "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
    pill:        9999,
};

const SidebarLogo = () => (
    <img
        src="/solrise-logo.png"
        alt="SolRise"
        style={{ height: 64, width: 'auto', objectFit: 'contain', display: 'block' }}
    />
);

const NAV_ITEMS = [
    { icon: '🔍', label: 'New Analysis',     key: 'analyze'    },
    { icon: '📊', label: 'View Results',     key: 'results'    },
    { icon: '⚡', label: 'Generate Website', key: 'generate'   },
    { icon: '📈', label: 'GEO Analyser',     key: 'geo'        },
    { icon: '🔄', label: 'Validation Loop',  key: 'validation' },
    { icon: '📁', label: 'Projects',         key: 'projects'   },
    { icon: '⚙️', label: 'Settings',         key: 'settings'   },
];

const PASSCODE = '1212';

const DashboardPage = ({ setActiveTab }) => {
    const [panel,    setPanel]    = useState('analyze');
    const [analysis, setAnalysis] = useState({
        clientUrl: '', competitors: ['', '', ''],
        clientName: '', location: '', industry: '',
        results: null, projectId: null,
    });
    const [unlocked,  setUnlocked]  = useState(false);
    const [input,     setInput]     = useState('');
    const [error,     setError]     = useState(false);

    const handleLogin = () => {
        if (input === PASSCODE) {
            setUnlocked(true);
            setError(false);
        } else {
            setError(true);
            setInput('');
        }
    };

    if (!unlocked) {
        return (
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                minHeight: '100vh', background: '#0F0F1A', fontFamily: SR.font,
            }}>
                <div style={{
                    background: '#1A1A2E', borderRadius: 20, padding: '3rem 2.5rem',
                    border: '1px solid rgba(247,161,79,0.15)', textAlign: 'center',
                    width: '100%', maxWidth: 360,
                }}>
                    <img src="/solrise-logo.png" alt="SolRise" style={{ height: 56, marginBottom: '1.5rem' }} />
                    <h2 style={{ color: SR.white, fontWeight: 700, fontSize: '1.3rem', marginBottom: '0.4rem' }}>
                        Internal Tools
                    </h2>
                    <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', marginBottom: '2rem' }}>
                        Enter your passcode to continue
                    </p>
                    <input
                        type="password"
                        value={input}
                        onChange={e => { setInput(e.target.value); setError(false); }}
                        onKeyDown={e => e.key === 'Enter' && handleLogin()}
                        placeholder="Passcode"
                        style={{
                            width: '100%', padding: '0.85rem 1rem', borderRadius: 10,
                            border: `1px solid ${error ? SR.coral : 'rgba(247,161,79,0.2)'}`,
                            background: 'rgba(255,255,255,0.05)', color: SR.white,
                            fontSize: '1rem', fontFamily: SR.font, marginBottom: '0.75rem',
                            outline: 'none', boxSizing: 'border-box', textAlign: 'center',
                            letterSpacing: '0.3em',
                        }}
                        autoFocus
                    />
                    {error && (
                        <p style={{ color: SR.coral, fontSize: '0.82rem', marginBottom: '0.75rem' }}>
                            Incorrect passcode. Try again.
                        </p>
                    )}
                    <button onClick={handleLogin} style={{
                        width: '100%', background: SR.btnGradient, color: SR.white,
                        border: 'none', borderRadius: 10, padding: '0.85rem',
                        fontSize: '1rem', fontWeight: 700, cursor: 'pointer', fontFamily: SR.font,
                    }}>
                        Unlock →
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#0F0F1A', fontFamily: SR.font }}>

            {/* ── Sidebar ─────────────────────────────────────────── */}
            <aside style={{
                width: 256,
                background: 'linear-gradient(180deg, #1A1A2E 0%, #12121F 100%)',
                color: SR.white,
                position: 'fixed', height: '100vh',
                borderRight: '1px solid rgba(247,161,79,0.12)',
                display: 'flex', flexDirection: 'column',
            }}>
                {/* Logo */}
                <div style={{
                    padding: '1.25rem 1.5rem',
                    borderBottom: '1px solid rgba(247,161,79,0.1)',
                    display: 'flex', flexDirection: 'column', gap: '0.5rem',
                }}>
                    <SidebarLogo />
                    <span style={{ fontSize: '0.72rem', color: 'rgba(247,161,79,0.5)' }}>
                        Internal Tools
                    </span>
                </div>

                {/* Nav */}
                <nav style={{ flex: 1, padding: '0.75rem 0' }}>
                    {NAV_ITEMS.map(item => {
                        const active = panel === item.key;
                        return (
                            <button key={item.key} onClick={() => setPanel(item.key)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                                    padding: '0.85rem 1.5rem', color: active ? SR.white : 'rgba(255,255,255,0.55)',
                                    border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer',
                                    background: active ? 'rgba(247,161,79,0.12)' : 'transparent',
                                    borderLeft: `3px solid ${active ? SR.orange : 'transparent'}`,
                                    fontSize: '0.92rem', fontWeight: active ? 600 : 400,
                                    transition: 'all 0.2s ease', fontFamily: SR.font,
                                }}>
                                <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
                                <span>{item.label}</span>
                            </button>
                        );
                    })}
                </nav>

                {/* Footer */}
                <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid rgba(247,161,79,0.1)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)' }}>
                        <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#27ae60', boxShadow: '0 0 6px #27ae60', flexShrink: 0 }} />
                        APIs Connected
                    </div>
                    {setActiveTab && (
                        <button onClick={() => setActiveTab('home')} style={{
                            background: 'transparent', border: '1px solid rgba(247,161,79,0.2)',
                            color: 'rgba(255,255,255,0.45)', borderRadius: 8, padding: '0.5rem 0.75rem',
                            fontSize: '0.78rem', cursor: 'pointer', fontFamily: SR.font, textAlign: 'left',
                        }}>
                            ← Back to website
                        </button>
                    )}
                </div>
            </aside>

            {/* ── Main content ────────────────────────────────────── */}
            <main style={{ flex: 1, marginLeft: 256, padding: '2rem', overflowY: 'auto' }}>
                <div style={{
                    background: '#1A1A2E', borderRadius: 20, padding: '2rem',
                    minHeight: 'calc(100vh - 4rem)',
                    border: '1px solid rgba(247,161,79,0.08)',
                }}>
                    {panel === 'analyze'    && <AnalyzePanel    state={analysis} setState={setAnalysis} setPanel={setPanel} />}
                    {panel === 'results'    && <ResultsPanel    results={analysis.results} />}
                    {panel === 'generate'   && <GeneratePanel   results={analysis.results} projectId={analysis.projectId} info={{ name: analysis.clientName, location: analysis.location, industry: analysis.industry }} />}
                    {panel === 'geo'        && <GEOPanel />}
                    {panel === 'validation' && <ValidationPanel projectId={analysis.projectId} results={analysis.results} />}
                    {panel === 'projects'   && <ProjectsPanel   setAnalysis={setAnalysis} setPanel={setPanel} />}
                    {panel === 'settings'   && <SettingsPanel />}
                </div>
            </main>
        </div>
    );
};

export default DashboardPage;
