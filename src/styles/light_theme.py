"""
Neo-Brutalist Light Mode CSS Definitions with Semantic CSS Custom Properties.
Exhaustive Streamlit Widget, Popover, Datepicker, Selectbox, Input, Divider, and Menu Overrides.
"""

LIGHT_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;900&family=Lexend:wght@400;700;900&display=swap');

:root {
    --bg: #FFFDF6;
    --surface: #FFFFFF;
    --surface-alt: #F4F0EA;
    --text: #000000;
    --text-muted: #4A4A4A;
    --border: #000000;
    --shadow: #000000;
    --primary: #FFE600;
    --primary-text: #000000;
    --secondary: #00E5FF;
    --secondary-text: #000000;
    --highlight: #FF5277;
    --highlight-text: #000000;
    --success: #00E676;
    --danger: #FF5277;
    --danger-text: #000000;
    --input-bg: #F4F0EA;
    --input-border: #000000;
    --divider: #000000;
    --badge-outline-bg: #FFFFFF;
    --badge-outline-border: #000000;
    --badge-outline-text: #000000;
}

/* Global Canvas & Typography */
html, body, [class*="css"], .stApp {
    font-family: 'Space Grotesk', 'Lexend', system-ui, -apple-system, sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* High Contrast Red Text Selection */
::selection {
    background-color: #FF5277 !important;
    color: #FFFFFF !important;
}

::-moz-selection {
    background-color: #FF5277 !important;
    color: #FFFFFF !important;
}

header[data-testid="stHeader"] {
    background-color: var(--bg) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--surface-alt) !important;
    border-right: 3px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* Headings & Paragraphs */
h1, h2, h3, h4, h5, h6, .neo-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 900 !important;
    color: var(--text) !important;
    letter-spacing: -0.02em;
}

p, span, label, div[data-testid="stMarkdownContainer"] p {
    color: var(--text);
}

/* Neo-Brutalist Base Cards */
.neo-card {
    background-color: var(--surface);
    border: 3px solid var(--border);
    box-shadow: 5px 5px 0px var(--shadow);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    color: var(--text);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.neo-card:hover {
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0px var(--shadow);
}

/* Neo-Brutalist Accent Cards */
.neo-card-yellow {
    background-color: var(--primary);
    border: 3px solid var(--border);
    box-shadow: 5px 5px 0px var(--shadow);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    color: var(--primary-text) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.neo-card-yellow:hover {
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0px var(--shadow);
}

.neo-card-yellow * {
    color: var(--primary-text) !important;
}

.neo-card-cyan {
    background-color: var(--secondary);
    border: 3px solid var(--border);
    box-shadow: 5px 5px 0px var(--shadow);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    color: var(--secondary-text) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.neo-card-cyan:hover {
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0px var(--shadow);
}

.neo-card-cyan * {
    color: var(--secondary-text) !important;
}

.neo-card-coral {
    background-color: var(--danger);
    border: 3px solid var(--border);
    box-shadow: 5px 5px 0px var(--shadow);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    color: var(--danger-text) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.neo-card-coral:hover {
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0px var(--shadow);
}

.neo-card-coral * {
    color: var(--danger-text) !important;
}

.neo-card-purple {
    background-color: #D8B4FE;
    border: 3px solid var(--border);
    box-shadow: 5px 5px 0px var(--shadow);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    color: var(--text) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.neo-card-purple:hover {
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0px var(--shadow);
}

.neo-card-purple * {
    color: var(--text) !important;
}

.neo-card-muted {
    background-color: var(--surface-alt);
    border: 3px solid var(--border);
    box-shadow: 4px 4px 0px var(--shadow);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    color: var(--text-muted);
}

/* Badges & Tags */
.neo-badge {
    display: inline-block;
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.25rem 0.6rem;
    border: 2px solid var(--border);
    box-shadow: 2px 2px 0px var(--shadow);
    border-radius: 2px;
    margin-right: 0.4rem;
    background-color: var(--primary);
    color: var(--primary-text) !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neo-badge:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px var(--shadow);
}

.neo-badge-cyan {
    background-color: var(--secondary);
    border: 2px solid var(--border);
    color: var(--secondary-text) !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neo-badge-cyan:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px var(--shadow);
}

.neo-badge-coral {
    background-color: var(--danger);
    border: 2px solid var(--border);
    color: var(--danger-text) !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neo-badge-coral:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px var(--shadow);
}

.neo-badge-purple {
    background-color: #C084FC;
    border: 2px solid var(--border);
    color: #000000 !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neo-badge-purple:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px var(--shadow);
}

.neo-badge-outline {
    background-color: var(--badge-outline-bg);
    color: var(--badge-outline-text) !important;
    border: 2px solid var(--badge-outline-border);
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neo-badge-outline:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px var(--shadow);
}

/* Button Elements */
div.stButton > button, 
[data-testid="stPopover"] > button,
[data-testid="stPopover"] button,
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-primary"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    background-color: var(--primary) !important;
    color: #000000 !important;
    border: 3px solid var(--border) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
    border-radius: 2px !important;
    padding: 0.5rem 1rem !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}

/* Children inside buttons */
div.stButton > button *,
[data-testid="stPopover"] button *,
button[data-testid="stBaseButton-secondary"] *,
button[data-testid="stBaseButton-primary"] * {
    color: #000000 !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

div.stButton > button:hover, 
[data-testid="stPopover"] button:hover,
button[data-testid="stBaseButton-secondary"]:hover {
    transform: translate(-2px, -2px) !important;
    box-shadow: 6px 6px 0px var(--shadow) !important;
    background-color: var(--primary) !important;
    color: #000000 !important;
}

div.stButton > button:active, 
[data-testid="stPopover"] button:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
}

/* Destructive Popover Trigger Buttons */
.neo-danger-btn > div.stButton > button,
.neo-danger-btn > [data-testid="stPopover"] > button {
    background-color: var(--danger) !important;
    color: #000000 !important;
    border: 3px solid var(--border) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
}

.neo-danger-btn > div.stButton > button *,
.neo-danger-btn > [data-testid="stPopover"] > button * {
    color: #000000 !important;
    background-color: transparent !important;
}

.neo-danger-btn > div.stButton > button:hover,
.neo-danger-btn > [data-testid="stPopover"] > button:hover {
    transform: translate(-2px, -2px) !important;
    box-shadow: 6px 6px 0px var(--shadow) !important;
    background-color: var(--danger) !important;
    color: #000000 !important;
}

.neo-danger-btn > div.stButton > button:active,
.neo-danger-btn > [data-testid="stPopover"] > button:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
}

/* Popover Content Container - Light Mode */
div[data-testid="stPopoverBody"], 
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[role="dialog"],
div[data-testid="stDialog"] {
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 3px solid var(--border) !important;
    box-shadow: 5px 5px 0px var(--shadow) !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}

div[data-testid="stPopoverBody"] *, 
div[data-baseweb="popover"] *,
div[role="dialog"] *,
div[data-testid="stDialog"] * {
    color: var(--text);
}

div[data-testid="stPopoverBody"] h1,
div[data-testid="stPopoverBody"] h2,
div[data-testid="stPopoverBody"] h3,
div[data-testid="stPopoverBody"] h4,
div[data-testid="stPopoverBody"] h5,
div[data-testid="stPopoverBody"] h6,
div[data-baseweb="popover"] h1,
div[data-baseweb="popover"] h2,
div[data-baseweb="popover"] h3,
div[data-baseweb="popover"] h4,
div[data-baseweb="popover"] h5,
div[data-baseweb="popover"] h6,
div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3,
div[role="dialog"] h4,
div[role="dialog"] h5,
div[role="dialog"] h6 {
    color: var(--text) !important;
}

div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"],
div[data-testid="stPopoverBody"] small,
div[data-baseweb="popover"] [data-testid="stCaptionContainer"],
div[data-baseweb="popover"] small,
div[role="dialog"] [data-testid="stCaptionContainer"],
div[role="dialog"] small {
    color: var(--text-muted) !important;
}

div[data-testid="stPopoverBody"] label,
div[data-testid="stPopoverBody"] label *,
div[data-baseweb="popover"] label,
div[data-baseweb="popover"] label *,
div[role="dialog"] label,
div[role="dialog"] label * {
    color: var(--text) !important;
    font-weight: 700 !important;
}

/* BaseWeb Selectbox Dropdown Menus - Light Mode */
div[data-baseweb="select"] {
    background-color: var(--input-bg) !important;
    border: 2.5px solid var(--border) !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
}

div[data-baseweb="select"] > div {
    background-color: var(--input-bg) !important;
    color: var(--text) !important;
    border: none !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: var(--text) !important;
}

div[data-baseweb="select"] svg {
    fill: var(--text) !important;
    color: var(--text) !important;
}

div[data-baseweb="menu"], 
ul[role="listbox"] {
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 2.5px solid var(--border) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
    border-radius: 2px !important;
}

li[role="option"] {
    background-color: var(--surface) !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.5rem 0.75rem !important;
}

li[role="option"] * {
    color: var(--text) !important;
}

li[role="option"]:hover, 
li[role="option"][aria-selected="true"],
li[role="option"]:focus {
    background-color: #FF5277 !important;
    color: #FFFFFF !important;
}

li[role="option"]:hover *, 
li[role="option"][aria-selected="true"] *,
li[role="option"]:focus * {
    color: #FFFFFF !important;
}

/* BaseWeb Datepicker Calendar Overrides - Light Mode */
div[data-baseweb="calendar"],
div[data-baseweb="calendar"] > div,
div[data-baseweb="datepicker"],
[data-baseweb="calendar"] [role="grid"] {
    background-color: var(--surface) !important;
    color: var(--text) !important;
}

[data-baseweb="calendar"] header,
[data-baseweb="calendar"] header * {
    background-color: var(--surface) !important;
    color: var(--text) !important;
}

[data-baseweb="calendar"] [aria-selected="true"] > div,
[data-baseweb="calendar"] [aria-selected="true"] {
    background-color: var(--highlight) !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
}

/* Buttons inside Popover Bodies & Dialogs */
div[data-testid="stPopoverBody"] div.stButton > button,
div[data-baseweb="popover"] div.stButton > button,
div[role="dialog"] div.stButton > button {
    background-color: var(--primary) !important;
    color: #000000 !important;
    border: 3px solid var(--border) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
    font-weight: 700 !important;
    border-radius: 2px !important;
}

div[data-testid="stPopoverBody"] div.stButton > button *,
div[data-baseweb="popover"] div.stButton > button *,
div[role="dialog"] div.stButton > button * {
    color: #000000 !important;
}

div[data-testid="stPopoverBody"] div.stButton > button:hover,
div[data-baseweb="popover"] div.stButton > button:hover,
div[role="dialog"] div.stButton > button:hover {
    transform: translate(-2px, -2px) !important;
    box-shadow: 6px 6px 0px var(--shadow) !important;
    background-color: var(--primary) !important;
    color: #000000 !important;
}

div[data-testid="stPopoverBody"] div.stButton > button:active,
div[data-baseweb="popover"] div.stButton > button:active,
div[role="dialog"] div.stButton > button:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
}

/* Exhaustive Form Input Overrides - Light Mode */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="textarea"],
div[data-testid="stTextInput"] > div,
div[data-testid="stTextArea"] > div,
div[data-testid="stDateInput"] > div,
div[data-testid="stNumberInput"] > div {
    background-color: var(--input-bg) !important;
    border: 2.5px solid var(--input-border) !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}

div[data-baseweb="input"] *,
div[data-baseweb="base-input"] *,
div[data-baseweb="textarea"] *,
div[data-testid="stTextInput"] *,
div[data-testid="stTextArea"] *,
div[data-testid="stDateInput"] *,
div[data-testid="stNumberInput"] * {
    background-color: transparent !important;
    color: var(--text) !important;
}

input,
textarea,
select,
input[type="text"],
input[type="number"],
input[type="date"] {
    background-color: transparent !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    -webkit-text-fill-color: var(--text) !important;
}

/* Autofill Overrides for WebKit & Blink browsers */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
textarea:-webkit-autofill,
textarea:-webkit-autofill:hover,
textarea:-webkit-autofill:focus,
select:-webkit-autofill,
select:-webkit-autofill:hover,
select:-webkit-autofill:focus {
    -webkit-text-fill-color: var(--text) !important;
    -webkit-box-shadow: 0 0 0px 1000px var(--input-bg) inset !important;
    transition: background-color 5000s ease-in-out 0s !important;
}

input::placeholder,
textarea::placeholder {
    color: var(--text-muted) !important;
    opacity: 0.8 !important;
}

/* Focus States for Inputs */
div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="base-input"]:focus-within {
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
    border-color: var(--border) !important;
}

/* Checkboxes - Light Mode Double Size & Perfect Center Alignment */
[data-testid="stCheckbox"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0.15rem 0 !important;
}

[data-testid="stCheckbox"] label {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 0 auto !important;
    padding: 0 !important;
    width: auto !important;
}

[data-testid="stCheckbox"] label > div,
[data-testid="stCheckbox"] span[data-baseweb="checkbox"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 0 auto !important;
}

[data-testid="stCheckbox"] label span {
    color: var(--text) !important;
    font-weight: 700 !important;
}

[data-testid="stCheckbox"] input[type="checkbox"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 2.25rem !important;
    height: 2.25rem !important;
    min-width: 2.25rem !important;
    min-height: 2.25rem !important;
    background-color: #FFFFFF !important;
    border: 3px solid #000000 !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    margin: 0 auto !important;
    padding: 0 !important;
    outline: none !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
}

[data-testid="stCheckbox"] input[type="checkbox"]:checked {
    background-color: #FF5277 !important;
    border-color: #FF5277 !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E") !important;
    background-size: 85% 85% !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
}

[data-testid="stCheckbox"] div[role="checkbox"],
[data-testid="stCheckbox"] span[data-baseweb="checkbox"] > div {
    width: 2.25rem !important;
    height: 2.25rem !important;
    min-width: 2.25rem !important;
    min-height: 2.25rem !important;
    border: 3px solid #000000 !important;
    border-radius: 5px !important;
    background-color: #FFFFFF !important;
    box-shadow: 2px 2px 0px var(--shadow) !important;
}

[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"],
[data-testid="stCheckbox"] span[data-baseweb="checkbox"][aria-checked="true"] > div {
    background-color: #FF5277 !important;
    border-color: #FF5277 !important;
}

/* Disabled Checkbox Styles (Future Read-Only Dates) */
[data-testid="stCheckbox"] input[type="checkbox"]:disabled,
[data-testid="stCheckbox"] span[data-baseweb="checkbox"][aria-disabled="true"],
[data-testid="stCheckbox"] div[role="checkbox"][aria-disabled="true"] {
    cursor: not-allowed !important;
    opacity: 0.55 !important;
    background-color: var(--surface-alt) !important;
}

[data-testid="stCheckbox"] div[role="checkbox"] svg,
[data-testid="stCheckbox"] span[data-baseweb="checkbox"] svg {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
    color: #FFFFFF !important;
}

/* Radio Buttons */
div[data-testid="stRadio"] label, 
div[data-testid="stRadio"] p,
div[data-testid="stRadio"] span {
    color: var(--text) !important;
    font-weight: 700 !important;
}

/* Expanders */
[data-testid="stExpander"], details {
    background-color: var(--surface) !important;
    border: 3px solid var(--border) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}

[data-testid="stExpander"]:hover, details:hover {
    transform: translate(-1px, -1px) !important;
    box-shadow: 6px 6px 0px var(--shadow) !important;
}

summary {
    color: var(--text) !important;
    font-weight: 700 !important;
}

/* Dividers */
hr {
    border: none !important;
    border-top: 3px solid var(--divider) !important;
    margin: 1.5rem 0 !important;
    opacity: 1 !important;
}

/* Progress bar container */
.stProgress > div > div > div > div {
    background-color: var(--success) !important;
    border-radius: 0px !important;
}

.stProgress > div > div {
    background-color: var(--surface-alt) !important;
    border: 3px solid var(--border) !important;
    box-shadow: 3px 3px 0px var(--shadow) !important;
    border-radius: 2px !important;
}

/* Navigation items */
.neo-nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    font-weight: 700;
    font-size: 1rem;
    color: var(--text);
    background-color: var(--surface);
    border: 3px solid var(--border);
    box-shadow: 3px 3px 0px var(--shadow);
    border-radius: 2px;
    margin-bottom: 0.75rem;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neo-nav-item:hover {
    transform: translate(-2px, -2px);
    box-shadow: 5px 5px 0px var(--shadow);
}

.neo-nav-item.active {
    background-color: var(--primary);
    color: var(--primary-text) !important;
    border: 3px solid var(--border);
    box-shadow: 4px 4px 0px var(--shadow);
}

.neo-nav-item.active:hover {
    transform: translate(-2px, -2px);
    box-shadow: 6px 6px 0px var(--shadow);
}

.neo-nav-item.disabled {
    background-color: var(--surface-alt);
    color: var(--text-muted);
    border: 2px solid var(--border);
    box-shadow: 2px 2px 0px var(--shadow);
    opacity: 0.75;
}

.neo-footer {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-muted);
    border-top: 3px solid var(--divider);
    padding-top: 1rem;
    margin-top: 2rem;
}

/* Responsive Timeline Table Container (Phase 7) */
.neo-timeline-wrapper {
    overflow-x: auto !important;
    width: 100% !important;
    margin-bottom: 1.5rem !important;
    -webkit-overflow-scrolling: touch;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border: 3px solid var(--border) !important;
    box-shadow: 4px 4px 0px var(--shadow) !important;
    border-radius: 2px !important;
    background-color: var(--surface) !important;
}

/* Custom Clear Neo-Brutalist Scrollbars */
[data-testid="stVerticalBlockBorderWrapper"],
.neo-timeline-wrapper {
    scrollbar-width: thin !important;
    scrollbar-color: #000000 #F4F0EA !important;
}

[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar,
.neo-timeline-wrapper ::-webkit-scrollbar {
    width: 9px !important;
    height: 9px !important;
}

[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-track,
.neo-timeline-wrapper ::-webkit-scrollbar-track {
    background: #F4F0EA !important;
    border-left: 2px solid #000000 !important;
}

[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb,
.neo-timeline-wrapper ::-webkit-scrollbar-thumb {
    background: #000000 !important;
    border-radius: 2px !important;
}

[data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb:hover,
.neo-timeline-wrapper ::-webkit-scrollbar-thumb:hover {
    background: #FF5277 !important;
}

/* Responsive Mobile & Tablet Scaling (Phase 8) */
@media (max-width: 768px) {
    .neo-card, .neo-card-yellow, .neo-card-cyan, .neo-card-coral, .neo-card-muted {
        padding: 0.85rem 1rem !important;
        box-shadow: 3px 3px 0px var(--shadow) !important;
    }

    div.stButton > button, [data-testid="stPopover"] > button {
        font-size: 0.85rem !important;
        padding: 0.4rem 0.75rem !important;
        box-shadow: 3px 3px 0px var(--shadow) !important;
    }

    h1 {
        font-size: 2rem !important;
    }
}
}
</style>
"""
