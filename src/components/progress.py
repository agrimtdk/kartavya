"""
Progress Visualization UI Component for kartavya.
Renders real-time overall timeline progress metrics and gauges using semantic CSS custom variables.
"""

import streamlit as st
from src.data.task_store import get_overall_completion


def render_overall_progress() -> None:
    """Render overall timeline progress metrics card and gauge."""
    metrics = get_overall_completion()
    pct = metrics["percentage"]
    completed = metrics["completed"]
    total = metrics["total"]

    st.markdown(
        f"""
        <div class="neo-card-cyan">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
                <div>
                    <span class="neo-badge neo-badge-coral">LIVE METRICS</span>
                    <h2 style="margin: 0.3rem 0 0 0; font-size: 1.6rem; display: inline-block; vertical-align: middle; color: var(--primary-text) !important;">
                        TIMELINE PROGRESS
                    </h2>
                </div>
                <div style="text-align: right; color: var(--primary-text) !important;">
                    <span style="font-size: 2.25rem; font-weight: 900; line-height: 1; letter-spacing: -0.03em; color: var(--primary-text) !important;">
                        {pct}%
                    </span>
                    <div style="font-weight: 800; font-size: 0.85rem; text-transform: uppercase; margin-top: 0.2rem; color: var(--primary-text) !important;">
                        {completed} / {total} COMPLETED
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Progress bar
    norm_pct = min(max(pct / 100.0, 0.0), 1.0)
    st.progress(norm_pct)
