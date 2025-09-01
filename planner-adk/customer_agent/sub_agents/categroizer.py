from google.adk.agents import LlmAgent
import json
from google.adk.tools import FunctionTool

def categorize_inquiry(inquiry_text: str) -> dict:
    """
    Categorizes a customer inquiry into "Technical Support", "Billing", or "General Inquiry"
    based on predefined keyword rules.

    Args:
        inquiry_text: The raw customer inquiry string.

    Returns:
        A dictionary with the original inquiry and its determined category.
    """
    tech_keywords = ["internet", "network", "wifi", "connection", "login", "password", "software", "app", "error", "bug", "not working", "broken"]
    billing_keywords = ["bill", "billing", "invoice", "payment", "charge", "refund", "subscription"]

    if any(keyword in inquiry_text.lower() for keyword in tech_keywords):
        category = "Technical Support"
    elif any(keyword in inquiry_text.lower() for keyword in billing_keywords):
        category = "Billing"
    else:
        category = "General Inquiry"

    return {
        "original_inquiry": inquiry_text,
        "category": category
    }

# This is the key change: create a FunctionTool from your Python function
ValidationTool = FunctionTool(func=categorize_inquiry)