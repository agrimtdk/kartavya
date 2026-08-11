"""
Header UI component for kartavya (Phase 6 with Global Search).
Renders Neo-Brutalist branding, active workspace badge, daily quote, and Global Search modal popover.
"""

import html
from datetime import datetime
import streamlit as st
from src.config import APP_NAME, APP_SUBTITLE, DEFAULT_TAGLINE
from src.data.workspace_store import get_active_workspace, set_active_workspace
from src.services.quote_service import get_daily_quote
from src.services.search_service import global_search


def render_header() -> None:
    """Render the application header with brutalist styling, active workspace badge, daily quote, and search popover."""
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    active_ws = get_active_workspace()
    quote_data = get_daily_quote()

    ws_name = html.escape(str(active_ws.get("name", "Personal"))).replace("\n", " ")
    ws_desc = html.escape(str(active_ws.get("description", ""))).replace("\n", " ")
    q_text = str(quote_data.get("quote", "")).replace("\n", " ").strip()
    q_author = str(quote_data.get("author", "")).replace("\n", " ").strip()

    col_h1, col_h2 = st.columns([4, 1])

    with col_h1:
        desc_html = f"<span style='font-size: 0.85rem; font-weight: 700; color: var(--primary-text) !important; opacity: 0.9; margin-left: 0.5rem;'>{ws_desc}</span>" if ws_desc else ""
        header_html = (
            f'<div class="neo-card-yellow" style="margin-bottom: 0.5rem;">'
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">'
            f'<div>'
            f'<h1 style="font-size: 2.75rem; margin: 0; line-height: 1; text-transform: lowercase; color: var(--primary-text) !important;">{APP_NAME}</h1>'
            f'<p style="font-weight: 700; font-size: 1.1rem; margin: 0.5rem 0 0 0; letter-spacing: 0.02em; color: var(--primary-text) !important;">{DEFAULT_TAGLINE}</p>'
            f'<div style="font-style: italic; font-weight: 600; font-size: 0.95rem; margin-top: 0.35rem; color: var(--primary-text) !important; opacity: 0.95;">“{q_text}” — <strong>{q_author}</strong></div>'
            f'<div style="margin-top: 0.6rem;">'
            f'<span class="neo-badge neo-badge-coral" style="font-size: 0.85rem; padding: 0.3rem 0.65rem;">📌 WORKSPACE: {ws_name.upper()}</span>'
            f'{desc_html}'
            f'</div>'
            f'</div>'
            f'<div style="text-align: right;">'
            f'<span class="neo-badge neo-badge-cyan">{today_str}</span>'
            f'<div style="margin-top: 0.4rem; font-weight: 800; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--primary-text) !important;">{APP_SUBTITLE}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(header_html, unsafe_allow_html=True)

    with col_h2:
        with st.popover("🔍 SEARCH", use_container_width=True):
            st.markdown("#### Instant Global Search")
            q_input = st.text_input("Search Workspaces, Tasks, Reminders, Goals...", key="header_global_search_input")
            if q_input.strip():
                results = global_search(q_input)
                if not results:
                    st.caption("No matching items found.")
                else:
                    st.markdown(f"**Found {len(results)} matches:**")
                    for r in results[:8]:
                        card_html = (
                            f'<div class="neo-card" style="padding: 0.5rem 0.75rem; margin-bottom: 0.4rem;">'
                            f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                            f'<strong style="font-size: 0.9rem;">{html.escape(r["title"])}</strong>'
                            f'<span class="neo-badge {r["badge_class"]}" style="font-size: 0.65rem;">{r["type"]}</span>'
                            f'</div>'
                            f'<div style="font-size: 0.75rem; opacity: 0.85; margin-top: 0.2rem;">'
                            f'📍 <strong>{html.escape(r["workspace_name"])}</strong> • {html.escape(r["context"])}'
                            f'</div>'
                            f'</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                        if r["workspace_id"] != "global" and r["workspace_id"] != active_ws["id"]:
                            if st.button(f"Switch to {r['workspace_name']}", key=f"btn_sw_{r['type']}_{r['title']}_{r['workspace_id']}"):
                                set_active_workspace(r["workspace_id"])
                                st.rerun()
