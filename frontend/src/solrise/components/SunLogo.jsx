import React from 'react';
import { SR, gradientText } from '../tokens';

// The SolRise sunrise dome icon
export const SunIcon = ({ size = 48 }) => (
    <svg width={size} height={Math.round(size * 0.78)} viewBox="0 0 64 50" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="srSunGrad" x1="32" y1="0" x2="32" y2="50" gradientUnits="userSpaceOnUse">
                <stop offset="0%"   stopColor="#6EA9D6" />
                <stop offset="22%"  stopColor="#9C8BD9" />
                <stop offset="44%"  stopColor="#F39BB2" />
                <stop offset="65%"  stopColor="#F9C96B" />
                <stop offset="82%"  stopColor="#F7A14F" />
                <stop offset="100%" stopColor="#F07A63" />
            </linearGradient>
        </defs>
        {/* Dome shape — semicircle with slightly organic curved base */}
        <path
            d="M 5 46 Q 4 40 6 35 A 26 26 0 0 1 58 35 Q 60 40 59 46 Q 50 50 32 50 Q 14 50 5 46 Z"
            fill="url(#srSunGrad)"
        />
    </svg>
);

// Full logo: use real PNG if available, fallback to programmatic SVG+text
const SolRiseLogo = ({ size = 42, textSize = '1.5rem', onClick }) => (
    <div
        onClick={onClick}
        style={{
            display: 'inline-flex',
            alignItems: 'center',
            cursor: onClick ? 'pointer' : 'default',
            userSelect: 'none',
        }}
    >
        <img
            src="/solrise-logo.svg"
            alt="SolRise"
            style={{
                height: size * 2,   /* SVG viewBox is square; 2× renders the logo content at correct visual size */
                width: size * 2,
                objectFit: 'contain',
                display: 'block',
                flexShrink: 0,
            }}
            onError={e => {
                e.currentTarget.src = '/solrise-logo.png'; // fallback to PNG
                e.currentTarget.onError = () => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.nextSibling.style.display = 'inline-flex';
                };
            }}
        />
        {/* Fallback shown only if PNG fails to load */}
        <span style={{ display: 'none', alignItems: 'center', gap: '0.55rem' }}>
            <SunIcon size={size} />
            <span style={{
                ...gradientText,
                fontFamily: SR.fontSerif,
                fontSize: textSize,
                fontWeight: 700,
                letterSpacing: '-0.02em',
                lineHeight: 1,
            }}>
                SolRise
            </span>
        </span>
    </div>
);

export default SolRiseLogo;
