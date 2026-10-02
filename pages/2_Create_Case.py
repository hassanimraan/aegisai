import streamlit as st

from database.supabase_client import get_supabase


st.set_page_config(
    page_title="Create Case - AegisAI",
    page_icon="📝",
    layout="wide"
)


# ==========================================
# AUTH CHECK
# ==========================================

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()


user = st.session_state["user"]


# ==========================================
# PAGE HEADER
# ==========================================

st.title("📝 Create Approval Case")

st.write(
    "Create a procurement or capital expenditure approval "
    "case for AI-powered compliance review."
)

st.divider()


# ==========================================
# CASE FORM
# ==========================================

with st.form("create_case_form"):

    st.subheader("Request Information")

    title = st.text_input(
        "Request Title",
        placeholder="e.g. Industrial Testing Equipment Procurement"
    )

    department = st.selectbox(
        "Department",
        [
            "Engineering",
            "Procurement",
            "Finance",
            "Projects",
            "Administration",
            "HR"
        ]
    )

    requester = st.text_input(
        "Requester",
        placeholder="e.g. Engr. Ahmed Raza, Manager Engineering"
    )

    amount = st.number_input(
        "Amount (PKR)",
        min_value=0.0,
        step=1000.0,
        format="%.2f"
    )

    request_type = st.selectbox(
        "Request Type",
        [
            "Capital Expenditure",
            "Procurement",
            "Other"
        ]
    )

    description = st.text_area(
        "Request Description",
        placeholder="Describe what is being requested."
    )

    business_justification = st.text_area(
        "Business Justification",
        placeholder="Explain why this request is required."
    )

    st.divider()

    submitted = st.form_submit_button(
        "Create Approval Case",
        type="primary",
        use_container_width=True
    )


# ==========================================
# SAVE CASE
# ==========================================

if submitted:

    if not title.strip():
        st.error("Please enter the request title.")
        st.stop()

    if not requester.strip():
        st.error("Please enter the requester.")
        st.stop()

    if amount <= 0:
        st.error("Amount must be greater than zero.")
        st.stop()

    if not description.strip():
        st.error("Please enter the request description.")
        st.stop()

    if not business_justification.strip():
        st.error("Please enter the business justification.")
        st.stop()

    try:

        supabase = get_supabase()

        response = supabase.table("cases").insert({
            "user_id": user.id,
            "title": title.strip(),
            "department": department,
            "amount": amount,
            "description": (
                f"Request Type: {request_type}\n\n"
                f"Requester: {requester.strip()}\n\n"
                f"{description.strip()}\n\n"
                f"Business Justification:\n"
                f"{business_justification.strip()}"
            ),
            "status": "DRAFT"
        }).execute()

        if response.data:

            case_id = response.data[0]["id"]

            st.success(
                f"Approval case created successfully. "
                f"Case ID: {case_id}"
            )

            st.info(
                "Next step: upload the supporting documents "
                "for this case."
            )

        else:

            st.error("Case could not be created.")

    except Exception as e:

        st.error(
            f"Error creating case: {str(e)}"
        )
