import React, { useState } from 'react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, BarChart, CartesianGrid, XAxis, YAxis, Bar, Cell, ReferenceLine } from 'recharts';

const ResultsPanel = ({ results }) => {
    const [downloading, setDownloading] = useState(false);

    const downloadPDF = async () => {
        setDownloading(true);
        try {
            const response = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ results })
            });
            if (!response.ok) throw new Error('PDF generation failed');
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `solrise_report_${(results.clientName || 'report').replace(/\s+/g, '_').toLowerCase()}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert('PDF download failed: ' + e.message);
        }
        setDownloading(false);
    };
    if (!results) return (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: '#95a5a6' }}>
            <span style={{ fontSize: '4rem' }}>📊</span>
            <h2 style={{ color: 'white', marginTop: '1rem' }}>No Analysis Results Yet</h2>
            <p>Run an analysis first to see results here</p>
        </div>
    );

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>📊 Analysis Results</h1>
                    <p style={{ color: '#95a5a6' }}>SEO & GEO analysis for {results.clientName}</p>
                </div>
                <button onClick={downloadPDF} disabled={downloading} style={{
                    background: 'linear-gradient(135deg, #e74c3c, #c0392b)', color: 'white',
                    padding: '0.75rem 1.25rem', border: 'none', borderRadius: 10,
                    cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem', whiteSpace: 'nowrap',
                    opacity: downloading ? 0.7 : 1
                }}>
                    {downloading ? '⏳ Generating...' : '📄 Download PDF Report'}
                </button>
            </div>

            {/* Score Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                {[
                    { label: 'Overall Score', score: results.overallScore, color: '#F7A14F' },
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
                            <Radar name="Client" dataKey="client" stroke="#F7A14F" fill="#F7A14F" fillOpacity={0.5} />
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
                            <Bar dataKey="score" fill="#F7A14F" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Semantic Similarity Positioning */}
            {results.semanticSimilarity && results.semanticSimilarity.length > 0 && (
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)', marginBottom: '2rem' }}>
                    <div style={{ marginBottom: '1rem' }}>
                        <h3 style={{ marginBottom: '0.25rem' }}>Semantic Similarity Positioning</h3>
                        <p style={{ color: '#95a5a6', fontSize: '0.85rem', margin: 0 }}>
                            How similar your content is to each competitor — lower means better differentiation, 40–70% is the competitive sweet spot.
                        </p>
                    </div>
                    <ResponsiveContainer width="100%" height={Math.max(180, results.semanticSimilarity.length * 52)}>
                        <BarChart data={results.semanticSimilarity} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#34495e" horizontal={false} />
                            <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fill: '#95a5a6', fontSize: 11 }} />
                            <YAxis dataKey="domain" type="category" width={180} tick={{ fill: '#e0e0e0', fontSize: 11 }} />
                            <Tooltip
                                formatter={(v, name) => [`${v}%`, 'Similarity']}
                                labelFormatter={label => `vs ${label}`}
                                contentStyle={{ background: '#1a1f2e', border: '1px solid #34495e', borderRadius: 8 }}
                                labelStyle={{ color: 'white' }}
                            />
                            <ReferenceLine x={40} stroke="#F7A14F" strokeDasharray="4 4" label={{ value: '40%', fill: '#F7A14F', fontSize: 10, position: 'top' }} />
                            <ReferenceLine x={70} stroke="#e74c3c" strokeDasharray="4 4" label={{ value: '70%', fill: '#e74c3c', fontSize: 10, position: 'top' }} />
                            <Bar dataKey="similarity" radius={[0, 6, 6, 0]} label={{ position: 'right', formatter: v => `${v}%`, fill: '#95a5a6', fontSize: 11 }}>
                                {results.semanticSimilarity.map((entry, i) => (
                                    <Cell key={i} fill={
                                        entry.similarity > 70 ? '#e74c3c' :
                                        entry.similarity >= 40 ? '#F7A14F' :
                                        '#F9E4A0'
                                    } />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem', fontSize: '0.8rem', color: '#95a5a6' }}>
                        <span><span style={{ color: '#f1c40f' }}>■</span> &lt;40% — Highly differentiated</span>
                        <span><span style={{ color: '#F7A14F' }}>■</span> 40–70% — Competitive sweet spot</span>
                        <span><span style={{ color: '#e74c3c' }}>■</span> &gt;70% — Too similar, needs differentiation</span>
                    </div>
                </div>
            )}

            {/* Top Keywords Chart */}
            {results.topKeywords && results.topKeywords.length > 0 && (() => {
                // Normalise scores to 0–100 for display regardless of whether they're TF-IDF or search volumes
                const kwMax = Math.max(...results.topKeywords.map(k => k.score), 1);
                const bgMax = results.topBigrams?.length ? Math.max(...results.topBigrams.map(k => k.score), 1) : 1;
                const kwData = results.topKeywords.slice(0, 12).map(({ keyword, score }) => ({ keyword, score: Math.round((score / kwMax) * 100) }));
                const bgData = results.topBigrams?.slice(0, 12).map(({ phrase, score }) => ({ phrase, score: Math.round((score / bgMax) * 100) }));
                return (
                <div style={{ marginBottom: '2rem' }}>
                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)', marginBottom: '1.5rem' }}>
                        <h3 style={{ marginBottom: '1rem' }}>Top Keywords (Relative Score)</h3>
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={kwData} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="#34495e" />
                                <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fill: '#95a5a6' }} />
                                <YAxis dataKey="keyword" type="category" width={160} tick={{ fill: '#95a5a6', fontSize: 10 }} />
                                <Tooltip formatter={v => [`${v}%`, 'Score']} />
                                <Bar dataKey="score" fill="#F7A14F" radius={[0, 4, 4, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {bgData && bgData.length > 0 && (
                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                            <h3 style={{ marginBottom: '1rem' }}>Key Phrases (Bigrams)</h3>
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={bgData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#34495e" />
                                    <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fill: '#95a5a6' }} />
                                    <YAxis dataKey="phrase" type="category" width={160} tick={{ fill: '#95a5a6', fontSize: 10 }} />
                                    <Tooltip formatter={v => [`${v}%`, 'Score']} />
                                    <Bar dataKey="score" fill="#9C8BD9" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>
                );
            })()}

            {/* GEO Components */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)', marginBottom: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>GEO Component Scores</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                    {results.geoComponents.map((c, i) => (
                        <div key={i} style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 10 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                <span>{c.name}</span>
                                <span style={{ color: c.score >= 0.7 ? '#F7A14F' : '#e74c3c' }}>{(c.score * 100).toFixed(0)}%</span>
                            </div>
                            <div style={{ height: 8, background: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden', marginBottom: '0.5rem' }}>
                                <div style={{
                                    height: '100%', borderRadius: 4, width: `${c.score * 100}%`,
                                    background: c.score >= 0.7 ? '#F7A14F' : c.score >= 0.5 ? '#f39c12' : '#e74c3c'
                                }} />
                            </div>
                            <p style={{ color: '#95a5a6', fontSize: '0.8rem', margin: 0 }}>{c.tip}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* GEO Improvement Suggestions */}
            {(() => {
                const geo = results.geoMetrics || {};
                const suggestions = [];
                if ((geo.claimDensity || 0) < 4) suggestions.push({ icon: '📊', label: 'Claim Density', status: 'critical', fix: `Current: ${(geo.claimDensity || 0).toFixed(1)}/100 words. Target: 4+. Add statistics, percentages, and factual statements.` });
                if ((geo.citability || 0) < 0.6) suggestions.push({ icon: '💬', label: 'Citability', status: 'high', fix: `Score: ${Math.round((geo.citability || 0) * 100)}%. Add at least 5 quotable statements, expert opinions, and data-backed claims.` });
                if ((geo.extractability || 0) < 0.6) suggestions.push({ icon: '🔍', label: 'Extractability', status: 'high', fix: `Score: ${Math.round((geo.extractability || 0) * 100)}%. Structure content with clear H2/H3 headers, short paragraphs, and bullet points.` });
                if ((geo.avgSentenceLength || 0) > 25) suggestions.push({ icon: '✂️', label: 'Sentence Length', status: 'medium', fix: `Avg: ${(geo.avgSentenceLength || 0).toFixed(0)} words. Reduce to 15–20 words per sentence for better AI extraction.` });
                if ((geo.readability || 0) < 0.6) suggestions.push({ icon: '📖', label: 'Readability', status: 'medium', fix: `Score: ${Math.round((geo.readability || 0) * 100)}%. Use simpler vocabulary, shorter paragraphs, and clear topic sentences.` });
                if ((geo.coveragePrediction || 0) < 50) suggestions.push({ icon: '🎯', label: 'AI Coverage Prediction', status: 'medium', fix: `${geo.coveragePrediction || 0}% probability. Increase authority signals: add schema markup, FAQ section, and location-specific content.` });
                if (suggestions.length === 0) suggestions.push({ icon: '✅', label: 'GEO Optimized', status: 'good', fix: 'Your content is well-optimized for AI engines. Maintain claim density and keep content updated.' });

                const statusStyles = {
                    critical: { background: 'rgba(231,76,60,0.08)', borderLeft: '3px solid #e74c3c' },
                    high:     { background: 'rgba(243,156,18,0.08)', borderLeft: '3px solid #f39c12' },
                    medium:   { background: 'rgba(52,152,219,0.08)', borderLeft: '3px solid #3498db' },
                    good:     { background: 'rgba(247,161,79,0.08)', borderLeft: '3px solid #F7A14F' },
                };

                return (
                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)', marginBottom: '2rem' }}>
                        <h3 style={{ marginBottom: '1.5rem' }}>🤖 GEO Improvement Suggestions</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                            {suggestions.map((s, i) => (
                                <div key={i} style={{ padding: '1rem', borderRadius: 10, ...statusStyles[s.status] }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.95rem' }}>
                                        <span>{s.icon}</span>
                                        <span>{s.label}</span>
                                    </div>
                                    <p style={{ color: '#95a5a6', fontSize: '0.85rem', margin: 0, lineHeight: 1.5 }}>{s.fix}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })()}

            {/* Recommendations */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>🎯 Priority Recommendations</h3>
                {results.recommendations.map((r, i) => (
                    <div key={i} style={{
                        padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 10, marginBottom: '0.75rem',
                        borderLeft: `4px solid ${r.priority === 'CRITICAL' ? '#e74c3c' : r.priority === 'HIGH' ? '#f39c12' : '#3498db'}`
                    }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, marginRight: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: 4, background: 'rgba(255,255,255,0.1)' }}>{r.priority}</span>
                        <span style={{ color: '#F7A14F', fontSize: '0.85rem', fontWeight: 600 }}>{r.category}</span>
                        <p style={{ color: '#95a5a6', fontSize: '0.9rem', marginTop: '0.5rem', marginBottom: 0 }}>{r.message}</p>
                    </div>
                ))}
            </div>

            {/* Runtime Performance */}
            {results.performanceTiming && (
                <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 15, padding: '1.5rem', marginTop: '2rem' }}>
                    <div style={{ marginBottom: '1.25rem' }}>
                        <h3 style={{ margin: '0 0 0.4rem', fontSize: '1.05rem', fontWeight: 700, color: 'white' }}>⏱ Runtime Performance</h3>
                        <p style={{ margin: 0, fontSize: '0.87rem', color: '#95a5a6', lineHeight: 1.6 }}>
                            Runtime metrics from all test runs were collected to evaluate the scalability and efficiency of the system.
                            The results show that the SolRise pipeline performs well for interactive client sessions within a reasonable time frame.
                        </p>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                        {[
                            { label: 'Scraping Time',    key: 'scrapingTime',    icon: '🌐', desc: 'Crawling client + competitors' },
                            { label: 'NLP Time',         key: 'nlpTime',         icon: '🧠', desc: 'Keyword extraction & GEO scoring' },
                            { label: 'Generation Time',  key: 'generationTime',  icon: '⚙️', desc: 'Competitive & semantic analysis' },
                            { label: 'End-to-End Time',  key: 'endToEndTime',    icon: '⏱️', desc: 'Total pipeline wall-clock time' },
                        ].map(({ label, key, icon, desc }) => {
                            const val = results.performanceTiming[key];
                            const display = val != null ? (val >= 60 ? `${(val / 60).toFixed(1)}m` : `${val}s`) : '—';
                            return (
                                <div key={key} style={{ textAlign: 'center', padding: '1rem 0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: 12, border: '1px solid rgba(255,255,255,0.05)' }}>
                                    <div style={{ fontSize: '1.5rem', marginBottom: '0.4rem' }}>{icon}</div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#F7A14F', lineHeight: 1 }}>{display}</div>
                                    <div style={{ fontSize: '0.82rem', color: 'white', fontWeight: 600, margin: '0.35rem 0 0.25rem' }}>{label}</div>
                                    <div style={{ fontSize: '0.74rem', color: '#6c7a89', lineHeight: 1.4 }}>{desc}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Optimized Prompt Preview */}
            {results.generatedPrompt && (
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid #F7A14F', marginTop: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#F7A14F' }}>✨ AI-Optimized Website Prompt</h3>
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
