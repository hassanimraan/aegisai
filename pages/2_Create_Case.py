import streamlit as st
from pypdf import PdfReader

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
# HEADER
# ==========================================

st.title("📝 Create Approval Case")

st.write(
    "Create a procurement or capital expenditure "
    "approval case and upload its supporting documents."
)

st.divider()


# ==========================================
# CREATE CASE
# ==========================================

st.subheader("1. Request Information")

with st.form("create_case_form"):

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
        "Request Description"
    )

    business_justification = st.text_area(
        "Business Justification"
    )

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

        response = (
            supabase
            .table("cases")
            .insert({
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
            })
            .execute()
        )

        if response.data:

            case_id = response.data[0]["id"]

            st.session_state["current_case_id"] = case_id

            st.success(
                "Approval case created successfully."
            )

            st.info(
                f"Case ID: {case_id}"
            )

        else:

            st.error(
                "Case could not be created."
            )

    except Exception as e:

        st.error(
            f"Error creating case: {str(e)}"
        )


# ==========================================
# DOCUMENT UPLOAD
# ==========================================

if "current_case_id" in st.session_state:

    case_id = st.session_state["current_case_id"]

    st.divider()

    st.subheader("2. Upload Supporting Documents")

    st.write(
        "Upload the PDF documents required for the approval review."
    )

    document_type = st.selectbox(
        "Document Type",
        [
            "Purchase Request",
            "Business Justification",
            "Vendor Quotation",
            "Technical Evaluation",
            "Comparative Statement",
            "Approval Request",
            "Other"
        ]
    )

    uploaded_file = st.file_uploader(
        "Select PDF document",
        type=["pdf"]
    )

    if uploaded_file:

        st.write(
            f"Selected: **{uploaded_file.name}**"
        )

        if st.button(
            "📤 Upload & Extract Text",
            type="primary"
        ):

            try:

                # ------------------------------
                # READ PDF
                # ------------------------------

                reader = PdfReader(
                    uploaded_file
                )

                extracted_pages = []

                for page in reader.pages:

                    text = page.extract_text()

                    if text:
                        extracted_pages.append(
                            text
                        )

                extracted_text = "\n\n".join(
                    extracted_pages
                )

                # ------------------------------
                # CHECK TEXT
                # ------------------------------

                if not extracted_text.strip():

                    st.warning(
                        "No selectable text was found "
                        "in this PDF. OCR will be added "
                        "in a later processing step."
                    )

                    st.stop()

                # ------------------------------
                # SAVE DOCUMENT
                # ------------------------------

                supabase = get_supabase()

                response = (
                    supabase
                    .table("documents")
                    .insert({
                        "case_id": case_id,
                        "document_name": uploaded_file.name,
                        "document_type": document_type,
                        "extracted_text": extracted_text
                    })
                    .execute()
                )

                if response.data:

                    st.success(
                        f"{uploaded_file.name} uploaded successfully."
                    )

                    st.info(
                        f"Extracted approximately "
                        f"{len(extracted_text):,} characters."
                    )

                    st.session_state[
                        "document_uploaded"
                    ] = True

                else:

                    st.error(
                        "Document could not be saved."
                    )

            except Exception as e:

                st.error(
                    f"Error processing document: {str(e)}"
                )


# ==========================================
# CURRENT CASE DOCUMENTS
# ==========================================

if "current_case_id" in st.session_state:

    case_id = st.session_state["current_case_id"]

    st.divider()

    st.subheader("3. Uploaded Documents")

    try:

        supabase = get_supabase()

        response = (
            supabase
            .table("documents")
            .select("*")
            .eq("case_id", case_id)
            .order("created_at")
            .execute()
        )

        documents = response.data or []

        if documents:

            for index, document in enumerate(
                documents,
                start=1
            ):

                st.write(
                    f"**{index}. "
                    f"{document.get('document_name', '-')}"
                    f"** — "
                    f"{document.get('document_type', '-')}"
                )

        else:

            st.info(
                "No documents uploaded yet."
            )

    except Exception as e:

        st.error(
            f"Unable to load documents: {str(e)}"
        )
