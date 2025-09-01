# from .sub_agents import CategorizerAgent, ResponderAgent
from .sub_agents.categroizer import ValidationTool
from .sub_agents.responder import TriggerN8NTool
from google.adk.agents import SequentialAgent, LlmAgent, Agent
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
from httpx import AsyncClient
import os
from dotenv import load_dotenv
load_dotenv()


client = AsyncClient()
BASE_URL = os.getenv("BASE_URL")

class CustomerAgentOrchestrator:
    def __init__(self):
        # Root Agent
        self.root_agent = LlmAgent(
            name='CustomerInquiryProcessorPipeline',
            # Key change: Use the `tools` parameter instead of `sub_agents`
            model="gemini-2.0-flash",
            instruction="""
                You are a customer service assistant. Your sole purpose is to process customer inquiries.
                For every customer inquiry you receive, you must use the 'generate_response' tool to categorize it and provide a pre-defined response.
                You MUST use this tool and respond ONLY with the tool's output.
                """,
            tools=[ValidationTool, TriggerN8NTool],
            description="A pipeline that processes customer inquiries by categorizing them and generating appropriate pre-defined responses",
        )


class ValidateJsonRequest(BaseModel):
    """Request model for validating JSON data"""
    requestId: str = Field(..., description="ID of the pre-authorization request")
    # payerId: str = Field(..., description="ID of the payer")
    jsonData: Dict[str, Any] = Field(..., description="JSON data to validate")

class N8NWebhookRequest(BaseModel):
    """Request model for calling N8N webhook"""
    request_id: str = Field(..., description="ID of the pre-authorization request")
    user_id: str = Field(..., description="ID of the user initiating the request.")
    patient_id: str = Field(..., description="ID of the patient.")
    patient_name: str = Field(..., description="Name of the patient.")
    payer_id: str = Field(..., description="ID of the payer.")
    prompt: str = Field(..., description="Prompt/instructions for N8N workflow")
    validatedJson: Dict[str, Any] = Field(..., description="Validated JSON data to send to N8N")


class N8NWebhookResponse(BaseModel):
    """Response model for N8N webhook call"""
    workflow_triggered: bool = Field(..., description="Pre-authorization work flow triggered or not")
    workflow_id: Optional[str] = Field(None, description="workflow id")
    message: str = Field(..., description="Result message")

class ValidationError(BaseModel):
    """Model for validation errors"""
    field: str = Field(..., description="Field that failed validation")
    error: str = Field(..., description="Error description")
    severity: str = Field(..., description="Error severity: error, warning, info")

class ValidateJsonResponse(BaseModel):
    """Response model for JSON validation"""
    requestId: str = Field(..., description="Pre-authorization request ID")
    # payerId: str = Field(..., description="Payer ID")
    isValid: bool = Field(..., description="Whether the JSON passed all validations")
    validationErrors: list[ValidationError] = Field(default=[], description="List of validation errors")
    validationWarnings: list[ValidationError] = Field(default=[], description="List of validation warnings")
    validationSummary: str = Field(..., description="Summary of validation results")
    status: str = Field(..., description="Updated request status")
    validatedAt: datetime = Field(..., description="Timestamp when validation was performed")



async def validate_json(request: ValidateJsonRequest) -> ValidateJsonResponse:
    """
    Simulates JSON data validation by returning a hardcoded response.
    This bypasses the external API call for testing purposes.
    """
    print("Skipping API call to validate-json and returning hardcoded data.")
        # Check if the request is a Pydantic model or a dictionary

    if isinstance(request, dict):
        request_id = request.get("requestId")
    else:
        # Fallback for when it's the expected Pydantic model
        request_id = request.requestId
    
    print(f"req id is : {request_id}")
    
    # You can customize this hardcoded response for different test cases
    hardcoded_response = {
        "requestId": request_id,
        "isValid": True,
        "validationErrors": [],
        "validationWarnings": [],
        "validationSummary": "Validation successful! All required fields are present and valid.",
        "status": "validated",
        "validatedAt": datetime.now().isoformat()
    }
    print(f"hardcoded daata is : {hardcoded_response}")
    
    # Return the Pydantic model instance
    return ValidateJsonResponse(**hardcoded_response) 
    


async def call_n8n_webhook(request: N8NWebhookRequest) -> N8NWebhookResponse:
    """Calls an N8N webhook with the provided request data."""
    try:
        # Handle both dict and Pydantic model inputs
        if isinstance(request, dict):
            validated_json_data = request.get("validatedJson")
            request_id_data = request.get("request_id")
            print("in if")
        else:
            validated_json_data = request.validatedJson
            request_id_data = request.request_id
            print("in else")
            
        new_payload = {
            "request_id": request_id_data,
            "user_id": "hardcoded_user_123",
            "patient_id": validated_json_data.get("personnumber", "N/A"),
            "patient_name": validated_json_data.get("patientfirstname", "N/A") + " " + validated_json_data.get("patientlastname", "N/A"),
            "payer_id": validated_json_data.get("payerid", "N/A"),
            "prompt": "Trigger N8N workflow for pre-authorization request.",
            "validated_json": validated_json_data
        }

        print(f"Calling N8N webhook with data: {new_payload}")

        response = await client.post(f"{BASE_URL}/trigger-n8n", json=new_payload)
        print(f"after Calling N8N webhook apiiiiiiiiiiiiiii:")
        print(f"response issss: {response}")
        response.raise_for_status()

        # The response from the external API needs to match your N8NWebhookResponse model
        # For example, the external API should return something like:
        # {"workflow_triggered": true, "message": "Workflow triggered", "workflow_id": "xyz123"}
        return N8NWebhookResponse(**response.json())

    except Exception as e:
        print(f"Error calling N8N webhook: {e}")
        # The return data must now match your N8NWebhookResponse model
        return N8NWebhookResponse(
            workflow_triggered=False,
            workflow_id=None,
            message=f"An error occurred: {str(e)}"
        )

class CustomerAgentOrchestrator:
    def __init__(self):
        # Root Agent
        self.root_agent = LlmAgent(
            name='CustomerInquiryProcessorPipeline',
            # Key change: Use the `tools` parameter instead of `sub_agents`
            model="gemini-2.0-flash",
            description=(
                "You are a helpful medical assistant agent designed to automate "
                "the pre-authorization workflow for patients by coordinating with external APIs. "
                "You must follow strict workflows, first validate data, and provide structured responses "
                "Then call_n8n_webhook to trigger the workflow"
                "using the given Pydantic models."
            ),
            instruction=(
                "You are responsible for planning and executing the complete pre-authorization workflow. "
                "Your tasks include:\n\n"
                "1. **Validate JSON**\n"
                "   - Call `validate_json()` with `ValidateJsonRequest`.\n"
                "   - Collect and return a `ValidateJsonResponse` containing errors, warnings, and summary.\n"
                "   - If validation fails, do not proceed further until user action is taken.\n\n"
                "2. **Trigger N8N Workflow**\n"
                "   - Call `call_n8n_webhook()` with `N8NWebhookRequest`.\n"
                "   - Ensure the validatedJson are passed correctly.\n"
                "   - Return a `N8NWebhookResponse`.\n\n"
                "3. **Error Handling**\n"
                "   - If any step fails, capture the exception and return the correct error model for that step.\n"
                "   - Always include a helpful message field with context on what failed.\n\n"
                "The output of each step MUST be one of the defined Pydantic response models. "
                "Never return raw text or unstructured output."
            ),
            tools=[validate_json, call_n8n_webhook]
        )