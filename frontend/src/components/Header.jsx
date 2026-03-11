import React from 'react';

const Header = ({ activeTab, setActiveTab, isScrolled }) => (
    <header style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        padding: '1rem 2rem',
        background: isScrolled ? 'rgba(44, 62, 80, 0.98)' : 'rgba(74, 107, 124, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(122, 156, 176, 0.3)',
        transition: 'all 0.3s ease'
    }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div onClick={() => setActiveTab('home')} style={{ cursor: 'pointer' }}>
                <svg width="180" height="36" viewBox="0 0 600 120">
                    <text x="0" y="85" fontFamily="Georgia, serif" fontSize="72" fontWeight="300" fill="white">Atlantic digital</text>
                    <text x="420" y="28" fontFamily="system-ui" fontSize="14" fill="rgba(255,255,255,0.7)">marketing agency</text>
                </svg>
            </div>

            <nav style={{ display: 'flex', gap: '0.5rem' }}>
                {['home', 'services', 'analyzer', 'about', 'contact'].map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)}
                        style={{
                            background: activeTab === tab ? 'rgba(255,255,255,0.2)' : 'rgba(44, 62, 80, 0.3)',
                            color: 'white', padding: '0.6rem 1.2rem', border: 'none',
                            borderRadius: 50, fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem'
                        }}>
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </nav>

            <button onClick={() => setActiveTab('dashboard')}
                style={{
                    background: activeTab === 'dashboard' ? '#1a5a2e' : '#2C3E50',
                    color: 'white', padding: '0.7rem 1.5rem', border: 'none',
                    borderRadius: 50, fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem'
                }}>
                🔐 Internal Dashboard
            </button>
        </div>
    </header>
);

export default Header;
