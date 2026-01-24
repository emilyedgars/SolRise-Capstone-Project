import React from 'react';

const AboutPage = () => (
    <main style={{ paddingTop: 80 }}>
        <section style={{ padding: '5rem 2rem', minHeight: '80vh' }}>
            <div style={{ maxWidth: 800, margin: '0 auto' }}>
                <h1 style={{
                    fontSize: '2.5rem', fontWeight: 700, textAlign: 'center', marginBottom: '2rem',
                    background: 'linear-gradient(135deg, #2C3E50, #4A6B7C)',
                    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
                }}>About Atlantic Digital</h1>

                <p style={{ fontSize: '1.1rem', lineHeight: 1.8, color: '#5A6B7D', marginBottom: '1.5rem', textAlign: 'center' }}>
                    We're not your typical marketing agency. We're data scientists and AI engineers who happen to be marketing experts.
                </p>
                <p style={{ fontSize: '1.1rem', lineHeight: 1.8, color: '#5A6B7D', marginBottom: '2rem', textAlign: 'center' }}>
                    Our proprietary combination of AI models, web scraping technology, and advanced analytics gives you an unfair advantage.
                </p>

                <div style={{
                    background: 'linear-gradient(135deg, #2C3E50, #4A6B7C)', padding: '3rem',
                    borderRadius: 25, color: 'white', textAlign: 'center', marginTop: '3rem'
                }}>
                    <h3 style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>Ready to be your Customers' First Choice?</h3>
                    <p style={{ lineHeight: 1.7, opacity: 0.95 }}>
                        Join forward-thinking businesses leveraging AI and data science to lead their markets.
                    </p>
                </div>
            </div>
        </section>
    </main>
);

export default AboutPage;
