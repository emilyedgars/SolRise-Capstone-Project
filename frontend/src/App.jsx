import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import ServicesPage from './pages/ServicesPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import DashboardPage from './pages/DashboardPage';

const App = () => {
    const [activeTab, setActiveTab] = useState('home');
    const [isScrolled, setIsScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => setIsScrolled(window.scrollY > 50);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div className="app">
            <Header activeTab={activeTab} setActiveTab={setActiveTab} isScrolled={isScrolled} />

            {activeTab === 'home' && <HomePage setActiveTab={setActiveTab} />}
            {activeTab === 'services' && <ServicesPage />}
            {activeTab === 'about' && <AboutPage />}
            {activeTab === 'contact' && <ContactPage />}
            {activeTab === 'dashboard' && <DashboardPage />}

            {activeTab !== 'dashboard' && <Footer />}
        </div>
    );
};

export default App;
