import streamlit as st

from agents.risk_agent import run_risk_agent
from rag.retriever import search_policies
from database.supabase_client import get_supabase


st.set_page_config(
    page_title="Risk Test - AegisAI",
    page_icon="⚠️",
    layout="wide"
)

st.title("⚠️ AegisAI Risk Agent Test")


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()


# ---------------------------------------------------------
# Supabase
# ---------------------------------------------------------

try:
    supabase = get_supabase()
    user_id = st.session_state["user"].id

except Exception as e:
    st.error(f"Supabase connection failed: {e}")
    st.stop()


# ---------------------------------------------------------
# Load Cases
# ---------------------------------------------------------

try:

    cases_response = (
        supabase
        .table("cases")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    cases = cases_response.data or []

except Exception as e:

    st.error(f"Could not load cases: {e}")
    st.stop()


if not cases:
    st.info("No approval cases found.")
    st.stop()


# ---------------------------------------------------------
# Case Selection
# ---------------------------------------------------------

case_options = {}

for case in cases:

    try:
        amount_display = (
            f"PKR {float(case['amount']):,.0f}"
        )
    except Exception:
        amount_display = str(case.get("amount", ""))

    label = (
        f"{case['title']} — "
        f"{amount_display}"
    )

    case_options[label] = case


selected_label = st.selectbox(
    "Select approval case",
    list(case_options.keys())
)

case = case_options[selected_label]


# ---------------------------------------------------------
# Case Information
# ---------------------------------------------------------

st.subheader("Case Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.write(
        f"**Title:** {case.get('title', '')}"
    )

with col2:
    st.write(
        f"**Department:** {case.get('department', '')}"
    )

with col3:

    try:
        amount_display = (
            f"PKR {float(case['amount']):,.0f}"
        )
    except Exception:
        amount_display = str(case.get("amount", ""))

    st.write(
        f"**Amount:** {amount_display}"
    )


st.divider()


# ---------------------------------------------------------
# Load Documents
# ---------------------------------------------------------

st.subheader("Uploaded Documents")

try:

    documents_response = (
        supabase
        .table("documents")
        .select(
            "id, case_id, document_name, "
            "document_type, extracted_text, created_at"
        )
        .eq("case_id", case["id"])
        .execute()
    )

    documents = documents_response.data or []

except Exception as e:

    st.error(
        f"Could not load documents: {e}"
    )

    st.stop()


if not documents:

    st.warning(
        "No documents were found for this case."
    )

    st.stop()


for index, document in enumerate(
    documents,
    start=1
):

    st.write(
        f"**{index}. {document['document_name']}** "
        f"— {document['document_type']}"
    )


st.success(
    f"{len(documents)} document(s) found."
)


st.divider()


# ---------------------------------------------------------
# Run Risk Agent
# ---------------------------------------------------------

if st.button(
    "⚠️ Run Risk Agent",
    type="primary",
    use_container_width=True
):

    # -----------------------------------------------------
    # Retrieve Policies
    # -----------------------------------------------------

    try:

        with st.spinner(
            "Retrieving risk-related policies..."
        ):

            query = f"""
Analyze procurement risks for this approval request.

Requested amount: PKR {case['amount']}

Identify risks related to:

- procurement process
- documentation
- vendor evaluation
- technical and commercial evaluation
- financial process
- conflict of interest
- approval and governance

Focus especially on:

Vendor Evaluation Policy,
Conflict of Interest Policy,
Procurement Policy,
Procurement SOP,
and relevant Financial Approval requirements.
"""

            policy_evidence = search_policies(
                query,
                top_k=10
            )

        st.success(
            "Risk policy retrieval completed."
        )

    except Exception as e:

        st.error(
            f"Policy retrieval failed: {e}"
        )

        st.stop()


    # -----------------------------------------------------
    # Run Risk Agent
    # -----------------------------------------------------

    try:

        with st.spinner(
            "Running Risk Agent..."
        ):

            result = run_risk_agent(
                case_data=case,
                documents=documents,
                policy_evidence=policy_evidence
            )

        st.success(
            "Risk Agent completed successfully."
        )

    except Exception as e:

        st.error(
            f"Risk Agent failed: {e}"
        )

        st.stop()


    # -----------------------------------------------------
    # Display Result
    # -----------------------------------------------------

    st.subheader("Risk Assessment")

    st.markdown(result)


    # -----------------------------------------------------
    # Display Retrieved Evidence
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "Retrieved Risk Policy Evidence"
    )

    for index, item in enumerate(
        policy_evidence,
        start=1
    ):

        st.markdown(
            f"**{index}. "
            f"{item['policy_id']} — "
            f"{item['section_id']} — "
            f"{item['section_title']}**"
        )

        st.write(
            f"Similarity: "
            f"{item['similarity']:.4f}"
        )

        st.info(
            item["content"]
        )
