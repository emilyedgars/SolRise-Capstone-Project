import React from 'react';

const SettingsPanel = () => (
    <div style={{ color: 'white' }}>
        <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>⚙️ Settings</h1>
            <p style={{ color: '#95a5a6' }}>Configure API connections and preferences</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {[
                { icon: '🔑', title: 'Claude API', type: 'password', placeholder: 'sk-ant-...', status: '✓ Connected', statusColor: '#4ECDC4' },
                { icon: '🗄️', title: 'MongoDB', type: 'text', placeholder: 'mongodb+srv://...', status: '✓ Connected', statusColor: '#4ECDC4' },
                { icon: '🦙', title: 'Ollama (Local LLM)', type: 'text', placeholder: 'http://localhost:11434', status: '⚠️ Not configured', statusColor: '#f39c12' },
                { icon: '📊', title: 'Google Search Console', type: 'button', status: '○ Not connected', statusColor: '#95a5a6' }
            ].map((s, i) => (
                <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>{s.icon} {s.title}</h3>
                    {s.type !== 'button' ? (
                        <input type={s.type} placeholder={s.placeholder}
                            style={{
                                width: '100%', padding: '0.9rem 1rem', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 10, color: 'white', fontSize: '0.95rem', boxSizing: 'border-box'
                            }} />
                    ) : (
                        <button style={{
                            background: 'rgba(78, 205, 196, 0.1)', border: '1px solid rgba(78, 205, 196, 0.3)',
                            color: '#4ECDC4', padding: '0.75rem 1.5rem', borderRadius: 10, cursor: 'pointer', width: '100%'
                        }}>
                            Connect Google Account
                        </button>
                    )}
                    <div style={{ marginTop: '0.75rem', color: s.statusColor, fontSize: '0.85rem' }}>{s.status}</div>
                </div>
            ))}
        </div>
    </div>
);

export default SettingsPanel;
