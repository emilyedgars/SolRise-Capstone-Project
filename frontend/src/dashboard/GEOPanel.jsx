import React, { useState } from 'react';

const GEOPanel = () => {
    const [url, setUrl] = useState('');
    const [analyzing, setAnalyzing] = useState(false);
    const [results, setResults] = useState(null);

    const analyze = async () => {
        if (!url) return;
        setAnalyzing(true);

        try {
            const response = await fetch('/api/geo-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();

            // Transform API response to UI format if needed
            // Assuming API returns { geo_score: 0.x, components: [...] }
            setResults({
                score: Math.round(data.geo_score * 100),
                checklist: data.components.map(c => ({
                    label: c.name,
                    pass: c.score > 0.6,
                    count: `${Math.round(c.score * 10)}/10 score`
                }))
            });

        } catch (error) {
            console.error(error);
            alert('Error passing URL');
        }

        setAnalyzing(false);
    };

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>🤖 GEO Analyzer</h1>
                <p style={{ color: '#95a5a6' }}>Analyze any URL for Generative Engine Optimization readiness</p>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
                <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Enter URL to analyze..."
                    style={{ flex: 1, padding: '0.9rem 1rem', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: 'white', fontSize: '0.95rem' }} />
                <button onClick={analyze} disabled={analyzing}
                    style={{ background: 'linear-gradient(135deg, #4ECDC4, #44A08D)', color: 'white', padding: '0.9rem 1.5rem', border: 'none', borderRadius: 10, cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap' }}>
                    {analyzing ? '⏳' : '🔍'} Analyze
                </button>
            </div>

            {results && (
                <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '2rem' }}>
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            width: 200, height: 200, borderRadius: '50%', margin: '0 auto 1rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: `conic-gradient(#4ECDC4 0deg, #4ECDC4 ${3.6 * results.score}deg, #34495e ${3.6 * results.score}deg, #34495e 360deg)`
                        }}>
                            <div style={{ width: 160, height: 160, borderRadius: '50%', background: '#242b3d', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '3rem', fontWeight: 700 }}>
                                {results.score}
                            </div>
                        </div>
                        <div style={{ marginTop: '1rem', fontSize: '1.2rem', fontWeight: 600 }}>
                            {results.score >= 75 ? '✅ Good' : results.score >= 50 ? '⚠️ Needs Improvement' : '❌ Poor'}
                        </div>
                    </div>

                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15 }}>
                        <h4 style={{ marginBottom: '1rem' }}>GEO Checklist</h4>
                        {results.checklist.map((item, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                <span style={{ color: item.pass ? '#4ECDC4' : '#e74c3c' }}>{item.pass ? '✓' : '✗'}</span>
                                <span>{item.label}</span>
                                <span style={{ marginLeft: 'auto', color: '#95a5a6', fontSize: '0.85rem' }}>{item.count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default GEOPanel;
