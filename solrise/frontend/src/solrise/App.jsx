/**
 * SolRise — Draft 2
 *
 * To activate this draft, change frontend/src/main.jsx to:
 *   import App from './solrise/App'
 *
 * To go back to Atlantic Digital draft 1:
 *   import App from './App'  (the original)
 */
import React, { useState, useEffect } from 'react';
import Header   from './components/Header';
import Footer   from './components/Footer';
import HomePage     from './pages/HomePage';
import ServicesPage from './pages/ServicesPage';
import AboutPage    from './pages/AboutPage';
import QuizPage     from './pages/QuizPage';
import DashboardPage from '../pages/DashboardPage';

const isDashboard = tab => tab === 'dashboard';

const App = () => {
    const [activeTab,  setActiveTab]  = useState('home');
    const [isScrolled, setIsScrolled] = useState(false);

    useEffect(() => {
        const onScroll = () => setIsScrolled(window.scrollY > 50);
        window.addEventListener('scroll', onScroll);
        return () => window.removeEventListener('scroll', onScroll);
    }, []);

    return (
        <div style={{ fontFamily: "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif" }}>
            {!isDashboard(activeTab) && (
                <Header
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    isScrolled={isScrolled}
                />
            )}

            {activeTab === 'home'      && <HomePage      setActiveTab={setActiveTab} />}
            {activeTab === 'services'  && <ServicesPage  setActiveTab={setActiveTab} />}
            {activeTab === 'about'     && <AboutPage     setActiveTab={setActiveTab} />}
            {activeTab === 'quiz'      && <QuizPage      setActiveTab={setActiveTab} />}
            {activeTab === 'dashboard' && <DashboardPage setActiveTab={setActiveTab} />}

            {!isDashboard(activeTab) && activeTab !== 'quiz' && (
                <Footer setActiveTab={setActiveTab} />
            )}
        </div>
    );
};

export default App;
