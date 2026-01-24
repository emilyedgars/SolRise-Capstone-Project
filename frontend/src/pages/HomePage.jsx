import React, { useState, useEffect } from 'react';

const HomePage = ({ setActiveTab }) => {
    const [visible, setVisible] = useState(new Set());

    useEffect(() => {
        [100, 300, 500, 700, 900].forEach((delay, i) =>
            setTimeout(() => setVisible(prev => new Set([...prev, i])), delay)
        );
    }, []);

    const animStyle = (i) => ({
        opacity: visible.has(i) ? 1 : 0,
        transform: visible.has(i) ? 'translateY(0)' : 'translateY(30px)',
        transition: 'all 0.8s ease-out'
    });

    return (
        <main>
            <section style={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #F7F4F0 0%, #D6E8F0 50%, #E8DDD4 100%)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                paddingTop: 80, position: 'relative', overflow: 'hidden'
            }}>
                <div style={{ textAlign: 'center', maxWidth: 900, padding: '2rem', position: 'relative', zIndex: 2 }}>
                    <div style={{
                        ...animStyle(0), display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                        background: 'rgba(107, 143, 163, 0.25)', color: '#2C3E50', padding: '0.5rem 1.2rem',
                        borderRadius: 50, fontSize: '0.9rem', fontWeight: 600, marginBottom: '1.5rem'
                    }}>
                        🤖 AI-Powered Marketing Intelligence
                    </div>

                    <h1 style={{
                        ...animStyle(1), fontSize: 'clamp(2.5rem, 5vw, 4rem)', fontWeight: 700,
                        marginBottom: '1rem', lineHeight: 1.2, color: '#2C3E50'
                    }}>
                        Marketing that Drives<br />Innovation & Revenue
                    </h1>

                    <p style={{
                        ...animStyle(2), fontSize: 'clamp(1.2rem, 2.5vw, 1.5rem)', fontWeight: 600,
                        marginBottom: '1rem', color: '#4A6B7C'
                    }}>
                        Harness AI, Web Scraping & Advanced Analytics
                    </p>

                    <p style={{
                        ...animStyle(3), fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '2rem',
                        color: '#5A6B7D', maxWidth: 700, margin: '0 auto 2rem'
                    }}>
                        We apply AI, web scraping, and advanced analytics to derive actionable insights.
                        <strong style={{ color: '#2C3E50', fontSize: '1.1em' }}> DATA-DRIVEN. NO ASSUMPTIONS.</strong>
                    </p>

                    <div style={{ ...animStyle(4), display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                        <button onClick={() => setActiveTab('contact')}
                            style={{
                                background: '#2C3E50', color: 'white', padding: '0.8rem 1.8rem',
                                border: 'none', borderRadius: 50, fontWeight: 600, cursor: 'pointer', fontSize: '1rem'
                            }}>
                            Start Free Analysis
                        </button>
                        <button onClick={() => setActiveTab('services')}
                            style={{
                                background: 'transparent', color: '#2C3E50', padding: '0.8rem 1.8rem',
                                border: '2px solid #2C3E50', borderRadius: 50, fontWeight: 600, cursor: 'pointer', fontSize: '1rem'
                            }}>
                            See Our Services
                        </button>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section style={{ padding: '4rem 2rem', background: 'white' }}>
                <div style={{
                    maxWidth: 1200, margin: '0 auto', display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem'
                }}>
                    {[
                        { num: '10M+', label: 'Data Points Analyzed', icon: '📊' },
                        { num: '450%', label: 'Avg ROAS Improvement', icon: '📈' },
                        { num: '95%', label: 'GEO Citation Rate', icon: '🎯' },
                        { num: '24/7', label: 'AI Monitoring', icon: '🤖' }
                    ].map((s, i) => (
                        <div key={i} style={{
                            background: 'white', padding: '2rem', borderRadius: 20,
                            textAlign: 'center', boxShadow: '0 10px 30px rgba(74, 107, 124, 0.15)',
                            border: '1px solid rgba(122, 156, 176, 0.1)'
                        }}>
                            <span style={{ fontSize: '2rem', marginBottom: '0.5rem', display: 'block' }}>{s.icon}</span>
                            <div style={{
                                fontSize: '2.5rem', fontWeight: 700, background: 'linear-gradient(135deg, #2C3E50, #4A6B7C)',
                                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
                            }}>{s.num}</div>
                            <div style={{ fontSize: '0.9rem', color: '#5A6B7D', fontWeight: 600, marginTop: '0.5rem' }}>{s.label}</div>
                        </div>
                    ))}
                </div>
            </section>
        </main>
    );
};

export default HomePage;
