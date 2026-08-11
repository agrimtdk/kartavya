"""
Workspace UI Component for kartavya (Phase 3 Dynamic Workspaces).

Renders sidebar workspace switcher with Neo-Brutalist active styling (.neo-nav-item.active),
popover modals for workspace creation (enforcing 10 max limit),
and active workspace settings (renaming, editing description, and deletion with confirmation).
"""

import html
import streamlit as st
from src.data.workspace_store import (
    get_workspaces,
    get_active_workspace_id,
    get_active_workspace,
    set_active_workspace,
    create_workspace,
    rename_workspace,
    delete_workspace,
    MAX_WORKSPACES,
    MIN_WORKSPACES,
)


from src.config import MAX_WORKSPACE_NAME_LEN


def render_workspace_navigator() -> None:
    """Render workspace list, active workspace indicator, creation, and settings in sidebar."""
    workspaces = get_workspaces()
    active_ws_id = get_active_workspace_id()
    active_ws = get_active_workspace()
    ws_count = len(workspaces)

    st.markdown("### 🗂️ Workspaces")

    # Render Workspace Selector Buttons
    for ws in workspaces:
        is_active = ws["id"] == active_ws_id
        btn_label = f"📌 {ws['name']}" if is_active else f"📄 {ws['name']}"
        btn_type = "primary" if is_active else "secondary"

        if st.button(
            btn_label,
            key=f"ws_select_{ws['id']}",
            use_container_width=True,
            type=btn_type,
        ):
            if not is_active:
                set_active_workspace(ws["id"])
                st.rerun()

    col1, col2 = st.columns([1, 1], gap="small")

    # Create Workspace Button & Popover
    with col1:
        with st.popover("➕ NEW", use_container_width=True):
            st.markdown("#### Create Workspace")
            st.caption(f"Workspaces: {ws_count} / {MAX_WORKSPACES}")

            if ws_count >= MAX_WORKSPACES:
                st.warning(f"⚠️ Maximum limit of {MAX_WORKSPACES} workspaces reached.")
            else:
                new_ws_name = st.text_input(
                    "Workspace Name",
                    placeholder="e.g. Coding, Hobbies, College",
                    max_chars=MAX_WORKSPACE_NAME_LEN,
                    key="input_new_ws_name",
                )
                new_ws_desc = st.text_area(
                    "Description (Optional)",
                    placeholder="Brief workspace goal...",
                    key="input_new_ws_desc",
                    height=80,
                )

                if st.button("Confirm Create", use_container_width=True, key="btn_confirm_create_ws"):
                    success, msg, new_id = create_workspace(new_ws_name, new_ws_desc)
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)

    # Active Workspace Settings Popover
    with col2:
        with st.popover("⚙️ EDIT", use_container_width=True):
            st.markdown(f"#### Edit '{active_ws['name']}'")

            edit_name = st.text_input(
                "Rename Workspace",
                value=active_ws["name"],
                max_chars=MAX_WORKSPACE_NAME_LEN,
                key="input_edit_ws_name",
            )

            edit_desc = st.text_area(
                "Update Description",
                value=active_ws.get("description", ""),
                key="input_edit_ws_desc",
                height=80,
            )

            if st.button("Save Changes", use_container_width=True, key="btn_confirm_edit_ws"):
                success, msg = rename_workspace(active_ws_id, edit_name, edit_desc)
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("<hr>", unsafe_allow_html=True)

            # Delete Workspace Section
            st.markdown('<div class="neo-danger-btn">', unsafe_allow_html=True)
            if ws_count <= MIN_WORKSPACES:
                st.caption("⚠️ Cannot delete the final remaining workspace.")
            else:
                st.markdown("##### 🗑️ Delete Active Workspace")
                st.caption("Deleting this workspace will remove all tasks and dates inside it.")
                confirm_check = st.checkbox(
                    "I confirm I want to delete this workspace",
                    key="check_confirm_delete_ws",
                )

                if st.button("⚠️ Confirm Delete Workspace", use_container_width=True, key="btn_confirm_delete_ws"):
                    if confirm_check:
                        success, msg = delete_workspace(active_ws_id)
                        if success:
                            st.toast(msg, icon="🗑️")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Please check the confirmation box first.")
            st.markdown('</div>', unsafe_allow_html=True)
