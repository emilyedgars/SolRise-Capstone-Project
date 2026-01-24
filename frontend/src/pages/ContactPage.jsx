import React, { useState } from 'react';

const ContactPage = () => {
    const [form, setForm] = useState({ name: '', email: '', website: '', competitors: '' });
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        await new Promise(r => setTimeout(r, 2000));
        setSubmitting(false);
        setSubmitted(true);
    };

    return (
        <main style={{ paddingTop: 80 }}>
            <section style={{ padding: '5rem 2rem', background: 'linear-gradient(135deg, #2C3E50, #4A6B7C)', minHeight: '100vh' }}>
                <div style={{ maxWidth: 1000, margin: '0 auto' }}>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 700, textAlign: 'center', marginBottom: '1rem', color: 'white' }}>
                        Get Your Free AI Analysis
                    </h1>
                    <p style={{ textAlign: 'center', fontSize: '1.1rem', color: 'rgba(255,255,255,0.9)', marginBottom: '3rem', maxWidth: 600, margin: '0 auto 3rem' }}>
                        Our smart competitor analysis delivers comprehensive reports identifying exactly what your competitors do that you don't.
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '3rem' }}>
                        <div style={{ color: 'white' }}>
                            <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>Contact Information</h3>
                            <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>📧 atlanticdigitalusa@gmail.com</div>
                            <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>📞 +34611512450</div>
                            <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>🤖 AI Chat: Available 24/7</div>
                        </div>

                        <form onSubmit={handleSubmit} style={{
                            background: 'rgba(255,255,255,0.1)', padding: '2.5rem',
                            borderRadius: 25, backdropFilter: 'blur(15px)', border: '1px solid rgba(255,255,255,0.2)'
                        }}>
                            {submitted ? (
                                <div style={{ textAlign: 'center', color: 'white', padding: '2rem' }}>
                                    <span style={{ fontSize: '3rem' }}>✅</span>
                                    <h3>Analysis Request Received!</h3>
                                    <p>We'll email you the full report within 24 hours.</p>
                                </div>
                            ) : (
                                <>
                                    {['Full Name', 'Email Address', 'Website URL', 'Top 3 Competitors (optional)'].map((label, i) => (
                                        <div key={i} style={{ marginBottom: '1.5rem' }}>
                                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>{label}</label>
                                            {i < 3 ? (
                                                <input type={i === 1 ? 'email' : i === 2 ? 'url' : 'text'}
                                                    style={{ width: '100%', padding: '1rem', border: 'none', borderRadius: 15, background: 'rgba(255,255,255,0.9)', fontSize: '1rem', boxSizing: 'border-box' }}
                                                    value={form[['name', 'email', 'website', 'competitors'][i]]}
                                                    onChange={e => setForm({ ...form, [['name', 'email', 'website', 'competitors'][i]]: e.target.value })}
                                                    required={i < 3} />
                                            ) : (
                                                <textarea style={{ width: '100%', padding: '1rem', border: 'none', borderRadius: 15, background: 'rgba(255,255,255,0.9)', fontSize: '1rem', minHeight: 80, resize: 'vertical', boxSizing: 'border-box' }}
                                                    value={form.competitors} onChange={e => setForm({ ...form, competitors: e.target.value })}
                                                    placeholder="competitor1.com, competitor2.com, competitor3.com" />
                                            )}
                                        </div>
                                    ))}
                                    <button type="submit" disabled={submitting}
                                        style={{
                                            width: '100%', background: submitting ? 'linear-gradient(135deg, #e67e22, #f39c12)' : '#2C3E50',
                                            color: 'white', padding: '1rem', border: 'none', borderRadius: 50, fontWeight: 600, cursor: 'pointer', fontSize: '1rem'
                                        }}>
                                        {submitting ? '🔄 Analyzing with AI...' : 'Get Free AI Analysis'}
                                    </button>
                                </>
                            )}
                        </form>
                    </div>
                </div>
            </section>
        </main>
    );
};

export default ContactPage;
