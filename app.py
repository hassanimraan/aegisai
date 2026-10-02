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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.page_link(
            "pages/1_Dashboard.py",
            label="📊 Dashboard",
            icon="📊"
        )

    with col2:
        st.page_link(
            "pages/2_Create_Case.py",
            label="📝 Create Approval Case",
            icon="📝"
        )

    with col3:
        st.page_link(
            "pages/5_Case_History.py",
            label="📁 Case History",
            icon="📁"
        )

    st.divider()

    st.subheader("AI Review")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.page_link(
            "pages/3_Case_Review.py",
            label="🤖 AI Case Review",
            icon="🤖"
        )

    with col2:
        st.page_link(
            "pages/4_Decision.py",
            label="✅ Human Decision",
            icon="✅"
        )

    with col3:
        st.page_link(
            "pages/6_Report.py",
            label="📄 Reports",
            icon="📄"
        )

    st.divider()

    if st.button(
        "Logout",
        type="secondary"
    ):

        logout_user()
        st.rerun()
