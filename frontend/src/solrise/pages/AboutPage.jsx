import React from 'react';
import { SR, gradientText, btnPrimary } from '../tokens';
import { SunIcon } from '../components/SunLogo';

const VALUES = [
    { icon: '🔬', title: 'Data First',       desc: 'Every recommendation is backed by real data — no guesswork, no generic advice.' },
    { icon: '🤖', title: 'AI at the Core',   desc: 'We build with the latest AI tools so your business stays ahead of the curve.' },
    { icon: '🌅', title: 'Rise Together',    desc: 'Your success is our success. We measure our work by your growth, nothing else.' },
    { icon: '🔒', title: 'Radical Clarity',  desc: 'We explain everything in plain English. You\'ll always know what we\'re doing and why.' },
];

const AboutPage = ({ setActiveTab }) => (
    <main style={{ paddingTop: 80, fontFamily: SR.font, background: SR.bg }}>
        {/* Hero */}
        <section style={{
            padding: '5rem 2rem 4rem',
            background: SR.heroGradient,
            textAlign: 'center',
            position: 'relative', overflow: 'hidden',
        }}>
            <div style={{
                position: 'absolute', bottom: -60, left: '50%',
                transform: 'translateX(-50%)', opacity: 0.06, pointerEvents: 'none',
            }}>
                <SunIcon size={400} />
            </div>
            <div style={{ maxWidth: 680, margin: '0 auto', position: 'relative', zIndex: 1 }}>
                <h1 style={{
                    fontSize: 'clamp(2rem, 4vw, 3.2rem)', fontWeight: 800,
                    color: SR.dark, letterSpacing: '-0.025em',
                    marginBottom: '1.25rem', lineHeight: 1.15,
                }}>
                    We help businesses{' '}
                    <span style={gradientText}>rise to the top</span>
                    <br />of search — and AI.
                </h1>
                <p style={{ color: SR.gray, fontSize: '1.1rem', lineHeight: 1.75, maxWidth: 540, margin: '0 auto' }}>
                    We're data scientists and AI engineers who happen to be marketing experts.
                    Our proprietary combination of AI models, web scraping, and advanced analytics
                    gives your business an unfair advantage.
                </p>
            </div>
        </section>

        {/* Mission */}
        <section style={{ padding: '4rem 2rem', background: SR.white }}>
            <div style={{
                maxWidth: 900, margin: '0 auto',
                display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '2rem', alignItems: 'center',
            }}>
                <div>
                    <span style={{
                        color: SR.coral, fontWeight: 700, fontSize: '0.85rem',
                        letterSpacing: '0.08em', textTransform: 'uppercase',
                        display: 'block', marginBottom: '0.75rem',
                    }}>
                        Our Mission
                    </span>
                    <h2 style={{
                        fontSize: 'clamp(1.6rem, 3vw, 2.2rem)', fontWeight: 800,
                        color: SR.dark, letterSpacing: '-0.02em',
                        lineHeight: 1.25, marginBottom: '1.25rem',
                    }}>
                        Make every business<br />discoverable everywhere
                    </h2>
                    <p style={{ color: SR.gray, lineHeight: 1.75, fontSize: '0.97rem' }}>
                        Search is changing. Google still matters — but now AI tools like ChatGPT,
                        Perplexity, and Google AI Overviews are where millions of customers find answers.
                        We make sure your business shows up in both worlds.
                    </p>
                </div>
                <div style={{
                    background: SR.heroGradient,
                    borderRadius: SR.xl, padding: '2.5rem',
                    border: `1px solid ${SR.border}`,
                }}>
                    {[
                        { label: 'Websites Analysed',  val: '500+' },
                        { label: 'Keywords Tracked',   val: '2M+' },
                        { label: 'Reports Delivered',  val: '300+' },
                        { label: 'Avg Score Lift',     val: '+38%' },
                    ].map((item, i) => (
                        <div key={i} style={{
                            display: 'flex', justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '0.75rem 0',
                            borderBottom: i < 3 ? `1px solid ${SR.border}` : 'none',
                        }}>
                            <span style={{ color: SR.gray, fontSize: '0.9rem' }}>{item.label}</span>
                            <span style={{
                                fontWeight: 800, fontSize: '1.3rem',
                                ...gradientText,
                            }}>{item.val}</span>
                        </div>
                    ))}
                </div>
            </div>
        </section>

        {/* Values */}
        <section style={{ padding: '4rem 2rem', background: SR.bg }}>
            <div style={{ maxWidth: 1100, margin: '0 auto' }}>
                <h2 style={{
                    textAlign: 'center', fontSize: '2rem', fontWeight: 800,
                    color: SR.dark, letterSpacing: '-0.02em',
                    marginBottom: '2.5rem',
                }}>
                    What we stand for
                </h2>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '1.25rem',
                }}>
                    {VALUES.map((v, i) => (
                        <div key={i} style={{
                            background: SR.white, borderRadius: SR.xl,
                            padding: '2rem', border: `1px solid ${SR.border}`,
                            boxShadow: SR.cardShadow,
                        }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.85rem' }}>{v.icon}</div>
                            <h3 style={{ fontWeight: 700, fontSize: '1.05rem', color: SR.dark, marginBottom: '0.5rem' }}>
                                {v.title}
                            </h3>
                            <p style={{ color: SR.gray, fontSize: '0.88rem', lineHeight: 1.65, margin: 0 }}>
                                {v.desc}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>

        {/* CTA */}
        <section style={{ padding: '4rem 2rem', background: SR.white }}>
            <div style={{
                maxWidth: 680, margin: '0 auto', textAlign: 'center',
                background: `linear-gradient(135deg, ${SR.orange}, ${SR.coral})`,
                borderRadius: 28, padding: '3.5rem 2.5rem',
                boxShadow: '0 16px 56px rgba(240,122,99,0.28)',
                position: 'relative', overflow: 'hidden',
            }}>
                <div style={{
                    position: 'absolute', right: -30, top: -30,
                    opacity: 0.12, pointerEvents: 'none',
                }}>
                    <SunIcon size={180} />
                </div>
                <h2 style={{
                    fontSize: '2rem', fontWeight: 800, color: SR.white,
                    marginBottom: '0.75rem', position: 'relative', zIndex: 1,
                }}>
                    Ready to be your customers' first choice?
                </h2>
                <p style={{
                    color: 'rgba(255,255,255,0.88)', lineHeight: 1.7,
                    marginBottom: '2rem', position: 'relative', zIndex: 1,
                }}>
                    Join forward-thinking businesses using AI and data science to lead their market.
                </p>
                <button
                    onClick={() => setActiveTab && setActiveTab('quiz')}
                    style={{
                        background: SR.white, color: SR.coral, border: 'none',
                        borderRadius: SR.pill, padding: '0.9rem 2.5rem',
                        fontWeight: 800, cursor: 'pointer', fontSize: '1rem',
                        boxShadow: '0 4px 18px rgba(0,0,0,0.15)',
                        position: 'relative', zIndex: 1,
                    }}
                >
                    Get Your Free Report →
                </button>
            </div>
        </section>
    </main>
);

export default AboutPage;
