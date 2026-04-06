import { useState, useEffect } from 'react';

const ValidationPanel = ({ projectId, results }) => {
    const [validating, setValidating] = useState(false);
    const [iterations, setIterations] = useState([]);
    const [seoBefore, setSeoBefore] = useState(null);
    const [geoBefore, setGeoBefore] = useState(null);
    const [hasHtml, setHasHtml] = useState(false);
    const [error, setError] = useState('');

    // Load saved validation results from MongoDB on mount
    useEffect(() => {
        if (!projectId) return;
        fetch(`/api/project/${projectId}`)
            .then(r => r.json())
            .then(data => {
                if (data.generated_html) setHasHtml(true);
                if (data.validation_loop?.length) {
                    setIterations(data.validation_loop);
                    setSeoBefore(data.results?.seoScore ?? data.results?.seo_score ?? null);
                    setGeoBefore(data.results?.geoScore ?? data.results?.geo_score ?? null);
                }
            })
            .catch(() => {});
    }, [projectId]);

    const run = async () => {
        if (!projectId) { setError('No project found. Run analysis first.'); return; }
        setValidating(true); setError(''); setIterations([]);
        try {
            const res = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId }),
            });
            const data = await res.json();
            if (!res.ok) { setError(data.error || 'Validation failed'); setValidating(false); return; }
            setIterations(data.iterations || []);
            setSeoBefore(data.seo_before);
            setGeoBefore(data.geo_before);
        } catch (e) {
            setError(e.message);
        }
        setValidating(false);
    };

    // Build before/after table from real results + last iteration
    const lastIter = iterations[iterations.length - 1];
    const beforeAfter = [
        {
            metric: 'SEO Score',
            before: seoBefore != null ? (seoBefore <= 1 ? (seoBefore * 100).toFixed(0) + '%' : seoBefore + '%') : '—',
            after: lastIter ? (lastIter.seo * 100).toFixed(0) + '%' : '—',
            improvement: seoBefore != null && lastIter ? '+' + ((lastIter.seo - seoBefore) * 100).toFixed(0) + '%' : '—',
        },
        {
            metric: 'GEO Score',
            before: geoBefore != null ? (geoBefore <= 1 ? (geoBefore * 100).toFixed(0) + '%' : geoBefore + '%') : '—',
            after: lastIter ? (lastIter.geo * 100).toFixed(0) + '%' : '—',
            improvement: geoBefore != null && lastIter ? '+' + ((lastIter.geo - geoBefore) * 100).toFixed(0) + '%' : '—',
        },
    ];

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>🔄 Agentic Validation Loop</h1>
                <p style={{ color: '#95a5a6' }}>Iteratively validates generated HTML against SEO/GEO targets and saves results</p>
            </div>

            {/* Before / After Comparison Table — only shown after a validation run */}
            {iterations.length > 0 && (
                <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 14, padding: '1.5rem', marginBottom: '2rem' }}>
                    <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600, color: '#95a5a6', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Post-Generation Score Improvements
                    </h3>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.92rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                                {['Metric', 'Before', 'After', 'Improvement'].map(h => (
                                    <th key={h} style={{ padding: '0.6rem 1rem', textAlign: h === 'Metric' ? 'left' : 'center', color: '#95a5a6', fontWeight: 600, fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {beforeAfter.map((row, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                    <td style={{ padding: '0.75rem 1rem', color: 'white', fontWeight: 500 }}>{row.metric}</td>
                                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', color: '#95a5a6' }}>{row.before}</td>
                                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', color: '#F7A14F', fontWeight: 600 }}>{row.after}</td>
                                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                                        <span style={{ background: 'rgba(247,161,79,0.12)', color: '#F7A14F', padding: '0.2rem 0.65rem', borderRadius: 20, fontWeight: 700, fontSize: '0.85rem' }}>{row.improvement}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Status / error */}
            {!hasHtml && projectId && (
                <div style={{ background: 'rgba(243,156,18,0.08)', border: '1px solid rgba(243,156,18,0.25)', borderRadius: 12, padding: '1rem', marginBottom: '1rem', color: '#f39c12', fontSize: '0.9rem' }}>
                    ⚠️ No generated website found for this project. Go to <b>Generate</b> tab first.
                </div>
            )}
            {error && (
                <div style={{ background: 'rgba(231,76,60,0.1)', border: '1px solid rgba(231,76,60,0.3)', borderRadius: 12, padding: '1rem', marginBottom: '1rem', color: '#e74c3c', fontSize: '0.9rem' }}>
                    ❌ {error}
                </div>
            )}

            <button onClick={run} disabled={validating || !hasHtml}
                style={{
                    background: 'linear-gradient(135deg, #F7A14F, #F07A63)', color: 'white', padding: '1rem 2rem',
                    border: 'none', borderRadius: 12, fontSize: '1rem', fontWeight: 600,
                    cursor: validating || !hasHtml ? 'not-allowed' : 'pointer',
                    opacity: validating || !hasHtml ? 0.6 : 1,
                    width: '100%', marginBottom: '2rem',
                }}>
                {validating ? '🔄 Running Validation Loop...' : '🚀 Run Validation Loop'}
            </button>

            {/* Iteration results */}
            {iterations.length > 0 && (
                <div>
                    <h3 style={{ color: '#95a5a6', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
                        Validation Results — {iterations.length} iteration{iterations.length > 1 ? 's' : ''}
                    </h3>
                    {iterations.map((iter, i) => (
                        <div key={i} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', padding: '1.25rem 1.5rem', borderRadius: 12, marginBottom: '0.75rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                                <span style={{ color: '#F7A14F', fontWeight: 700 }}>Iteration {iter.iteration}</span>
                                <span style={{ fontSize: '1.4rem', fontWeight: 700, color: iter.overall >= 0.8 ? '#27ae60' : '#F7A14F' }}>
                                    {(iter.overall * 100).toFixed(0)}%
                                </span>
                            </div>
                            <div style={{ display: 'flex', gap: '1.5rem', color: '#95a5a6', fontSize: '0.88rem', marginBottom: '0.75rem' }}>
                                <span>SEO: <b style={{ color: 'white' }}>{(iter.seo * 100).toFixed(0)}%</b></span>
                                <span>GEO: <b style={{ color: 'white' }}>{(iter.geo * 100).toFixed(0)}%</b></span>
                                {iter.score != null && <span>HTML Score: <b style={{ color: 'white' }}>{iter.score}%</b></span>}
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                                {(iter.feedback || []).map((f, j) => (
                                    <span key={j} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.3rem 0.7rem', borderRadius: 20, fontSize: '0.8rem', color: '#95a5a6' }}>{f}</span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ValidationPanel;
