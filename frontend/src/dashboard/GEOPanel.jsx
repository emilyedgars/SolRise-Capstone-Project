import React, { useState } from 'react';

const GEOPanel = () => {
    const [url, setUrl] = useState('');
    const [analyzing, setAnalyzing] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const analyze = async () => {
        if (!url) return;
        setAnalyzing(true);
        setError('');
        setResults(null);

        try {
            const response = await fetch('/api/geo-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                setError(data.error || 'Analysis failed');
                setAnalyzing(false);
                return;
            }

            const m = data.metrics || {};
            setResults({
                score: Math.round((data.score || 0) * 100),
                url: data.url,
                checklist: [
                    { label: 'Extractability', pass: (m.extractability || 0) >= 0.6, value: m.extractability || 0, tip: 'Content structured for AI extraction' },
                    { label: 'Citability', pass: (m.citability || 0) >= 0.6, value: m.citability || 0, tip: 'Quotable statements & statistics' },
                    { label: 'Claim Density', pass: (m.claimDensity || 0) >= 4, value: m.claimDensity || 0, tip: 'Factual claims per 100 words (target: 4+)', raw: true },
                    { label: 'AI Coverage Prediction', pass: (m.coveragePrediction || 0) >= 50, value: m.coveragePrediction || 0, tip: 'Likelihood of AI citation (%)', raw: true },
                ]
            });

        } catch (e) {
            setError('Could not reach the server. Make sure the backend is running.');
        }

        setAnalyzing(false);
    };

    const scoreColor = (s) => s >= 75 ? '#F7A14F' : s >= 50 ? '#f39c12' : '#e74c3c';

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>🤖 GEO Analyzer</h1>
                <p style={{ color: '#95a5a6' }}>Analyze any URL for Generative Engine Optimization readiness</p>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                <input
                    value={url}
                    onChange={e => setUrl(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && analyze()}
                    placeholder="https://example.com"
                    style={{ flex: 1, padding: '0.9rem 1rem', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: 'white', fontSize: '0.95rem' }}
                />
                <button onClick={analyze} disabled={analyzing || !url}
                    style={{ background: 'linear-gradient(135deg, #F7A14F, #F07A63)', color: 'white', padding: '0.9rem 1.5rem', border: 'none', borderRadius: 10, cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap', opacity: (!url || analyzing) ? 0.6 : 1 }}>
                    {analyzing ? '⏳ Analyzing...' : '🔍 Analyze'}
                </button>
            </div>

            {error && (
                <div style={{ background: 'rgba(231,76,60,0.15)', border: '1px solid rgba(231,76,60,0.4)', borderRadius: 10, padding: '1rem', marginBottom: '1rem', color: '#e74c3c' }}>
                    {error}
                </div>
            )}

            {results && (
                <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '2rem', marginTop: '1rem' }}>
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            width: 200, height: 200, borderRadius: '50%', margin: '0 auto 1rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: `conic-gradient(${scoreColor(results.score)} 0deg, ${scoreColor(results.score)} ${3.6 * results.score}deg, #34495e ${3.6 * results.score}deg, #34495e 360deg)`
                        }}>
                            <div style={{ width: 160, height: 160, borderRadius: '50%', background: '#242b3d', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                <span style={{ fontSize: '2.8rem', fontWeight: 700, color: scoreColor(results.score) }}>{results.score}</span>
                                <span style={{ fontSize: '0.8rem', color: '#95a5a6' }}>/ 100</span>
                            </div>
                        </div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 600, color: scoreColor(results.score) }}>
                            {results.score >= 75 ? '✅ GEO Ready' : results.score >= 50 ? '⚠️ Needs Work' : '❌ Poor GEO Score'}
                        </div>
                        <div style={{ color: '#95a5a6', fontSize: '0.8rem', marginTop: '0.5rem', wordBreak: 'break-all' }}>{results.url}</div>
                    </div>

                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15 }}>
                        <h4 style={{ marginBottom: '1.25rem', color: '#F7A14F' }}>GEO Breakdown</h4>
                        {results.checklist.map((item, i) => (
                            <div key={i} style={{ marginBottom: '1.25rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ color: item.pass ? '#F7A14F' : '#e74c3c', fontSize: '1rem' }}>{item.pass ? '✓' : '✗'}</span>
                                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.label}</span>
                                    </div>
                                    <span style={{ color: item.pass ? '#F7A14F' : '#e74c3c', fontWeight: 700 }}>
                                        {item.raw ? item.value : `${Math.round(item.value * 100)}%`}
                                    </span>
                                </div>
                                {!item.raw && (
                                    <div style={{ height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden', marginBottom: '0.25rem' }}>
                                        <div style={{ height: '100%', borderRadius: 3, width: `${item.value * 100}%`, background: item.pass ? '#F7A14F' : '#e74c3c', transition: 'width 0.8s ease' }} />
                                    </div>
                                )}
                                <p style={{ color: '#95a5a6', fontSize: '0.8rem', margin: 0 }}>{item.tip}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default GEOPanel;
