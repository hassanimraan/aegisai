import streamlit as st

from services.authentication import (
    login_user,
    signup_user,
    logout_user
)


st.set_page_config(
    page_title="AegisAI",
    page_icon="🛡️",
    layout="wide"
)


def show_login():
    st.title("🛡️ AegisAI")
    st.subheader("Intelligent Approval & Compliance System")

    st.write(
        "AI-powered policy intelligence, multi-agent review, "
        "and human-controlled approvals."
    )

    st.divider()

    tab_login, tab_signup = st.tabs([
        "Login",
        "Create Account"
    ])

    # =========================
    # LOGIN
    # =========================

    with tab_login:

        st.subheader("Sign In")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
            key="login_button"
        ):

            email = email.strip()

            if email == "" or password == "":
                st.warning(
                    "Please enter your email and password."
                )
            else:

                success, message = login_user(
                    email,
                    password
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    # =========================
    # SIGNUP
    # =========================

    with tab_signup:

        st.subheader("Create Account")

        name = st.text_input(
            "Full Name",
            key="signup_name"
        )

        email = st.text_input(
            "Email",
            key="signup_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm_password"
        )

        if st.button(
            "Create Account",
            type="primary",
            use_container_width=True,
            key="signup_button"
        ):

            name = name.strip()
            email = email.strip()

            if not name:
                st.error("Please enter your full name.")

            elif not email:
                st.error("Please enter your email.")

            elif not password:
                st.error("Please enter a password.")

            elif not confirm_password:
                st.error("Please confirm your password.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            elif len(password) < 6:
                st.error(
                    "Password must contain at least 6 characters."
                )

            else:

                success, message = signup_user(
                    name,
                    email,
                    password
                )

                if success:
                    st.success(
                        "Account created successfully."
                    )
                    st.rerun()

                else:
                    st.error(message)


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

    if st.button("Logout"):

        logout_user()

        st.rerun()


# =========================
# APPLICATION ENTRY POINT
# =========================

if "user" not in st.session_state:

    show_login()

else:

    show_application()
