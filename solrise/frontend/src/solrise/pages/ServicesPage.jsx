import React, { useState } from 'react';
import { SR, gradientText, btnPrimary } from '../tokens';

const SERVICES = [
    {
        icon: '🔍', tag: 'Search Rankings',
        title: 'SEO Optimisation',
        desc: 'Search Engine Optimisation improves how your website ranks on Google. We analyse your keywords, fix technical issues, and optimise your content so the right people find you first.',
        features: ['TF-IDF + semantic keyword analysis', 'Technical SEO audit & on-page fixes', 'Schema markup implementation', 'Keyword gap & competitor benchmarking'],
        color: SR.sky,
    },
    {
        icon: '🌐', tag: 'AI Visibility',
        title: 'GEO (AI Search)',
        desc: 'Generative Engine Optimisation gets your business cited by AI systems like ChatGPT, Perplexity, Gemini, Claude, Copilot & Google AI Overviews. The new frontier of search where traditional SEO is not enough.',
        features: ['GEO citation & extractability scoring', 'Claim density & citability analysis', 'FAQ & structured content for AI answers', 'Readability optimisation for AI parsing'],
        color: SR.orange,
    },
    {
        icon: '🎯', tag: 'Intelligence',
        title: 'Competitor Intel',
        desc: 'See exactly what your top competitors are doing online and where you can overtake them. We scan their websites, spot the gaps, and show you what to do about it.',
        features: ['Topics & keywords they rank for that you don\'t', 'Side-by-side score comparison against each competitor', 'Content and messaging gaps you can win back', 'Actionable opportunities ranked by impact'],
        color: SR.coral,
    },
    {
        icon: '📊', tag: 'Analytics',
        title: 'Advanced Analytics',
        desc: 'We turn your data into a clear, actionable report your in-house marketing team can actually use. No guesswork, no jargon, just the numbers that matter.',
        features: ['Branded PDF report with scores & keyword gaps', 'ROI-focused insights your team can act on today', 'Competitor benchmarking in plain language', 'Trend signals to guide your next campaign'],
        color: SR.yellow,
    },
    {
        icon: '⚡', tag: 'AI Generation',
        title: 'Website Generation',
        desc: 'Every insight from your analysis is fed directly into building or refreshing your website: keyword gaps, GEO readiness, competitor benchmarks, and content recommendations. The result is a site that is optimised from day one.',
        features: ['SEO & GEO findings baked into every page', 'Schema markup added automatically', 'Competitor gaps addressed in your content', 'AI-generated copy validated for quality & accuracy'],
        color: SR.pink,
    },
    {
        icon: '🧑‍💼', tag: 'Human-in-the-Loop',
        title: 'Marketing Analyst Review',
        desc: 'Every AI output is reviewed by a professional marketing analyst. We ensure strategy, tone, and accuracy are on point. The best results come from AI and human expertise working together.',
        features: ['Expert review of all AI-generated content', 'Strategic alignment & brand consistency', 'Quality assurance before delivery', 'Ongoing analyst support & feedback loop'],
        color: SR.lavender,
    },
];

const ServicesPage = ({ setActiveTab }) => {
    const [hovered, setHovered] = useState(null);

    return (
        <main style={{ paddingTop: 80, fontFamily: SR.font, background: SR.bg }}>
            {/* Hero */}
            <section style={{
                padding: '5rem 2rem 3rem',
                background: SR.heroGradient,
                textAlign: 'center',
            }}>
                <div style={{ maxWidth: 640, margin: '0 auto' }}>
                    <div style={{
                        display: 'inline-block',
                        background: 'rgba(247,161,79,0.12)',
                        border: `1px solid rgba(247,161,79,0.28)`,
                        color: SR.coral, padding: '0.4rem 1rem',
                        borderRadius: SR.pill, fontSize: '0.85rem', fontWeight: 600,
                        marginBottom: '1.5rem',
                    }}>
                        What We Do
                    </div>
                    <h1 style={{
                        fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 800,
                        color: SR.dark, letterSpacing: '-0.02em',
                        marginBottom: '1rem', lineHeight: 1.2,
                    }}>
                        Full-stack AI marketing that <span style={gradientText}>actually impacts</span>
                    </h1>
                    <p style={{ color: SR.gray, fontSize: '1.05rem', lineHeight: 1.7, whiteSpace: 'nowrap' }}>
                        From technical SEO to AI search visibility, we cover every angle so you don't have to.
                    </p>
                </div>
            </section>

            {/* Services grid */}
            <section style={{ padding: '4rem 2rem' }}>
                <div style={{
                    maxWidth: 1150, margin: '0 auto',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                    gap: '1.75rem',
                }}>
                    {SERVICES.map((s, i) => (
                        <div
                            key={i}
                            onMouseEnter={() => setHovered(i)}
                            onMouseLeave={() => setHovered(null)}
                            style={{
                                background: SR.white,
                                borderRadius: SR.xl,
                                padding: '2.25rem',
                                border: `${hovered === i ? '2px' : '1px'} solid ${hovered === i ? s.color : SR.border}`,
                                boxShadow: hovered === i ? `0 12px 48px ${s.color}55` : SR.cardShadow,
                                transform: hovered === i ? 'scale(1.03)' : 'scale(1)',
                                transition: 'all 0.25s ease',
                                borderTop: `3px solid ${s.color}`,
                                cursor: 'default',
                            }}
                        >
                            {/* Icon + tag */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
                                <div style={{
                                    width: 56, height: 56, borderRadius: SR.md,
                                    background: `${s.color}18`,
                                    border: `1px solid ${s.color}33`,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '1.5rem', flexShrink: 0,
                                }}>
                                    {s.icon}
                                </div>
                                <span style={{
                                    background: `${s.color}18`,
                                    color: s.color, border: `1px solid ${s.color}44`,
                                    padding: '0.25rem 0.7rem', borderRadius: SR.pill,
                                    fontSize: '0.75rem', fontWeight: 700,
                                }}>
                                    {s.tag}
                                </span>
                            </div>

                            <h3 style={{
                                fontSize: '1.25rem', fontWeight: 700,
                                color: SR.dark, marginBottom: '0.65rem',
                            }}>
                                {s.title}
                            </h3>
                            <p style={{
                                color: SR.gray, lineHeight: 1.65, fontSize: '0.92rem',
                                marginBottom: '1.25rem',
                            }}>
                                {s.desc}
                            </p>
                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                                {s.features.map((f, j) => (
                                    <li key={j} style={{
                                        color: SR.gray, fontSize: '0.88rem',
                                        marginBottom: '0.45rem',
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                    }}>
                                        <span style={{ color: s.color, fontWeight: 700 }}>✓</span> {f}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section style={{ padding: '4rem 2rem', textAlign: 'center', background: SR.white }}>
                <div style={{ maxWidth: 560, margin: '0 auto' }}>
                    <h2 style={{
                        fontSize: '2rem', fontWeight: 800, color: SR.dark,
                        marginBottom: '0.75rem', letterSpacing: '-0.02em',
                    }}>
                        Not sure where to start?
                    </h2>
                    <p style={{ color: SR.gray, fontSize: '1rem', lineHeight: 1.7, marginBottom: '2rem' }}>
                        Take our 2-minute quiz and we'll tell you exactly which services will move the needle for your business.
                    </p>
                    <button onClick={() => setActiveTab && setActiveTab('quiz')} style={btnPrimary}>
                        Take the Free Quiz →
                    </button>
                </div>
            </section>
        </main>
    );
};

export default ServicesPage;
