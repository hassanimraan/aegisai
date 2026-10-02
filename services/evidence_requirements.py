"""
Policy-driven evidence requirements for AegisAI.

This module does NOT hard-code a universal document checklist.
It determines requirements from the policy evidence supplied
by the RAG layer and the case context.
"""

import re


def _amount(case_data):
    try:
        return float(case_data.get("amount") or 0)
    except (TypeError, ValueError):
        return 0.0


def _text(value):
    return str(value or "").lower()


def _has_document(documents, document_type):
    target = _text(document_type)

    for doc in documents:
        doc_type = _text(doc.get("document_type"))
        if doc_type == target:
            return True

    return False


def _document_types(documents):
    return {
        _text(doc.get("document_type"))
        for doc in documents
    }


def determine_requirements(case_data, documents, policy_evidence):
    """
    Determine mandatory evidence from the supplied policy evidence.

    Returns a list of structured requirements.
    """

    amount = _amount(case_data)
    case_text = _text(
        " ".join(
            [
                str(case_data.get("title", "")),
                str(case_data.get("description", "")),
                str(case_data.get("business_justification", "")),
            ]
        )
    )

    requirements = []

    policy_text = "\n".join(
        _text(item.get("content"))
        for item in policy_evidence
    )

    # ---------------------------------------------------------
    # Basic capital expenditure documentation
    # ---------------------------------------------------------

    if (
        "capital expenditure" in policy_text
        or "capital expenditure request" in policy_text
    ):
        requirements.append({
            "id": "purchase_request",
            "name": "Purchase Request",
            "document_type": "Purchase Request",
            "mandatory": True,
            "reason": "Required by the applicable procurement/financial process.",
            "status": "COMPLETE"
            if _has_document(documents, "Purchase Request")
            else "MISSING",
        })

        requirements.append({
            "id": "business_justification",
            "name": "Business Justification",
            "document_type": "Business Justification",
            "mandatory": True,
            "reason": "Required to establish the business need.",
            "status": "COMPLETE"
            if _has_document(documents, "Business Justification")
            else "MISSING",
        })

    # ---------------------------------------------------------
    # Competitive procurement above PKR 500,000
    # ---------------------------------------------------------

    competitive_above_500k = (
        amount > 500000
        and (
            "three vendor quotations" in policy_text
            or "at least three vendor quotations" in policy_text
            or "above pkR 500,000" in policy_text
            or "above pkr 500,000" in policy_text
        )
    )

    # Do not automatically impose quotations merely because
    # the amount is high. The policy evidence must establish it.
    if competitive_above_500k:

        requirements.append({
            "id": "vendor_quotations",
            "name": "Three Vendor Quotations",
            "document_type": "Vendor Quotation",
            "mandatory": True,
            "minimum_count": 3,
            "reason": "Applicable policy requires three quotations for competitive procurement above PKR 500,000.",
            "status": "COMPLETE"
            if sum(
                1
                for doc in documents
                if _text(doc.get("document_type")) == "vendor quotation"
            ) >= 3
            else "MISSING",
        })

        requirements.append({
            "id": "comparative_statement",
            "name": "Comparative Statement",
            "document_type": "Comparative Statement",
            "mandatory": True,
            "reason": "Required for competitive procurement.",
            "status": "COMPLETE"
            if _has_document(documents, "Comparative Statement")
            else "MISSING",
        })

    # ---------------------------------------------------------
    # Specialized / technically complex procurement
    # ---------------------------------------------------------

    specialized = any(
        phrase in case_text
        for phrase in [
            "specialized equipment",
            "specialised equipment",
            "technical equipment",
            "engineering service",
            "technically complex",
            "industrial equipment",
            "testing equipment",
        ]
    )

    if (
        specialized
        and (
            "technical evaluation" in policy_text
            or "specialized equipment" in policy_text
            or "technically complex" in policy_text
        )
    ):
        requirements.append({
            "id": "technical_evaluation",
            "name": "Technical Evaluation",
            "document_type": "Technical Evaluation",
            "mandatory": True,
            "reason": "Required for specialized or technically complex procurement.",
            "status": "COMPLETE"
            if _has_document(documents, "Technical Evaluation")
            else "MISSING",
        })

    # ---------------------------------------------------------
    # Financial Review
    # ---------------------------------------------------------

    financial_review_required = (
        "financial review before approval" in policy_text
        or "financial review" in policy_text
    )

    if financial_review_required:
        requirements.append({
            "id": "financial_review",
            "name": "Financial Review",
            "document_type": None,
            "mandatory": True,
            "reason": "Applicable policy requires financial review before approval.",
            "status": "COMPLETE"
            if any(
                "financial review" in _text(doc.get("extracted_text"))
                or "finance review" in _text(doc.get("extracted_text"))
                for doc in documents
            )
            else "MISSING",
        })

    # ---------------------------------------------------------
    # Approval requirement
    # ---------------------------------------------------------

    if amount > 0:
        requirements.append({
            "id": "approval_request",
            "name": "Required Approval",
            "document_type": "Approval Request",
            "mandatory": True,
            "reason": "Required approval authority must be established before PO/approval.",
            "status": "COMPLETE"
            if _has_document(documents, "Approval Request")
            else "MISSING",
        })

    # ---------------------------------------------------------
    # Remove duplicates
    # ---------------------------------------------------------

    unique = {}

    for requirement in requirements:
        unique[requirement["id"]] = requirement

    return list(unique.values())


def get_missing_requirements(requirements):
    return [
        item
        for item in requirements
        if item.get("mandatory") and item.get("status") == "MISSING"
    ]


def evidence_gate(requirements):
    missing = get_missing_requirements(requirements)

    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "missing_count": len(missing),
    }
