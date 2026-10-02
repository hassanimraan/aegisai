import streamlit as st

from database.supabase_client import get_supabase
from rag.retriever import search_policies
from config.settings import get_gemini_api_key

from google import genai


MODEL = "gemini-3.6-flash"


st.set_page_config(
    page_title="Human Decision - AegisAI",
    page_icon="⚖️",
    layout="wide"
)


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

if "user" not in st.session_state:
    st.warning("Please log in from the main AegisAI page.")
    st.stop()


st.title("⚖️ Human Review & Decision")

st.write(
    "Review the AI assessment, ask grounded questions using the "
    "AegisAI assistant, and make the final human decision."
)

st.divider()


# ---------------------------------------------------------
# Supabase
# ---------------------------------------------------------

try:
    supabase = get_supabase()

except Exception as e:
    st.error(f"Unable to connect to Supabase: {e}")
    st.stop()


# ---------------------------------------------------------
# Load Cases
# ---------------------------------------------------------

try:

    response = (
        supabase
        .table("cases")
        .select("*")
        .eq(
            "user_id",
            st.session_state["user"].id
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    cases = response.data or []

except Exception as e:
    st.error(f"Unable to load cases: {e}")
    st.stop()


if not cases:
    st.info(
        "No approval cases are available for human review."
    )
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


# ---------------------------------------------------------
# Case Information
# ---------------------------------------------------------

st.subheader("📋 Case Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.write(f"**Title:** {case['title']}")

with col2:
    st.write(f"**Department:** {case['department']}")

with col3:
    st.write(f"**Amount:** PKR {case['amount']}")


st.write(
    f"**Status:** {case.get('status', 'UNKNOWN')}"
)

st.divider()


# ---------------------------------------------------------
# Latest AI Review
# ---------------------------------------------------------

try:

    review_response = (
        supabase
        .table("ai_reviews")
        .select("*")
        .eq(
            "case_id",
            case["id"]
        )
        .order(
            "created_at",
            desc=True
        )
        .limit(1)
        .execute()
    )

    reviews = review_response.data or []

except Exception as e:
    st.error(
        f"Unable to load AI review: {e}"
    )
    st.stop()


if not reviews:

    st.warning(
        "No completed AI review is available for this case."
    )

    st.info(
        "Temporary development mode: create a test AI review "
        "without calling Gemini."
    )

    if st.button(
        "🧪 Create Temporary Test Review",
        type="secondary",
        use_container_width=True
    ):

        test_synthesis = """
OVERALL STATUS: ATTENTION

EXECUTIVE SUMMARY:
The PKR 4,800,000 Industrial Testing procurement request
has documentation and financial process gaps. The supplied
Purchase Request is consistent with the requested amount,
but mandatory procurement documentation and financial review
evidence are not yet available.

COMPLIANCE ASSESSMENT:
ATTENTION — Mandatory procurement documentation is incomplete.

FINANCIAL ASSESSMENT:
ATTENTION — Financial review evidence and budget information
are not available.

RISK ASSESSMENT:
MEDIUM — Documentation and procurement process risks require
clarification. No confirmed misconduct or material financial
discrepancy has been identified.

KEY FINDINGS:
- Three vendor quotations are required.
- Technical evaluation is required.
- Comparative statement is required.
- Financial review evidence is missing.
- General Manager approval applies to this amount under
  POL-003 DA-03.
- Human review is required.

AI RECOMMENDATION:
RETURN FOR CLARIFICATION

HUMAN REVIEW REQUIRED:
YES
"""

        try:

            supabase.table("ai_reviews").insert(
                {
                    "case_id": case["id"],
                    "compliance_result":
                        "ATTENTION — Mandatory procurement documentation is incomplete.",
                    "financial_result":
                        "ATTENTION — Financial review evidence is missing.",
                    "risk_result":
                        "MEDIUM — Documentation and procurement process risks require clarification.",
                    "synthesis":
                        test_synthesis,
                    "recommendation":
                        "RETURN FOR CLARIFICATION"
                }
            ).execute()

            st.success(
                "✅ Temporary test AI review created."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create test review: {e}"
            )

    st.stop()

review = reviews[0]


# ---------------------------------------------------------
# AI Recommendation
# ---------------------------------------------------------

st.subheader("🤖 AI Assessment")

recommendation = review.get(
    "recommendation",
    "Not available"
)

st.info(
    f"**AI Recommendation:** {recommendation}"
)


with st.expander(
    "View Consolidated AI Assessment",
    expanded=True
):

    st.write(
        review.get(
            "synthesis",
            "No consolidated assessment available."
        )
    )


st.divider()


# ---------------------------------------------------------
# Grounded Chatbot
# ---------------------------------------------------------

st.subheader("💬 AegisAI Review Assistant")

st.write(
    "Ask questions about the case, supplied documents, "
    "or applicable PEIS policies."
)


# Initialize chat history

if "decision_chat_messages" not in st.session_state:
    st.session_state["decision_chat_messages"] = []


# Display previous messages

for message in st.session_state["decision_chat_messages"]:

    with st.chat_message(
        message["role"]
    ):
        st.write(
            message["content"]
        )


question = st.chat_input(
    "Ask about this case or its applicable policies..."
)


if question:

    st.session_state[
        "decision_chat_messages"
    ].append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.write(question)


    try:

        # -------------------------------------------------
        # Load Documents
        # -------------------------------------------------

        documents_response = (
            supabase
            .table("documents")
            .select("*")
            .eq(
                "case_id",
                case["id"]
            )
            .execute()
        )

        documents = (
            documents_response.data or []
        )


        # -------------------------------------------------
        # Retrieve Policy Evidence
        # -------------------------------------------------

        policy_evidence = search_policies(
            question,
            top_k=6
        )


        policy_text = "\n\n".join(
            [
                f"{item['policy_id']} — "
                f"{item['policy_name']}\n"
                f"{item['section_id']} — "
                f"{item['section_title']}\n"
                f"{item['content']}"
                for item in policy_evidence
            ]
        )


        # -------------------------------------------------
        # Document Context
        # -------------------------------------------------

        document_text = "\n\n".join(
            [
                f"DOCUMENT: {doc['document_name']}\n"
                f"TYPE: {doc['document_type']}\n"
                f"CONTENT:\n{doc['extracted_text']}"
                for doc in documents
            ]
        )


        # -------------------------------------------------
        # Previous Chat
        # -------------------------------------------------

        chat_history = "\n\n".join(
            [
                f"{message['role'].upper()}: "
                f"{message['content']}"
                for message
                in st.session_state[
                    "decision_chat_messages"
                ][-6:]
            ]
        )


        # -------------------------------------------------
        # Gemini
        # -------------------------------------------------

        client = genai.Client(
            api_key=get_gemini_api_key()
        )


        prompt = f"""
You are the AegisAI Review Assistant.

You help a human reviewer understand an approval case.

Your answers MUST be grounded ONLY in:

1. The supplied case information
2. The supplied case documents
3. The retrieved PEIS policy evidence
4. The supplied AI review

Do not invent policies, facts, documents, approvals,
financial reviews, vendor information, or requirements.

If the available evidence is insufficient, clearly say:

"That cannot be determined from the available evidence."

Do not make the final approval decision.

The human reviewer must remain responsible for
Approve / Return / Reject.

==================================================
CASE
==================================================

Title: {case.get("title", "")}

Department: {case.get("department", "")}

Amount: PKR {case.get("amount", "")}

Description:

{case.get("description", "")}


==================================================
SUPPLIED DOCUMENTS
==================================================

{document_text}


==================================================
RETRIEVED POLICY EVIDENCE
==================================================

{policy_text}


==================================================
AI REVIEW
==================================================

{review.get("synthesis", "")}


==================================================
CONVERSATION
==================================================

{chat_history}


==================================================

USER QUESTION:

{question}

Answer clearly and briefly.

When referring to a policy, cite its policy ID
and section ID, for example:

POL-001 P-02

Do not provide a final human decision.
"""


        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )


        answer = response.text


        st.session_state[
            "decision_chat_messages"
        ].append(
            {
                "role": "assistant",
                "content": answer
            }
        )


        with st.chat_message("assistant"):
            st.write(answer)


    except Exception as e:

        st.error(
            f"Assistant failed: {e}"
        )


st.divider()


# ---------------------------------------------------------
# Human Decision
# ---------------------------------------------------------

st.subheader("👤 Human Final Decision")

st.warning(
    "The AI recommendation is advisory only. "
    "The final decision must be made by the human reviewer."
)


decision = st.radio(
    "Select Decision",
    [
        "Approve",
        "Return",
        "Reject"
    ],
    horizontal=True
)


comments = st.text_area(
    "Reviewer Comments",
    placeholder="Enter your decision comments..."
)


if decision in ["Return", "Reject"] and not comments.strip():

    st.info(
        "Reviewer comments are required for Return or Reject."
    )


if st.button(
    "Submit Final Decision",
    type="primary",
    use_container_width=True
):

    if decision in ["Return", "Reject"] and not comments.strip():

        st.error(
            "Please enter reviewer comments."
        )

        st.stop()


    st.success(
        f"Human decision selected: {decision}"
    )

    st.info(
        "Decision saving and audit trail will be connected "
        "in the next step."
    )
