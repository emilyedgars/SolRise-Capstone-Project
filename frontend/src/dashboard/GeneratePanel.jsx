import React, { useState } from 'react';

const GeneratePanel = ({ results, info, projectId }) => {
    const [generating, setGenerating] = useState(false);
    const [html, setHtml] = useState('');
    const [prompt, setPrompt] = useState(results?.generatedPrompt || '');
    const [stats, setStats] = useState(null);
    const [showPreview, setShowPreview] = useState(false);

    const generate = async () => {
        if (!projectId) { alert('No project ID found. Run analysis first.'); return; }
        setGenerating(true);

        try {
            const response = await fetch('/api/generate-website', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    custom_prompt: prompt
                })
            });

            if (!response.ok) throw new Error('Generation failed');

            const data = await response.json();
            setHtml(data.html);
            setStats({ score: data.score, iterations: data.iterations });

        } catch (e) {
            console.error(e);
            alert('Error generating website: ' + e.message);
        }
        setGenerating(false);
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(html);
        alert('HTML copied to clipboard!');
    };

    const downloadHtml = () => {
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `optimized-website-${projectId}.html`;
        a.click();
    };

    if (!results) return (
        <div style={{ padding: '2rem', background: 'rgba(243, 156, 18, 0.1)', border: '1px solid rgba(243, 156, 18, 0.3)', borderRadius: 12, color: '#f39c12', textAlign: 'center' }}>
            ⚠️ Run an analysis first to generate an optimized website based on the results.
        </div>
    );

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>⚡ Generate Optimized Website</h1>
                <p style={{ color: '#95a5a6' }}>Generate SEO/GEO-optimized HTML using Ollama Local AI</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                {[['Client', info.name], ['Location', info.location], ['Industry', info.industry], ['Keywords Found', results.keywordGaps?.length || 0]].map(([l, v], i) => (
                    <div key={i} style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 10 }}>
                        <span style={{ color: '#95a5a6', fontSize: '0.85rem' }}>{l}:</span>
                        <span style={{ color: 'white', fontWeight: 600, display: 'block', marginTop: '0.25rem' }}>{v || 'Not set'}</span>
                    </div>
                ))}
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#4ECDC4', fontWeight: 600 }}>Optimized Prompt (Editable)</label>
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    style={{
                        width: '100%', minHeight: '150px', padding: '1rem',
                        background: '#1a1f2e', border: '1px solid rgba(78, 205, 196, 0.3)',
                        borderRadius: 12, color: '#e0fbff', fontFamily: 'monospace', fontSize: '0.85rem',
                        resize: 'vertical'
                    }}
                />
            </div>

            <button onClick={generate} disabled={generating}
                style={{
                    background: 'linear-gradient(135deg, #4ECDC4, #44A08D)', color: 'white', padding: '1rem 2rem',
                    border: 'none', borderRadius: 12, fontSize: '1rem', fontWeight: 600, cursor: 'pointer', width: '100%',
                    opacity: generating ? 0.7 : 1, marginBottom: '2rem',
                    transition: 'all 0.3s ease'
                }}>
                {generating ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                        <div className="spinner" style={{
                            width: '20px', height: '20px', border: '3px solid rgba(255,255,255,0.3)',
                            borderTop: '3px solid white', borderRadius: '50%', animation: 'spin 1s linear infinite'
                        }} />
                        <span>Generating... This may take ~2-3 minutes. Please wait. ☕</span>
                    </div>
                ) : '🚀 Generate Optimized Website'}
            </button>

            {html && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3>Generated HTML</h3>
                        {stats && (
                            <div style={{ background: 'rgba(78, 205, 196, 0.2)', color: '#4ECDC4', padding: '0.5rem 1rem', borderRadius: 20, fontSize: '0.85rem' }}>
                                ✓ Score: {(stats.score * 100).toFixed(0)}% (Iterations: {stats.iterations})
                            </div>
                        )}
                    </div>
                    <div style={{ background: '#1a1f2e', borderRadius: 12, padding: '1rem', maxHeight: 300, overflow: 'auto' }}>
                        <pre style={{ color: '#95a5a6', fontSize: '0.8rem', fontFamily: 'monospace', margin: 0, whiteSpace: 'pre-wrap' }}>{html.slice(0, 2000)}...</pre>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                        <button onClick={copyToClipboard} style={{
                            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                            color: 'white', padding: '0.75rem 1.5rem', borderRadius: 10, cursor: 'pointer', fontSize: '0.9rem'
                        }}>📋 Copy HTML</button>
                        <button onClick={downloadHtml} style={{
                            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                            color: 'white', padding: '0.75rem 1.5rem', borderRadius: 10, cursor: 'pointer', fontSize: '0.9rem'
                        }}>💾 Download</button>
                        <button onClick={() => setShowPreview(!showPreview)} style={{
                            background: showPreview ? '#4ECDC4' : 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: showPreview ? 'black' : 'white', padding: '0.75rem 1.5rem', borderRadius: 10, cursor: 'pointer', fontSize: '0.9rem'
                        }}>👁️ {showPreview ? 'Hide Preview' : 'Show Preview'}</button>
                    </div>

                    {showPreview && (
                        <div style={{ marginTop: '2rem', border: '1px solid #4ECDC4', borderRadius: 12, overflow: 'hidden', background: 'white' }}>
                            <div style={{ background: '#f0f0f0', padding: '0.5rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #ddd' }}>
                                <span style={{ color: '#333', fontSize: '0.85rem', fontWeight: 600 }}>Live Preview</span>
                                <div style={{ display: 'flex', gap: '5px' }}>
                                    {[1, 2, 3].map(i => <div key={i} style={{ width: 10, height: 10, borderRadius: '50%', background: i === 1 ? '#ff5f56' : i === 2 ? '#ffbd2e' : '#27c93f' }} />)}
                                </div>
                            </div>
                            <iframe
                                title="Website Preview"
                                srcDoc={html}
                                style={{ width: '100%', height: '600px', border: 'none' }}
                            />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default GeneratePanel;
