import React, { useState, useEffect } from 'react';

const ProjectsPanel = ({ setAnalysis, setPanel }) => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                const data = await response.json();
                setProjects(data);
            }
        } catch (e) {
            console.error("Failed to fetch projects", e);
        }
        setLoading(false);
    };

    const handleView = (project) => {
        setAnalysis({
            clientName: project.client_name,
            clientUrl: project.client_url,
            location: project.location,
            industry: project.industry,
            competitors: project.competitors,
            results: project.results
        });
        setPanel('results');
    };

    return (
        <div style={{ color: 'white' }}>
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>📁 Projects</h1>
                <p style={{ color: '#95a5a6' }}>Manage your client analysis projects</p>
            </div>

            {loading ? (
                <div style={{ color: '#95a5a6' }}>Loading projects...</div>
            ) : projects.length === 0 ? (
                <div style={{ color: '#95a5a6' }}>No projects found. Start a new analysis!</div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    {projects.map((p, i) => (
                        <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: 15, border: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{p.client_name}</h3>
                                <span style={{
                                    padding: '0.25rem 0.75rem', borderRadius: 20, fontSize: '0.75rem', fontWeight: 600,
                                    background: p.status === 'complete' ? '#4ECDC4' : '#f39c12', textTransform: 'capitalize'
                                }}>{p.status}</span>
                            </div>
                            <div style={{ display: 'flex', gap: '1.5rem', color: '#95a5a6', fontSize: '0.9rem', marginBottom: '1rem' }}>
                                <span>📅 {new Date(p.created_at).toLocaleDateString()}</span>
                                {p.results && <span>📊 Score: {(p.results.overallScore * 100).toFixed(0)}%</span>}
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <button onClick={() => handleView(p)} style={{
                                    background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                                    color: 'white', padding: '0.5rem 1rem', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem'
                                }}>View</button>
                                <button className="export-btn" onClick={() => window.open(`/api/export/${p._id}?format=json`, '_blank')} style={{
                                    background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                                    color: 'white', padding: '0.5rem 1rem', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem'
                                }}>Export</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ProjectsPanel;
