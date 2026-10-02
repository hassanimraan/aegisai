```python
"""
AegisAI - Policy-Driven Evidence Requirements

This module determines case evidence requirements from:
    1. The applicable PEIS policy evidence retrieved by RAG.
    2. The case amount and description.
    3. The documents already uploaded for the case.

Important design principle:
    AegisAI must NOT assume a universal document checklist.

For example:
    - A competitive procurement above PKR 500,000 requires
      at least 3 vendor quotations under POL-001 / POL-004.
    - A case that qualifies for an approved single-source
      exception should not automatically be forced to provide
      3 quotations.
    - Technical Evaluation is conditional on specialized or
      technically complex procurement.
    - If the supplied policy does not establish a requirement,
      this module should not invent one.
"""

import re


# ==========================================================
# NORMALIZATION HELPERS
# ==========================================================

def _text(value):
    """Return normalized lowercase text."""
    return str(value or "").strip().lower()


def _amount(case_data):
    """Safely convert case amount to float."""
    try:
        return float(case_data.get("amount") or 0)
    except (TypeError, ValueError):
        return 0.0


def _document_type(document):
    """Return normalized document type."""
    return _text(document.get("document_type"))


def _document_text(document):
    """Return searchable text from an uploaded document."""
    return _text(
        " ".join(
            [
                str(document.get("document_name", "")),
                str(document.get("document_type", "")),
                str(document.get("extracted_text", "")),
            ]
        )
    )


def _all_policy_text(policy_evidence):
    """
    Combine retrieved policy evidence into one normalized string.
    """
    return "\n".join(
        _text(item.get("content"))
        for item in policy_evidence
        if item.get("content")
    )


def _has_policy_phrase(policy_text, phrases):
    """Return True if any supplied phrase exists in policy text."""
    return any(
        phrase.lower() in policy_text
        for phrase in phrases
    )


def _has_document_type(documents, document_type):
    """
    Check whether at least one uploaded document has the
    specified document type.
    """
    target = _text(document_type)

    return any(
        _document_type(document) == target
        for document in documents
    )


def _document_count(documents, document_type):
    """
    Count uploaded documents of a specific type.
    """
    target = _text(document_type)

    return sum(
        1
        for document in documents
        if _document_type(document) == target
    )


def _has_financial_review_evidence(documents):
    """
    Determine whether an uploaded document contains explicit
    evidence of a financial review.

    The AI agent's own analysis does NOT count as evidence.
    """
    financial_phrases = [
        "financial review",
        "finance review",
        "reviewed by finance",
        "reviewed by finance department",
        "finance department review",
        "financially reviewed",
        "financial approval",
    ]

    for document in documents:

        text = _document_text(document)

        if any(
            phrase in text
            for phrase in financial_phrases
        ):
            return True

    return False


def _has_single_source_exception(documents, case_text):
    """
    Detect whether the supplied case/document evidence indicates
    a documented single-source exception.

    This does NOT decide whether the exception is valid or approved.
    It only identifies evidence that may affect the quotation
    requirement.

    Final compliance remains the responsibility of the agents
    and human reviewer.
    """

    exception_phrases = [
        "single source",
        "single-source",
        "sole source",
        "sole-source",
        "single vendor",
        "single-vendor",
        "approved single source",
        "approved single-source",
        "single source justification",
        "single-source justification",
    ]

    combined_text = case_text

    for document in documents:
        combined_text += " " + _document_text(document)

    return any(
        phrase in combined_text
        for phrase in exception_phrases
    )


def _is_specialized_procurement(case_data):
    """
    Identify whether the case appears to involve specialized,
    technical, engineering, industrial, or technically complex
    procurement.

    This is a case-context signal used only where the supplied
    policy makes Technical Evaluation conditional.
    """

    case_text = _text(
        " ".join(
            [
                str(case_data.get("title", "")),
                str(case_data.get("description", "")),
                str(case_data.get("business_justification", "")),
                str(case_data.get("request_type", "")),
            ]
        )
    )

    specialized_terms = [
        "specialized equipment",
        "specialised equipment",
        "technical equipment",
        "technically complex",
        "technical procurement",
        "engineering equipment",
        "engineering service",
        "engineering services",
        "industrial equipment",
        "testing equipment",
        "laboratory equipment",
        "automation equipment",
        "control system",
        "technical system",
        "specialized system",
        "specialised system",
    ]

    return any(
        term in case_text
        for term in specialized_terms
    )


def _is_capital_expenditure(case_data, case_text):
    """
    Determine whether the case is explicitly a capital expenditure
    case.
    """

    request_type = _text(
        case_data.get("request_type")
    )

    return (
        "capital expenditure" in request_type
        or "capex" in request_type
        or "capital expenditure" in case_text
        or "capex" in case_text
    )


def _is_procurement_case(case_data, case_text):
    """
    Determine whether the case is a procurement-related case.
    """

    request_type = _text(
        case_data.get("request_type")
    )

    return (
        "procurement" in request_type
        or "purchase" in request_type
        or "procurement" in case_text
        or "purchase" in case_text
    )


# ==========================================================
# REQUIREMENT CREATION
# ==========================================================

def _make_requirement(
    requirement_id,
    name,
    document_type=None,
    mandatory=True,
    reason="",
    status="MISSING",
    minimum_count=None,
    evidence_rule=None,
):
    """
    Create a consistent requirement object.

    Keeping the structure consistent makes it easier for:
        - Streamlit UI
        - Supabase JSONB
        - Evidence Gate
        - future reporting
    """

    requirement = {
        "id": requirement_id,
        "name": name,
        "document_type": document_type,
        "mandatory": mandatory,
        "reason": reason,
        "status": status,
    }

    if minimum_count is not None:
        requirement["minimum_count"] = minimum_count

    if evidence_rule:
        requirement["evidence_rule"] = evidence_rule

    return requirement


# ==========================================================
# MAIN REQUIREMENT ENGINE
# ==========================================================

def determine_requirements(
    case_data,
    documents,
    policy_evidence,
):
    """
    Determine mandatory evidence requirements for a case.

    Inputs:
        case_data:
            Current case record.

        documents:
            Uploaded case documents.

        policy_evidence:
            RAG-retrieved PEIS policy records.

    Returns:
        List of requirement dictionaries.
    """

    case_data = case_data or {}
    documents = documents or []
    policy_evidence = policy_evidence or []

    amount = _amount(case_data)

    case_text = _text(
        " ".join(
            [
                str(case_data.get("title", "")),
                str(case_data.get("description", "")),
                str(case_data.get("business_justification", "")),
                str(case_data.get("request_type", "")),
            ]
        )
    )

    policy_text = _all_policy_text(
        policy_evidence
    )

    requirements = []

    # ======================================================
    # POLICY AVAILABILITY
    # ======================================================

    if not policy_evidence:

        return []


    # ======================================================
    # CASE TYPE
    # ======================================================

    capital_expenditure = _is_capital_expenditure(
        case_data,
        case_text,
    )

    procurement_case = _is_procurement_case(
        case_data,
        case_text,
    )


    # ======================================================
    # PURCHASE REQUEST
    # ======================================================

    purchase_request_policy = _has_policy_phrase(
        policy_text,
        [
            "purchase request",
            "purchase requisition",
        ],
    )

    if (
        purchase_request_policy
        and (capital_expenditure or procurement_case)
    ):

        requirements.append(
            _make_requirement(
                requirement_id="purchase_request",
                name="Purchase Request",
                document_type="Purchase Request",
                mandatory=True,
                reason=(
                    "Applicable PEIS procurement procedure "
                    "requires a Purchase Request."
                ),
                status=(
                    "COMPLETE"
                    if _has_document_type(
                        documents,
                        "Purchase Request",
                    )
                    else "MISSING"
                ),
                evidence_rule="POL-004 / SOP-01",
            )
        )


    # ======================================================
    # BUSINESS JUSTIFICATION
    # ======================================================

    business_justification_policy = _has_policy_phrase(
        policy_text,
        [
            "business justification",
            "business need",
            "business justification",
        ],
    )

    if (
        business_justification_policy
        and (capital_expenditure or procurement_case)
    ):

        requirements.append(
            _make_requirement(
                requirement_id="business_justification",
                name="Business Justification",
                document_type="Business Justification",
                mandatory=True,
                reason=(
                    "Applicable PEIS policy requires the "
                    "business need/justification to be documented."
                ),
                status=(
                    "COMPLETE"
                    if _has_document_type(
                        documents,
                        "Business Justification",
                    )
                    else "MISSING"
                ),
                evidence_rule="POL-004 / SOP-02",
            )
        )


    # ======================================================
    # QUOTATIONS
    # ======================================================

    quotation_policy_exists = _has_policy_phrase(
        policy_text,
        [
            "three vendor quotations",
            "at least three vendor quotations",
            "3 vendor quotations",
            "three quotations",
        ],
    )

    competitive_procurement_above_threshold = (
        amount > 500000
        and quotation_policy_exists
    )

    single_source_indicator = _has_single_source_exception(
        documents,
        case_text,
    )

    if competitive_procurement_above_threshold:

        if single_source_indicator:

            # ------------------------------------------------
            # SINGLE-SOURCE INDICATED
            # ------------------------------------------------
            #
            # Do NOT force three quotations merely because the
            # amount exceeds PKR 500,000.
            #
            # The case/document evidence indicates that a
            # single-source route may apply. We therefore require
            # the justification rather than inventing quotations.
            #

            requirements.append(
                _make_requirement(
                    requirement_id="single_source_justification",
                    name="Single-Source Justification",
                    document_type="Single-Source Justification",
                    mandatory=True,
                    reason=(
                        "The case indicates a single-source route. "
                        "The applicable policy allows the quotation "
                        "requirement to be addressed through a "
                        "documented and approved single-source "
                        "justification."
                    ),
                    status=(
                        "COMPLETE"
                        if (
                            _has_document_type(
                                documents,
                                "Single-Source Justification",
                            )
                            or any(
                                (
                                    "single source justification"
                                    in _document_text(document)
                                    or
                                    "single-source justification"
                                    in _document_text(document)
                                )
                                for document in documents
                            )
                        )
                        else "MISSING"
                    ),
                    evidence_rule="POL-001 / exception route",
                )
            )

        else:

            # ------------------------------------------------
            # COMPETITIVE PROCUREMENT
            # ------------------------------------------------

            quotation_count = _document_count(
                documents,
                "Vendor Quotation",
            )

            requirements.append(
                _make_requirement(
                    requirement_id="vendor_quotations",
                    name="Three Vendor Quotations",
                    document_type="Vendor Quotation",
                    mandatory=True,
                    minimum_count=3,
                    reason=(
                        "Applicable PEIS policy requires at least "
                        "three vendor quotations for competitive "
                        "procurement above PKR 500,000."
                    ),
                    status=(
                        "COMPLETE"
                        if quotation_count >= 3
                        else "MISSING"
                    ),
                    evidence_rule="POL-001 / P-02; POL-004 / SOP-09",
                )
            )


            # ------------------------------------------------
            # COMPARATIVE STATEMENT
            # ------------------------------------------------

            comparative_statement_policy = _has_policy_phrase(
                policy_text,
                [
                    "comparative statement",
                    "comparative analysis",
                ],
            )

            if comparative_statement_policy:

                requirements.append(
                    _make_requirement(
                        requirement_id="comparative_statement",
                        name="Comparative Statement",
                        document_type="Comparative Statement",
                        mandatory=True,
                        reason=(
                            "Applicable PEIS procurement procedure "
                            "requires a Comparative Statement for "
                            "competitive procurement."
                        ),
                        status=(
                            "COMPLETE"
                            if _has_document_type(
                                documents,
                                "Comparative Statement",
                            )
                            else "MISSING"
                        ),
                        evidence_rule="POL-001 / P-04; POL-004 / SOP-05",
                    )
                )


    # ======================================================
    # TECHNICAL EVALUATION
    # ======================================================

    technical_evaluation_policy = _has_policy_phrase(
        policy_text,
        [
            "technical evaluation",
            "technical evaluation required",
            "specialized equipment",
            "technically complex",
        ],
    )

    if (
        technical_evaluation_policy
        and _is_specialized_procurement(case_data)
    ):

        requirements.append(
            _make_requirement(
                requirement_id="technical_evaluation",
                name="Technical Evaluation",
                document_type="Technical Evaluation",
                mandatory=True,
                reason=(
                    "Applicable PEIS policy requires technical "
                    "evaluation for specialized equipment, "
                    "engineering services, or technically "
                    "complex procurement."
                ),
                status=(
                    "COMPLETE"
                    if _has_document_type(
                        documents,
                        "Technical Evaluation",
                    )
                    else "MISSING"
                ),
                evidence_rule="POL-001 / P-03; POL-004 / SOP-04",
            )
        )


    # ======================================================
    # FINANCIAL REVIEW
    # ======================================================

    financial_review_policy = _has_policy_phrase(
        policy_text,
        [
            "financial review before approval",
            "financial review",
        ],
    )

    if financial_review_policy:

        requirements.append(
            _make_requirement(
                requirement_id="financial_review",
                name="Financial Review",
                document_type=None,
                mandatory=True,
                reason=(
                    "Applicable PEIS policy requires financial "
                    "review before approval."
                ),
                status=(
                    "COMPLETE"
                    if _has_financial_review_evidence(
                        documents
                    )
                    else "MISSING"
                ),
                evidence_rule="POL-004 / SOP-06",
            )
        )


    # ======================================================
    # REQUIRED APPROVAL
    # ======================================================

    approval_policy = _has_policy_phrase(
        policy_text,
        [
            "required approval",
            "approval before po",
            "approval before purchase order",
            "approval authority",
            "delegation of authority",
        ],
    )

    if approval_policy and amount > 0:

        requirements.append(
            _make_requirement(
                requirement_id="approval_request",
                name="Required Approval",
                document_type="Approval Request",
                mandatory=True,
                reason=(
                    "Applicable PEIS policy requires approval "
                    "by the authority applicable to the request "
                    "amount before the PO/approval is issued."
                ),
                status=(
                    "COMPLETE"
                    if _has_document_type(
                        documents,
                        "Approval Request",
                    )
                    else "MISSING"
                ),
                evidence_rule="POL-003 / DA; POL-004 / SOP-07",
            )
        )


    # ======================================================
    # REMOVE DUPLICATES
    # ======================================================

    unique_requirements = {}

    for requirement in requirements:

        requirement_id = requirement.get("id")

        if requirement_id:
            unique_requirements[
                requirement_id
            ] = requirement

    return list(
        unique_requirements.values()
    )


# ==========================================================
# MISSING REQUIREMENTS
# ==========================================================

def get_missing_requirements(requirements):
    """
    Return all mandatory requirements that are not complete.
    """

    missing = []

    for requirement in requirements or []:

        if not requirement.get("mandatory", False):
            continue

        if requirement.get("status") != "COMPLETE":

            missing.append(
                requirement
            )

    return missing


# ==========================================================
# EVIDENCE GATE
# ==========================================================

def evidence_gate(requirements):
    """
    Evaluate whether the case has all mandatory evidence.

    Returns a JSON-serializable dictionary suitable for:
        - Streamlit
        - Supabase JSONB
        - Decision-page enforcement
    """

    requirements = requirements or []

    missing = get_missing_requirements(
        requirements
    )

    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "missing_count": len(missing),
        "total_requirements": len(
            [
                requirement
                for requirement in requirements
                if requirement.get("mandatory", False)
            ]
        ),
    }
```
