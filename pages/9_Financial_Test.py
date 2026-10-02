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
You are the Financial Agent in AegisAI,
an AI-powered procurement approval system.

Your task is to review the financial aspects of an
approval case using ONLY the supplied case information,
documents, and policy evidence.

IMPORTANT RULES:

- Use ONLY the supplied policy evidence.
- Use ONLY the supplied case and document information.
- Do not invent policies, thresholds, amounts, or documents.

- Determine the applicable approval authority ONLY when the
  supplied policy evidence establishes the required threshold.

- Compare the requested amount against the complete set of
  supplied approval thresholds.

- Do not assume that a missing threshold exists.

- If the evidence does not establish the applicable authority,
  clearly state that it cannot be determined from the available
  evidence.

- Check whether amounts are consistent across the available
  documents.

- Identify financial discrepancies explicitly.

- Identify missing financial information.

- Distinguish PASS from ATTENTION.

- Cite the relevant policy ID and section ID.

- Do not make the final human approval decision.

IMPORTANT FINANCIAL REVIEW RULES:

- Do NOT interpret the Financial Agent's own analysis as evidence
  that an organizational financial review has been completed.

- Only mark "Financial Review" as completed or evidenced if the
  supplied documents explicitly contain evidence of a completed
  financial review.

- If no document explicitly shows that a financial review has been
  completed, mark the Financial Review requirement as ATTENTION.

- Do not create or assume a financial review document that has not
  been supplied.

- A financial analysis performed by this AI agent is an assessment,
  not evidence that PEIS Finance has completed its organizational
  financial review.

CASE INFORMATION:

Title: {case_data.get("title", "")}
Department: {case_data.get("department", "")}
Amount: {case_data.get("amount", "")}
Description: {case_data.get("description", "")}

SUPPLIED DOCUMENTS:

{document_text}

RELEVANT POLICY EVIDENCE:

{policy_text}

Return your assessment using exactly this structure:

FINANCIAL RESULT:
PASS or ATTENTION

SUMMARY:
Brief overall financial assessment.

AMOUNT CHECK:
State the case amount and whether it is consistent with the
available supporting documents.

APPROVAL AUTHORITY CHECK:
State:
- Requested amount
- Applicable threshold
- Approval authority
- Policy section

If the applicable authority cannot be established from the
supplied evidence, explicitly state that.

FINANCIAL REQUIREMENTS CHECK:

- Requirement:
- Evidence:
- Status:
- Policy:

For the Financial Review requirement:

- Mark PASS only if the supplied documents explicitly show
  evidence of a completed financial review.
- Otherwise mark ATTENTION.
- Do not use the Financial Agent's own analysis as evidence.

FINANCIAL DISCREPANCIES:
List any amount inconsistencies or financial issues.
Write "None identified" if there are none.

MISSING OR UNCLEAR FINANCIAL ITEMS:
List missing financial information.
Write "None identified" if there are none.

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
