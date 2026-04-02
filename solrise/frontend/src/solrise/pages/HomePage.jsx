import React, { useState, useEffect, useRef } from 'react';
import { SR, gradientText, btnPrimary, btnOutline } from '../tokens';
import { SunIcon } from '../components/SunLogo';
import SolRiseLogo from '../components/SunLogo';

const STATS = [
    { label: 'Avg SEO Score Improvement',  icon: '📊', value: 93, prefix: '',  suffix: '%'  },
    { label: 'Avg GEO Score Improvement',  icon: '📈', value: 75, prefix: '+', suffix: '%'  },
    { label: 'Human & AI Monitoring',       icon: '🧑‍💼', value: 24, prefix: '',  suffix: '/7' },
    { label: 'Minutes to Full Report',      icon: '⚡',   value: 5,  prefix: '<', suffix: ' min' },
];

const StatCard = ({ s }) => {
    const [count, setCount] = useState(0);
    const ref = useRef(null);
    const started = useRef(false);

    useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting && !started.current) {
                started.current = true;
                const duration = 1400;
                const start = performance.now();
                const animate = (now) => {
                    const elapsed = now - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const eased = 1 - Math.pow(1 - progress, 3);
                    setCount(Math.round(eased * s.value));
                    if (progress < 1) requestAnimationFrame(animate);
                };
                requestAnimationFrame(animate);
            }
        }, { threshold: 0.4 });
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [s.value]);

    return (
        <div ref={ref} style={{
            textAlign: 'center', padding: '2rem 1.5rem',
            borderRadius: SR.lg, background: SR.bg,
            border: '1px solid rgba(247,161,79,0.18)',
            transition: 'all 0.25s ease',
            cursor: 'default',
        }}>
            <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.6rem' }}>{s.icon}</span>
            <div style={{ fontSize: '2.4rem', fontWeight: 800, ...gradientText, marginBottom: '0.35rem' }}>
                {s.prefix}{count}{s.suffix}
            </div>
            <div style={{ fontSize: '0.88rem', color: SR.gray, fontWeight: 500 }}>{s.label}</div>
        </div>
    );
};

const SERVICES = [
    { icon: '🔍', title: 'SEO Optimisation',     desc: 'Rank higher on Google with data-driven keyword strategy and technical SEO.',                                         color: SR.sky      },
    { icon: '🤖', title: 'GEO (AI Search)',       desc: 'Get cited by ChatGPT, Perplexity, Gemini, Claude, Copilot & Google AI Overviews.',                                  color: SR.orange   },
    { icon: '🎯', title: 'Competitor Intel',      desc: 'Know exactly what your competitors rank for and how to beat them.',                                                 color: SR.coral    },
    { icon: '⚡', title: 'AI Website Generation', desc: 'Generate or update your existing website with fully optimised, schema-rich content from your analysis.',            color: SR.pink     },
];

const StepCard = ({ s, onClick }) => {
    const [hovered, setHovered] = useState(false);
    return (
        <div
            onClick={onClick}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                display: 'flex', alignItems: 'flex-start', gap: '1.5rem',
                background: hovered ? SR.white : SR.lightGray,
                borderRadius: SR.xl,
                padding: '1.75rem 2rem',
                border: `1px solid ${hovered ? SR.orange : SR.border}`,
                transform: hovered ? 'scale(1.025)' : 'scale(1)',
                boxShadow: hovered ? '0 8px 32px rgba(247,161,79,0.15)' : 'none',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease',
                cursor: 'pointer',
            }}
        >
            <div style={{
                flexShrink: 0, width: 52, height: 52,
                borderRadius: SR.md, background: SR.btnGradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 800, color: SR.white, fontSize: '0.9rem',
                boxShadow: SR.btnShadow,
            }}>
                {s.num}
            </div>
            <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: SR.dark, marginBottom: '0.4rem' }}>
                    {s.title}
                </h3>
                <p style={{ fontSize: '0.9rem', color: SR.gray, lineHeight: 1.65, margin: 0 }}>
                    {s.desc}
                </p>
            </div>
            <span style={{
                flexShrink: 0, fontSize: '1.1rem',
                color: hovered ? SR.orange : SR.midGray,
                transition: 'color 0.2s ease, transform 0.2s ease',
                transform: hovered ? 'translateX(4px)' : 'translateX(0)',
                display: 'inline-block',
            }}>→</span>
        </div>
    );
};

const STEPS = [
    { num: '01', title: 'We Analyse Your Site',      desc: 'Our AI scans your entire website, competitors, and keyword landscape.' },
    { num: '02', title: 'You Get a Full Report',     desc: 'A clear PDF report with scores, keyword gaps, and GEO readiness.' },
    { num: '03', title: 'We Build Your Action Plan', desc: 'Step-by-step recommendations you can act on immediately.' },
    { num: '04', title: 'We Build or Optimise Your Website', desc: 'We create a new website from scratch or optimise your existing one to maximise your SEO and GEO scores.' },
];

const HomePage = ({ setActiveTab }) => {
    const [vis, setVis] = useState(new Set());
    const [hoveredService, setHoveredService] = useState(null);

    useEffect(() => {
        [0, 1, 2, 3, 4].forEach((i, _, arr) =>
            setTimeout(() => setVis(prev => new Set([...prev, i])), 120 + i * 180)
        );
    }, []);

    const anim = (i) => ({
        opacity:   vis.has(i) ? 1 : 0,
        transform: vis.has(i) ? 'translateY(0)' : 'translateY(28px)',
        transition: 'opacity 0.7s ease-out, transform 0.7s ease-out',
    });

    return (
        <main style={{ fontFamily: SR.font, background: SR.bg }}>
            {/* ── Hero ─────────────────────────────────────────────── */}
            <section style={{
                minHeight: '100vh',
                background: SR.heroGradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                paddingTop: 80, position: 'relative', overflow: 'hidden',
            }}>
                {/* Decorative blobs */}
                <div style={{
                    position: 'absolute', top: '8%', right: '6%',
                    width: 420, height: 420, borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(247,161,79,0.14) 0%, transparent 70%)',
                    pointerEvents: 'none',
                }} />
                <div style={{
                    position: 'absolute', bottom: '10%', left: '-5%',
                    width: 360, height: 360, borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(110,169,214,0.12) 0%, transparent 70%)',
                    pointerEvents: 'none',
                }} />

                <div style={{
                    textAlign: 'center', maxWidth: 820, padding: '2rem',
                    position: 'relative', zIndex: 2,
                }}>
                    {/* Logo */}
                    <div style={{ ...anim(0), display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
                        <SolRiseLogo size={64} textSize="2.2rem" />
                    </div>

                    {/* Badge */}
                    <div style={{
                        ...anim(0),
                        display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                        background: 'rgba(247,161,79,0.12)',
                        border: `1px solid rgba(247,161,79,0.28)`,
                        color: SR.coral, padding: '0.45rem 1.1rem',
                        borderRadius: SR.pill, fontSize: '0.88rem', fontWeight: 600,
                        marginBottom: '2rem',
                    }}>
                        ✦ Data-Driven Marketing Agency
                    </div>

                    {/* Headline */}
                    <h1 style={{
                        ...anim(1),
                        fontSize: 'clamp(2.8rem, 5.5vw, 4.5rem)',
                        fontWeight: 800, lineHeight: 1.15,
                        marginBottom: '1.25rem',
                        color: SR.dark,
                        letterSpacing: '-0.03em',
                    }}>
                        Help your business{' '}
                        <span style={gradientText}>rise</span>{' '}
                        to the top
                    </h1>

                    <p style={{
                        ...anim(2),
                        fontSize: 'clamp(1rem, 1.8vw, 1.15rem)',
                        color: SR.gray, lineHeight: 1.75,
                        maxWidth: 720, margin: '0 auto 2.5rem',
                    }}>
                        We use AI, web scraping & advanced analytics to put your business in front of the right people, on <strong style={{textDecoration:'underline'}}>Google</strong> and in <strong style={{textDecoration:'underline'}}>AI</strong> answers.
                    </p>

                    {/* CTAs */}
                    <div style={{
                        ...anim(3),
                        display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap',
                    }}>
                        <button onClick={() => setActiveTab('quiz')}
                            style={btnPrimary}
                            onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.06)'}
                            onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                        >
                            Get Free Analysis →
                        </button>
                        <button onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                            style={btnOutline}
                            onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.06)'}
                            onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                        >
                            See How It Works
                        </button>
                    </div>

                    {/* Social proof micro-copy */}
                    <div style={{
                        ...anim(4),
                        marginTop: '2.5rem', color: SR.midGray,
                        fontSize: '0.85rem', display: 'flex',
                        alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                    }}>
                        <span>✓ No credit card</span>
                        <span style={{ opacity: 0.35 }}>·</span>
                        <span>✓ Immediate report</span>
                        <span style={{ opacity: 0.35 }}>·</span>
                        <span>✓ 100% personalised</span>
                    </div>
                </div>

                {/* Large sun watermark */}
                <div style={{
                    position: 'absolute', bottom: -60, left: '50%',
                    transform: 'translateX(-50%)',
                    opacity: 0.06, pointerEvents: 'none',
                }}>
                    <SunIcon size={520} />
                </div>
            </section>

            {/* ── Stats ─────────────────────────────────────────────── */}
            <section style={{ background: SR.white, padding: '4rem 2rem' }}>
                <div style={{
                    maxWidth: 1100, margin: '0 auto',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1.5rem',
                }}>
                    {STATS.map((s, i) => <StatCard key={i} s={s} />)}
                </div>
            </section>

            {/* ── Services Preview ─────────────────────────────────── */}
            <section style={{ background: SR.bg, padding: '2rem 2rem 5rem' }}>
                <div style={{ maxWidth: 1100, margin: '0 auto' }}>
                    <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                        <h2 style={{
                            fontSize: 'clamp(1.8rem, 3vw, 2.5rem)', fontWeight: 800,
                            color: SR.dark, letterSpacing: '-0.02em', marginBottom: '0.75rem',
                        }}>
                            Everything your business needs to{' '}
                            <span style={gradientText}>get found</span>
                        </h2>
                        <p style={{ color: SR.gray, fontSize: '1.05rem', maxWidth: 500, margin: '0 auto' }}>
                            One platform. Dual optimisation. Real results.
                        </p>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                        gap: '1.5rem',
                    }}>
                        {SERVICES.map((s, i) => (
                            <div key={i}
                                onMouseEnter={() => setHoveredService(i)}
                                onMouseLeave={() => setHoveredService(null)}
                                style={{
                                    background: SR.white, padding: '2rem',
                                    borderRadius: SR.xl,
                                    border: `${hoveredService === i ? '2px' : '1px'} solid ${hoveredService === i ? s.color : SR.border}`,
                                    borderTop: `3px solid ${s.color}`,
                                    boxShadow: hoveredService === i ? `0 12px 48px ${s.color}55` : SR.cardShadow,
                                    transform: hoveredService === i ? 'scale(1.03)' : 'scale(1)',
                                    transition: 'all 0.25s ease',
                                    cursor: 'default',
                                }}>
                                <div style={{
                                    width: 52, height: 52,
                                    background: `${s.color}18`,
                                    border: `1px solid ${s.color}33`,
                                    borderRadius: SR.md, display: 'flex',
                                    alignItems: 'center', justifyContent: 'center',
                                    fontSize: '1.5rem', marginBottom: '1.25rem',
                                }}>
                                    {s.icon}
                                </div>
                                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: SR.dark, marginBottom: '0.6rem' }}>
                                    {s.title}
                                </h3>
                                <p style={{ fontSize: '0.9rem', color: SR.gray, lineHeight: 1.65 }}>
                                    {s.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── How It Works ─────────────────────────────────────── */}
            <section id="how-it-works" style={{ background: SR.white, padding: '5rem 2rem' }}>
                <div style={{ maxWidth: 900, margin: '0 auto' }}>
                    <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
                        <h2 style={{
                            fontSize: 'clamp(1.8rem, 3vw, 2.4rem)',
                            fontWeight: 800, color: SR.dark,
                            letterSpacing: '-0.02em', marginBottom: '0.75rem',
                        }}>
                            How it works
                        </h2>
                        <p style={{ color: SR.gray, fontSize: '1rem' }}>Four simple steps to a stronger online presence.</p>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {STEPS.map((s, i) => (
                            <StepCard key={i} s={s} onClick={() => setActiveTab('quiz')} />
                        ))}
                    </div>
                </div>
            </section>

            {/* ── CTA Banner ───────────────────────────────────────── */}
            <section style={{ padding: '2rem 2rem 5rem', background: SR.bg }}>
                <div style={{
                    maxWidth: 740, margin: '0 auto', textAlign: 'center',
                    background: `linear-gradient(135deg, ${SR.orange}, ${SR.coral})`,
                    borderRadius: 32, padding: '3.5rem 2.5rem',
                    boxShadow: '0 20px 60px rgba(240,122,99,0.3)',
                    position: 'relative', overflow: 'hidden',
                }}>
                    {/* Watermark sun */}
                    <div style={{
                        position: 'absolute', right: -40, top: -40, opacity: 0.12, pointerEvents: 'none',
                    }}>
                        <SunIcon size={200} />
                    </div>

                    <h2 style={{
                        fontSize: 'clamp(1.8rem, 3.5vw, 2.5rem)',
                        fontWeight: 800, color: SR.white,
                        marginBottom: '1rem', letterSpacing: '-0.02em',
                        position: 'relative', zIndex: 1,
                    }}>
                        Your free report is waiting
                    </h2>
                    <p style={{
                        color: 'rgba(255,255,255,0.88)', fontSize: '1.05rem',
                        lineHeight: 1.7, marginBottom: '2rem',
                        position: 'relative', zIndex: 1,
                        textAlign: 'center',
                    }}>
                        Answer 5 quick questions and we'll deliver a personalised SEO & GEO analysis straight to your inbox.
                    </p>
                    <button
                        onClick={() => setActiveTab('quiz')}
                        style={{
                            background: SR.white, color: SR.coral,
                            border: 'none', borderRadius: SR.pill,
                            padding: '0.9rem 2.5rem', fontWeight: 800,
                            cursor: 'pointer', fontSize: '1rem',
                            boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                            position: 'relative', zIndex: 1,
                        }}
                    >
                        Start Free Analysis →
                    </button>
                </div>
            </section>
        </main>
    );
};

export default HomePage;
