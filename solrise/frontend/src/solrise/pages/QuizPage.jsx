import React, { useState } from 'react';
import { SR, gradientText, btnPrimary } from '../tokens';
import { SunIcon } from '../components/SunLogo';

// ── Quiz step definitions ──────────────────────────────────────────────────
const STEPS = [
    {
        id: 'url',
        icon: '🌐',
        question: "What's your website URL?",
        subtitle: "We'll run a live AI scan on your site, for free.",
        type: 'url',
        field: 'website',
        placeholder: 'https://yourbusiness.com',
        validate: v => v && v.includes('.'),
    },
    {
        id: 'competitors',
        icon: '🎯',
        question: "Who are your competitors?",
        subtitle: "Add at least one. The more you add, the richer your benchmarking report.",
        type: 'competitors',
        field: 'competitors',
        placeholder: 'https://competitor.com',
        validate: v => Array.isArray(v) && v.length > 0 && v[0].includes('.'),
    },
    {
        id: 'industry',
        icon: '🏢',
        question: 'What industry are you in?',
        subtitle: "We'll benchmark you against the right standards.",
        type: 'pills',
        field: 'industry',
        options: [
            'E-commerce', 'Healthcare', 'Finance & Banking',
            'Real Estate', 'Legal Services', 'Restaurant & Food',
            'Technology / SaaS', 'Education', 'Travel & Tourism',
            'Beauty & Wellness', 'Professional Services', 'Other',
        ],
    },
    {
        id: 'goal',
        icon: '🎯',
        question: "What's your main goal?",
        subtitle: "We'll tailor the report to what matters most to you.",
        type: 'cards',
        field: 'goal',
        options: [
            { value: 'seo',    icon: '🔍', title: 'Rank Higher on Google',   desc: 'Improve your search engine rankings' },
            { value: 'geo',    icon: '🤖', title: 'Appear in AI Answers',    desc: 'Get cited by ChatGPT, Gemini, Claude & Perplexity' },
            { value: 'both',   icon: '⚡', title: 'Both',                    desc: 'Full SEO + GEO optimisation' },
            { value: 'unsure', icon: '🗺️', title: "Not Sure Yet",           desc: "Let's figure it out together" },
        ],
    },
    {
        id: 'challenges',
        icon: '⚡',
        question: 'What challenges are you facing?',
        subtitle: 'Select all that apply.',
        type: 'multiselect',
        field: 'challenges',
        options: [
            'Low website traffic',
            'Not ranking on Google',
            'Competitors outranking me',
            'AI tools never mention my business',
            'My content feels outdated',
            'No idea where to even start',
        ],
    },
    {
        id: 'contact',
        icon: '🏢',
        question: 'Almost there — what\'s your company name?',
        subtitle: 'Your personalised AI report will be shown immediately.',
        type: 'contact',
        fields: [
            { key: 'name', label: 'Company Name', type: 'text', placeholder: 'Acme Ltd', required: true },
        ],
    },
];

// ── Shared styles ──────────────────────────────────────────────────────────
const inputStyle = {
    width: '100%', padding: '0.9rem 1.1rem',
    border: `1.5px solid ${SR.border}`,
    borderRadius: SR.md, fontSize: '1rem',
    fontFamily: SR.font, color: SR.dark,
    background: SR.white, outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.2s',
};

// ── Teaser Report ──────────────────────────────────────────────────────────
const ScoreDial = ({ score, label, color }) => (
    <div style={{
        textAlign: 'center', padding: '1.5rem',
        background: SR.white, borderRadius: SR.xl,
        border: `1px solid ${SR.border}`,
        boxShadow: SR.cardShadow, flex: 1,
    }}>
        <div style={{
            fontSize: '2.8rem', fontWeight: 800,
            color, marginBottom: '0.25rem',
        }}>
            {score}<span style={{ fontSize: '1.2rem', fontWeight: 600, color: SR.gray }}>/100</span>
        </div>
        <div style={{ fontSize: '0.88rem', color: SR.gray, fontWeight: 600 }}>{label}</div>
    </div>
);

// ── Lead capture modal ─────────────────────────────────────────────────────
const LeadModal = ({ answers, onClose }) => {
    const [form, setForm] = useState({
        name:    answers.name  || '',
        email:   answers.email || '',
        phone:   answers.phone || '',
        website: answers.website || '',
    });
    const [submitting, setSubmitting] = useState(false);
    const [done,       setDone]       = useState(false);
    const [err,        setErr]        = useState('');

    const update = f => e => setForm(p => ({ ...p, [f]: e.target.value }));

    const handleSubmit = async e => {
        e.preventDefault();
        if (!form.email) { setErr('Email is required.'); return; }
        setSubmitting(true);
        setErr('');
        try {
            const resp = await fetch('/api/leads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...form,
                    industry:   answers.industry   || '',
                    goal:       answers.goal        || '',
                    challenges: answers.challenges  || [],
                    source:     'full_report_request',
                }),
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error);
            setDone(true);
        } catch (e) {
            setErr('Something went wrong. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    const modalInput = {
        width: '100%', padding: '0.85rem 1rem',
        border: `1.5px solid ${SR.border}`, borderRadius: SR.md,
        fontSize: '0.95rem', fontFamily: SR.font,
        color: SR.dark, background: SR.white,
        outline: 'none', boxSizing: 'border-box',
    };

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'rgba(0,0,0,0.45)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '1rem',
        }} onClick={e => e.target === e.currentTarget && onClose()}>
            <div style={{
                background: SR.white, borderRadius: 24, padding: '2.5rem',
                width: '100%', maxWidth: 460, position: 'relative',
                boxShadow: '0 24px 80px rgba(0,0,0,0.18)',
            }}>
                <button onClick={onClose} style={{
                    position: 'absolute', top: '1.25rem', right: '1.25rem',
                    background: 'none', border: 'none', fontSize: '1.4rem',
                    cursor: 'pointer', color: SR.gray, lineHeight: 1,
                }}>×</button>

                {done ? (
                    <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
                        <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: SR.dark, marginBottom: '0.5rem' }}>
                            You're on the list!
                        </h3>
                        <p style={{ color: SR.gray, fontSize: '0.92rem', lineHeight: 1.6 }}>
                            A SolRise specialist will send your full report within 24 hours.
                        </p>
                        <button onClick={onClose} style={{ ...btnPrimary, marginTop: '1.5rem', padding: '0.75rem 2rem' }}>
                            Close
                        </button>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div style={{ fontSize: '1.75rem', marginBottom: '0.75rem' }}>🔓</div>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: SR.dark, marginBottom: '0.35rem' }}>
                            Get your full report
                        </h3>
                        <p style={{ color: SR.gray, fontSize: '0.88rem', marginBottom: '1.75rem', lineHeight: 1.6 }}>
                            A SolRise specialist will unlock the complete analysis and send it to you within 24 hours.
                        </p>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {[
                                { key: 'name',    label: 'Full Name',       type: 'text',  placeholder: 'Jane Smith',           required: true  },
                                { key: 'email',   label: 'Email Address',   type: 'email', placeholder: 'jane@yourbusiness.com', required: true  },
                                { key: 'phone',   label: 'Phone (optional)',type: 'tel',   placeholder: '+34 600 000 000',       required: false },
                                { key: 'website', label: 'Website URL',     type: 'url',   placeholder: 'https://yourbusiness.com', required: false },
                            ].map(f => (
                                <div key={f.key}>
                                    <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', color: SR.dark, marginBottom: '0.35rem' }}>
                                        {f.label}{f.required && <span style={{ color: SR.coral }}> *</span>}
                                    </label>
                                    <input
                                        type={f.type}
                                        placeholder={f.placeholder}
                                        value={form[f.key] || ''}
                                        onChange={update(f.key)}
                                        style={modalInput}
                                    />
                                </div>
                            ))}
                        </div>

                        {err && (
                            <p style={{ color: SR.coral, fontSize: '0.85rem', marginTop: '0.75rem' }}>{err}</p>
                        )}

                        <button type="submit" disabled={submitting} style={{
                            ...btnPrimary, width: '100%', marginTop: '1.5rem',
                            opacity: submitting ? 0.7 : 1, cursor: submitting ? 'default' : 'pointer',
                        }}>
                            {submitting ? 'Sending…' : 'Send Me the Full Report →'}
                        </button>

                        <p style={{ color: SR.midGray, fontSize: '0.78rem', textAlign: 'center', marginTop: '0.75rem' }}>
                            🔒 Your information is private and will never be shared.
                        </p>
                    </form>
                )}
            </div>
        </div>
    );
};


const ReportPreview = ({ results, answers }) => {
    const siteName = answers?.website?.replace(/https?:\/\//, '').replace(/\/$/, '') ?? 'your site';
    const seo = toPercent(results?.seoScore ?? results?.scores?.seo);
    const geo = toPercent(results?.geoScore ?? results?.scores?.geo);
    const overall = toPercent(results?.overallScore) || Math.round((seo + geo) / 2);
    const scoreColor = overall >= 70 ? '#27ae60' : overall >= 45 ? SR.orange : SR.coral;
    const gaps = results?.keywordGaps?.slice(0, 4) ?? [];
    const recs = results?.recommendations?.slice(0, 5) ?? [];

    return (
        <div style={{
            background: SR.white, borderRadius: 16,
            border: `1px solid ${SR.border}`,
            boxShadow: '0 8px 40px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)',
            overflow: 'hidden', fontFamily: SR.font,
            transform: 'rotate(-0.4deg)',
            transformOrigin: 'center top',
        }}>
            {/* Report header bar */}
            <div style={{
                background: 'linear-gradient(135deg, #1A1A2E 0%, #2a2a45 100%)',
                padding: '1rem 1.25rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <img src="/solrise-logo.png" alt="SolRise" style={{ height: 22, filter: 'brightness(0) invert(1)' }} />
                    <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.72rem' }}>|</span>
                    <span style={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.72rem', fontWeight: 600 }}>SEO & GEO Full Report</span>
                </div>
                <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.65rem' }}>{siteName}</span>
            </div>

            {/* Score row */}
            <div style={{ display: 'flex', borderBottom: `1px solid ${SR.border}` }}>
                {[
                    { label: 'Overall', value: overall, color: scoreColor },
                    { label: 'SEO',     value: seo,     color: SR.orange },
                    { label: 'GEO (AI)',value: geo,     color: '#9C8BD9' },
                ].map((s, i) => (
                    <div key={i} style={{
                        flex: 1, padding: '0.9rem 0.75rem', textAlign: 'center',
                        borderRight: i < 2 ? `1px solid ${SR.border}` : 'none',
                    }}>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: s.color, lineHeight: 1 }}>
                            {s.value}<span style={{ fontSize: '0.65rem', color: SR.gray, fontWeight: 500 }}>/100</span>
                        </div>
                        <div style={{ fontSize: '0.65rem', color: SR.gray, marginTop: '0.2rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{s.label}</div>
                        {/* Mini bar */}
                        <div style={{ height: 3, background: '#f0ede8', borderRadius: 2, marginTop: '0.4rem', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${s.value}%`, background: s.color, borderRadius: 2 }} />
                        </div>
                    </div>
                ))}
            </div>

            {/* Keyword gaps section — partially blurred */}
            <div style={{ padding: '0.9rem 1.25rem', borderBottom: `1px solid ${SR.border}` }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: SR.dark, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
                    🔍 Keyword Gap Analysis
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {(gaps.length > 0 ? gaps : [{ keyword: '—' }, { keyword: '—' }, { keyword: '—' }]).map((g, i) => (
                        <div key={i} style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            padding: '0.3rem 0.5rem', background: '#f9f7f4', borderRadius: 6,
                            filter: i > 0 ? 'blur(3.5px)' : 'none',
                        }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: SR.dark }}>{g?.keyword ?? g}</span>
                            <span style={{ fontSize: '0.65rem', background: SR.btnGradient, color: 'white', borderRadius: 20, padding: '0.1rem 0.45rem', fontWeight: 700 }}>
                                {g?.score ? `${toPercent(g.score)}%` : 'Gap'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recommendations — first 2 visible, rest blurred */}
            <div style={{ padding: '0.9rem 1.25rem' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: SR.dark, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.6rem' }}>
                    ⚡ Actionable Recommendations
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {(recs.length > 0 ? recs : [
                        { action: 'Add FAQ schema markup to your top 3 service pages to unlock rich snippets and increase click-through rate by ~20%.' },
                        { action: 'Publish a 900-word authoritative guide targeting your #1 keyword gap — competitors rank for this but you have no content.' },
                        { action: 'Rewrite meta titles to lead with the primary keyword within the first 30 characters on all core pages.' },
                        { action: 'Add an "About the Author" section with credentials to every blog post to boost E-E-A-T signals for AI citability.' },
                        { action: 'Implement structured data (LocalBusiness + Service schema) so ChatGPT and Perplexity can verify and cite your business.' },
                    ]).map((r, i) => {
                        const text = typeof r === 'string' ? r : r?.action ?? r?.text ?? r?.recommendation ?? '';
                        const isBlurred = i >= 2;
                        return (
                            <div key={i} style={{
                                display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
                                padding: '0.45rem 0.6rem', borderRadius: 7,
                                background: isBlurred ? '#f9f7f4' : 'linear-gradient(90deg, rgba(247,161,79,0.07), rgba(240,122,99,0.04))',
                                border: `1px solid ${isBlurred ? 'transparent' : 'rgba(247,161,79,0.18)'}`,
                                filter: isBlurred ? 'blur(3.5px)' : 'none',
                                userSelect: isBlurred ? 'none' : 'auto',
                                pointerEvents: isBlurred ? 'none' : 'auto',
                            }}>
                                <span style={{
                                    minWidth: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                                    background: SR.btnGradient, color: 'white',
                                    fontSize: '0.6rem', fontWeight: 800,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    marginTop: '0.05rem',
                                }}>{i + 1}</span>
                                <span style={{ fontSize: '0.73rem', color: SR.dark, lineHeight: 1.5 }}>{text}</span>
                            </div>
                        );
                    })}
                </div>
                <p style={{ fontSize: '0.68rem', color: SR.gray, margin: '0.6rem 0 0', textAlign: 'right' }}>
                    +{Math.max(0, (results?.recommendations?.length ?? 8) - 2)} more detailed recommendations in full report
                </p>
            </div>
        </div>
    );
};

const LockOverlay = ({ answers, results }) => {
    const [showModal, setShowModal] = useState(false);

    return (
        <>
            {/* Report preview */}
            <div style={{ marginTop: '1.5rem' }}>
                <ReportPreview results={results} answers={answers} />
            </div>

            {/* CTA card */}
            <div style={{
                background: SR.white, border: `1px solid ${SR.border}`,
                borderRadius: SR.xl, marginTop: '1rem',
                padding: '1.75rem 1.5rem',
                textAlign: 'center',
                boxShadow: SR.cardShadow,
            }}>
                <h3 style={{
                    fontSize: '1.1rem', fontWeight: 800, color: SR.dark,
                    marginBottom: '0.35rem', lineHeight: 1.3,
                }}>
                    Get your full report
                </h3>
                <p style={{
                    color: SR.gray, fontSize: '0.86rem',
                    margin: '0 auto 1.4rem', maxWidth: 340,
                    lineHeight: 1.6,
                }}>
                    Get the complete keyword gap analysis, competitor benchmarks, GEO insights, and a step-by-step action plan.
                </p>
                <button
                    onClick={() => setShowModal(true)}
                    style={{
                        ...btnPrimary,
                        fontSize: '0.95rem', padding: '0.9rem 2.25rem',
                        animation: 'lockPulse 2.2s ease-in-out infinite',
                    }}
                >
                    Send Full Report to My Inbox →
                </button>
            </div>

            {showModal && <LeadModal answers={answers} onClose={() => setShowModal(false)} />}

            <style>{`
                @keyframes lockPulse {
                    0%   { box-shadow: 0 4px 20px rgba(247,161,79,0.35), 0 0 0 0 rgba(247,161,79,0.45); }
                    50%  { box-shadow: 0 4px 28px rgba(240,122,99,0.45), 0 0 0 10px rgba(247,161,79,0); }
                    100% { box-shadow: 0 4px 20px rgba(247,161,79,0.35), 0 0 0 0 rgba(247,161,79,0); }
                }
            `}</style>
        </>
    );
};

// Scores come back as 0–1 decimals from the pipeline; convert to 0–100
const toPercent = v => v == null ? 0 : v <= 1 ? Math.round(v * 100) : Math.round(v);

const TeaserReport = ({ results, answers, setActiveTab }) => {
    const seoScore = toPercent(results?.seoScore ?? results?.scores?.seo);
    const geoScore = toPercent(results?.geoScore ?? results?.scores?.geo);
    const overall  = toPercent(results?.overallScore) || Math.round((seoScore + geoScore) / 2);
    const keywords = results?.keywordGaps?.slice(0, 2) ?? [];
    const insights = results?.competitiveInsights?.slice(0, 1) ?? [];
    const siteName = answers.website?.replace(/https?:\/\//, '').replace(/\/$/, '') ?? 'your site';

    const scoreColor = overall >= 70 ? '#27ae60' : overall >= 45 ? SR.orange : SR.coral;

    return (
        <div style={{
            minHeight: '100vh', background: SR.heroGradient,
            paddingTop: 80, fontFamily: SR.font, paddingBottom: '4rem',
        }}>
            <div style={{ maxWidth: 700, margin: '0 auto', padding: '2rem 1.5rem' }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <SunIcon size={52} />
                    <h1 style={{
                        fontSize: 'clamp(1.6rem, 3vw, 2.2rem)', fontWeight: 800,
                        color: SR.dark, marginTop: '1rem', marginBottom: '0.4rem',
                        letterSpacing: '-0.02em',
                    }}>
                        Your Free SEO & GEO Report
                    </h1>
                    <p style={{ color: SR.gray, fontSize: '0.95rem' }}>
                        Analysis for <strong style={{ color: SR.dark }}>{siteName}</strong>
                    </p>
                </div>

                {/* Overall score */}
                <div style={{
                    background: SR.white, borderRadius: SR.xl, padding: '2rem',
                    border: `1px solid ${SR.border}`, boxShadow: SR.cardShadow,
                    textAlign: 'center', marginBottom: '1.5rem',
                }}>
                    <p style={{ color: SR.gray, fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
                        Overall Score
                    </p>
                    <div style={{ fontSize: '4rem', fontWeight: 800, color: scoreColor, lineHeight: 1 }}>
                        {overall}
                        <span style={{ fontSize: '1.5rem', color: SR.gray, fontWeight: 600 }}>/100</span>
                    </div>
                    <p style={{ color: SR.gray, fontSize: '0.88rem', marginTop: '0.5rem' }}>
                        {overall >= 70 ? 'Good foundation — room to grow' : overall >= 45 ? 'Moderate — significant opportunities identified' : 'Needs attention — several critical gaps found'}
                    </p>
                </div>

                {/* SEO + GEO scores */}
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                    <ScoreDial score={Math.round(seoScore)} label="SEO Score"       color={SR.orange} />
                    <ScoreDial score={Math.round(geoScore)} label="GEO (AI) Score"  color={SR.lavender ?? '#9C8BD9'} />
                </div>

                {/* Top keyword gap (1 visible) */}
                {keywords.length > 0 && (
                    <div style={{
                        background: SR.white, borderRadius: SR.xl, padding: '1.5rem',
                        border: `1px solid ${SR.border}`, boxShadow: SR.cardShadow,
                        marginBottom: '1rem',
                    }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: SR.dark, marginBottom: '1rem' }}>
                            🔍 Top Keyword Gap
                        </h3>
                        <div style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            padding: '0.75rem 1rem', background: SR.lightGray ?? '#F5F3EF',
                            borderRadius: SR.md,
                        }}>
                            <span style={{ fontWeight: 600, color: SR.dark, fontSize: '0.95rem' }}>
                                {keywords[0]?.keyword ?? keywords[0]}
                            </span>
                            <span style={{
                                background: SR.btnGradient, color: 'white',
                                borderRadius: SR.pill, padding: '0.2rem 0.75rem',
                                fontSize: '0.78rem', fontWeight: 700,
                            }}>
                                Gap: {keywords[0]?.score ? `${toPercent(keywords[0].score)}%` : 'High'}
                            </span>
                        </div>
                        <p style={{ color: SR.midGray, fontSize: '0.8rem', marginTop: '0.75rem', marginBottom: 0 }}>
                            Your competitor ranks for this — you don't.
                        </p>
                    </div>
                )}

                {/* Competitive insight (1 visible) */}
                {insights.length > 0 && (
                    <div style={{
                        background: SR.white, borderRadius: SR.xl, padding: '1.5rem',
                        border: `1px solid ${SR.border}`, boxShadow: SR.cardShadow,
                        marginBottom: '1rem',
                    }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: SR.dark, marginBottom: '0.75rem' }}>
                            🎯 Key Competitive Insight
                        </h3>
                        <p style={{ color: SR.gray, fontSize: '0.9rem', margin: 0, lineHeight: 1.6 }}>
                            {insights[0]}
                        </p>
                    </div>
                )}

                {/* Lock overlay for the rest */}
                <LockOverlay answers={answers} results={results} />

                {/* Back button */}
                <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                    <button
                        onClick={() => setActiveTab && setActiveTab('home')}
                        style={{
                            background: 'none', border: `1.5px solid ${SR.border}`,
                            color: SR.gray, borderRadius: SR.pill,
                            padding: '0.7rem 1.5rem', cursor: 'pointer',
                            fontWeight: 600, fontSize: '0.88rem', fontFamily: SR.font,
                        }}
                    >
                        ← Back to Home
                    </button>
                </div>
            </div>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

// ── Loading screen ─────────────────────────────────────────────────────────
const LoadingScreen = ({ website }) => (
    <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center',
        justifyContent: 'center', background: SR.heroGradient,
        paddingTop: 80, fontFamily: SR.font,
    }}>
        <div style={{ textAlign: 'center', maxWidth: 480, padding: '2rem' }}>
            <div style={{
                width: 64, height: 64, border: `4px solid rgba(247,161,79,0.2)`,
                borderTop: `4px solid ${SR.orange}`, borderRadius: '50%',
                animation: 'spin 0.9s linear infinite', margin: '0 auto 2rem',
            }} />
            <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: SR.dark, marginBottom: '0.75rem' }}>
                Analysing your site…
            </h2>
            <p style={{ color: SR.gray, fontSize: '0.95rem', lineHeight: 1.7, marginBottom: '1.5rem' }}>
                Running SEO checks, scanning <strong>{website?.replace(/https?:\/\//, '') ?? 'your site'}</strong>, and benchmarking against your competitor.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start', display: 'inline-flex' }}>
                {['Scraping website content', 'Running NLP analysis', 'Scoring GEO readiness', 'Identifying keyword gaps', 'Benchmarking competitors'].map((step, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.88rem', color: SR.gray }}>
                        <span style={{ color: SR.orange }}>↻</span> {step}
                    </div>
                ))}
            </div>
            <p style={{ color: SR.midGray, fontSize: '0.78rem', marginTop: '2rem' }}>
                This usually takes under 2 minutes
            </p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
);

// ── Main QuizPage component ───────────────────────────────────────────────
const QuizPage = ({ setActiveTab }) => {
    const [step,       setStep]       = useState(0);
    const [answers,    setAnswers]    = useState({});
    const [loading,    setLoading]    = useState(false);
    const [results,    setResults]    = useState(null);
    const [error,      setError]      = useState(null);
    const [dir,        setDir]        = useState(1);
    const [animKey,    setAnimKey]    = useState(0);

    const current  = STEPS[step];
    const total    = STEPS.length;
    const progress = (step / total) * 100;

    const goTo = (nextStep, direction) => {
        setDir(direction);
        setAnimKey(k => k + 1);
        setStep(nextStep);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const canContinue = () => {
        const s = STEPS[step];
        const val = answers[s.field];
        if (s.type === 'multiselect') return val && val.length > 0;
        if (s.type === 'contact') return s.fields.filter(f => f.required).every(f => answers[f.key]);
        if (s.validate) return s.validate(val);
        return !!val;
    };

    const handleNext = async () => {
        if (step < total - 1) {
            goTo(step + 1, 1);
        } else {
            // Submit — run analysis
            setLoading(true);
            setError(null);
            try {
                const resp = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        clientUrl:    answers.website,
                        competitors:  (answers.competitors || []).filter(v => v && v.includes('.')),
                        clientName:   answers.name || 'Anonymous',
                        clientEmail:  answers.email || '',
                        clientPhone:  answers.phone || '',
                        industry:     answers.industry || '',
                        location:     '',
                    }),
                });
                const data = await resp.json();
                if (data.error) throw new Error(data.error);
                setResults(data.results ?? data);
            } catch (e) {
                setError('Analysis failed. Please try again.');
            } finally {
                setLoading(false);
            }
        }
    };

    const handleBack = () => { if (step > 0) goTo(step - 1, -1); };
    const setSingle  = (field, value) => setAnswers(a => ({ ...a, [field]: value }));
    const toggleMulti = (field, value) => setAnswers(a => {
        const cur = a[field] || [];
        return { ...a, [field]: cur.includes(value) ? cur.filter(v => v !== value) : [...cur, value] };
    });

    // Show loading
    if (loading) return <LoadingScreen website={answers.website} />;

    // Show teaser report
    if (results) return <TeaserReport results={results} answers={answers} setActiveTab={setActiveTab} />;

    // ── Render step content ───────────────────────────────────────────────
    const renderContent = () => {
        const s = current;

        if (s.type === 'url') return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <input
                    type="url"
                    placeholder={s.placeholder}
                    value={answers[s.field] || ''}
                    onChange={e => setSingle(s.field, e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && canContinue() && handleNext()}
                    style={{ ...inputStyle, fontSize: '1.1rem', padding: '1rem 1.25rem' }}
                    autoFocus
                />
                <p style={{ color: SR.midGray, fontSize: '0.82rem', margin: 0 }}>
                    Example: https://mybakery.com
                </p>
            </div>
        );

        if (s.type === 'competitors') {
            const list = answers[s.field] || [''];
            const update = (i, val) => {
                const next = [...list];
                next[i] = val;
                setSingle(s.field, next);
            };
            const addRow = () => setSingle(s.field, [...list, '']);
            const removeRow = (i) => {
                const next = list.filter((_, idx) => idx !== i);
                setSingle(s.field, next.length ? next : ['']);
            };
            return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {list.map((val, i) => (
                        <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <input
                                type="url"
                                placeholder={`https://competitor${i + 1}.com`}
                                value={val}
                                onChange={e => update(i, e.target.value)}
                                style={{ ...inputStyle, flex: 1 }}
                                autoFocus={i === 0}
                            />
                            {list.length > 1 && (
                                <button onClick={() => removeRow(i)} style={{
                                    flexShrink: 0, width: 36, height: 36, borderRadius: '50%',
                                    border: `1.5px solid ${SR.border}`, background: SR.white,
                                    color: SR.gray, cursor: 'pointer', fontSize: '1rem',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>×</button>
                            )}
                        </div>
                    ))}
                    <button onClick={addRow} style={{
                        background: 'none', border: `1.5px dashed ${SR.border}`,
                        borderRadius: SR.md, padding: '0.7rem 1rem',
                        color: SR.gray, cursor: 'pointer', fontSize: '0.88rem',
                        fontFamily: SR.font, textAlign: 'left',
                    }}>
                        + Add another competitor
                    </button>
                    <p style={{ color: SR.midGray, fontSize: '0.82rem', margin: 0 }}>
                        Add as many as you like. At least one is required.
                    </p>
                </div>
            );
        }

        if (s.type === 'pills') return (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', justifyContent: 'center' }}>
                {s.options.map(opt => {
                    const selected = answers[s.field] === opt;
                    return (
                        <button key={opt} onClick={() => setSingle(s.field, opt)} style={{
                            padding: '0.6rem 1.2rem', borderRadius: SR.pill,
                            border: `1.5px solid ${selected ? SR.orange : SR.border}`,
                            background: selected ? 'linear-gradient(135deg, rgba(247,161,79,0.15), rgba(240,122,99,0.15))' : SR.white,
                            color: selected ? SR.coral : SR.gray,
                            fontWeight: selected ? 700 : 500, cursor: 'pointer',
                            fontSize: '0.9rem', fontFamily: SR.font, transition: 'all 0.18s ease',
                        }}>
                            {opt}
                        </button>
                    );
                })}
            </div>
        );

        if (s.type === 'cards') return (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                {s.options.map(opt => {
                    const selected = answers[s.field] === opt.value;
                    return (
                        <button key={opt.value} onClick={() => setSingle(s.field, opt.value)} style={{
                            padding: '1.5rem 1.25rem', borderRadius: SR.xl,
                            border: `2px solid ${selected ? SR.orange : SR.border}`,
                            background: selected ? 'linear-gradient(135deg, rgba(247,161,79,0.12), rgba(240,122,99,0.12))' : SR.white,
                            cursor: 'pointer', textAlign: 'center', fontFamily: SR.font,
                            boxShadow: selected ? `0 0 0 4px rgba(247,161,79,0.18)` : SR.cardShadow,
                            transition: 'all 0.2s ease',
                        }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.6rem' }}>{opt.icon}</div>
                            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: selected ? SR.coral : SR.dark, marginBottom: '0.35rem' }}>{opt.title}</div>
                            <div style={{ fontSize: '0.78rem', color: SR.midGray, lineHeight: 1.4 }}>{opt.desc}</div>
                        </button>
                    );
                })}
            </div>
        );

        if (s.type === 'multiselect') return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {s.options.map(opt => {
                    const selected = (answers[s.field] || []).includes(opt);
                    return (
                        <button key={opt} onClick={() => toggleMulti(s.field, opt)} style={{
                            display: 'flex', alignItems: 'center', gap: '0.85rem',
                            padding: '0.9rem 1.2rem', borderRadius: SR.md,
                            border: `1.5px solid ${selected ? SR.orange : SR.border}`,
                            background: selected ? 'linear-gradient(90deg, rgba(247,161,79,0.1), rgba(240,122,99,0.08))' : SR.white,
                            cursor: 'pointer', textAlign: 'left', fontFamily: SR.font, transition: 'all 0.18s ease',
                        }}>
                            <div style={{
                                width: 22, height: 22, borderRadius: 6, flexShrink: 0,
                                border: `2px solid ${selected ? SR.orange : SR.border}`,
                                background: selected ? SR.btnGradient : 'transparent',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all 0.15s',
                            }}>
                                {selected && <span style={{ color: 'white', fontSize: '0.75rem', fontWeight: 800 }}>✓</span>}
                            </div>
                            <span style={{ fontSize: '0.95rem', fontWeight: selected ? 600 : 400, color: selected ? SR.dark : SR.gray }}>{opt}</span>
                        </button>
                    );
                })}
            </div>
        );

        if (s.type === 'contact') return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {s.fields.map(f => (
                    <div key={f.key}>
                        <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', color: SR.dark, marginBottom: '0.4rem' }}>
                            {f.label}{f.required && <span style={{ color: SR.coral }}> *</span>}
                        </label>
                        <input
                            type={f.type} placeholder={f.placeholder}
                            value={answers[f.key] || ''}
                            onChange={e => setSingle(f.key, e.target.value)}
                            style={inputStyle}
                        />
                    </div>
                ))}
                <p style={{ color: SR.midGray, fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    🔒 Your information is private and will never be shared.
                </p>
            </div>
        );

        return null;
    };

    // ── Quiz screen ────────────────────────────────────────────────────────
    return (
        <div style={{
            minHeight: '100vh', background: SR.heroGradient, fontFamily: SR.font,
            paddingTop: 80, display: 'flex', flexDirection: 'column', alignItems: 'center',
        }}>
            {/* Progress bar */}
            <div style={{ position: 'fixed', top: 0, left: 0, right: 0, height: 4, zIndex: 999, background: 'rgba(247,161,79,0.12)' }}>
                <div style={{ height: '100%', background: SR.btnGradient, width: `${progress}%`, transition: 'width 0.4s ease', boxShadow: `0 0 10px ${SR.orange}` }} />
            </div>

            <div style={{ width: '100%', maxWidth: 640, padding: '2rem 1.5rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
                {/* Step dots */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                        {STEPS.map((_, i) => (
                            <div key={i} style={{
                                height: 4, borderRadius: 2, width: i <= step ? 24 : 16,
                                background: i < step ? SR.btnGradient : i === step ? SR.orange : SR.border,
                                transition: 'all 0.3s ease',
                            }} />
                        ))}
                    </div>
                    <span style={{ color: SR.midGray, fontSize: '0.82rem', fontWeight: 600 }}>{step + 1} of {total}</span>
                </div>

                {/* Question card */}
                <div key={animKey} style={{
                    background: SR.white, borderRadius: 28, padding: '2.5rem',
                    boxShadow: '0 12px 50px rgba(247,161,79,0.12)', border: `1px solid ${SR.border}`,
                    animation: `quizSlide${dir > 0 ? 'In' : 'Back'} 0.35s ease-out`, flex: 1,
                }}>
                    <div style={{
                        width: 52, height: 52, borderRadius: SR.md,
                        background: 'linear-gradient(135deg, rgba(247,161,79,0.15), rgba(240,122,99,0.15))',
                        border: `1px solid rgba(247,161,79,0.25)`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.5rem', marginBottom: '1.5rem',
                    }}>
                        {current.icon}
                    </div>
                    <h2 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.9rem)', fontWeight: 800, color: SR.dark, letterSpacing: '-0.02em', marginBottom: '0.5rem', lineHeight: 1.25 }}>
                        {current.question}
                    </h2>
                    <p style={{ color: SR.gray, fontSize: '0.95rem', marginBottom: '2rem', lineHeight: 1.6 }}>
                        {current.subtitle}
                    </p>

                    {error && (
                        <div style={{ padding: '0.75rem 1rem', background: 'rgba(240,122,99,0.1)', border: `1px solid ${SR.coral}`, borderRadius: SR.md, color: SR.coral, fontSize: '0.88rem', marginBottom: '1rem' }}>
                            {error}
                        </div>
                    )}

                    {renderContent()}
                </div>

                {/* Navigation */}
                <div style={{ display: 'flex', justifyContent: step === 0 ? 'flex-end' : 'space-between', alignItems: 'center', marginTop: '1.5rem', gap: '1rem' }}>
                    {step > 0 && (
                        <button onClick={handleBack} style={{
                            background: 'none', border: `1.5px solid ${SR.border}`, color: SR.gray,
                            borderRadius: SR.pill, padding: '0.75rem 1.5rem', fontWeight: 600,
                            cursor: 'pointer', fontSize: '0.95rem', fontFamily: SR.font, transition: 'all 0.2s',
                        }}>
                            ← Back
                        </button>
                    )}
                    <button onClick={handleNext} disabled={!canContinue()} style={{
                        ...btnPrimary, opacity: canContinue() ? 1 : 0.45,
                        cursor: canContinue() ? 'pointer' : 'default',
                        minWidth: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                    }}>
                        {step === total - 1 ? 'See My Free Report →' : 'Continue →'}
                    </button>
                </div>

                {current.type !== 'url' && current.type !== 'competitor' && current.type !== 'contact' && (
                    <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                        <button onClick={() => goTo(step + 1, 1)} style={{
                            background: 'none', border: 'none', color: SR.midGray,
                            cursor: 'pointer', fontSize: '0.82rem', textDecoration: 'underline', fontFamily: SR.font,
                        }}>
                            Skip this step
                        </button>
                    </div>
                )}
            </div>

            <style>{`
                @keyframes quizSlideIn   { from { opacity: 0; transform: translateX(30px);  } to { opacity: 1; transform: translateX(0); } }
                @keyframes quizSlideBack { from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); } }
                @keyframes spin          { to   { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

export default QuizPage;
