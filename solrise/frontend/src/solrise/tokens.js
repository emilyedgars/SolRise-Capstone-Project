// SolRise Design Tokens
export const SR = {
    // Gradients
    sunGradient: 'linear-gradient(180deg, #6EA9D6 0%, #9C8BD9 25%, #F39BB2 45%, #F9C96B 65%, #F7A14F 80%, #F07A63 100%)',
    textGradient: 'linear-gradient(90deg, #F06564, #F39A63, #F5B765)',
    btnGradient:  'linear-gradient(135deg, #F7A14F 0%, #F07A63 100%)',
    heroGradient: 'linear-gradient(165deg, #FFF9F4 0%, #FFF3E8 50%, #FFF6F4 100%)',

    // Brand colors
    orange:   '#F7A14F',
    coral:    '#F07A63',
    yellow:   '#F9C96B',
    pink:     '#F39BB2',
    lavender: '#9C8BD9',
    sky:      '#6EA9D6',

    // Neutrals
    bg:        '#FFFCF8',
    white:     '#FFFFFF',
    dark:      '#1A1A2E',
    gray:      '#6B7280',
    midGray:   '#9CA3AF',
    lightGray: '#F5F3EF',
    border:    'rgba(247, 161, 79, 0.18)',

    // Shadows
    cardShadow:  '0 4px 24px rgba(247, 122, 79, 0.10)',
    hoverShadow: '0 8px 40px rgba(247, 122, 79, 0.22)',
    btnShadow:   '0 4px 20px rgba(240, 122, 99, 0.35)',

    // Typography
    font: "'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, sans-serif",
    fontSerif: "Georgia, 'Times New Roman', serif",

    // Radius
    sm:   8,
    md:   16,
    lg:   24,
    xl:   32,
    pill: 9999,
};

// Reusable inline style objects
export const gradientText = {
    background: SR.textGradient,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
};

export const btnPrimary = {
    background: SR.btnGradient,
    color: SR.white,
    border: 'none',
    borderRadius: SR.pill,
    padding: '0.85rem 2.2rem',
    fontWeight: 700,
    cursor: 'pointer',
    fontSize: '1rem',
    boxShadow: SR.btnShadow,
    transition: 'all 0.25s ease',
    letterSpacing: '0.01em',
};

export const btnOutline = {
    background: 'transparent',
    color: SR.dark,
    border: `2px solid ${SR.orange}`,
    borderRadius: SR.pill,
    padding: '0.8rem 2rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '1rem',
    transition: 'all 0.25s ease',
};
