from google import genai

from config.settings import get_gemini_api_key


MODEL = "gemini-3.6-flash"


def run_financial_agent(
    case_data,
    documents,
    policy_evidence
):
    client = genai.Client(
        api_key=get_gemini_api_key()
    )

    document_text = "\n\n".join(
        [
            f"DOCUMENT: {doc['document_name']}\n"
            f"TYPE: {doc['document_type']}\n"
            f"CONTENT:\n{doc['extracted_text']}"
            for doc in documents
        ]
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

    prompt = f"""
You are the Financial Agent in AegisAI.

Review the financial aspects of the approval case using ONLY
the supplied case information, documents, and policy evidence.

IMPORTANT RULES:

1. Do not invent policies, thresholds, amounts, documents,
   or facts.

2. Determine approval authority only from the supplied
   policy evidence.

3. Compare the requested amount against the supplied
   approval thresholds.

4. Check whether amounts are consistent across the
   available documents.

5. Identify financial discrepancies.

6. Identify missing financial information.

7. Do not make the final human approval decision.

8. The Financial Agent's own analysis is NOT evidence that
   an organizational financial review has been completed.

9. Mark Financial Review as PASS only when the supplied
   documents explicitly contain evidence of a completed
   financial review.

10. If there is no explicit evidence of a completed financial
    review, mark Financial Review as ATTENTION.

11. Do not assume or invent a Financial Review document.

CASE INFORMATION:

Title: {case_data.get("title", "")}
Department: {case_data.get("department", "")}
Amount: {case_data.get("amount", "")}
Description: {case_data.get("description", "")}

SUPPLIED DOCUMENTS:

{document_text}

RELEVANT POLICY EVIDENCE:

{policy_text}

Return the assessment using this structure:

FINANCIAL RESULT:
PASS or ATTENTION

SUMMARY:
Brief financial assessment.

AMOUNT CHECK:
State the case amount and whether it is consistent with
available supporting documents.

APPROVAL AUTHORITY CHECK:
Requested amount:
Applicable threshold:
Approval authority:
Policy section:

FINANCIAL REQUIREMENTS CHECK:

- Requirement:
- Evidence:
- Status:
- Policy:

FINANCIAL DISCREPANCIES:
List discrepancies.
Write "None identified" if none exist.

MISSING OR UNCLEAR FINANCIAL ITEMS:
List missing information.
Write "None identified" if none exists.

POLICY EVIDENCE:
List the policy sections used.

RECOMMENDATION:
State whether the financial aspects appear compliant or
require clarification/escalation.

Do not provide a final human approval decision.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text
