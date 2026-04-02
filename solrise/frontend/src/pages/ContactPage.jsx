import { useState } from 'react';

const ContactPage = () => {
    const [form, setForm] = useState({ name: '', email: '', phone: '', website: '', goal: 'both', message: '' });
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        await new Promise(r => setTimeout(r, 2000));
        setSubmitting(false);
        setSubmitted(true);
    };

    const inputStyle = {
        width: '100%', padding: '1rem', border: 'none', borderRadius: 15,
        background: 'rgba(255,255,255,0.9)', fontSize: '1rem', boxSizing: 'border-box',
    };

    return (
        <main style={{ paddingTop: 80 }}>
            <section style={{ padding: '5rem 2rem', background: 'linear-gradient(135deg, #2C3E50, #4A6B7C)', minHeight: '100vh' }}>
                <div style={{ maxWidth: 1000, margin: '0 auto' }}>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 700, textAlign: 'center', marginBottom: '1rem', color: 'white' }}>
                        Get Your Free AI Analysis
                    </h1>
                    <p style={{ textAlign: 'center', fontSize: '1.1rem', color: 'rgba(255,255,255,0.9)', marginBottom: '3rem', maxWidth: 600, margin: '0 auto 3rem' }}>
                        Tell us about your business and we'll deliver a personalised SEO &amp; GEO report within 24 hours.
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '3rem' }}>
                        <div style={{ color: 'white' }}>
                            <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>Contact Information</h3>
                            <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>📧 atlanticdigitalusa@gmail.com</div>
                            <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>📞 +34 611 512 450</div>
                            <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>🤖 AI Chat: Available 24/7</div>
                            <div style={{ marginTop: '2.5rem', padding: '1.5rem', background: 'rgba(78,205,196,0.15)', borderRadius: 15, border: '1px solid rgba(78,205,196,0.3)' }}>
                                <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.6, color: 'rgba(255,255,255,0.85)' }}>
                                    🔒 Free analysis includes your overall SEO &amp; GEO scores. Full keyword gap analysis and improvement plan delivered after onboarding.
                                </p>
                            </div>
                        </div>

                        <form onSubmit={handleSubmit} style={{
                            background: 'rgba(255,255,255,0.1)', padding: '2.5rem',
                            borderRadius: 25, backdropFilter: 'blur(15px)', border: '1px solid rgba(255,255,255,0.2)'
                        }}>
                            {submitted ? (
                                <div style={{ textAlign: 'center', color: 'white', padding: '2rem' }}>
                                    <span style={{ fontSize: '3rem' }}>✅</span>
                                    <h3>Request Received!</h3>
                                    <p>We'll be in touch within 24 hours with your personalised report.</p>
                                </div>
                            ) : (
                                <>
                                    <div style={{ marginBottom: '1.5rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>Full Name *</label>
                                        <input type="text" required value={form.name} onChange={update('name')} style={inputStyle} placeholder="Your name" />
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                                        <div>
                                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>Email Address *</label>
                                            <input type="email" required value={form.email} onChange={update('email')} style={inputStyle} placeholder="you@business.com" />
                                        </div>
                                        <div>
                                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>Phone Number</label>
                                            <input type="tel" value={form.phone} onChange={update('phone')} style={inputStyle} placeholder="+34 600 000 000" />
                                        </div>
                                    </div>

                                    <div style={{ marginBottom: '1.5rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>Website URL *</label>
                                        <input type="url" required value={form.website} onChange={update('website')} style={inputStyle} placeholder="https://yourbusiness.com" />
                                    </div>

                                    <div style={{ marginBottom: '1.5rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>What do you want to improve?</label>
                                        <select value={form.goal} onChange={update('goal')} style={{ ...inputStyle, cursor: 'pointer' }}>
                                            <option value="both">Both SEO &amp; GEO (recommended)</option>
                                            <option value="seo">SEO — improve Google search rankings</option>
                                            <option value="geo">GEO — appear in AI answers (ChatGPT, Perplexity…)</option>
                                            <option value="unsure">Not sure yet</option>
                                        </select>
                                    </div>

                                    <div style={{ marginBottom: '1.5rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>
                                            Any specific challenges? <span style={{ fontWeight: 400, opacity: 0.7 }}>(optional)</span>
                                        </label>
                                        <textarea
                                            value={form.message} onChange={update('message')}
                                            placeholder="e.g. We don't appear in local search results, or ChatGPT never mentions us..."
                                            rows={3}
                                            style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit', minHeight: 80 }}
                                        />
                                    </div>

                                    <button type="submit" disabled={submitting}
                                        style={{
                                            width: '100%', background: submitting ? 'linear-gradient(135deg, #4ECDC4, #44A08D)' : '#2C3E50',
                                            color: 'white', padding: '1rem', border: 'none', borderRadius: 50,
                                            fontWeight: 600, cursor: 'pointer', fontSize: '1rem'
                                        }}>
                                        {submitting ? '🔄 Sending...' : 'Request Free Analysis'}
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
