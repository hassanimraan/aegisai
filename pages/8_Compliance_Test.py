import streamlit as st

from agents.compliance_agent import run_compliance_agent
from rag.retriever import search_policies
from database.supabase_client import get_supabase


st.set_page_config(
    page_title="Compliance Test - AegisAI",
    page_icon="✅",
    layout="wide"
)

st.title("✅ AegisAI Compliance Agent Test")

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

supabase = get_supabase()
user_id = st.session_state["user"].id

# -----------------------------
# Load Cases
# -----------------------------

cases_response = (
    supabase
    .table("cases")
    .select("*")
    .eq("user_id", user_id)
    .order("created_at", desc=True)
    .execute()
)

cases = cases_response.data or []

if not cases:
    st.info("No approval cases found.")
    st.stop()

case_options = {}

for case in cases:
    label = (
        f"{case['title']} — "
        f"PKR {float(case['amount']):,.0f}"
    )
    case_options[label] = case

selected_label = st.selectbox(
    "Select approval case",
    list(case_options.keys())
)

case = case_options[selected_label]

st.subheader("Case Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.write(f"**Title:** {case['title']}")

with col2:
    st.write(f"**Department:** {case['department']}")

with col3:
    st.write(
        f"**Amount:** PKR {float(case['amount']):,.0f}"
    )

st.divider()

# -----------------------------
# Load Documents
# -----------------------------

st.subheader("Uploaded Documents")

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

if not documents:
    st.warning(
        "No documents were found for this case in the database."
    )

    st.write("**Debug information:**")
    st.code(
        f"User ID: {user_id}\n"
        f"Case ID: {case['id']}\n"
        f"Documents returned: {len(documents)}"
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

# -----------------------------
# Run Compliance Agent
# -----------------------------

if st.button(
    "🤖 Run Compliance Agent",
    type="primary",
    use_container_width=True
):

    try:

        with st.spinner(
            "Retrieving policies and running Compliance Agent..."
        ):

            query = f"""
            Review procurement compliance for a PKR
            {case['amount']} approval request in the
            {case['department']} department.

            Check required procurement documents,
            vendor quotations, technical evaluation,
            comparative statement, approval requirements,
            and relevant compliance rules.
            """

            policy_evidence = search_policies(
                query,
                top_k=8
            )

            result = run_compliance_agent(
                case_data=case,
                documents=documents,
                policy_evidence=policy_evidence
            )

        st.success(
            "Compliance Agent completed successfully."
        )

        st.subheader("Compliance Assessment")

        st.markdown(result)

        st.divider()

        st.subheader("Retrieved Policy Evidence")

        for index, item in enumerate(
            policy_evidence,
            start=1
        ):

            st.markdown(
                f"**{index}. {item['policy_id']} — "
                f"{item['section_id']} — "
                f"{item['section_title']}**"
            )

            st.write(
                f"Similarity: {item['similarity']:.4f}"
            )

            st.info(item["content"])

    except Exception as e:

        st.error(
            f"Compliance Agent test failed: {str(e)}"
        )
