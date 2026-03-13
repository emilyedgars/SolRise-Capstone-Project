import React, { useState } from 'react';

const SR = {
    orange:      '#F7A14F',
    coral:       '#F07A63',
    white:       '#FFFFFF',
    gray:        'rgba(255,255,255,0.55)',
    border:      'rgba(247,161,79,0.15)',
    cardBg:      'rgba(247,161,79,0.06)',
    btnGradient: 'linear-gradient(135deg, #F7A14F 0%, #F07A63 100%)',
    btnShadow:   '0 4px 20px rgba(240,122,99,0.35)',
    font:        "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
    pill:        9999,
};

const AnalyzePanel = ({ state, setState, setPanel }) => {
    const [running, setRunning] = useState(false);
    const [step, setStep] = useState(0);
    const [logs, setLogs] = useState([]);

    const steps = [
        { label: 'Scraping Websites',     icon: '📥', dur: 2000 },
        { label: 'Preprocessing Text',    icon: '🔧', dur: 1500 },
        { label: 'TF-IDF Analysis',       icon: '📊', dur: 2000 },
        { label: 'Semantic Embeddings',   icon: '🧠', dur: 2500 },
        { label: 'GEO Analysis',          icon: '🤖', dur: 2000 },
        { label: 'Competitor Comparison', icon: '⚔️', dur: 1500 },
        { label: 'Generating Report',     icon: '📝', dur: 1000 },
    ];

    const run = async () => {
        if (!state.clientUrl || !state.clientName) { alert('Please fill in client URL and name'); return; }
        setRunning(true); setLogs([]);
        setStep(0);

        try {
            setLogs(prev => [...prev, '🚀 Starting analysis...']);

            // Start simulation of steps for UI feedback while waiting for API
            const stepInterval = setInterval(() => {
                setStep(s => {
                    if (s < steps.length - 1) return s + 1;
                    return s;
                });
            }, 2000);

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    clientUrl: state.clientUrl,
                    clientName: state.clientName,
                    location: state.location,
                    industry: state.industry,
                    competitors: state.competitors
                })
            });

            clearInterval(stepInterval);

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `Server error (${response.status})`);
            }

            const data = await response.json();

            setLogs(prev => [...prev, '✅ Analysis complete!']);
            setState(prev => ({ ...prev, results: data.results, projectId: data.project_id }));
            setStep(steps.length);
            setRunning(false);
            // setPanel('results'); // Removed auto-redirect to debug
        } catch (error) {
            console.error(error);
            const msg = error.name === 'TypeError' && error.message.includes('fetch')
                ? 'Cannot connect to backend server. Please ensure the Flask app is running.'
                : error.message;
            setLogs(prev => [...prev, '❌ Error: ' + msg]);
            setRunning(false);
            alert('Analysis Failed: ' + msg);
        }
    };

    const inputStyle = {
        width: '100%', padding: '0.9rem 1rem',
        background: SR.cardBg, border: `1px solid ${SR.border}`,
        borderRadius: 10, color: SR.white, fontSize: '0.95rem',
        boxSizing: 'border-box', fontFamily: SR.font, outline: 'none',
    };

    const labelStyle = { display: 'block', marginBottom: '0.5rem', color: SR.gray, fontSize: '0.9rem' };
    const sectionStyle = { marginBottom: '2rem', padding: '1.5rem', background: SR.cardBg, borderRadius: 15, border: `1px solid ${SR.border}` };

    return (
        <div style={{ color: SR.white, fontFamily: SR.font }}>
            <div style={{ marginBottom: '2rem', borderBottom: `1px solid ${SR.border}`, paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>🔍 New SEO/GEO Analysis</h1>
                <p style={{ color: SR.gray }}>Enter client and competitor information to run comprehensive analysis</p>
            </div>

            <div style={sectionStyle}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: SR.orange, marginBottom: '1rem' }}>Client Information</h3>

                <div style={{ marginBottom: '1rem' }}>
                    <label style={labelStyle}>Client Website URL *</label>
                    <input style={inputStyle} placeholder="https://client-website.com" value={state.clientUrl}
                        onChange={e => setState(prev => ({ ...prev, clientUrl: e.target.value }))} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    {[['Client Name *', 'clientName', 'Business Name'], ['Location', 'location', 'City, State'], ['Industry', 'industry', 'e.g., Dental']].map(([label, key, ph]) => (
                        <div key={key}>
                            <label style={labelStyle}>{label}</label>
                            <input style={inputStyle} placeholder={ph} value={state[key]} onChange={e => setState(prev => ({ ...prev, [key]: e.target.value }))} />
                        </div>
                    ))}
                </div>
            </div>

            <div style={sectionStyle}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: SR.orange, marginBottom: '1rem' }}>Competitor URLs</h3>
                {state.competitors.map((comp, i) => (
                    <div key={i} style={{ marginBottom: '1rem' }}>
                        <label style={labelStyle}>Competitor {i + 1}</label>
                        <input style={inputStyle} placeholder={`https://competitor${i + 1}.com`} value={comp}
                            onChange={e => { const c = [...state.competitors]; c[i] = e.target.value; setState(prev => ({ ...prev, competitors: c })); }} />
                    </div>
                ))}
                <button onClick={() => setState(prev => ({ ...prev, competitors: [...prev.competitors, ''] }))}
                    style={{
                        background: 'transparent', border: `1px dashed rgba(247,161,79,0.4)`, color: SR.orange,
                        padding: '0.75rem 1rem', borderRadius: 10, cursor: 'pointer', fontSize: '0.9rem',
                        width: '100%', marginTop: '0.5rem', fontFamily: SR.font,
                    }}>
                    + Add Competitor
                </button>
            </div>

            {running && (
                <div style={{ marginBottom: '2rem', padding: '1.5rem', background: 'rgba(247,161,79,0.07)', borderRadius: 15, border: `1px solid rgba(247,161,79,0.2)` }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: SR.orange, marginBottom: '1rem' }}>Analysis Progress</h3>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
                        {steps.map((s, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: i <= step ? 1 : 0.4 }}>
                                <div style={{
                                    width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '0.9rem',
                                    background: i < step ? SR.btnGradient : i === step ? SR.orange : 'rgba(255,255,255,0.08)',
                                }}>
                                    {i < step ? '✓' : s.icon}
                                </div>
                                <span style={{ fontSize: '0.85rem', color: SR.gray }}>{s.label}</span>
                            </div>
                        ))}
                    </div>
                    <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1rem', borderRadius: 10, maxHeight: 200, overflowY: 'auto', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {logs.map((log, i) => <div key={i} style={{ color: SR.gray, marginBottom: '0.25rem' }}>{log}</div>)}
                    </div>
                </div>
            )}

            {step === steps.length ? (
                <button onClick={() => setPanel('results')} style={{
                    background: SR.btnGradient, color: SR.white, padding: '1rem 2rem',
                    border: 'none', borderRadius: SR.pill, fontSize: '1rem', fontWeight: 700,
                    cursor: 'pointer', width: '100%', boxShadow: SR.btnShadow, fontFamily: SR.font,
                }}>
                    🎉 Analysis Complete — View Results
                </button>
            ) : (
                <button onClick={run} disabled={running} style={{
                    background: running ? 'rgba(247,161,79,0.3)' : SR.btnGradient, color: SR.white, padding: '1rem 2rem',
                    border: 'none', borderRadius: SR.pill, fontSize: '1rem', fontWeight: 700,
                    cursor: running ? 'default' : 'pointer', width: '100%',
                    boxShadow: running ? 'none' : SR.btnShadow, fontFamily: SR.font,
                }}>
                    {running ? '⏳ Running Analysis...' : '✦ Run Full SEO/GEO Analysis'}
                </button>
            )}
        </div>
    );
};

export default AnalyzePanel;
