import React, { useState } from 'react';
import AnalyzePanel from '../dashboard/AnalyzePanel';
import ResultsPanel from '../dashboard/ResultsPanel';
import GeneratePanel from '../dashboard/GeneratePanel';
import GEOPanel from '../dashboard/GEOPanel';
import ValidationPanel from '../dashboard/ValidationPanel';
import ProjectsPanel from '../dashboard/ProjectsPanel';
import SettingsPanel from '../dashboard/SettingsPanel';

const DashboardPage = () => {
    const [panel, setPanel] = useState('analyze');
    const [analysis, setAnalysis] = useState({ clientUrl: '', competitors: ['', '', ''], clientName: '', location: '', industry: '', results: null, projectId: null });

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#1a1f2e' }}>
            {/* Sidebar */}
            <aside style={{
                width: 260, background: 'linear-gradient(180deg, #2C3E50 0%, #1a252f 100%)', color: 'white',
                position: 'fixed', height: '100vh', borderRight: '1px solid rgba(78, 205, 196, 0.1)'
            }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'center' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🌊</div>
                    <span style={{ display: 'block', fontSize: '1.2rem', fontWeight: 700 }}>Atlantic Digital</span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#4ECDC4', marginTop: '0.25rem' }}>Internal Tools</span>
                </div>

                <nav style={{ flex: 1, padding: '1rem 0' }}>
                    {[
                        { icon: '🔍', label: 'New Analysis', key: 'analyze' },
                        { icon: '📊', label: 'View Results', key: 'results' },
                        { icon: '⚡', label: 'Generate Website', key: 'generate' },
                        { icon: '📈', label: 'GEO Analyzer', key: 'geo' },
                        { icon: '🔄', label: 'Validation Loop', key: 'validation' },
                        { icon: '📁', label: 'Projects', key: 'projects' },
                        { icon: '⚙️', label: 'Settings', key: 'settings' }
                    ].map(item => (
                        <button key={item.key} onClick={() => setPanel(item.key)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.9rem 1.5rem',
                                color: 'white', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer',
                                background: panel === item.key ? 'rgba(255,255,255,0.15)' : 'transparent',
                                borderLeft: panel === item.key ? '3px solid #4ECDC4' : '3px solid transparent',
                                fontSize: '0.95rem', transition: 'all 0.2s ease'
                            }}>
                            <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                            <span>{item.label}</span>
                        </button>
                    ))}
                </nav>

                <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#95a5a6' }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#4ECDC4' }} />
                        APIs Connected
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main style={{ flex: 1, marginLeft: 260, padding: '2rem', overflowY: 'auto' }}>
                <div style={{ background: '#242b3d', borderRadius: 20, padding: '2rem', minHeight: 'calc(100vh - 4rem)' }}>
                    {panel === 'analyze' && <AnalyzePanel state={analysis} setState={setAnalysis} setPanel={setPanel} />}
                    {panel === 'results' && <ResultsPanel results={analysis.results} />}
                    {panel === 'generate' && <GeneratePanel results={analysis.results} projectId={analysis.projectId} info={{ name: analysis.clientName, location: analysis.location, industry: analysis.industry }} />}
                    {panel === 'geo' && <GEOPanel />}
                    {panel === 'validation' && <ValidationPanel />}
                    {panel === 'projects' && <ProjectsPanel setAnalysis={setAnalysis} setPanel={setPanel} />}
                    {panel === 'settings' && <SettingsPanel />}
                </div>
            </main>
        </div>
    );
};

export default DashboardPage;
