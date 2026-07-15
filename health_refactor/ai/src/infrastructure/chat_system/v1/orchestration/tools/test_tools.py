"""In-memory test tools for local orchestration smoke tests.

Defined with ``@tool`` per LangGraph quickstart:
https://docs.langchain.com/oss/python/langgraph/quickstart
"""
from langchain_core.tools import BaseTool, tool

COMPANY_DOCS: dict[str, str] = {
    "refund_policy": """Acme Refund Policy
- Full refund within 30 days of delivery for unused items in original packaging.
- Opened or used items: store credit only within 14 days.
- Digital products: refund within 14 days if the file was not downloaded.
- Refunds are processed in 5-7 business days to the original payment method.
- To start a refund, contact support with your order number.""",
    "shipping_policy": """Acme Shipping Policy
- Standard shipping: 3-5 business days (free over $50).
- Express shipping: 1-2 business days (flat $12.99).
- Orders placed before 2pm local time ship the same business day.
- Tracking is emailed once the package leaves our warehouse.""",
    "warranty": """Acme Product Warranty
- Electronics: 12-month manufacturer warranty against defects.
- Accessories: 90-day warranty.
- Warranty covers manufacturing faults, not accidental damage or misuse.
- Proof of purchase required for all warranty claims.""",
    "privacy_policy": """Acme Privacy Policy
- We collect name, email, and order details to fulfill purchases and support.
- Payment data is handled by our PCI-compliant payment provider; we do not store card numbers.
- We do not sell personal data to third parties.
- You may request data export or deletion by emailing privacy@acme.example.""",
}

AVAILABLE_DOC_KEYS = tuple(COMPANY_DOCS.keys())


@tool
def get_company_doc(doc_key: str) -> str:
    """Look up official Acme company documentation.

    Args:
        doc_key: Document key — refund_policy, shipping_policy, warranty, or privacy_policy.
    """
    key = doc_key.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in COMPANY_DOCS:
        return (
            f"Unknown doc_key '{doc_key}'. "
            f"Available keys: {', '.join(AVAILABLE_DOC_KEYS)}"
        )
    return COMPANY_DOCS[key]


def build_test_tools() -> list[BaseTool]:
    """Tools list for ``model.bind_tools(tools)`` in local smoke tests."""
    return [get_company_doc]


def tools_by_name(tools: list[BaseTool]) -> dict[str, BaseTool]:
    """Map tool name → tool, as in the LangGraph quickstart."""
    return {tool.name: tool for tool in tools}
