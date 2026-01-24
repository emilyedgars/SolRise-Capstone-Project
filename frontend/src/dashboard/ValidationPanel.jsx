import React, { useState } from 'react';

const ValidationPanel = () => {
    const [html, setHtml] = useState('');
    const [validating, setValidating] = useState(false);
    const [iterations, setIterations] = useState([]);

    const run = async () => {
        setValidating(true); setIterations([]);
        // Mock validation loop as we don't have a direct backend endpoint for "just validation loop" separated from generation yet
        // In a real app, this would call an endpoint that parses and validates HTML
        for (let i = 1; i <= 3; i++) {
            await new Promise(r => setTimeout(r, 2000));
            setIterations(prev => [...prev, {
                iteration: i, overall: 0.6 + (i * 0.08), seo: 0.65 + (i * 0.07), geo: 0.55 + (i * 0.1),
                feedback: i < 3 ? ['Add more quotables', 'Include schema', 'Improve entities'] : ['All targets met!']
            }]);
        }
        setValidating(false);
    };

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>🔄 Agentic Validation Loop</h1>
                <p style={{ color: '#95a5a6' }}>Iteratively improve generated HTML until SEO/GEO targets are met</p>
            </div>

            <textarea value={html} onChange={e => setHtml(e.target.value)} placeholder="Paste your generated HTML here..."
                style={{
                    width: '100%', minHeight: 200, padding: '1rem', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 12, color: 'white', fontFamily: 'monospace', fontSize: '0.85rem', resize: 'vertical', boxSizing: 'border-box', marginBottom: '1rem'
                }} />

            <button onClick={run} disabled={validating || !html}
                style={{
                    background: 'linear-gradient(135deg, #4ECDC4, #44A08D)', color: 'white', padding: '1rem 2rem',
                    border: 'none', borderRadius: 12, fontSize: '1rem', fontWeight: 600, cursor: 'pointer', width: '100%', marginBottom: '2rem'
                }}>
                {validating ? '🔄 Running Validation Loop...' : '🚀 Start Validation Loop'}
            </button>

            {iterations.length > 0 && iterations.map((iter, i) => (
                <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 12, marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ color: '#4ECDC4', fontWeight: 600 }}>Iteration {iter.iteration}</span>
                        <span style={{ fontSize: '1.5rem', fontWeight: 700, color: iter.overall >= 0.8 ? '#4ECDC4' : '#f39c12' }}>{(iter.overall * 100).toFixed(0)}%</span>
                    </div>
                    <div style={{ display: 'flex', gap: '1.5rem', color: '#95a5a6', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                        <span>SEO: {(iter.seo * 100).toFixed(0)}%</span>
                        <span>GEO: {(iter.geo * 100).toFixed(0)}%</span>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {iter.feedback.map((f, j) => (
                            <span key={j} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.35rem 0.75rem', borderRadius: 20, fontSize: '0.8rem', color: '#95a5a6' }}>{f}</span>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default ValidationPanel;
