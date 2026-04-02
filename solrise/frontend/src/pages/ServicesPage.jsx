import React from 'react';

const ServicesPage = () => (
    <main style={{ paddingTop: 80 }}>
        <section style={{ padding: '5rem 2rem', minHeight: '80vh' }}>
            <div style={{ maxWidth: 1200, margin: '0 auto' }}>
                <h1 style={{
                    fontSize: '2.5rem', fontWeight: 700, textAlign: 'center', marginBottom: '1rem',
                    background: 'linear-gradient(135deg, #2C3E50, #4A6B7C)',
                    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
                }}>Our Services</h1>
                <p style={{
                    textAlign: 'center', fontSize: '1.1rem', color: '#5A6B7D', marginBottom: '3rem',
                    maxWidth: 600, margin: '0 auto 3rem'
                }}>
                    Full-stack AI marketing solutions combining SEO, GEO, and data intelligence
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem' }}>
                    {[
                        { icon: '🤖', title: 'AI Ad Generation', desc: 'Generate high-converting ads using AI', features: ['LLM + Diffusion creation', 'A/B testing', 'Automated iteration'] },
                        { icon: '🔍', title: 'SEO & GEO Optimization', desc: 'Dual optimization for search and AI discovery', features: ['TF-IDF + Semantic analysis', 'GEO citation optimization', 'Schema markup'] },
                        { icon: '🎯', title: 'Competitor Intelligence', desc: 'Advanced web scraping monitors competitors', features: ['Keyword gap analysis', 'Content extraction', 'Pricing monitoring'] },
                        { icon: '📊', title: 'Advanced Analytics', desc: 'Comprehensive data analysis', features: ['Real-time tracking', 'ROI optimization', 'Predictive modeling'] },
                        { icon: '📈', title: 'Content Gap Reports', desc: 'Identify missing content opportunities', features: ['Keyword opportunities', 'Topic authority', 'Content calendar'] },
                        { icon: '⚡', title: 'Website Generation', desc: 'AI-powered website generation', features: ['Claude API integration', 'Agentic validation', 'Schema included'] }
                    ].map((s, i) => (
                        <div key={i} style={{
                            background: 'white', padding: '2.5rem', borderRadius: 20,
                            boxShadow: '0 10px 40px rgba(74, 107, 124, 0.15)', borderTop: '4px solid #2C3E50'
                        }}>
                            <div style={{
                                width: 70, height: 70, background: '#2C3E50', borderRadius: 18,
                                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.8rem', marginBottom: '1.5rem'
                            }}>
                                {s.icon}
                            </div>
                            <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem', color: '#2C3E50' }}>{s.title}</h3>
                            <p style={{ color: '#5A6B7D', lineHeight: 1.7, marginBottom: '1.5rem' }}>{s.desc}</p>
                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                                {s.features.map((f, j) => (
                                    <li key={j} style={{ color: '#5A6B7D', marginBottom: '0.5rem', paddingLeft: '0.5rem' }}>→ {f}</li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    </main>
);

export default ServicesPage;
