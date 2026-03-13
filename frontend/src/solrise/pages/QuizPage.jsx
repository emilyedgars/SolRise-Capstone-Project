import React, { useState } from 'react';
import { SR, gradientText, btnPrimary } from '../tokens';
import { SunIcon } from '../components/SunLogo';

// ── Quiz step definitions ──────────────────────────────────────────────────
const STEPS = [
    {
        id: 'url',
        icon: '🌐',
        question: "What's your website URL?",
        subtitle: "We'll run a live AI scan on your site — for free.",
        type: 'url',
        field: 'website',
        placeholder: 'https://yourbusiness.com',
        validate: v => v && v.includes('.'),
    },
    {
        id: 'industry',
        icon: '🏢',
        question: 'What industry are you in?',
        subtitle: "We'll benchmark you against the right competitors.",
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
            { value: 'geo',    icon: '🤖', title: 'Appear in AI Answers',    desc: 'Get cited by ChatGPT & Perplexity' },
            { value: 'both',   icon: '⚡', title: 'Both — I want it all',    desc: 'Full SEO + GEO optimisation' },
            { value: 'unsure', icon: '🗺️', title: "I'm Not Sure Yet",       desc: "Let's figure it out together" },
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
        icon: '📬',
        question: 'Where should we send your report?',
        subtitle: 'Your personalised AI analysis will be ready within 24 hours.',
        type: 'contact',
        fields: [
            { key: 'name',  label: 'Your Full Name',  type: 'text',  placeholder: 'Jane Smith',              required: true },
            { key: 'email', label: 'Email Address',   type: 'email', placeholder: 'jane@yourbusiness.com',  required: true },
            { key: 'phone', label: 'Phone (optional)', type: 'tel',  placeholder: '+34 600 000 000',         required: false },
        ],
    },
];

// ── Shared styles ─────────────────────────────────────────────────────────
const inputStyle = {
    width: '100%', padding: '0.9rem 1.1rem',
    border: `1.5px solid ${SR.border}`,
    borderRadius: SR.md, fontSize: '1rem',
    fontFamily: SR.font, color: SR.dark,
    background: SR.white, outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.2s',
};

// ── Main QuizPage component ───────────────────────────────────────────────
const QuizPage = ({ setActiveTab }) => {
    const [step,      setStep]      = useState(0);
    const [answers,   setAnswers]   = useState({});
    const [submitted, setSubmitted] = useState(false);
    const [submitting,setSubmitting]= useState(false);
    const [dir,       setDir]       = useState(1);  // 1 = forward, -1 = back
    const [animKey,   setAnimKey]   = useState(0);  // force re-mount for animation

    const current = STEPS[step];
    const total   = STEPS.length;
    const progress = ((step) / total) * 100;

    // ── navigation ────────────────────────────────────────────────────────
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
        if (s.type === 'contact') {
            return s.fields.filter(f => f.required).every(f => answers[f.key]);
        }
        if (s.validate) return s.validate(val);
        return !!val;
    };

    const handleNext = async () => {
        if (step < total - 1) {
            goTo(step + 1, 1);
        } else {
            setSubmitting(true);
            await new Promise(r => setTimeout(r, 1600));
            setSubmitting(false);
            setSubmitted(true);
        }
    };

    const handleBack = () => {
        if (step > 0) goTo(step - 1, -1);
    };

    // ── answer setters ────────────────────────────────────────────────────
    const setSingle = (field, value) => setAnswers(a => ({ ...a, [field]: value }));
    const toggleMulti = (field, value) => setAnswers(a => {
        const cur = a[field] || [];
        return { ...a, [field]: cur.includes(value) ? cur.filter(v => v !== value) : [...cur, value] };
    });

    // ── render step content ───────────────────────────────────────────────
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

        if (s.type === 'pills') return (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', justifyContent: 'center' }}>
                {s.options.map(opt => {
                    const selected = answers[s.field] === opt;
                    return (
                        <button
                            key={opt}
                            onClick={() => setSingle(s.field, opt)}
                            style={{
                                padding: '0.6rem 1.2rem',
                                borderRadius: SR.pill,
                                border: `1.5px solid ${selected ? SR.orange : SR.border}`,
                                background: selected
                                    ? 'linear-gradient(135deg, rgba(247,161,79,0.15), rgba(240,122,99,0.15))'
                                    : SR.white,
                                color: selected ? SR.coral : SR.gray,
                                fontWeight: selected ? 700 : 500,
                                cursor: 'pointer',
                                fontSize: '0.9rem',
                                fontFamily: SR.font,
                                transition: 'all 0.18s ease',
                            }}
                        >
                            {opt}
                        </button>
                    );
                })}
            </div>
        );

        if (s.type === 'cards') return (
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '1rem',
            }}>
                {s.options.map(opt => {
                    const selected = answers[s.field] === opt.value;
                    return (
                        <button
                            key={opt.value}
                            onClick={() => setSingle(s.field, opt.value)}
                            style={{
                                padding: '1.5rem 1.25rem',
                                borderRadius: SR.xl,
                                border: `2px solid ${selected ? SR.orange : SR.border}`,
                                background: selected
                                    ? 'linear-gradient(135deg, rgba(247,161,79,0.12), rgba(240,122,99,0.12))'
                                    : SR.white,
                                cursor: 'pointer', textAlign: 'center',
                                fontFamily: SR.font,
                                boxShadow: selected ? `0 0 0 4px rgba(247,161,79,0.18)` : SR.cardShadow,
                                transition: 'all 0.2s ease',
                            }}
                        >
                            <div style={{ fontSize: '2rem', marginBottom: '0.6rem' }}>{opt.icon}</div>
                            <div style={{
                                fontWeight: 700, fontSize: '0.95rem',
                                color: selected ? SR.coral : SR.dark,
                                marginBottom: '0.35rem',
                            }}>
                                {opt.title}
                            </div>
                            <div style={{ fontSize: '0.78rem', color: SR.midGray, lineHeight: 1.4 }}>
                                {opt.desc}
                            </div>
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
                        <button
                            key={opt}
                            onClick={() => toggleMulti(s.field, opt)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '0.85rem',
                                padding: '0.9rem 1.2rem',
                                borderRadius: SR.md,
                                border: `1.5px solid ${selected ? SR.orange : SR.border}`,
                                background: selected
                                    ? 'linear-gradient(90deg, rgba(247,161,79,0.1), rgba(240,122,99,0.08))'
                                    : SR.white,
                                cursor: 'pointer', textAlign: 'left',
                                fontFamily: SR.font, transition: 'all 0.18s ease',
                            }}
                        >
                            <div style={{
                                width: 22, height: 22, borderRadius: 6, flexShrink: 0,
                                border: `2px solid ${selected ? SR.orange : SR.border}`,
                                background: selected ? SR.btnGradient : 'transparent',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all 0.15s',
                            }}>
                                {selected && <span style={{ color: 'white', fontSize: '0.75rem', fontWeight: 800 }}>✓</span>}
                            </div>
                            <span style={{
                                fontSize: '0.95rem', fontWeight: selected ? 600 : 400,
                                color: selected ? SR.dark : SR.gray,
                            }}>
                                {opt}
                            </span>
                        </button>
                    );
                })}
            </div>
        );

        if (s.type === 'contact') return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {s.fields.map(f => (
                    <div key={f.key}>
                        <label style={{
                            display: 'block', fontWeight: 600,
                            fontSize: '0.88rem', color: SR.dark,
                            marginBottom: '0.4rem',
                        }}>
                            {f.label}{f.required && <span style={{ color: SR.coral }}> *</span>}
                        </label>
                        <input
                            type={f.type}
                            placeholder={f.placeholder}
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

    // ── Success screen ─────────────────────────────────────────────────────
    if (submitted) return (
        <div style={{
            minHeight: '100vh', display: 'flex', alignItems: 'center',
            justifyContent: 'center', background: SR.heroGradient,
            paddingTop: 80, fontFamily: SR.font,
        }}>
            <div style={{
                textAlign: 'center', maxWidth: 560, padding: '3rem 2rem',
                background: SR.white, borderRadius: 32,
                boxShadow: '0 24px 80px rgba(247,161,79,0.18)',
                border: `1px solid ${SR.border}`,
            }}>
                <div style={{ marginBottom: '1.5rem' }}>
                    <SunIcon size={72} />
                </div>
                <h2 style={{
                    fontSize: '2rem', fontWeight: 800, color: SR.dark,
                    marginBottom: '0.75rem', letterSpacing: '-0.02em',
                }}>
                    You're all set!
                </h2>
                <p style={{
                    color: SR.gray, fontSize: '1.05rem', lineHeight: 1.7,
                    marginBottom: '0.5rem',
                }}>
                    We're analysing <strong style={{ color: SR.dark }}>{answers.website || 'your website'}</strong> right now.
                    Your personalised SEO & GEO report will land in your inbox within 24 hours.
                </p>
                <p style={{ color: SR.midGray, fontSize: '0.88rem', marginBottom: '2.5rem' }}>
                    📬 We'll send it to <strong>{answers.email}</strong>
                </p>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button
                        onClick={() => setActiveTab && setActiveTab('home')}
                        style={{
                            background: 'none', color: SR.gray, border: `1.5px solid ${SR.border}`,
                            borderRadius: SR.pill, padding: '0.8rem 1.6rem',
                            cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem',
                            fontFamily: SR.font,
                        }}
                    >
                        Back to Home
                    </button>
                </div>
            </div>
        </div>
    );

    // ── Quiz screen ────────────────────────────────────────────────────────
    return (
        <div style={{
            minHeight: '100vh',
            background: SR.heroGradient,
            fontFamily: SR.font,
            paddingTop: 80,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
        }}>
            {/* Progress bar */}
            <div style={{
                position: 'fixed', top: 0, left: 0, right: 0,
                height: 4, zIndex: 999, background: 'rgba(247,161,79,0.12)',
            }}>
                <div style={{
                    height: '100%', background: SR.btnGradient,
                    width: `${progress}%`,
                    transition: 'width 0.4s ease',
                    boxShadow: `0 0 10px ${SR.orange}`,
                }} />
            </div>

            <div style={{
                width: '100%', maxWidth: 640,
                padding: '2rem 1.5rem',
                flex: 1, display: 'flex', flexDirection: 'column',
            }}>
                {/* Step counter */}
                <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: '2.5rem',
                }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                        {STEPS.map((_, i) => (
                            <div key={i} style={{
                                height: 4, borderRadius: 2,
                                width: i <= step ? 24 : 16,
                                background: i < step
                                    ? SR.btnGradient
                                    : i === step
                                        ? SR.orange
                                        : SR.border,
                                transition: 'all 0.3s ease',
                            }} />
                        ))}
                    </div>
                    <span style={{ color: SR.midGray, fontSize: '0.82rem', fontWeight: 600 }}>
                        {step + 1} of {total}
                    </span>
                </div>

                {/* Question card */}
                <div
                    key={animKey}
                    style={{
                        background: SR.white,
                        borderRadius: 28,
                        padding: '2.5rem',
                        boxShadow: '0 12px 50px rgba(247,161,79,0.12)',
                        border: `1px solid ${SR.border}`,
                        animation: `quizSlide${dir > 0 ? 'In' : 'Back'} 0.35s ease-out`,
                        flex: 1,
                    }}
                >
                    {/* Step icon */}
                    <div style={{
                        width: 52, height: 52, borderRadius: SR.md,
                        background: 'linear-gradient(135deg, rgba(247,161,79,0.15), rgba(240,122,99,0.15))',
                        border: `1px solid rgba(247,161,79,0.25)`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.5rem', marginBottom: '1.5rem',
                    }}>
                        {current.icon}
                    </div>

                    {/* Question */}
                    <h2 style={{
                        fontSize: 'clamp(1.4rem, 3vw, 1.9rem)',
                        fontWeight: 800, color: SR.dark,
                        letterSpacing: '-0.02em', marginBottom: '0.5rem',
                        lineHeight: 1.25,
                    }}>
                        {current.question}
                    </h2>
                    <p style={{
                        color: SR.gray, fontSize: '0.95rem',
                        marginBottom: '2rem', lineHeight: 1.6,
                    }}>
                        {current.subtitle}
                    </p>

                    {renderContent()}
                </div>

                {/* Navigation buttons */}
                <div style={{
                    display: 'flex',
                    justifyContent: step === 0 ? 'flex-end' : 'space-between',
                    alignItems: 'center',
                    marginTop: '1.5rem', gap: '1rem',
                }}>
                    {step > 0 && (
                        <button
                            onClick={handleBack}
                            style={{
                                background: 'none', border: `1.5px solid ${SR.border}`,
                                color: SR.gray, borderRadius: SR.pill,
                                padding: '0.75rem 1.5rem', fontWeight: 600,
                                cursor: 'pointer', fontSize: '0.95rem',
                                fontFamily: SR.font, transition: 'all 0.2s',
                            }}
                        >
                            ← Back
                        </button>
                    )}

                    <button
                        onClick={handleNext}
                        disabled={!canContinue() || submitting}
                        style={{
                            ...btnPrimary,
                            opacity: canContinue() ? 1 : 0.45,
                            cursor: canContinue() ? 'pointer' : 'default',
                            minWidth: 180,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                        }}
                    >
                        {submitting ? (
                            <>
                                <span style={{
                                    width: 16, height: 16, border: '2px solid rgba(255,255,255,0.4)',
                                    borderTop: '2px solid white', borderRadius: '50%',
                                    animation: 'spin 0.8s linear infinite', display: 'inline-block',
                                }} />
                                Sending…
                            </>
                        ) : step === total - 1 ? (
                            'Get My Free Report →'
                        ) : (
                            'Continue →'
                        )}
                    </button>
                </div>

                {/* Skip link for optional steps */}
                {current.type !== 'url' && current.type !== 'contact' && (
                    <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                        <button
                            onClick={() => goTo(step + 1, 1)}
                            style={{
                                background: 'none', border: 'none',
                                color: SR.midGray, cursor: 'pointer',
                                fontSize: '0.82rem', textDecoration: 'underline',
                                fontFamily: SR.font,
                            }}
                        >
                            Skip this step
                        </button>
                    </div>
                )}
            </div>

            {/* Keyframe animations injected inline */}
            <style>{`
                @keyframes quizSlideIn {
                    from { opacity: 0; transform: translateX(30px); }
                    to   { opacity: 1; transform: translateX(0); }
                }
                @keyframes quizSlideBack {
                    from { opacity: 0; transform: translateX(-30px); }
                    to   { opacity: 1; transform: translateX(0); }
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

export default QuizPage;
