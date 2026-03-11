import React, { useState } from 'react';

const AnalyzerPage = () => {
    const [step, setStep] = useState('form'); // form | loading | results
    const [clientUrl, setClientUrl] = useState('');
    const [clientName, setClientName] = useState('');
    const [location, setLocation] = useState('');
    const [industry, setIndustry] = useState('');
    const [phone, setPhone] = useState('');
    const [goal, setGoal] = useState('both');
    const [message, setMessage] = useState('');
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');
    const [downloading, setDownloading] = useState(false);
    const [progress, setProgress] = useState('Scraping websites...');

    const runAnalysis = async () => {
        if (!clientUrl) { setError('Please enter your website URL.'); return; }
        setError('');
        setStep('loading');

        const progressSteps = [
            'Scraping your website...',
            'Extracting keywords with TF-IDF...',
            'Running GEO analysis...',
            'Checking AI readiness...',
            'Generating recommendations...',
        ];
        let pi = 0;
        const progressTimer = setInterval(() => {
            pi = (pi + 1) % progressSteps.length;
            setProgress(progressSteps[pi]);
        }, 4000);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    clientUrl,
                    clientName: clientName || clientUrl,
                    location,
                    industry,
                    competitors: [],
                    contactPhone: phone,
                    contactGoal: goal,
                    contactMessage: message,
                })
            });

            clearInterval(progressTimer);
            const data = await response.json();

            if (!response.ok || data.error) {
                setError(data.error || 'Analysis failed. Please try again.');
                setStep('form');
                return;
            }

            setResults(data.results || data);
            setStep('results');
        } catch (e) {
            clearInterval(progressTimer);
            setError('Could not reach the server. Please try again later.');
            setStep('form');
        }
    };

    const downloadPDF = async () => {
        setDownloading(true);
        try {
            const response = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ results, mode: 'teaser' })
            });
            if (!response.ok) throw new Error('PDF generation failed');
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `seo_geo_preview_${(clientName || 'report').replace(/\s+/g, '_').toLowerCase()}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert('PDF download failed: ' + e.message);
        }
        setDownloading(false);
    };

    const scoreColor = (v) => {
        const f = parseFloat(v) || 0;
        if (f >= 0.7) return '#27ae60';
        if (f >= 0.5) return '#f39c12';
        return '#e74c3c';
    };

    const inputStyle = {
        width: '100%', padding: '0.85rem 1rem', borderRadius: 10, fontSize: '0.95rem',
        border: '1.5px solid #dde1e7', background: '#fafbfc', color: '#2C3E50',
        boxSizing: 'border-box', outline: 'none',
    };

    const labelStyle = { display: 'block', marginBottom: '0.4rem', fontWeight: 600, color: '#4A6B7C', fontSize: '0.9rem' };

    if (step === 'loading') return (
        <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#F7F4F0' }}>
            <div style={{ textAlign: 'center', maxWidth: 480 }}>
                <div style={{ fontSize: '3.5rem', marginBottom: '1.5rem' }}>🔍</div>
                <h2 style={{ color: '#2C3E50', marginBottom: '0.75rem', fontSize: '1.6rem' }}>Analyzing your website</h2>
                <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>{progress}</p>
                <div style={{ background: '#e0e0e0', borderRadius: 99, height: 6, overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: 'linear-gradient(90deg, #4ECDC4, #44A08D)', borderRadius: 99, animation: 'slide 2s ease-in-out infinite', width: '60%' }} />
                </div>
                <p style={{ color: '#bdc3c7', fontSize: '0.85rem', marginTop: '1.5rem' }}>This usually takes 30–60 seconds</p>
            </div>
            <style>{`@keyframes slide { 0%{margin-left:-60%} 100%{margin-left:100%} }`}</style>
        </div>
    );

    if (step === 'results' && results) return (
        <div style={{ background: '#F7F4F0', minHeight: '100vh', paddingTop: 100, paddingBottom: 60 }}>
            <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 style={{ color: '#2C3E50', fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>Your SEO/GEO Report Preview</h1>
                        <p style={{ color: '#7f8c8d' }}>{results.clientName || clientName}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <button onClick={downloadPDF} disabled={downloading} style={{
                            background: 'linear-gradient(135deg, #e74c3c, #c0392b)', color: 'white',
                            padding: '0.75rem 1.5rem', border: 'none', borderRadius: 10,
                            cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem', opacity: downloading ? 0.7 : 1
                        }}>
                            {downloading ? '⏳ Generating...' : '📄 Download Preview PDF'}
                        </button>
                        <button onClick={() => { setStep('form'); setResults(null); }} style={{
                            background: 'transparent', color: '#4A6B7C', padding: '0.75rem 1.5rem',
                            border: '1.5px solid #4A6B7C', borderRadius: 10, cursor: 'pointer', fontWeight: 600
                        }}>
                            ← New Analysis
                        </button>
                    </div>
                </div>

                {/* Score cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                    {[
                        { label: 'Overall Score', val: results.overallScore, icon: '⭐' },
                        { label: 'SEO Score',     val: results.seoScore,     icon: '🔍' },
                        { label: 'GEO Score',     val: results.geoScore,     icon: '🤖' },
                        { label: 'Competitive',   val: results.competitiveScore, icon: '⚔️' },
                    ].map((s, i) => (
                        <div key={i} style={{ background: 'white', borderRadius: 14, padding: '1.25rem', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{s.icon}</div>
                            <div style={{ fontSize: '2rem', fontWeight: 700, color: scoreColor(s.val) }}>{Math.round((s.val||0)*100)}%</div>
                            <div style={{ color: '#7f8c8d', fontSize: '0.85rem', marginTop: '0.25rem' }}>{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Keyword gaps */}
                {results.keywordGaps?.length > 0 && (
                    <div style={{ background: 'white', borderRadius: 14, padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                        <h3 style={{ color: '#2C3E50', marginBottom: '1rem' }}>🔑 Top Keyword Opportunities</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {results.keywordGaps.slice(0, 5).map((g, i) => (
                                <span key={i} style={{
                                    padding: '0.4rem 0.9rem', borderRadius: 20, fontSize: '0.85rem', fontWeight: 600,
                                    background: g.priority === 'high' ? '#fdecea' : '#eaf4fb',
                                    color: g.priority === 'high' ? '#c0392b' : '#2980b9',
                                    border: `1px solid ${g.priority === 'high' ? '#f5c6cb' : '#bee3f8'}`
                                }}>
                                    {g.keyword}
                                </span>
                            ))}
                            {results.keywordGaps.length > 5 && (
                                <span style={{ padding: '0.4rem 0.9rem', borderRadius: 20, fontSize: '0.85rem', background: '#f4f6f7', color: '#95a5a6', border: '1px solid #dde1e7' }}>
                                    +{results.keywordGaps.length - 5} more in full report
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Recommendations preview */}
                {results.recommendations?.length > 0 && (
                    <div style={{ background: 'white', borderRadius: 14, padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                        <h3 style={{ color: '#2C3E50', marginBottom: '1rem' }}>🎯 Priority Actions (Preview)</h3>
                        {results.recommendations.slice(0, 3).map((r, i) => (
                            <div key={i} style={{
                                padding: '0.9rem 1rem', borderRadius: 10, marginBottom: '0.75rem',
                                borderLeft: `4px solid ${r.priority === 'CRITICAL' ? '#e74c3c' : r.priority === 'HIGH' ? '#f39c12' : '#3498db'}`,
                                background: '#fafbfc'
                            }}>
                                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: r.priority === 'CRITICAL' ? '#e74c3c' : '#f39c12', marginBottom: '0.25rem' }}>
                                    {r.priority} · {r.category}
                                </div>
                                <p style={{ color: '#2C3E50', fontSize: '0.9rem', margin: 0 }}>{r.message}</p>
                            </div>
                        ))}
                        {results.recommendations.length > 3 && (
                            <p style={{ color: '#bdc3c7', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                                +{results.recommendations.length - 3} more recommendations in the full report
                            </p>
                        )}
                    </div>
                )}

                {/* CTA to unlock full report */}
                <div style={{
                    background: 'linear-gradient(135deg, #1a2332, #2C3E50)', borderRadius: 16,
                    padding: '2rem', textAlign: 'center', boxShadow: '0 4px 24px rgba(0,0,0,0.15)'
                }}>
                    <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🔒</div>
                    <h2 style={{ color: 'white', marginBottom: '0.75rem', fontSize: '1.4rem' }}>Unlock Your Full Report</h2>
                    <p style={{ color: '#95a5a6', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                        Get the complete GEO metrics, all keyword gaps, AI improvement suggestions, and a personalised action plan — developed by our experts at Atlantic Digital.
                    </p>
                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                        <a href="mailto:hello@atlantic-digital.com" style={{
                            background: 'linear-gradient(135deg, #4ECDC4, #44A08D)', color: 'white',
                            padding: '0.85rem 1.75rem', borderRadius: 10, fontWeight: 700, textDecoration: 'none', fontSize: '0.95rem'
                        }}>
                            📧 Contact Atlantic Digital
                        </a>
                        <a href="tel:+34XXXXXXXXX" style={{
                            background: 'transparent', color: '#4ECDC4', padding: '0.85rem 1.75rem',
                            border: '1.5px solid #4ECDC4', borderRadius: 10, fontWeight: 700, textDecoration: 'none', fontSize: '0.95rem'
                        }}>
                            📞 Book a Free Call
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div style={{ background: '#F7F4F0', minHeight: '100vh', paddingTop: 100, paddingBottom: 60 }}>
            <div style={{ maxWidth: 680, margin: '0 auto', padding: '0 1.5rem' }}>
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(78,205,196,0.15)', color: '#2C8C85', padding: '0.4rem 1rem', borderRadius: 50, fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem' }}>
                        🤖 Free SEO & GEO Analysis
                    </div>
                    <h1 style={{ color: '#2C3E50', fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 700, marginBottom: '0.75rem' }}>Analyze Your Website</h1>
                    <p style={{ color: '#7f8c8d', fontSize: '1.05rem', lineHeight: 1.6 }}>
                        Get a free SEO & AI-readiness (GEO) score with keyword gaps and actionable recommendations.
                    </p>
                </div>

                {error && (
                    <div style={{ background: '#fdecea', border: '1px solid #f5c6cb', borderRadius: 10, padding: '1rem', marginBottom: '1.5rem', color: '#c0392b' }}>
                        {error}
                    </div>
                )}

                <div style={{ background: 'white', borderRadius: 16, padding: '2rem', boxShadow: '0 4px 24px rgba(0,0,0,0.07)' }}>
                    {/* Website info */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={labelStyle}>Your Website URL *</label>
                        <input value={clientUrl} onChange={e => setClientUrl(e.target.value)}
                            placeholder="https://yourbusiness.com" style={inputStyle} />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                        <div>
                            <label style={labelStyle}>Business Name</label>
                            <input value={clientName} onChange={e => setClientName(e.target.value)}
                                placeholder="My Business" style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>Location</label>
                            <input value={location} onChange={e => setLocation(e.target.value)}
                                placeholder="Madrid" style={inputStyle} />
                        </div>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={labelStyle}>Industry</label>
                        <input value={industry} onChange={e => setIndustry(e.target.value)}
                            placeholder="e.g. Dry Cleaning, Dental, Legal" style={inputStyle} />
                    </div>

                    {/* Contact info divider */}
                    <div style={{ borderTop: '1px solid #eef0f3', margin: '1.5rem 0', paddingTop: '1.5rem' }}>
                        <p style={{ color: '#4A6B7C', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Contact Information
                        </p>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                            <div>
                                <label style={labelStyle}>Phone Number</label>
                                <input value={phone} onChange={e => setPhone(e.target.value)}
                                    placeholder="+34 600 000 000" style={inputStyle} type="tel" />
                            </div>
                            <div>
                                <label style={labelStyle}>What do you want to improve?</label>
                                <select value={goal} onChange={e => setGoal(e.target.value)} style={{ ...inputStyle, cursor: 'pointer' }}>
                                    <option value="both">Both SEO & GEO</option>
                                    <option value="seo">SEO (Search Rankings)</option>
                                    <option value="geo">GEO (AI Search Visibility)</option>
                                    <option value="unsure">Not sure yet</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label style={labelStyle}>Any specific challenges? <span style={{ color: '#bdc3c7', fontWeight: 400 }}>(optional)</span></label>
                            <textarea value={message} onChange={e => setMessage(e.target.value)}
                                placeholder="e.g. We don't appear in Google results for our main service..."
                                rows={3}
                                style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit' }} />
                        </div>
                    </div>

                    <button onClick={runAnalysis} style={{
                        width: '100%', padding: '1rem', background: 'linear-gradient(135deg, #4ECDC4, #44A08D)',
                        color: 'white', border: 'none', borderRadius: 12, fontSize: '1rem', fontWeight: 700,
                        cursor: 'pointer', letterSpacing: '0.02em'
                    }}>
                        🚀 Run Free Analysis
                    </button>

                    <p style={{ color: '#bdc3c7', fontSize: '0.8rem', textAlign: 'center', marginTop: '1rem' }}>
                        Analysis takes ~30–60 seconds. No account required.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default AnalyzerPage;
