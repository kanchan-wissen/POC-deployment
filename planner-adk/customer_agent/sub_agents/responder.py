import json
from google.adk.tools import FunctionTool

def generate_response(categorized_inquiry: dict) -> dict:
    """
    Generates a pre-defined response based on the category of a customer inquiry.

    Args:
        categorized_inquiry: A dictionary containing the 'original_inquiry' and 'category' from the CategorizerTool.

    Returns:
        A dictionary with the original inquiry, category, and a suggested response.
    """
    category = categorized_inquiry.get("category")
    original_inquiry = categorized_inquiry.get("original_inquiry")

    responses = {
        "Technical Support": "Thank you for contacting technical support. Please provide your account number and we will connect you with a specialist.",
        "Billing": "Thank you for contacting billing. Please provide your account number and the invoice details, and we will assist you.",
        "General Inquiry": "Thank you for your inquiry. We will route your request to the appropriate department.",
    }

    suggested_response = responses.get(category, "Thank you for your inquiry. We will route your request to the appropriate department.")

    return {
        "original_inquiry": original_inquiry,
        "category": category,
        "suggested_response": suggested_response,
    }

# Create a FunctionTool from your Python function
TriggerN8NTool = FunctionTool(func=generate_response)

# from google.adk.agents import LlmAgent
# from dotenv import load_dotenv
# load_dotenv()

# ResponderAgent = LlmAgent(
#     name='responder',
#     model='gemini-2.0-flash',
#     description="An agent that takes categorized customer inquiries and generates appropriate pre-defined responses based on the determined category",
#     instruction="""
#             You are the Response Suggestion Agent in a Customer Inquiry Processor pipeline.
#             Your task is to take the categorized inquiry from the previous agent and provide an appropriate pre-defined response based on the category.
            
#             **Input**
#               Category Response: {category_response} # <--- This variable will contain the output from the Inquiry Categorizer Agent
            
#             **Response Rules:**
            
#                Technical Support Category → 
#                  "Thank you for contacting technical support. Please provide your account number and we will connect you with a specialist."
            
#                Billing Category → 
#                   "Thank you for contacting billing. Please provide your account number and the invoice details, and we will assist you."
            
#                General Inquiry Category → 
#                   "Thank you for your inquiry. We will route your request to the appropriate department."
            
#             Example:
#             Input Category Response: 
#             {
#                 "original_inquiry": "My internet is not working after the update, please help!",
#                 "category": "Technical Support"
#             }
            
#             Your Output:
#             {
#                 "original_inquiry": "My internet is not working after the update, please help!",
#                 "category": "Technical Support",
#                 "suggested_response": "Thank you for contacting technical support. Please provide your account number and we will connect you with a specialist."
#             }
            
#             Example:
#             Input Category Response:
#             {
#                 "original_inquiry": "I was charged twice for my subscription, need a refund",
#                 "category": "Billing"
#             }
            
#             Your Output:
#             {
#                 "original_inquiry": "I was charged twice for my subscription, need a refund",
#                 "category": "Billing",
#                 "suggested_response": "Thank you for contacting billing. Please provide your account number and the invoice details, and we will assist you."
#             }
            
#             Example:
#             Input Category Response:
#             {
#                 "original_inquiry": "What are your business hours?",
#                 "category": "General Inquiry"
#             }
            
#             Your Output:
#             {
#                 "original_inquiry": "What are your business hours?",
#                 "category": "General Inquiry",
#                 "suggested_response": "Thank you for your inquiry. We will route your request to the appropriate department."
#             }
            
#             IMPORTANT: Respond ONLY with raw JSON. Do NOT include any Markdown formatting like triple backticks (```), code fences, or text annotations.
#                        The response must be a valid JSON object without any wrapping.
#                        Example:
#                        {
#                          "original_inquiry": "...",
#                          "category": "...",
#                          "suggested_response": "..."
#                        }
#                        """,
# )