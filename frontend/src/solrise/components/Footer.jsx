import React from 'react';
import SolRiseLogo from './SunLogo';
import { SR, gradientText } from '../tokens';

const Footer = ({ setActiveTab }) => (
    <footer style={{
        background: 'linear-gradient(160deg, #2D1F3D 0%, #3D1F2A 50%, #2D1A18 100%)',
        color: SR.white,
        padding: '3.5rem 2.5rem 2rem',
    }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '2.5rem',
                marginBottom: '2.5rem'
            }}>
                {/* Brand */}
                <div>
                    <SolRiseLogo size={38} textSize="1.35rem" />
                    <p style={{
                        color: 'rgba(255,255,255,0.55)', fontSize: '0.88rem',
                        lineHeight: 1.7, marginTop: '1rem', maxWidth: 220
                    }}>
                        AI-powered SEO & GEO optimisation for businesses ready to grow.
                    </p>
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                        {['📧', '📞', '🌐'].map((icon, i) => (
                            <div key={i} style={{
                                width: 36, height: 36, borderRadius: '50%',
                                background: 'rgba(255,255,255,0.08)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '1rem', cursor: 'pointer',
                                transition: 'background 0.2s',
                            }}>
                                {icon}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Links */}
                <div>
                    <h4 style={{ color: SR.white, fontWeight: 700, fontSize: '0.9rem', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                        Platform
                    </h4>
                    {['home', 'services', 'about'].map(tab => (
                        <div key={tab}
                            onClick={() => setActiveTab && setActiveTab(tab)}
                            style={{
                                color: 'rgba(255,255,255,0.55)', fontSize: '0.88rem',
                                marginBottom: '0.6rem', cursor: 'pointer',
                                transition: 'color 0.2s',
                            }}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </div>
                    ))}
                </div>

                {/* Contact */}
                <div>
                    <h4 style={{ color: SR.white, fontWeight: 700, fontSize: '0.9rem', marginBottom: '1rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                        Contact
                    </h4>
                    <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: '0.88rem', lineHeight: 1.8 }}>
                        hello@solrise.ai<br />
                        +34 611 512 450<br />
                        AI Chat: 24/7
                    </p>
                </div>

                {/* CTA */}
                <div style={{
                    background: 'linear-gradient(135deg, rgba(247,161,79,0.15), rgba(240,122,99,0.15))',
                    borderRadius: SR.lg,
                    padding: '1.5rem',
                    border: '1px solid rgba(247,161,79,0.25)',
                }}>
                    <p style={{ color: SR.white, fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem' }}>
                        Ready to rise?
                    </p>
                    <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: '1rem' }}>
                        Get your free AI-powered SEO & GEO report.
                    </p>
                    <button
                        onClick={() => setActiveTab && setActiveTab('quiz')}
                        style={{
                            background: SR.btnGradient,
                            color: SR.white, border: 'none',
                            borderRadius: SR.pill, padding: '0.65rem 1.4rem',
                            fontWeight: 700, cursor: 'pointer', fontSize: '0.88rem',
                        }}
                    >
                        Start Free Analysis →
                    </button>
                </div>
            </div>

            <div style={{
                borderTop: '1px solid rgba(255,255,255,0.08)',
                paddingTop: '1.5rem',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                flexWrap: 'wrap', gap: '0.5rem',
            }}>
                <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.8rem', margin: 0 }}>
                    © 2025 SolRise. All rights reserved.
                </p>
                <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.8rem', margin: 0 }}>
                    Powered by AI · Built with Data · Optimised for Results
                </p>
            </div>
        </div>
    </footer>
);

export default Footer;
