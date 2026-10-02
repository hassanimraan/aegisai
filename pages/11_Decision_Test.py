import streamlit as st

from database.supabase_client import get_supabase
from rag.retriever import search_policies
from agents.compliance_agent import run_compliance_agent
from agents.financial_agent import run_financial_agent
from agents.risk_agent import run_risk_agent
from agents.decision_synthesizer import run_decision_synthesizer


st.set_page_config(
    page_title="Decision Synthesizer - AegisAI",
    page_icon="🧠",
    layout="wide"
)


if "user" not in st.session_state:
    st.warning("Please log in from the main AegisAI page.")
    st.stop()


st.title("🧠 Decision Synthesizer Test")
st.write(
    "Combines Compliance, Financial, and Risk Agent findings "
    "into a consolidated AI recommendation."
)

st.divider()


# ---------------------------------------------------------
# Load Cases
# ---------------------------------------------------------

try:
    supabase = get_supabase()

    response = (
        supabase
        .table("cases")
        .select("*")
        .eq("user_id", st.session_state["user"].id)
        .order("created_at", desc=True)
        .execute()
    )

    cases = response.data or []

except Exception as e:
    st.error(f"Unable to load cases: {e}")
    st.stop()


if not cases:
    st.info("No cases found. Create an approval case first.")
    st.stop()


case_options = {
    f"{case['title']} — PKR {case['amount']}": case
    for case in cases
}


selected_label = st.selectbox(
    "Select Approval Case",
    list(case_options.keys())
)

case = case_options[selected_label]


st.subheader("Selected Case")

col1, col2, col3 = st.columns(3)

with col1:
    st.write(f"**Title:** {case['title']}")

with col2:
    st.write(f"**Department:** {case['department']}")

with col3:
    st.write(f"**Amount:** PKR {case['amount']}")


# ---------------------------------------------------------
# Load Documents
# ---------------------------------------------------------

try:

    documents_response = (
        supabase
        .table("documents")
        .select("*")
        .eq("case_id", case["id"])
        .execute()
    )

    documents = documents_response.data or []

except Exception as e:
    st.error(f"Unable to load documents: {e}")
    st.stop()


st.write(f"**Documents available:** {len(documents)}")

if documents:

    for doc in documents:
        st.write(
            f"📄 {doc['document_name']} "
            f"— {doc['document_type']}"
        )

else:
    st.warning("No documents found for this case.")


st.divider()


# ---------------------------------------------------------
# Run Decision Synthesizer
# ---------------------------------------------------------

if st.button(
    "🧠 Run Decision Synthesizer",
    type="primary",
    use_container_width=True
):

    if not documents:
        st.error(
            "At least one document is required before running "
            "the Decision Synthesizer."
        )
        st.stop()

    try:

        # -------------------------------------------------
        # Compliance
        # -------------------------------------------------

        with st.spinner(
            "Running Compliance Agent..."
        ):

            compliance_query = f"""
Review procurement compliance for this case.

Title: {case['title']}
Amount: PKR {case['amount']}

Focus on:
- procurement requirements
- mandatory documentation
- vendor quotations
- technical evaluation
- comparative statement
- approval controls
- conflict-of-interest requirements
"""

            compliance_policies = search_policies(
                compliance_query,
                top_k=10
            )

            compliance_result = run_compliance_agent(
                case,
                documents,
                compliance_policies
            )


        # -------------------------------------------------
        # Financial
        # -------------------------------------------------

        with st.spinner(
            "Running Financial Agent..."
        ):

            financial_query = f"""
Review financial requirements for this case.

Title: {case['title']}
Amount: PKR {case['amount']}

Focus on:
- financial approval requirements
- delegated approval authority
- financial review
- amount consistency
- applicable approval threshold
"""

            financial_policies = search_policies(
                financial_query,
                top_k=10
            )

            financial_result = run_financial_agent(
                case,
                documents,
                financial_policies
            )


        # -------------------------------------------------
        # Risk
        # -------------------------------------------------

        with st.spinner(
            "Running Risk Agent..."
        ):

            risk_query = f"""
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

Retrieve and use relevant evidence from:

- Procurement Policy (POL-001)
- Financial Approval Policy (POL-002)
- Delegation of Authority Matrix (POL-003)
- Procurement SOP (POL-004)
- Vendor Evaluation Policy (POL-005)
- Conflict of Interest Policy (POL-006)

Do not assume that a risk exists merely because information
is missing. Distinguish confirmed risks from potential risks
and missing information.
"""

            risk_policies = search_policies(
                risk_query,
                top_k=10
            )

            risk_result = run_risk_agent(
                case,
                documents,
                risk_policies
            )


        # -------------------------------------------------
        # Decision Synthesizer
        # -------------------------------------------------

        with st.spinner(
            "Consolidating AI assessment..."
        ):

            decision_result = run_decision_synthesizer(
                case,
                compliance_result,
                financial_result,
                risk_result
            )


        # -------------------------------------------------
        # Display Results
        # -------------------------------------------------

        st.success(
            "Decision Synthesizer completed successfully."
        )

        st.divider()

        st.subheader("🧠 Consolidated AI Assessment")

        st.write(decision_result)

        st.divider()

        with st.expander(
            "Compliance Agent Result"
        ):
            st.write(compliance_result)

        with st.expander(
            "Financial Agent Result"
        ):
            st.write(financial_result)

        with st.expander(
            "Risk Agent Result"
        ):
            st.write(risk_result)


    except Exception as e:

        st.error(
            f"Decision Synthesizer failed: {e}"
        )
