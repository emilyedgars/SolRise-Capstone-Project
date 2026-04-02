import React, { useState } from 'react';
import SolRiseLogo from './SunLogo';
import { SR, btnPrimary } from '../tokens';

const NAV = ['home', 'services', 'about'];

const Header = ({ activeTab, setActiveTab, isScrolled }) => {
    const [hovered, setHovered] = useState(null);

    return (
        <header style={{
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
            padding: '1rem 2.5rem',
            background: isScrolled
                ? 'rgba(255, 252, 248, 0.97)'
                : 'rgba(255, 252, 248, 0.92)',
            backdropFilter: 'blur(20px)',
            borderBottom: isScrolled ? `1px solid ${SR.border}` : '1px solid transparent',
            transition: 'all 0.3s ease',
            boxShadow: isScrolled ? '0 2px 20px rgba(247, 161, 79, 0.08)' : 'none',
        }}>
            <div style={{
                maxWidth: 1200, margin: '0 auto',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
                {/* Logo */}
                <SolRiseLogo size={48} textSize="1.45rem" onClick={() => setActiveTab('home')} />

                {/* Nav */}
                <nav style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                    {NAV.map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            onMouseEnter={() => setHovered(tab)}
                            onMouseLeave={() => setHovered(null)}
                            style={{
                                background: 'none',
                                color: activeTab === tab ? SR.coral : SR.dark,
                                padding: '0.55rem 1.1rem',
                                border: 'none',
                                borderRadius: SR.pill,
                                fontWeight: activeTab === tab ? 700 : 500,
                                cursor: 'pointer',
                                fontSize: '0.95rem',
                                fontFamily: SR.font,
                                position: 'relative',
                                transition: 'all 0.2s',
                            }}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            {activeTab === tab && (
                                <span style={{
                                    position: 'absolute', bottom: 2, left: '50%',
                                    transform: 'translateX(-50%)',
                                    width: 20, height: 2, borderRadius: 2,
                                    background: SR.btnGradient,
                                }} />
                            )}
                        </button>
                    ))}
                </nav>

                {/* Right CTAs */}
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <button
                        onClick={() => setActiveTab('quiz')}
                        style={{ ...btnPrimary, padding: '0.65rem 1.5rem', fontSize: '0.9rem' }}
                    >
                        Get Free Analysis
                    </button>
                    <button
                        onClick={() => setActiveTab('dashboard')}
                        style={{
                            background: SR.dark,
                            color: SR.white,
                            padding: '0.65rem 1.2rem',
                            border: 'none',
                            borderRadius: SR.pill,
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '0.85rem',
                            fontFamily: SR.font,
                            opacity: 0.7,
                        }}
                    >
                        🔐
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Header;
