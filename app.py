def show_application():

    user = st.session_state["user"]

    st.title("🛡️ AegisAI")
    st.subheader("Intelligent Approval & Compliance System")

    st.write(
        "AI-powered policy intelligence, multi-agent review, "
        "and human-controlled approvals."
    )

    st.divider()

    st.success(
        f"Welcome, {user.email}"
    )

    st.subheader("Approval Management")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 📊 Dashboard")

        st.write(
            "View approval cases, statuses, and recent activity."
        )

        if st.button(
            "Open Dashboard",
            use_container_width=True
        ):
            st.switch_page("pages/1_Dashboard.py")

    with col2:

        st.markdown("### 📝 Create Approval Case")

        st.write(
            "Create a new procurement or capital expenditure case."
        )

        if st.button(
            "Create New Case",
            type="primary",
            use_container_width=True
        ):
            st.switch_page("pages/2_Create_Case.py")

    st.divider()

    st.subheader("System Status")

    st.success("🔐 Authentication: Connected")
    st.success("🗄️ Supabase Database: Connected")
    st.info("🤖 AI Review: Ready")
    st.info("📚 Policy RAG: Ready")

    st.divider()

    if st.button(
        "Logout",
        type="secondary"
    ):

        logout_user()
        st.rerun()
