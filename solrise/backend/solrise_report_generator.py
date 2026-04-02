"""
SolRise SEO/GEO Analysis Report Generator
==========================================
Branded PDF report with charts, recommendations, and professional styling
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os
import tempfile
from datetime import datetime

# =============================================================================
# SOLRISE BRAND COLORS
# =============================================================================
SOLRISE_COLORS = {
    'primary_orange': colors.HexColor('#F7A14F'),
    'coral':          colors.HexColor('#F07A63'),
    'soft_yellow':    colors.HexColor('#F9C96B'),
    'pink':           colors.HexColor('#F39BB2'),
    'lavender':       colors.HexColor('#9C8BD9'),
    'sky_blue':       colors.HexColor('#6EA9D6'),
    'text_dark':      colors.HexColor('#2D3748'),
    'text_light':     colors.HexColor('#718096'),
    'white':          colors.white,
    'light_bg':       colors.HexColor('#FFF9F5'),
    'dark_bg':        colors.HexColor('#1A1A2E'),
}

MPL_COLORS = ['#F7A14F', '#F07A63', '#F9C96B', '#F39BB2', '#9C8BD9', '#6EA9D6']

# =============================================================================
# STYLES
# =============================================================================
def get_solrise_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SolRiseTitle',    parent=styles['Title'],   fontSize=28, textColor=SOLRISE_COLORS['coral'],          spaceAfter=20, alignment=TA_CENTER,  fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SolRiseHeading',  parent=styles['Heading1'],fontSize=16, textColor=SOLRISE_COLORS['primary_orange'],  spaceBefore=20,spaceAfter=10, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SolRiseSubheading',parent=styles['Heading2'],fontSize=13, textColor=SOLRISE_COLORS['coral'],           spaceBefore=14,spaceAfter=7,  fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SolRiseBody',     parent=styles['Normal'],  fontSize=10, textColor=SOLRISE_COLORS['text_dark'],       spaceAfter=6,  leading=15,   fontName='Helvetica'))
    styles.add(ParagraphStyle(name='SolRiseCaption',  parent=styles['Normal'],  fontSize=9,  textColor=SOLRISE_COLORS['text_light'],      spaceAfter=4,  leading=13,   fontName='Helvetica'))
    styles.add(ParagraphStyle(name='SolRiseHighlight',parent=styles['Normal'],  fontSize=11, textColor=SOLRISE_COLORS['primary_orange'],  spaceAfter=6,                fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SolRiseFooter',   parent=styles['Normal'],  fontSize=9,  textColor=SOLRISE_COLORS['text_light'],      alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SolRiseCallout',  parent=styles['Normal'],  fontSize=10, textColor=SOLRISE_COLORS['text_dark'],       spaceAfter=6,  leading=15,   fontName='Helvetica', backColor=SOLRISE_COLORS['light_bg'], borderPadding=(8,8,8,8)))
    return styles


# =============================================================================
# CHART HELPERS
# =============================================================================
def _logo_dimensions(path, target_width_inch):
    """Return (w_in, h_in) preserving aspect ratio."""
    try:
        from PIL import Image as _PIL
        img = _PIL.open(path)
        w, h = img.size
        aspect = w / h
        tw = target_width_inch * inch
        return tw, tw / aspect
    except Exception:
        return target_width_inch * inch, target_width_inch * inch


def create_score_gauge(score, title, filename):
    import numpy as np
    fig, ax = plt.subplots(figsize=(3.5, 2.8), subplot_kw={'projection': 'polar'})
    ax.set_theta_offset(3.14159)
    ax.set_theta_direction(-1)
    ax.set_thetamin(0)
    ax.set_thetamax(180)

    theta_bg = np.linspace(0, np.pi, 180)
    ax.fill_between(theta_bg, 0.3, 0.95, color='#E2E8F0', alpha=0.6)

    score_angle = score / 100 * np.pi
    theta_score = np.linspace(0, score_angle, max(2, int(score * 2)))
    color = '#27ae60' if score >= 70 else ('#F9C96B' if score >= 50 else '#F07A63')
    ax.fill_between(theta_score, 0.3, 0.95, color=color, alpha=0.85)

    ax.annotate(f'{score}%', xy=(np.pi/2, 0), fontsize=20, fontweight='bold',
                ha='center', va='center', color='#2D3748')
    ax.annotate(title, xy=(np.pi/2, -0.38), fontsize=9,
                ha='center', va='center', color='#718096')
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.tight_layout(pad=0.5)
    plt.savefig(filename, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    return filename


def create_keyword_bar_chart(keywords, scores, filename):
    """Horizontal bar chart — scores normalised to 0-100%."""
    import numpy as np
    n = min(len(keywords), 10)
    keywords, scores = keywords[:n], scores[:n]

    # Normalise to 0-100 if values are in 0-1 range
    max_s = max(scores) if scores else 1
    norm_scores = [s / max_s * 100 for s in scores]

    fig, ax = plt.subplots(figsize=(7, max(3.5, n * 0.45)))
    y_pos = range(n)
    bar_colors = [MPL_COLORS[i % len(MPL_COLORS)] for i in range(n)]
    bars = ax.barh(y_pos, norm_scores, color=bar_colors, height=0.55, edgecolor='white')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(keywords, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Opportunity Score (%)', fontsize=9, color='#2D3748')
    ax.set_xlim(0, 115)
    ax.set_title('Keyword Gap Opportunities', fontsize=13, fontweight='bold', color='#F07A63', pad=12)

    for bar, s in zip(bars, norm_scores):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
                f'{s:.0f}%', va='center', fontsize=8, color='#718096')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    plt.tight_layout()
    plt.savefig(filename, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    return filename


def create_competitor_comparison(client_name, competitors, scores, filename):
    fig, ax = plt.subplots(figsize=(7, 4))
    names = [client_name] + competitors
    n = len(names)
    bar_colors = ['#F07A63'] + [MPL_COLORS[(i+1) % len(MPL_COLORS)] for i in range(len(competitors))]
    bars = ax.bar(range(n), scores[:n], color=bar_colors[:n], width=0.55, edgecolor='white')
    ax.set_xticks(range(n))
    ax.set_xticklabels(names, fontsize=9, rotation=20, ha='right')
    ax.set_ylabel('Overall Score (%)', fontsize=9, color='#2D3748')
    ax.set_title('Competitive Positioning', fontsize=13, fontweight='bold', color='#F07A63', pad=12)
    ax.set_ylim(0, 110)
    for bar, sc in zip(bars, scores[:n]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{sc:.0f}%', ha='center', fontsize=10, fontweight='bold', color='#2D3748')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    plt.tight_layout()
    plt.savefig(filename, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    return filename


def create_geo_breakdown_pie(geo_scores, filename):
    """Full-page pie chart — large figure, no squeezing."""
    labels = ['Extractability\n(35%)', 'Readability\n(25%)', 'Citability\n(25%)', 'Schema\n(10%)', 'FAQ\n(5%)']
    weights = [0.35, 0.25, 0.25, 0.10, 0.05]
    raw = [
        geo_scores.get('extractability', 0.5),
        geo_scores.get('readability',    0.5),
        geo_scores.get('citability',     0.5),
        geo_scores.get('schema',         0.5),
        geo_scores.get('faq',            0.3),
    ]
    # Weighted contribution
    sizes = [r * w * 100 for r, w in zip(raw, weights)]

    fig, ax = plt.subplots(figsize=(7, 6))
    pie_colors = ['#F7A14F', '#F07A63', '#F9C96B', '#9C8BD9', '#6EA9D6']
    explode = [0.04, 0, 0, 0, 0]

    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=labels, colors=pie_colors,
        autopct='%1.1f%%', startangle=90, pctdistance=0.72,
        wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'},
    )
    for at in autotexts:
        at.set_color('white'); at.set_fontweight('bold'); at.set_fontsize(10)
    for t in texts:
        t.set_fontsize(10); t.set_color('#2D3748')

    # Inner score label
    weighted_total = sum(r * w for r, w in zip(raw, weights))
    ax.text(0, 0, f'{weighted_total*100:.0f}%\nGEO', ha='center', va='center',
            fontsize=14, fontweight='bold', color='#2D3748')

    ax.set_title('GEO Score Breakdown — Weighted Contribution', fontsize=13, fontweight='bold',
                 color='#F07A63', pad=15)
    plt.tight_layout()
    plt.savefig(filename, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    return filename


# =============================================================================
# TABLE HELPERS
# =============================================================================
def _score_status(v):
    return ('✓ Strong', SOLRISE_COLORS['sky_blue']) if v >= 0.7 else \
           ('~ Moderate', SOLRISE_COLORS['soft_yellow']) if v >= 0.5 else \
           ('✗ Needs Work', SOLRISE_COLORS['coral'])


# =============================================================================
# PDF REPORT GENERATOR
# =============================================================================
class SolRiseReportGenerator:
    def __init__(self, output_path, logo_path=None, tmpdir=None):
        self.output_path = output_path
        self.logo_path = logo_path
        self.tmpdir = tmpdir or tempfile.mkdtemp()
        self.styles = get_solrise_styles()
        self.width, self.height = A4

    # ------------------------------------------------------------------
    def _header_footer(self, canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(SOLRISE_COLORS['primary_orange'])
        canvas.rect(0, self.height - 38, self.width, 38, fill=True, stroke=False)
        # Logo in header — aspect-ratio-safe
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                canvas.drawImage(self.logo_path, 18, self.height - 34,
                                 width=28, height=28,
                                 preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        canvas.setFillColor(SOLRISE_COLORS['white'])
        canvas.setFont('Helvetica-Bold', 11)
        canvas.drawRightString(self.width - 18, self.height - 24, 'SolRise · SEO & GEO Analysis Report')
        # Footer line
        canvas.setStrokeColor(SOLRISE_COLORS['soft_yellow'])
        canvas.setLineWidth(1.5)
        canvas.line(30, 38, self.width - 30, 38)
        canvas.setFillColor(SOLRISE_COLORS['text_light'])
        canvas.setFont('Helvetica', 8)
        canvas.drawString(30, 24, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        canvas.drawRightString(self.width - 30, 24, f"Page {doc.page}")
        canvas.drawCentredString(self.width / 2, 24, 'www.solrise.ai  |  Confidential')
        canvas.restoreState()

    # ------------------------------------------------------------------
    def generate_report(self, analysis_data):
        doc = SimpleDocTemplate(self.output_path, pagesize=A4,
                                rightMargin=36, leftMargin=36,
                                topMargin=60, bottomMargin=56)
        story = []
        S = self.styles

        client_name   = analysis_data.get('client_name', 'Client')
        client_url    = analysis_data.get('client_url', '')
        industry      = analysis_data.get('industry', '')
        location      = analysis_data.get('location', '')
        overall_score = int(analysis_data.get('overall_score', 60))
        seo_score     = int(analysis_data.get('seo_score', 60))
        geo_score     = int(analysis_data.get('geo_score', 50))
        comp_score    = int(analysis_data.get('competitive_score', 50))

        # ── COVER ────────────────────────────────────────────────────────────
        story.append(Spacer(1, 1.2 * inch))

        # Logo — correct aspect ratio
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                lw, lh = _logo_dimensions(self.logo_path, 1.8)
                logo_img = Image(self.logo_path, width=lw, height=lh)
                logo_img.hAlign = 'CENTER'
                story.append(logo_img)
                story.append(Spacer(1, 0.4 * inch))
            except Exception:
                pass

        story.append(Paragraph('SEO &amp; GEO Analysis Report', S['SolRiseTitle']))
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(f'<b>{client_name}</b>',
                               ParagraphStyle('CoverClient', parent=S['SolRiseBody'],
                                              fontSize=15, alignment=TA_CENTER,
                                              textColor=SOLRISE_COLORS['text_dark'])))
        if client_url:
            story.append(Paragraph(client_url, ParagraphStyle('CoverURL', parent=S['SolRiseCaption'], alignment=TA_CENTER)))
        if industry or location:
            story.append(Paragraph(f'{industry}  ·  {location}',
                                   ParagraphStyle('CoverMeta', parent=S['SolRiseCaption'], alignment=TA_CENTER)))
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(datetime.now().strftime('%B %d, %Y'),
                               ParagraphStyle('CoverDate', parent=S['SolRiseCaption'], alignment=TA_CENTER)))
        story.append(Spacer(1, 0.6 * inch))

        # Score summary boxes on cover
        cover_scores = [
            ('Overall Score', overall_score, '#F07A63'),
            ('SEO Score',     seo_score,     '#F7A14F'),
            ('GEO Score',     geo_score,     '#9C8BD9'),
        ]
        box_rows = [[
            Paragraph(f'<font color="{c}"><b>{v}%</b></font><br/><font color="#718096">{lbl}</font>',
                      ParagraphStyle('BoxScore', parent=S['SolRiseBody'], alignment=TA_CENTER, fontSize=12))
            for lbl, v, c in cover_scores
        ]]
        bt = Table(box_rows, colWidths=[1.6*inch, 1.6*inch, 1.6*inch])
        bt.setStyle(TableStyle([
            ('BOX',          (0,0), (-1,-1), 1,   SOLRISE_COLORS['soft_yellow']),
            ('INNERGRID',    (0,0), (-1,-1), 0.5, SOLRISE_COLORS['soft_yellow']),
            ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING',   (0,0), (-1,-1), 12),
            ('BOTTOMPADDING',(0,0), (-1,-1), 12),
            ('BACKGROUND',   (0,0), (-1,-1), SOLRISE_COLORS['light_bg']),
        ]))
        bt.hAlign = 'CENTER'
        story.append(bt)
        story.append(Spacer(1, 0.5 * inch))

        summary_text = (
            f'This report provides a comprehensive analysis of <b>{client_name}</b>\'s '
            f'digital presence across traditional SEO metrics and AI-focused GEO '
            f'(Generative Engine Optimization) factors. Results are benchmarked against '
            f'competitors and actionable opportunities are identified and prioritized.'
        )
        story.append(Paragraph(summary_text, S['SolRiseBody']))
        story.append(PageBreak())

        # ── SCORE OVERVIEW ───────────────────────────────────────────────────
        story.append(Paragraph('Score Overview', S['SolRiseHeading']))
        story.append(Paragraph(
            'Scores are computed on a 0–100 scale. Each metric reflects a different dimension '
            'of your website\'s discoverability and credibility.', S['SolRiseBody']))
        story.append(Spacer(1, 0.2 * inch))

        # Gauges
        for key, title, fname in [
            (overall_score, 'Overall Score', 'gauge_overall.png'),
            (seo_score,     'SEO Score',     'gauge_seo.png'),
            (geo_score,     'GEO Score',     'gauge_geo.png'),
        ]:
            create_score_gauge(key, title, os.path.join(self.tmpdir, fname))

        g_row = [Image(os.path.join(self.tmpdir, f), width=1.9*inch, height=1.5*inch)
                 for f in ['gauge_overall.png', 'gauge_seo.png', 'gauge_geo.png']]
        gauge_table = Table([g_row], colWidths=[2.1*inch, 2.1*inch, 2.1*inch])
        gauge_table.setStyle(TableStyle([
            ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND',   (0,0), (-1,-1), SOLRISE_COLORS['light_bg']),
            ('BOX',          (0,0), (-1,-1), 0.5, SOLRISE_COLORS['soft_yellow']),
        ]))
        story.append(gauge_table)
        story.append(Spacer(1, 0.25 * inch))

        # Score methodology table
        story.append(Paragraph('What each score measures:', S['SolRiseSubheading']))

        # A4 usable width = 595 - 36 - 36 = 523pt ≈ 7.26 inch
        # Col widths must sum to ≤ 7.26 inch
        _P = lambda txt, bold=False, center=False: Paragraph(
            f'<b>{txt}</b>' if bold else txt,
            ParagraphStyle('_tc', parent=S['SolRiseBody'], fontSize=9,
                           alignment=1 if center else 0))

        methodology = [
            [_P('Score', bold=True), _P('What it measures', bold=True),
             _P('Key factors', bold=True), _P(client_name, bold=True, center=True)],
            [_P('Overall\n(0–100)', bold=True),
             _P('Weighted combination of SEO + GEO + Competitive position'),
             _P('SEO×35% + GEO×50% + Comp×15%'),
             _P(f'{overall_score}%', center=True)],
            [_P('SEO\n(0–100)', bold=True),
             _P('Technical on-page optimisation & keyword relevance'),
             _P('Keywords, meta tags, headings, links, schema, word count'),
             _P(f'{seo_score}%', center=True)],
            [_P('GEO\n(0–100)', bold=True),
             _P('How likely AI systems are to cite your content'),
             _P('Extractability, claim density, citability, FAQ, readability'),
             _P(f'{geo_score}%', center=True)],
            [_P('Competitive\n(0–1)', bold=True),
             _P('Semantic similarity to competitor content'),
             _P('Cosine similarity of keyword embeddings vs competitors'),
             _P(f'{comp_score}%', center=True)],
        ]
        mt = Table(methodology, colWidths=[1.0*inch, 2.3*inch, 2.3*inch, 0.8*inch])
        mt.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), SOLRISE_COLORS['primary_orange']),
            ('TEXTCOLOR',    (0,0), (-1,0), SOLRISE_COLORS['white']),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, SOLRISE_COLORS['light_bg']]),
            ('GRID',         (0,0), (-1,-1), 0.4, SOLRISE_COLORS['soft_yellow']),
            ('TOPPADDING',   (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0), (-1,-1), 7),
            ('LEFTPADDING',  (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(mt)
        story.append(Spacer(1, 0.2 * inch))

        # Interpretation
        if overall_score >= 70:
            interp = (f'<b>Strong performance ({overall_score}%)</b> — Your site is well-optimised. '
                      f'Focus on closing the remaining gaps to reach the top tier.')
            ic = SOLRISE_COLORS['sky_blue']
        elif overall_score >= 50:
            interp = (f'<b>Moderate performance ({overall_score}%)</b> — Solid foundation with '
                      f'meaningful room to improve. Prioritise the high-impact recommendations below.')
            ic = SOLRISE_COLORS['soft_yellow']
        else:
            interp = (f'<b>Needs immediate attention ({overall_score}%)</b> — Implementing the '
                      f'recommendations in this report will substantially improve your visibility.')
            ic = SOLRISE_COLORS['coral']

        story.append(Paragraph(interp, ParagraphStyle('Interp', parent=S['SolRiseBody'],
                                                       textColor=ic, fontSize=11,
                                                       backColor=SOLRISE_COLORS['light_bg'],
                                                       borderPadding=(8,8,8,8))))
        story.append(PageBreak())

        # ── COMPETITIVE ANALYSIS ─────────────────────────────────────────────
        story.append(Paragraph('Competitive Analysis', S['SolRiseHeading']))
        story.append(Paragraph(
            f'The chart below compares <b>{client_name}</b>\'s overall score against analysed competitors. '
            f'A higher score indicates better SEO + GEO optimization.', S['SolRiseBody']))
        story.append(Spacer(1, 0.15 * inch))

        competitors    = analysis_data.get('competitors', ['Competitor A', 'Competitor B'])
        comp_scores    = analysis_data.get('competitor_scores', [70, 65])
        all_scores_val = [overall_score] + comp_scores

        create_competitor_comparison(client_name, competitors, all_scores_val,
                                     os.path.join(self.tmpdir, 'competitor_chart.png'))
        ci = Image(os.path.join(self.tmpdir, 'competitor_chart.png'), width=6.2*inch, height=3.4*inch)
        ci.hAlign = 'CENTER'
        story.append(ci)
        story.append(Spacer(1, 0.2 * inch))

        # Competitive insights
        story.append(Paragraph('Key Competitive Insights:', S['SolRiseSubheading']))
        insights = analysis_data.get('competitive_insights', [
            'Content depth may be below competitor average',
            'Competitors may use more structured data markup',
            'GEO citation readiness can be improved',
        ])
        for ins in insights:
            if ins.strip():
                story.append(Paragraph(f'• {ins}', S['SolRiseBody']))
        story.append(PageBreak())

        # ── TEASER CUTOFF — if mode='teaser' stop here and add lock page ─────
        teaser_mode = analysis_data.get('teaser_mode', False)
        if teaser_mode:
            story.append(Spacer(1, 1.2 * inch))
            # Lock page visual
            story.append(Paragraph('🔒', ParagraphStyle('LockIcon', parent=S['SolRiseBody'],
                                                          fontSize=48, alignment=1)))
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph('Full Report — Unlocked for SolRise Clients',
                                   ParagraphStyle('LockTitle', parent=S['SolRiseHeading'],
                                                  alignment=1, textColor=SOLRISE_COLORS['coral'])))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(
                'The full report includes:',
                ParagraphStyle('LockSub', parent=S['SolRiseBody'], alignment=1, fontSize=11)))
            story.append(Spacer(1, 0.15 * inch))

            locked_items = [
                '📊  Keyword Gap Analysis — ' + str(len(analysis_data.get('keyword_gaps', []))) + ' opportunities identified',
                '🤖  Full GEO Breakdown — per-factor scores & improvement guide',
                '✅  Prioritised Recommendations — with estimated impact %',
                '🗺️  90-Day Action Plan & Next Steps',
            ]
            for item in locked_items:
                story.append(Paragraph(item,
                    ParagraphStyle('LockItem', parent=S['SolRiseBody'], fontSize=11,
                                   alignment=1, textColor=SOLRISE_COLORS['text_dark'],
                                   spaceAfter=10)))

            story.append(Spacer(1, 0.5 * inch))
            story.append(HRFlowable(width='60%', thickness=2, color=SOLRISE_COLORS['soft_yellow'],
                                    spaceBefore=10, spaceAfter=20))
            story.append(Paragraph(
                '<b>Get your full report — contact SolRise today</b><br/><br/>'
                '📧 support@solrise.ai  |  🌐 www.solrise.ai',
                ParagraphStyle('LockCTA', parent=S['SolRiseBody'],
                               alignment=1, fontSize=13,
                               textColor=SOLRISE_COLORS['primary_orange'])))
            doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            return self.output_path

        # ── KEYWORD GAP ANALYSIS ─────────────────────────────────────────────
        story.append(Paragraph('Keyword Gap Analysis', S['SolRiseHeading']))
        story.append(Paragraph(
            'Keywords your competitors rank for but your site does not — each represents '
            'an untapped traffic opportunity. Scores are normalised to 100%.', S['SolRiseBody']))
        story.append(Spacer(1, 0.15 * inch))

        keyword_gaps = analysis_data.get('keyword_gaps', [])
        kw_names  = [k[0] for k in keyword_gaps[:10]]
        kw_scores = [k[1] for k in keyword_gaps[:10]]

        if kw_names:
            create_keyword_bar_chart(kw_names, kw_scores, os.path.join(self.tmpdir, 'keyword_chart.png'))
            ki = Image(os.path.join(self.tmpdir, 'keyword_chart.png'), width=6.2*inch, height=3.4*inch)
            ki.hAlign = 'CENTER'
            story.append(ki)
            story.append(Spacer(1, 0.2 * inch))

        # Keyword table
        if keyword_gaps:
            story.append(Paragraph('Keyword Opportunity Table:', S['SolRiseSubheading']))
            max_sc = max(k[1] for k in keyword_gaps) if keyword_gaps else 1
            _Kp = lambda txt, bold=False, center=False: Paragraph(
                f'<b>{txt}</b>' if bold else txt,
                ParagraphStyle('_kc', parent=S['SolRiseBody'], fontSize=9,
                               alignment=1 if center else 0))

            kw_table_data = [[_Kp('Keyword', bold=True), _Kp('Score', bold=True, center=True),
                              _Kp('Priority', bold=True, center=True), _Kp('Recommended Action', bold=True)]]
            for kw, sc in keyword_gaps[:8]:
                norm = sc / max_sc * 100
                priority = 'High' if norm >= 70 else ('Medium' if norm >= 40 else 'Low')
                action   = 'Create dedicated page' if priority == 'High' else \
                           ('Add content section' if priority == 'Medium' else 'Mention in copy')
                kw_table_data.append([_Kp(kw), _Kp(f'{norm:.0f}%', center=True),
                                      _Kp(priority, center=True), _Kp(action)])

            kwt = Table(kw_table_data, colWidths=[2.65*inch, 0.7*inch, 0.75*inch, 2.2*inch])
            kwt.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,0), SOLRISE_COLORS['primary_orange']),
                ('TEXTCOLOR',    (0,0), (-1,0), SOLRISE_COLORS['white']),
                ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, SOLRISE_COLORS['light_bg']]),
                ('GRID',         (0,0), (-1,-1), 0.4, SOLRISE_COLORS['soft_yellow']),
                ('TOPPADDING',   (0,0), (-1,-1), 7),
                ('BOTTOMPADDING',(0,0), (-1,-1), 7),
                ('LEFTPADDING',  (0,0), (-1,-1), 5),
            ]))
            story.append(kwt)

        story.append(PageBreak())

        # ── GEO ANALYSIS ─────────────────────────────────────────────────────
        story.append(Paragraph('GEO — Generative Engine Optimization', S['SolRiseHeading']))
        story.append(Paragraph(
            'GEO measures how likely AI systems (ChatGPT, Perplexity, Google AI Overviews) are '
            'to extract and cite your content. Each factor is weighted by its impact on AI citation.', S['SolRiseBody']))
        story.append(Spacer(1, 0.15 * inch))

        geo_breakdown = analysis_data.get('geo_breakdown', {
            'extractability': 0.5, 'readability': 0.5, 'citability': 0.5, 'schema': 0.5, 'faq': 0.3
        })

        create_geo_breakdown_pie(geo_breakdown, os.path.join(self.tmpdir, 'geo_pie.png'))
        gi = Image(os.path.join(self.tmpdir, 'geo_pie.png'), width=5.5*inch, height=4.7*inch)
        gi.hAlign = 'CENTER'
        story.append(gi)
        story.append(Spacer(1, 0.15 * inch))

        # GEO factor table
        story.append(Paragraph('GEO Factor Detail:', S['SolRiseSubheading']))
        factor_info = [
            ('Extractability', 'extractability', '35%',
             'How easily AI can pull clean facts and answers from your content',
             'Short paragraphs, bullet points, clear headings, ≥4 claims/100 words'),
            ('Readability',    'readability',    '25%',
             'Sentence clarity and structure for AI parsing',
             'Avg sentence ≤20 words, active voice, logical flow'),
            ('Citability',     'citability',     '25%',
             'Whether your content contains quotable, authoritative statements',
             'Statistics, expert claims, specific numbers, named sources'),
            ('Schema Markup',  'schema',         '10%',
             'Structured data enabling AI to understand your content type',
             'LocalBusiness, FAQPage, Article, Organization JSON-LD'),
            ('FAQ Quality',    'faq',             '5%',
             'FAQ sections directly answer user questions — high AI citation value',
             '4+ Q&A covering common queries with specific answers'),
        ]
        _Pg = lambda txt, bold=False, center=False: Paragraph(
            f'<b>{txt}</b>' if bold else txt,
            ParagraphStyle('_gc', parent=S['SolRiseBody'], fontSize=9,
                           alignment=1 if center else 0))

        geo_tbl_data = [[_Pg('Factor', bold=True), _Pg('Score', bold=True, center=True),
                         _Pg('Weight', bold=True, center=True), _Pg('What it measures', bold=True)]]
        for label, key, weight, what, _ in factor_info:
            val = geo_breakdown.get(key, 0.5)
            status_text, _ = _score_status(val)
            geo_tbl_data.append([
                _Pg(label, bold=True),
                _Pg(f'{val*100:.0f}%  {status_text}', center=True),
                _Pg(weight, center=True),
                _Pg(what),
            ])

        gt = Table(geo_tbl_data, colWidths=[1.15*inch, 1.25*inch, 0.65*inch, 3.25*inch])
        gt.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), SOLRISE_COLORS['coral']),
            ('TEXTCOLOR',     (0,0), (-1,0), SOLRISE_COLORS['white']),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, SOLRISE_COLORS['light_bg']]),
            ('GRID',          (0,0), (-1,-1), 0.4, SOLRISE_COLORS['pink']),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (-1,-1), 5),
            ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ]))
        story.append(gt)

        # GEO improvement tips
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('How to improve each GEO factor:', S['SolRiseSubheading']))
        for label, key, _, _, how in factor_info:
            val = geo_breakdown.get(key, 0.5)
            if val < 0.7:
                story.append(Paragraph(
                    f'<b>{label}</b> ({val*100:.0f}%) — {how}',
                    ParagraphStyle('GeoTip', parent=S['SolRiseBody'],
                                   textColor=SOLRISE_COLORS['text_dark'], leftIndent=10)))

        story.append(PageBreak())

        # ── RECOMMENDATIONS ───────────────────────────────────────────────────
        story.append(Paragraph('Recommendations', S['SolRiseHeading']))
        story.append(Paragraph(
            'Recommendations are ordered by priority. '
            'Estimated impact shows the expected score improvement upon implementation.',
            S['SolRiseBody']))
        story.append(Spacer(1, 0.15 * inch))

        recommendations = analysis_data.get('recommendations', [])
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations = sorted(recommendations,
                                  key=lambda r: priority_order.get(str(r.get('priority','')).upper(), 2))

        if recommendations:
            _Rh = lambda txt: Paragraph(f'<b>{txt}</b>',
                ParagraphStyle('_rh', parent=S['SolRiseBody'], fontSize=9,
                               textColor=SOLRISE_COLORS['white'], alignment=1))
            _Rc = lambda txt, center=False: Paragraph(txt,
                ParagraphStyle('_rc', parent=S['SolRiseBody'], fontSize=9,
                               alignment=1 if center else 0))

            PRI_LABEL = {'CRITICAL': 'Critical', 'HIGH': 'High', 'MEDIUM': 'Medium', 'LOW': 'Low'}
            PRI_COLOR = {'CRITICAL': '#e74c3c', 'HIGH': '#e67e22', 'MEDIUM': '#f39c12', 'LOW': '#3498db'}

            rec_tbl_data = [[_Rh('#'), _Rh('Priority'), _Rh('Area'), _Rh('Action'), _Rh('+Impact')]]
            for i, rec in enumerate(recommendations[:10], 1):
                pri    = str(rec.get('priority', 'Medium')).upper()
                color  = PRI_COLOR.get(pri, '#e67e22')
                label  = PRI_LABEL.get(pri, pri.title())
                title  = rec.get('title', rec.get('message', 'Improve'))
                desc   = rec.get('description', '')
                impact = rec.get('impact_pct', '')
                impact_str = f'+{impact}%' if impact else '—'

                # Truncate title to keep cell manageable; put desc on second line
                title_short = title[:90] + ('…' if len(title) > 90 else '')
                action_text = f'<b>{title_short}</b>'
                if desc:
                    desc_short = desc[:100] + ('…' if len(desc) > 100 else '')
                    action_text += f'<br/><font color="#718096" size="8">{desc_short}</font>'

                # Category: strip prefix for display
                cat = rec.get('category', '—')
                cat_display = cat.replace('GEO-', '').replace('SEO-', '').title()

                rec_tbl_data.append([
                    _Rc(str(i), center=True),
                    Paragraph(f'<font color="{color}"><b>■</b></font> {label}',
                              ParagraphStyle('_pri', parent=S['SolRiseBody'], fontSize=9)),
                    _Rc(cat_display, center=True),
                    Paragraph(action_text, ParagraphStyle('_act', parent=S['SolRiseBody'], fontSize=9,
                                                          leading=13)),
                    _Rc(impact_str, center=True),
                ])
            # Cols: # | Priority | Area | Action | Impact  — sum = 7.26 inch
            rt = Table(rec_tbl_data, colWidths=[0.28*inch, 0.85*inch, 0.75*inch, 4.6*inch, 0.58*inch])
            rt.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), SOLRISE_COLORS['primary_orange']),
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, SOLRISE_COLORS['light_bg']]),
                ('GRID',          (0,0), (-1,-1), 0.4, SOLRISE_COLORS['soft_yellow']),
                ('TOPPADDING',    (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                ('LEFTPADDING',   (0,0), (-1,-1), 5),
                ('RIGHTPADDING',  (0,0), (-1,-1), 5),
            ]))
            story.append(rt)
        else:
            story.append(Paragraph('No recommendations available. Run a full analysis to generate personalised advice.', S['SolRiseBody']))

        story.append(PageBreak())

        # ── NEXT STEPS ────────────────────────────────────────────────────────
        story.append(Paragraph('Next Steps', S['SolRiseHeading']))
        story.append(Spacer(1, 0.1 * inch))

        next_steps = [
            ('Immediate (Week 1)',  '🔴',
             'Address all CRITICAL recommendations — these have the highest impact on both '
             'SEO rankings and AI citation probability.'),
            ('Short-term (Weeks 2–4)', '🟠',
             'Target the top keyword gaps with new content sections or dedicated landing pages.'),
            ('Medium-term (Month 2)', '🟡',
             'Implement schema markup (LocalBusiness, FAQPage), add a FAQ section, '
             'and increase claim density across your main pages.'),
            ('Ongoing',  '🔵',
             'Re-run the SolRise analysis monthly to track score improvements and identify new opportunities.'),
        ]
        for phase, icon, desc in next_steps:
            story.append(Paragraph(f'{icon} <b>{phase}</b>', S['SolRiseHighlight']))
            story.append(Paragraph(desc, ParagraphStyle('NSDesc', parent=S['SolRiseBody'],
                                                         leftIndent=18, textColor=SOLRISE_COLORS['text_light'])))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 0.3 * inch))
        story.append(HRFlowable(width='80%', thickness=2, color=SOLRISE_COLORS['soft_yellow'],
                                spaceBefore=10, spaceAfter=16))
        story.append(Paragraph(
            '<b>Ready to optimize your digital presence?</b><br/><br/>'
            'Contact SolRise for a personalized optimization strategy:<br/>'
            '📧 support@solrise.ai  |  🌐 www.solrise.ai',
            ParagraphStyle('Contact', parent=S['SolRiseBody'],
                           alignment=TA_CENTER, fontSize=11)))

        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        return self.output_path
