/**
 * ─────────────────────────────────────────────
 *  SolRise — Draft 2 entry point
 * ─────────────────────────────────────────────
 *
 * TO SWITCH TO DRAFT 2:
 *   Open vite.config.js and change:
 *     input: 'src/main.jsx'
 *   to:
 *     input: 'src/main2.jsx'
 *
 * OR: simply rename this file to main.jsx
 *     (and rename the original main.jsx → main_v1.jsx first)
 *
 * TO GO BACK TO DRAFT 1:
 *   Revert the vite.config.js change, or swap file names back.
 * ─────────────────────────────────────────────
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './solrise/App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
