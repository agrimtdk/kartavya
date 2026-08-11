"""
Theme Management & CSS Injector for kartavya.
Injects Neo-Brutalist Light Mode styling.
"""

import streamlit as st
from src.styles.light_theme import LIGHT_THEME_CSS

THEME_LIGHT = "light"
SESSION_KEY_THEME = "kartavya_theme"


def init_theme() -> str:
    """Ensure theme is initialized to light mode in st.session_state."""
    st.session_state[SESSION_KEY_THEME] = THEME_LIGHT
    return THEME_LIGHT


def get_current_theme() -> str:
    """Get the currently active theme string ('light')."""
    return THEME_LIGHT


def set_theme(theme_name: str = THEME_LIGHT) -> None:
    """Set theme in st.session_state."""
    st.session_state[SESSION_KEY_THEME] = THEME_LIGHT


def apply_theme() -> None:
    """Inject the Neo-Brutalist Light Theme CSS into Streamlit page."""
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)
