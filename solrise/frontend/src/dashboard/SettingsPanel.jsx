import { useState, useEffect } from 'react';

const SettingsPanel = () => {
    const [ollamaStatus, setOllamaStatus] = useState({ connected: null, model: null, models: [] });

    useEffect(() => {
        fetch('/api/ollama-status')
            .then(r => r.json())
            .then(d => setOllamaStatus({ connected: d.connected, model: d.selected_model, models: d.models || [] }))
            .catch(() => setOllamaStatus({ connected: false, model: null, models: [] }));
    }, []);

    const ollamaLabel = ollamaStatus.connected === null
        ? '⏳ Checking...'
        : ollamaStatus.connected
            ? `✓ Connected · ${ollamaStatus.model || ''}`
            : '✗ Not running — start with: ollama serve';

    const ollamaColor = ollamaStatus.connected === null
        ? '#95a5a6'
        : ollamaStatus.connected ? '#F7A14F' : '#e74c3c';

    const cards = [
        { icon: '🔑', title: 'Claude API',          type: 'password', placeholder: 'sk-ant-...', status: '✓ Connected', statusColor: '#F7A14F' },
        { icon: '🗄️', title: 'MongoDB',              type: 'text',     placeholder: 'mongodb+srv://...', status: '✓ Connected', statusColor: '#F7A14F' },
        { icon: '🦙', title: 'Ollama (Local LLM)',   type: 'text',     placeholder: 'http://localhost:11434', status: ollamaLabel, statusColor: ollamaColor },
    ];

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>⚙️ Settings</h1>
                <p style={{ color: '#95a5a6' }}>Configure API connections and preferences</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {cards.map((s, i) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>{s.icon} {s.title}</h3>
                        <input
                            type={s.type}
                            placeholder={s.placeholder}
                            style={{
                                width: '100%', padding: '0.9rem 1rem',
                                background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 10, color: 'white', fontSize: '0.95rem', boxSizing: 'border-box'
                            }}
                        />
                        <div style={{ marginTop: '0.75rem', color: s.statusColor, fontSize: '0.85rem' }}>{s.status}</div>
                    </div>
                ))}
            </div>

            {ollamaStatus.connected && ollamaStatus.models?.length > 0 && (
                <div style={{ marginTop: '1.5rem', background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem' }}>🦙 Available Models</h3>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {ollamaStatus.models.map((m, i) => (
                            <span key={i} style={{ background: 'rgba(247,161,79,0.15)', color: '#F7A14F', padding: '0.3rem 0.75rem', borderRadius: 20, fontSize: '0.82rem' }}>{m}</span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default SettingsPanel;
