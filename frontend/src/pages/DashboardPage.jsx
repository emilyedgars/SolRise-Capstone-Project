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

// SolRise logo for sidebar (uses real PNG)
const SidebarLogo = () => (
    <img
        src="/solrise-logo.png"
        alt="SolRise"
        style={{ height: 36, width: 'auto', objectFit: 'contain', display: 'block' }}
    />
);

const NAV_ITEMS = [
    { icon: '🔍', label: 'New Analysis',      key: 'analyze'    },
    { icon: '📊', label: 'View Results',       key: 'results'    },
    { icon: '⚡', label: 'Generate Website',   key: 'generate'   },
    { icon: '📈', label: 'GEO Analyser',       key: 'geo'        },
    { icon: '🔄', label: 'Validation Loop',    key: 'validation' },
    { icon: '📁', label: 'Projects',           key: 'projects'   },
    { icon: '⚙️', label: 'Settings',           key: 'settings'   },
];

const DashboardPage = ({ setActiveTab }) => {
    const [panel,    setPanel]    = useState('analyze');
    const [analysis, setAnalysis] = useState({
        clientUrl: '', competitors: ['', '', ''],
        clientName: '', location: '', industry: '',
        results: null, projectId: null,
    });

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
                    {panel === 'validation' && <ValidationPanel />}
                    {panel === 'projects'   && <ProjectsPanel   setAnalysis={setAnalysis} setPanel={setPanel} />}
                    {panel === 'settings'   && <SettingsPanel />}
                </div>
            </main>
        </div>
    );
};

export default DashboardPage;
