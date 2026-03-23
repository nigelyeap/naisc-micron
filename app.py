"""
Smart Tool Log Parser -- Streamlit Dashboard
Micron @ AISG National AI Student Challenge

Run with:  streamlit run app.py
Backend:   python backend/run.py  (must be running on port 8000)
"""

import pathlib

import streamlit as st

from frontend.api_client import APIClient

# -- Page imports --
from pages.upload import render as render_upload
from pages.explorer import render as render_explorer
from pages.analytics_page import render as render_analytics
from pages.nl_query import render as render_nl_query
from pages.summary import render as render_summary

# ------------------------------------------------------------------ #
#  Page config
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="SLP | Micron Smart Log Parser",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%23131319'/><rect x='8' y='8' width='84' height='84' fill='none' stroke='%23ff46a0' stroke-width='2'/><text x='50' y='66' font-size='44' text-anchor='middle' fill='%23ff46a0' font-family='monospace' font-weight='bold'>SLP</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  CSS -- THE OBSIDIAN PROTOCOL
#  Every rule uses !important to override Streamlit 1.53's shadow DOM
# ------------------------------------------------------------------ #
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

/* ================================================================
   THE OBSIDIAN PROTOCOL -- FOUNDATION
   ================================================================ */

:root {
    /* Surface layers */
    --ob-bg:                  #131319;
    --ob-surface-lowest:      #0e0e14;
    --ob-surface-low:         #1b1b22;
    --ob-surface-container:   #1f1f26;
    --ob-surface-high:        #2a2930;
    --ob-surface-highest:     #35343b;
    --ob-surface-bright:      #393840;

    /* Primary palette */
    --ob-primary:             #ffb0cc;
    --ob-primary-container:   #ff46a0;
    --ob-secondary:           #ffbf81;
    --ob-secondary-container: #ff9800;
    --ob-tertiary:            #69df54;
    --ob-error:               #ffb4ab;

    /* Text */
    --ob-on-bg:               #e4e1ea;
    --ob-text-dim:            #8a8694;
    --ob-text-faint:          #4d4a55;

    /* Outline */
    --ob-outline:             #a88892;
    --ob-outline-variant:     #594048;

    /* Derived */
    --ob-ghost-border:        rgba(89, 64, 72, 0.15);
    --ob-glow-pink:           0 0 8px #e91e8c44;
    --ob-glow-ambient:        0 0 40px rgba(14, 14, 20, 0.4);
    --ob-grad:                linear-gradient(135deg, #ff46a0 0%, #ff9800 100%);

    /* Fonts */
    --font-display:   'Plus Jakarta Sans', 'Outfit', sans-serif;
    --font-mono:      'IBM Plex Mono', 'Consolas', monospace;
}

/* -- Root App -- */
.stApp, [data-testid="stAppViewContainer"],
.main .block-container,
[data-testid="stAppViewBlockContainer"] {
    background-color: var(--ob-bg) !important;
    color: var(--ob-on-bg) !important;
}

/* Scan-line texture on main workspace */
.stApp {
    background-image:
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(14, 14, 20, 0.12) 2px,
            rgba(14, 14, 20, 0.12) 4px
        ),
        radial-gradient(ellipse 900px 600px at 8% 8%, rgba(255,70,160,0.03) 0%, transparent 70%),
        radial-gradient(ellipse 600px 400px at 92% 85%, rgba(255,152,0,0.02) 0%, transparent 70%) !important;
    background-attachment: fixed !important;
}

/* -- Header bar -- */
header[data-testid="stHeader"] {
    background: rgba(19,19,25,0.88) !important;
    backdrop-filter: blur(20px) !important;
    border-bottom: none !important;
    box-shadow: var(--ob-glow-ambient) !important;
}
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* -- Sidebar -- */
section[data-testid="stSidebar"] {
    background: var(--ob-surface-lowest) !important;
    border-right: none !important;
    box-shadow: var(--ob-glow-ambient) !important;
    /* Scan-line texture for nav differentiation */
    background-image:
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(27, 27, 34, 0.3) 2px,
            rgba(27, 27, 34, 0.3) 4px
        ) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem !important;
}
section[data-testid="stSidebar"] * {
    color: var(--ob-on-bg) !important;
}

/* Sidebar radio nav -- 0px radius, surface shift on active */
section[data-testid="stSidebar"] .stRadio > div {
    gap: 2px !important;
}
section[data-testid="stSidebar"] .stRadio label {
    padding: 12px 18px !important;
    border-radius: 0px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-family: var(--font-mono) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border: none !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: var(--ob-surface-low) !important;
    border: none !important;
    transform: translateX(3px) !important;
}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] {
    background: var(--ob-surface-container) !important;
    border: none !important;
    border-left: 2px solid var(--ob-primary-container) !important;
    color: #fff !important;
    box-shadow: var(--ob-glow-pink) !important;
}

/* -- Typography -- */
h1, h2, h3, h4 {
    font-family: var(--font-display) !important;
    letter-spacing: -0.02em !important;
    color: var(--ob-on-bg) !important;
}

p, span, div, li, td, th, label {
    font-family: var(--font-mono) !important;
}

/* -- Buttons -- 0px radius, gradient primary */
.stButton > button {
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border-radius: 0px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1px solid var(--ob-ghost-border) !important;
    background: var(--ob-surface-container) !important;
    color: var(--ob-on-bg) !important;
    box-shadow: var(--ob-glow-ambient) !important;
}
.stButton > button:hover {
    background: var(--ob-surface-high) !important;
    border-color: var(--ob-ghost-border) !important;
    box-shadow: var(--ob-glow-pink) !important;
    color: #fff !important;
    /* Scan-line hover animation */
    background-image: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(255, 70, 160, 0.03) 2px,
        rgba(255, 70, 160, 0.03) 4px
    ) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--ob-grad) !important;
    border: none !important;
    color: #fff !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.4) !important;
    box-shadow: 0 0 20px rgba(255,70,160,0.15), var(--ob-glow-ambient) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 0 40px rgba(255,70,160,0.25), var(--ob-glow-pink) !important;
    transform: translateY(-1px) !important;
}

/* -- Inputs -- NO boxes, surface bg with LEFT accent bar */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    font-family: var(--font-mono) !important;
    background: var(--ob-surface-highest) !important;
    border: none !important;
    border-left: 2px solid var(--ob-primary) !important;
    color: var(--ob-on-bg) !important;
    border-radius: 0px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-left: 4px solid var(--ob-primary) !important;
    box-shadow: var(--ob-glow-pink) !important;
    outline: none !important;
}
.stSelectbox > div > div,
div[data-baseweb="select"] > div {
    background: var(--ob-surface-highest) !important;
    border: none !important;
    border-left: 2px solid var(--ob-primary) !important;
    border-radius: 0px !important;
}
.stSelectbox label, .stTextInput label, .stNumberInput label,
.stDateInput label, .stFileUploader label {
    font-family: var(--font-mono) !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--ob-text-dim) !important;
}

/* -- Metrics -- */
div[data-testid="stMetric"] {
    background: var(--ob-surface-container) !important;
    border: none !important;
    border-radius: 0px !important;
    padding: 18px 22px !important;
    box-shadow: var(--ob-glow-ambient) !important;
    transition: all 0.25s ease !important;
}
div[data-testid="stMetric"]:hover {
    background: var(--ob-surface-high) !important;
    box-shadow: var(--ob-glow-pink) !important;
}
div[data-testid="stMetric"] label {
    font-family: var(--font-mono) !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--ob-text-dim) !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-weight: 700 !important;
    color: var(--ob-on-bg) !important;
}

/* -- DataFrames -- 0px radius */
.stDataFrame {
    border-radius: 0px !important;
    overflow: hidden !important;
    border: none !important;
    box-shadow: var(--ob-glow-ambient) !important;
}

/* -- Expanders -- */
.streamlit-expanderHeader {
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    background: var(--ob-surface-container) !important;
    border: none !important;
    border-radius: 0px !important;
    transition: all 0.2s ease !important;
}
.streamlit-expanderHeader:hover {
    background: var(--ob-surface-high) !important;
    box-shadow: var(--ob-glow-pink) !important;
}

/* -- Tabs -- 0px radius, no border line */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px !important;
    border-bottom: none !important;
    background: var(--ob-surface-lowest) !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-mono) !important;
    font-size: 0.76rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 0px !important;
    color: var(--ob-text-dim) !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--ob-primary) !important;
    background: var(--ob-surface-low) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--ob-primary) !important;
    background: var(--ob-surface-container) !important;
    border-bottom: 2px solid var(--ob-primary-container) !important;
}

/* -- File uploader -- 0px radius, ghost border on hover */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--ob-ghost-border) !important;
    border-radius: 0px !important;
    padding: 12px !important;
    transition: all 0.3s ease !important;
    background: var(--ob-surface-container) !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--ob-outline-variant) !important;
    background: var(--ob-surface-high) !important;
    box-shadow: var(--ob-glow-pink) !important;
}

/* -- Spinner -- */
.stSpinner > div {
    border-top-color: var(--ob-primary-container) !important;
}

/* -- Alerts -- 0px radius */
.stAlert {
    border-radius: 0px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.84rem !important;
    box-shadow: var(--ob-glow-ambient) !important;
}

/* -- Code blocks -- */
.stCodeBlock, code, pre {
    font-family: var(--font-mono) !important;
    border-radius: 0px !important;
}

/* ================================================================
   ANIMATIONS
   ================================================================ */

@keyframes scanline {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
}
@keyframes pulse-square {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}
@keyframes fadeSlideUp {
    0% { opacity: 0; transform: translateY(12px); }
    100% { opacity: 1; transform: translateY(0); }
}
@keyframes gradient-rotate {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes scan-hover {
    0% { background-position: 0 0; }
    100% { background-position: 0 4px; }
}

/* ================================================================
   CUSTOM COMPONENTS -- OBSIDIAN PROTOCOL
   ================================================================ */

/* -- Hero Banner -- 0px radius, no border, surface shift + glow */
.ob-hero {
    position: relative;
    background: var(--ob-surface-low);
    padding: 38px 44px 34px;
    margin-bottom: 1.75rem;
    overflow: hidden;
    animation: fadeSlideUp 0.6s ease-out;
    box-shadow: var(--ob-glow-ambient);
}

/* Animated gradient top accent */
.ob-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #ff46a0, #ff9800, #69df54, #ff46a0);
    background-size: 300% 100%;
    animation: gradient-rotate 4s ease infinite;
    box-shadow: 0 0 20px rgba(255,70,160,0.3);
}

/* Side glow accents */
.ob-hero::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 40%; height: 100%;
    background: radial-gradient(ellipse at top right, rgba(255,70,160,0.04) 0%, transparent 60%);
    pointer-events: none;
}
.ob-hero .scanline {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255,70,160,0.06), transparent);
    animation: scanline 8s linear infinite;
    pointer-events: none;
}
.ob-hero-tag {
    font-family: var(--font-mono);
    font-size: 0.62rem;
    color: var(--ob-primary);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}
/* Pulse indicator: 2px x 2px square, blinks every 2s */
.ob-hero-tag .pulse {
    display: inline-block;
    width: 2px; height: 2px;
    background: var(--ob-primary-container);
    animation: pulse-square 2s ease-in-out infinite;
    box-shadow: 0 0 6px var(--ob-primary-container);
}
.ob-hero-title {
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 2.1rem;
    color: var(--ob-on-bg);
    margin: 0;
    letter-spacing: -0.02em;
    line-height: 1.15;
}
.ob-hero-title em {
    font-style: normal;
    background: var(--ob-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.ob-hero-sub {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--ob-text-dim);
    margin-top: 10px;
    letter-spacing: 0.04em;
}

/* -- Stat Cards -- 0px radius, no border, surface shift on hover */
.ob-stat {
    background: var(--ob-surface-container);
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeSlideUp 0.5s ease-out backwards;
    box-shadow: var(--ob-glow-ambient);
}
.ob-stat:hover {
    background: var(--ob-surface-high);
    box-shadow: var(--ob-glow-pink);
}
.ob-stat-label {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--ob-text-faint);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
.ob-stat-value {
    font-family: var(--font-mono);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--ob-on-bg);
    line-height: 1;
}
.ob-stat-value.grad {
    background: var(--ob-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.ob-stat-value.green { color: var(--ob-tertiary); }
.ob-stat-value.error { color: var(--ob-error); }
.ob-stat-value.secondary { color: var(--ob-secondary); }
.ob-stat-value.primary { color: var(--ob-primary); }

/* -- Section Titles -- no border-bottom, uppercase label style */
.ob-section {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--ob-on-bg);
    margin: 1.75rem 0 1rem 0;
    padding-bottom: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: fadeSlideUp 0.4s ease-out;
    letter-spacing: -0.02em;
}
.ob-section .pip {
    width: 2px; height: 2px;
    background: var(--ob-primary-container);
    flex-shrink: 0;
    box-shadow: 0 0 6px var(--ob-primary-container);
    animation: pulse-square 2s ease-in-out infinite;
}

/* -- Format Badges -- 0px radius */
.ob-fmt {
    display: inline-block;
    padding: 2px 10px;
    font-family: var(--font-mono);
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: all 0.2s ease;
}

/* -- Result Card -- 0px radius, no border lines, surface shift hover */
.ob-result {
    background: var(--ob-surface-container);
    border-left: 2px solid var(--ob-tertiary);
    padding: 18px 22px;
    margin-bottom: 1.75rem;
    animation: fadeSlideUp 0.4s ease-out backwards;
    box-shadow: var(--ob-glow-ambient);
    transition: all 0.25s ease;
}
.ob-result:hover {
    background: var(--ob-surface-high);
    box-shadow: var(--ob-glow-pink);
}
.ob-result.has-anomalies {
    border-left-color: var(--ob-error);
}
.ob-result.has-anomalies:hover {
    box-shadow: 0 0 8px rgba(255,180,171,0.15);
}
.ob-result-name {
    font-family: var(--font-mono);
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--ob-on-bg);
}
.ob-result-meta {
    display: flex;
    gap: 28px;
    margin-top: 12px;
    flex-wrap: wrap;
}
.ob-result-meta-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.ob-result-meta-label {
    font-family: var(--font-mono);
    font-size: 0.56rem;
    color: var(--ob-text-faint);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.ob-result-meta-val {
    font-family: var(--font-mono);
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--ob-on-bg);
}

/* -- Sidebar mini stats -- no border lines, surface shift */
.ob-sb-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
}
.ob-sb-stat-label {
    font-family: var(--font-mono);
    font-size: 0.64rem;
    color: var(--ob-text-faint);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.ob-sb-stat-value {
    font-family: var(--font-mono);
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--ob-on-bg);
}

/* -- Status Indicator -- 0px radius, square pulse dot */
.ob-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    font-family: var(--font-mono);
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    transition: all 0.2s ease;
}
.ob-status.online {
    background: rgba(105,223,84,0.06);
    color: var(--ob-tertiary);
}
.ob-status.offline {
    background: rgba(255,180,171,0.06);
    color: var(--ob-error);
}
.ob-status-dot {
    width: 2px; height: 2px;
}
.ob-status.online .ob-status-dot {
    background: var(--ob-tertiary);
    box-shadow: 0 0 6px var(--ob-tertiary);
    animation: pulse-square 2s ease-in-out infinite;
}
.ob-status.offline .ob-status-dot {
    background: var(--ob-error);
}

/* -- Severity Badges -- 0px radius */
.ob-sev {
    display: inline-block;
    padding: 2px 10px;
    font-family: var(--font-mono);
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: all 0.2s ease;
}
.ob-sev.info     { background: rgba(105,223,84,0.08); color: var(--ob-tertiary); }
.ob-sev.warning  { background: rgba(255,191,129,0.10); color: var(--ob-secondary); }
.ob-sev.error    { background: rgba(255,180,171,0.10); color: var(--ob-error); }
.ob-sev.critical { background: rgba(255,70,160,0.10); color: var(--ob-primary-container); }

/* -- Confidence bar -- 0px radius */
.ob-conf-bar {
    display: flex;
    align-items: center;
    gap: 8px;
}
.ob-conf-track {
    flex: 1;
    height: 3px;
    background: var(--ob-surface-highest);
    overflow: hidden;
}
.ob-conf-fill {
    height: 100%;
    transition: width 0.6s ease;
}
.ob-conf-label {
    font-family: var(--font-mono);
    font-size: 0.76rem;
    font-weight: 600;
    min-width: 38px;
    text-align: right;
}

/* -- Anomaly Row -- 0px radius, no border, left accent */
.ob-anomaly-row {
    background: var(--ob-surface-container);
    padding: 12px 16px;
    margin-bottom: 1.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.25s ease;
    box-shadow: var(--ob-glow-ambient);
}
.ob-anomaly-row:hover {
    background: var(--ob-surface-high);
    transform: translateX(3px);
    box-shadow: var(--ob-glow-pink);
}
.ob-anomaly-param {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--ob-on-bg);
}
.ob-anomaly-desc {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--ob-text-dim);
    margin-left: 14px;
}
.ob-anomaly-tag {
    font-family: var(--font-mono);
    font-size: 0.64rem;
    color: var(--ob-text-faint);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* -- Divider -- surface shift instead of line */
.ob-divider {
    height: 1.75rem;
    border: none;
    margin: 0;
}

/* -- Progress Bar Row -- */
.ob-bar-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    animation: fadeSlideUp 0.4s ease-out backwards;
    transition: all 0.2s ease;
}
.ob-bar-row:hover {
    transform: translateX(2px);
}
.ob-bar-label {
    font-family: var(--font-mono);
    font-size: 0.76rem;
    color: var(--ob-text-dim);
    min-width: 90px;
}
.ob-bar-track {
    flex: 1;
    height: 4px;
    background: var(--ob-surface-highest);
    overflow: hidden;
}
.ob-bar-fill {
    height: 100%;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 4px rgba(255,70,160,0.1);
}
.ob-bar-count {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--ob-on-bg);
    min-width: 52px;
    text-align: right;
}

/* -- Markdown overrides -- */
.stMarkdown, .stMarkdown p {
    color: var(--ob-on-bg) !important;
}

/* -- Plotly chart containers -- 0px radius, no border */
.stPlotlyChart {
    border-radius: 0px !important;
    overflow: hidden !important;
    box-shadow: var(--ob-glow-ambient) !important;
    border: none !important;
}

/* -- Glass overlay for floating elements -- */
.ob-glass {
    background: rgba(57, 56, 64, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
}

/* -- KPI hero metric with gradient text -- */
.ob-kpi-hero {
    font-family: var(--font-mono);
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1;
    background: var(--ob-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  API client & constants
# ------------------------------------------------------------------ #
client = APIClient()
SAMPLE_LOGS_DIR = pathlib.Path(__file__).resolve().parent / "sample_logs"

# Plotly layout matching the Obsidian Protocol theme
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(14,14,20,0.6)",
    font=dict(family="IBM Plex Mono, monospace", size=11, color="#8a8694"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.02)", zerolinecolor="rgba(255,255,255,0.03)",
               tickfont=dict(size=10)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.02)", zerolinecolor="rgba(255,255,255,0.03)",
               tickfont=dict(size=10)),
    colorway=["#ff46a0", "#ff9800", "#69df54", "#ffb0cc", "#ffbf81", "#a78bfa", "#f472b6"],
    margin=dict(l=48, r=20, t=44, b=32),
    hoverlabel=dict(bgcolor="#1f1f26", font_size=12, font_family="IBM Plex Mono",
                    bordercolor="#ff46a0"),
)

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def _backend_online() -> bool:
    return client.health_check()


def _api(fn, *a, **kw):
    """Call an API function, returning None on failure."""
    try:
        return fn(*a, **kw)
    except Exception as exc:
        st.error(f"API error: {exc}")
        return None


def _sev_badge(sev: str) -> str:
    s = str(sev).upper() if sev else "UNKNOWN"
    cls = {"INFO": "info", "WARNING": "warning", "ERROR": "error", "CRITICAL": "critical"}.get(s, "")
    return f'<span class="ob-sev {cls}">{s}</span>'


def _fmt_badge(fmt: str) -> str:
    colors = {
        "json": "#a78bfa", "xml": "#69df54", "csv": "#ffbf81",
        "syslog": "#ff9800", "kv": "#ffb0cc", "text": "#60a5fa",
        "binary": "#ffb4ab",
    }
    c = colors.get(str(fmt).lower().split("+")[0], "#8a8694")
    return (
        f'<span class="ob-fmt" style="background:{c}14;color:{c}">{fmt}</span>'
    )


def _conf_bar(val) -> str:
    try:
        v = float(val)
    except (TypeError, ValueError):
        return "---"
    if v >= 0.8:
        c = "var(--ob-tertiary)"
    elif v >= 0.5:
        c = "var(--ob-secondary)"
    else:
        c = "var(--ob-error)"
    w = int(v * 100)
    return (
        f'<div class="ob-conf-bar">'
        f'<div class="ob-conf-track"><div class="ob-conf-fill" style="width:{w}%;background:{c}"></div></div>'
        f'<span class="ob-conf-label" style="color:{c}">{v:.0%}</span>'
        f'</div>'
    )


def _section(title: str):
    st.markdown(f'<div class="ob-section"><span class="pip"></span>{title}</div>', unsafe_allow_html=True)


def _divider():
    st.markdown('<div class="ob-divider"></div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Hero header
# ------------------------------------------------------------------ #
st.markdown("""
<div class="ob-hero">
    <div class="scanline"></div>
    <div class="ob-hero-tag"><span class="pulse"></span> Micron @ AISG National AI Student Challenge</div>
    <h1 class="ob-hero-title">Smart Tool <em>Log Parser</em></h1>
    <p class="ob-hero-sub">AI-powered semiconductor equipment log analysis &middot; Multi-format parsing &middot; Anomaly detection</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  Sidebar
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 18px 0">
        <div style="font-family:var(--font-display);font-weight:800;font-size:1.3rem;color:var(--ob-on-bg);letter-spacing:-0.02em">
            <span style="background:var(--ob-grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">SLP</span>
        </div>
        <div style="font-family:var(--font-mono);font-size:0.58rem;color:var(--ob-text-faint);text-transform:uppercase;letter-spacing:0.1em;margin-top:2px">
            Smart Log Parser v1.0
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Upload & Parse", "Log Explorer", "Analytics", "NL Query", "Summary"],
        label_visibility="collapsed",
    )

    # Surface shift divider instead of 1px line
    st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)

    online = _backend_online()
    if online:
        st.markdown('<div class="ob-status online"><span class="ob-status-dot"></span>Backend Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ob-status offline"><span class="ob-status-dot"></span>Backend Offline</div>', unsafe_allow_html=True)

    if online:
        summary_sb = _api(client.get_summary)
        if summary_sb:
            st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
            for label, key in [("Files", "total_files"), ("Records", "total_records"), ("Anomalies", "total_anomalies")]:
                val = summary_sb.get(key, 0)
                st.markdown(
                    f'<div class="ob-sb-stat">'
                    f'<span class="ob-sb-stat-label">{label}</span>'
                    f'<span class="ob-sb-stat-value">{val:,}</span></div>',
                    unsafe_allow_html=True,
                )
            avg_c = summary_sb.get("avg_confidence", 0)
            c_color = "var(--ob-tertiary)" if avg_c >= 0.8 else "var(--ob-secondary)"
            st.markdown(
                f'<div class="ob-sb-stat">'
                f'<span class="ob-sb-stat-label">Avg Confidence</span>'
                f'<span class="ob-sb-stat-value" style="color:{c_color}">{avg_c:.0%}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:var(--font-mono);font-size:0.52rem;color:var(--ob-text-faint);'
        'text-align:center;padding:8px 0;letter-spacing:0.1em;text-transform:uppercase">Micron @ AISG 2025</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ #
#  Page routing
# ------------------------------------------------------------------ #
if page == "Upload & Parse":
    render_upload(client, SAMPLE_LOGS_DIR, _section, _divider, _fmt_badge, _api)
elif page == "Log Explorer":
    render_explorer(client, _section, _divider, _api)
elif page == "Analytics":
    render_analytics(client, _section, _divider, _api, PLOTLY_LAYOUT)
elif page == "NL Query":
    render_nl_query(client, _section, _divider, _api)
elif page == "Summary":
    render_summary(client, _section, _divider, _api)
