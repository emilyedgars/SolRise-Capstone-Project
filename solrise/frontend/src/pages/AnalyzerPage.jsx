import React, { useState } from 'react';

// SolRise tokens (inline — no import needed)
const SR = {
    orange:      '#F7A14F',
    coral:       '#F07A63',
    dark:        '#1A1A2E',
    gray:        '#6B7280',
    midGray:     '#9CA3AF',
    border:      'rgba(247,161,79,0.18)',
    bg:          '#FFFCF8',
    white:       '#FFFFFF',
    lightGray:   '#F5F3EF',
    btnGradient: 'linear-gradient(135deg, #F7A14F 0%, #F07A63 100%)',
    heroGradient:'linear-gradient(165deg, #FFF9F4 0%, #FFF3E8 50%, #FFF6F4 100%)',
    btnShadow:   '0 4px 20px rgba(240,122,99,0.35)',
    font:        "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
    pill:        9999,
    md:          16,
    lg:          24,
};

const AnalyzerPage = () => {
    const [step,        setStep]        = useState('form');
    const [clientUrl,   setClientUrl]   = useState('');
    const [clientName,  setClientName]  = useState('');
    const [location,    setLocation]    = useState('');
    const [industry,    setIndustry]    = useState('');
    const [phone,       setPhone]       = useState('');
    const [goal,        setGoal]        = useState('both');
    const [message,     setMessage]     = useState('');
    const [results,     setResults]     = useState(null);
    const [error,       setError]       = useState('');
    const [downloading, setDownloading] = useState(false);
    const [progress,    setProgress]    = useState('Scraping websites...');

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
            a.download = `solrise_preview_${(clientName || 'report').replace(/\s+/g, '_').toLowerCase()}.pdf`;
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
        if (f >= 0.5) return SR.orange;
        return SR.coral;
    };

    const inputStyle = {
        width: '100%', padding: '0.85rem 1rem',
        borderRadius: SR.md, fontSize: '0.95rem',
        border: `1.5px solid ${SR.border}`,
        background: SR.bg, color: SR.dark,
        boxSizing: 'border-box', outline: 'none',
        fontFamily: SR.font,
        transition: 'border-color 0.2s',
    };

    const labelStyle = {
        display: 'block', marginBottom: '0.4rem',
        fontWeight: 600, color: SR.dark, fontSize: '0.88rem',
    };

    // ── Loading screen ──────────────────────────────────────────────────────
    if (step === 'loading') return (
        <div style={{
            minHeight: '100vh', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            background: SR.heroGradient, fontFamily: SR.font,
        }}>
            <div style={{ textAlign: 'center', maxWidth: 480, padding: '2rem' }}>
                {/* Animated sun */}
                <div style={{
                    width: 72, height: 72, borderRadius: '50%',
                    background: SR.btnGradient,
                    margin: '0 auto 1.5rem',
                    boxShadow: SR.btnShadow,
                    animation: 'pulse 1.8s ease-in-out infinite',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '2rem',
                }}>
                    ☀️
                </div>
                <h2 style={{ color: SR.dark, marginBottom: '0.75rem', fontSize: '1.6rem', fontWeight: 800 }}>
                    Analysing your website
                </h2>
                <p style={{ color: SR.gray, marginBottom: '2rem', fontSize: '1rem' }}>{progress}</p>
                <div style={{ background: SR.border, borderRadius: 99, height: 5, overflow: 'hidden', background: 'rgba(247,161,79,0.15)' }}>
                    <div style={{
                        height: '100%', background: SR.btnGradient,
                        borderRadius: 99, animation: 'slide 2s ease-in-out infinite', width: '60%',
                        boxShadow: `0 0 8px ${SR.orange}`,
                    }} />
                </div>
                <p style={{ color: SR.midGray, fontSize: '0.85rem', marginTop: '1.5rem' }}>
                    This usually takes 30–60 seconds
                </p>
            </div>
            <style>{`
                @keyframes slide { 0%{margin-left:-60%} 100%{margin-left:100%} }
                @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.08);opacity:0.85} }
            `}</style>
        </div>
    );

    // ── Results screen ──────────────────────────────────────────────────────
    if (step === 'results' && results) return (
        <div style={{ background: SR.heroGradient, minHeight: '100vh', paddingTop: 100, paddingBottom: 60, fontFamily: SR.font }}>
            <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 1.5rem' }}>

                {/* Header row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 style={{ color: SR.dark, fontSize: '1.8rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                            Your SEO & GEO Report Preview
                        </h1>
                        <p style={{ color: SR.gray }}>{results.clientName || clientName}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <button onClick={downloadPDF} disabled={downloading} style={{
                            background: SR.btnGradient, color: 'white',
                            padding: '0.75rem 1.5rem', border: 'none', borderRadius: SR.pill,
                            cursor: 'pointer', fontWeight: 700, fontSize: '0.9rem',
                            boxShadow: SR.btnShadow, opacity: downloading ? 0.7 : 1,
                            fontFamily: SR.font,
                        }}>
                            {downloading ? '⏳ Generating...' : '📄 Download Preview PDF'}
                        </button>
                        <button onClick={() => { setStep('form'); setResults(null); }} style={{
                            background: 'transparent', color: SR.gray,
                            padding: '0.75rem 1.5rem',
                            border: `1.5px solid ${SR.border}`, borderRadius: SR.pill,
                            cursor: 'pointer', fontWeight: 600, fontFamily: SR.font,
                        }}>
                            ← New Analysis
                        </button>
                    </div>
                </div>

                {/* Score cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                    {[
                        { label: 'Overall Score', val: results.overallScore,      icon: '⭐' },
                        { label: 'SEO Score',     val: results.seoScore,          icon: '🔍' },
                        { label: 'GEO Score',     val: results.geoScore,          icon: '🤖' },
                        { label: 'Competitive',   val: results.competitiveScore,  icon: '⚔️' },
                    ].map((s, i) => (
                        <div key={i} style={{
                            background: SR.white, borderRadius: SR.lg, padding: '1.5rem',
                            boxShadow: '0 4px 20px rgba(247,161,79,0.1)',
                            border: `1px solid ${SR.border}`, textAlign: 'center',
                        }}>
                            <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{s.icon}</div>
                            <div style={{ fontSize: '2rem', fontWeight: 800, color: scoreColor(s.val) }}>
                                {Math.round((s.val || 0) * 100)}%
                            </div>
                            <div style={{ color: SR.gray, fontSize: '0.85rem', marginTop: '0.25rem', fontWeight: 500 }}>{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Keyword gaps */}
                {results.keywordGaps?.length > 0 && (
                    <div style={{
                        background: SR.white, borderRadius: SR.lg, padding: '1.5rem',
                        marginBottom: '1.5rem', boxShadow: '0 4px 20px rgba(247,161,79,0.08)',
                        border: `1px solid ${SR.border}`,
                    }}>
                        <h3 style={{ color: SR.dark, marginBottom: '1rem', fontWeight: 700 }}>🔑 Top Keyword Opportunities</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {results.keywordGaps.slice(0, 5).map((g, i) => (
                                <span key={i} style={{
                                    padding: '0.4rem 0.9rem', borderRadius: SR.pill,
                                    fontSize: '0.85rem', fontWeight: 600,
                                    background: g.priority === 'high'
                                        ? 'rgba(240,122,99,0.12)'
                                        : 'rgba(247,161,79,0.1)',
                                    color: g.priority === 'high' ? SR.coral : SR.orange,
                                    border: `1px solid ${g.priority === 'high' ? 'rgba(240,122,99,0.25)' : 'rgba(247,161,79,0.2)'}`,
                                }}>
                                    {g.keyword}
                                </span>
                            ))}
                            {results.keywordGaps.length > 5 && (
                                <span style={{
                                    padding: '0.4rem 0.9rem', borderRadius: SR.pill,
                                    fontSize: '0.85rem', background: SR.lightGray,
                                    color: SR.midGray, border: `1px solid ${SR.border}`,
                                }}>
                                    +{results.keywordGaps.length - 5} more in full report
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Recommendations preview */}
                {results.recommendations?.length > 0 && (
                    <div style={{
                        background: SR.white, borderRadius: SR.lg, padding: '1.5rem',
                        marginBottom: '1.5rem', boxShadow: '0 4px 20px rgba(247,161,79,0.08)',
                        border: `1px solid ${SR.border}`,
                    }}>
                        <h3 style={{ color: SR.dark, marginBottom: '1rem', fontWeight: 700 }}>🎯 Priority Actions (Preview)</h3>
                        {results.recommendations.slice(0, 3).map((r, i) => (
                            <div key={i} style={{
                                padding: '0.9rem 1rem', borderRadius: SR.md, marginBottom: '0.75rem',
                                borderLeft: `4px solid ${r.priority === 'CRITICAL' ? SR.coral : r.priority === 'HIGH' ? SR.orange : '#9C8BD9'}`,
                                background: SR.lightGray,
                            }}>
                                <div style={{
                                    fontSize: '0.75rem', fontWeight: 700,
                                    color: r.priority === 'CRITICAL' ? SR.coral : SR.orange,
                                    marginBottom: '0.25rem',
                                }}>
                                    {r.priority} · {r.category}
                                </div>
                                <p style={{ color: SR.dark, fontSize: '0.9rem', margin: 0 }}>{r.message}</p>
                            </div>
                        ))}
                        {results.recommendations.length > 3 && (
                            <p style={{ color: SR.midGray, fontSize: '0.85rem', marginTop: '0.5rem' }}>
                                +{results.recommendations.length - 3} more recommendations in the full report
                            </p>
                        )}
                    </div>
                )}

                {/* CTA unlock banner */}
                <div style={{
                    background: `linear-gradient(135deg, ${SR.orange}, ${SR.coral})`,
                    borderRadius: SR.lg, padding: '2.5rem', textAlign: 'center',
                    boxShadow: '0 20px 60px rgba(240,122,99,0.3)',
                    position: 'relative', overflow: 'hidden',
                }}>
                    <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🔒</div>
                    <h2 style={{ color: 'white', marginBottom: '0.75rem', fontSize: '1.4rem', fontWeight: 800 }}>
                        Unlock Your Full Report
                    </h2>
                    <p style={{ color: 'rgba(255,255,255,0.88)', marginBottom: '1.75rem', lineHeight: 1.65, maxWidth: 480, margin: '0 auto 1.75rem' }}>
                        Get the complete GEO metrics, all keyword gaps, AI improvement suggestions, and a personalised step-by-step action plan — developed by our experts at SolRise.
                    </p>
                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                        <a href="mailto:support@solrise.ai" style={{
                            background: 'white', color: SR.coral,
                            padding: '0.85rem 1.75rem', borderRadius: SR.pill,
                            fontWeight: 700, textDecoration: 'none', fontSize: '0.95rem',
                            boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                        }}>
                            📧 Contact SolRise
                        </a>
                        <a href="tel:+34XXXXXXXXX" style={{
                            background: 'transparent', color: 'white',
                            padding: '0.85rem 1.75rem',
                            border: '1.5px solid rgba(255,255,255,0.7)',
                            borderRadius: SR.pill, fontWeight: 700,
                            textDecoration: 'none', fontSize: '0.95rem',
                        }}>
                            📞 Book a Free Call
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );

    // ── Form screen ─────────────────────────────────────────────────────────
    return (
        <div style={{ background: SR.heroGradient, minHeight: '100vh', paddingTop: 100, paddingBottom: 60, fontFamily: SR.font }}>
            <div style={{ maxWidth: 680, margin: '0 auto', padding: '0 1.5rem' }}>

                {/* Heading */}
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <div style={{
                        display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                        background: 'rgba(247,161,79,0.12)', color: SR.coral,
                        padding: '0.4rem 1.1rem', borderRadius: SR.pill,
                        fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem',
                        border: `1px solid rgba(247,161,79,0.22)`,
                    }}>
                        ✦ Free AI-Powered Analysis
                    </div>
                    <h1 style={{ color: SR.dark, fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 800, marginBottom: '0.75rem', letterSpacing: '-0.02em' }}>
                        Analyse Your Website
                    </h1>
                    <p style={{ color: SR.gray, fontSize: '1.05rem', lineHeight: 1.65 }}>
                        Get a free SEO & AI-readiness (GEO) score with keyword gaps and actionable recommendations.
                    </p>
                </div>

                {error && (
                    <div style={{
                        background: 'rgba(240,122,99,0.1)', border: `1px solid rgba(240,122,99,0.3)`,
                        borderRadius: SR.md, padding: '1rem', marginBottom: '1.5rem', color: SR.coral,
                    }}>
                        {error}
                    </div>
                )}

                <div style={{
                    background: SR.white, borderRadius: SR.lg, padding: '2rem',
                    boxShadow: '0 8px 40px rgba(247,161,79,0.12)',
                    border: `1px solid ${SR.border}`,
                }}>
                    {/* URL */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={labelStyle}>Your Website URL *</label>
                        <input value={clientUrl} onChange={e => setClientUrl(e.target.value)}
                            placeholder="https://yourbusiness.com" style={inputStyle} type="url" />
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
                    <div style={{ borderTop: `1px solid ${SR.border}`, margin: '1.5rem 0', paddingTop: '1.5rem' }}>
                        <p style={{
                            color: SR.orange, fontSize: '0.82rem', fontWeight: 700,
                            marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.07em',
                        }}>
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
                                <select value={goal} onChange={e => setGoal(e.target.value)}
                                    style={{ ...inputStyle, cursor: 'pointer' }}>
                                    <option value="both">Both SEO & GEO</option>
                                    <option value="seo">SEO (Search Rankings)</option>
                                    <option value="geo">GEO (AI Search Visibility)</option>
                                    <option value="unsure">Not sure yet</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label style={labelStyle}>
                                Any specific challenges?{' '}
                                <span style={{ color: SR.midGray, fontWeight: 400 }}>(optional)</span>
                            </label>
                            <textarea value={message} onChange={e => setMessage(e.target.value)}
                                placeholder="e.g. We don't appear in Google results for our main service..."
                                rows={3}
                                style={{ ...inputStyle, resize: 'vertical', fontFamily: SR.font }} />
                        </div>
                    </div>

                    <button onClick={runAnalysis} style={{
                        width: '100%', padding: '1rem',
                        background: SR.btnGradient, color: 'white',
                        border: 'none', borderRadius: SR.pill,
                        fontSize: '1rem', fontWeight: 700,
                        cursor: 'pointer', letterSpacing: '0.02em',
                        boxShadow: SR.btnShadow, fontFamily: SR.font,
                    }}>
                        ✦ Run Free Analysis
                    </button>

                    <p style={{ color: SR.midGray, fontSize: '0.8rem', textAlign: 'center', marginTop: '1rem' }}>
                        Analysis takes ~30–60 seconds · No account required
                    </p>
                </div>
            </div>
        </div>
    );
};

export default AnalyzerPage;
