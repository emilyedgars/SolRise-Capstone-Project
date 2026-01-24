import React from 'react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, BarChart, CartesianGrid, XAxis, YAxis, Bar } from 'recharts';

const ResultsPanel = ({ results }) => {
    if (!results) return (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: '#95a5a6' }}>
            <span style={{ fontSize: '4rem' }}>📊</span>
            <h2 style={{ color: 'white', marginTop: '1rem' }}>No Analysis Results Yet</h2>
            <p>Run an analysis first to see results here</p>
        </div>
    );

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>📊 Analysis Results</h1>
                <p style={{ color: '#95a5a6' }}>SEO & GEO analysis for {results.clientName}</p>
            </div>

            {/* Score Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                {[
                    { label: 'Overall Score', score: results.overallScore, color: '#4ECDC4' },
                    { label: 'SEO Score', score: results.seoScore, color: '#3498db' },
                    { label: 'GEO Score', score: results.geoScore, color: '#9b59b6' },
                    { label: 'Competitive Parity', score: results.competitiveScore, color: '#e67e22' }
                ].map((s, i) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ color: '#95a5a6', fontSize: '0.9rem', marginBottom: '0.5rem' }}>{s.label}</div>
                        <div style={{ fontSize: '2rem', fontWeight: 700, color: s.color, marginBottom: '0.75rem' }}>{(s.score * 100).toFixed(0)}%</div>
                        <div style={{ height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ height: '100%', borderRadius: 3, width: `${s.score * 100}%`, background: s.color }} />
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ marginBottom: '1rem' }}>SEO vs GEO Breakdown</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <RadarChart data={results.radarData}>
                            <PolarGrid stroke="#34495e" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#95a5a6', fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#95a5a6' }} />
                            <Radar name="Client" dataKey="client" stroke="#4ECDC4" fill="#4ECDC4" fillOpacity={0.5} />
                            <Radar name="Competitors" dataKey="competitor" stroke="#e74c3c" fill="#e74c3c" fillOpacity={0.3} />
                            <Tooltip />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Top Keyword Gaps</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={results.keywordGaps} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#34495e" />
                            <XAxis type="number" tick={{ fill: '#95a5a6' }} />
                            <YAxis dataKey="keyword" type="category" tick={{ fill: '#95a5a6', fontSize: 11 }} width={120} />
                            <Tooltip />
                            <Bar dataKey="score" fill="#4ECDC4" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* GEO Components */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)', marginBottom: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>GEO Component Scores</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                    {results.geoComponents.map((c, i) => (
                        <div key={i} style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 10 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                <span>{c.name}</span>
                                <span style={{ color: c.score >= 0.7 ? '#4ECDC4' : '#e74c3c' }}>{(c.score * 100).toFixed(0)}%</span>
                            </div>
                            <div style={{ height: 8, background: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden', marginBottom: '0.5rem' }}>
                                <div style={{
                                    height: '100%', borderRadius: 4, width: `${c.score * 100}%`,
                                    background: c.score >= 0.7 ? '#4ECDC4' : c.score >= 0.5 ? '#f39c12' : '#e74c3c'
                                }} />
                            </div>
                            <p style={{ color: '#95a5a6', fontSize: '0.8rem', margin: 0 }}>{c.tip}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recommendations */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>🎯 Priority Recommendations</h3>
                {results.recommendations.map((r, i) => (
                    <div key={i} style={{
                        padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 10, marginBottom: '0.75rem',
                        borderLeft: `4px solid ${r.priority === 'CRITICAL' ? '#e74c3c' : r.priority === 'HIGH' ? '#f39c12' : '#3498db'}`
                    }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, marginRight: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: 4, background: 'rgba(255,255,255,0.1)' }}>{r.priority}</span>
                        <span style={{ color: '#4ECDC4', fontSize: '0.85rem', fontWeight: 600 }}>{r.category}</span>
                        <p style={{ color: '#95a5a6', fontSize: '0.9rem', marginTop: '0.5rem', marginBottom: 0 }}>{r.message}</p>
                    </div>
                ))}
            </div>

            {/* Optimized Prompt Preview */}
            {results.generatedPrompt && (
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid #4ECDC4', marginTop: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#4ECDC4' }}>✨ AI-Optimized Website Prompt</h3>
                    <p style={{ color: '#95a5a6', marginBottom: '1rem' }}>This prompt has been crafted based on the analysis gaps. Use it to generate a high-performing website.</p>
                    <div style={{ background: '#1a1f2e', padding: '1rem', borderRadius: 10, fontFamily: 'monospace', fontSize: '0.85rem', color: '#e0fbff', whiteSpace: 'pre-wrap', maxHeight: '200px', overflowY: 'auto' }}>
                        {results.generatedPrompt}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResultsPanel;
