# main.py
from fastapi import FastAPI, APIRouter, HTTPException
# from .models import CustomerInquiryRequest, CustomerInquiryResponse
from models import PreAuthRequest, PreAuthResponse
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
# from .customer_agent import CustomerAgentOrchestrator, root_agent
from  customer_agent import CustomerAgentOrchestrator
from google.genai import types
import json
import re
import uuid
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

# SQLlite DB init
DB_URL = "sqlite:///./multi_agent_data.db"
APP_NAME = "CustomerInquiryProcessor"

# Create a lifespan event to initialize and clean up the session service
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Application starting up...")  
    # Initialize the DatabaseSessionService instance and store it in app.state
    try:
        app.state.session_service =DatabaseSessionService(db_url=DB_URL)
        print("Database session service initialized successfully.")
    except Exception as e:
        print("Database session service initialized failed.")
        print(e)
    
    yield # This is where the application runs, handling requests
    # Shutdown code
    print("Application shutting down...")
    
# FastAPI application setup
app = FastAPI(
    title="ADK Agent for Pre Auth",
    description="Multi-agent system for pre Authorization",
    version="1.0.0",
    lifespan=lifespan,
)
# Initializing the Orchestrator
customer_agent = CustomerAgentOrchestrator()
router = APIRouter()

@router.post("/process-inquiry", response_model=PreAuthResponse)
async def process_customer_inquiry(
    request_body: PreAuthRequest
):
    print(f"inside post req---------------")
    """
    Endpoint to interact with the multi-agent ADK system.
    request_body: {"customer_inquiry": "My internet is not working after the update, please help!"}
    """
    # Extract customer inquiry from request
    # customer_inquiry = request_body.customer_inquiry
    
    # Generate unique IDs for this processing session
    unique_id = str(uuid.uuid4())
    session_id = unique_id
    user_id = unique_id

    try:
        # Get database session service from application state
        session_service: DatabaseSessionService = app.state.session_service
        print(f"session service:{session_service}")
        
        # Try to get existing session or create new one
        current_session = None
        try:
            current_session = await session_service.get_session(
                app_name=APP_NAME,
                user_id = user_id,
                session_id=session_id,
            )
            print(f"current_session session:{current_session}")
        except Exception as e:
            print(f"Existing Session retrieval failed for session_id='{session_id}' "
                    f"and user_uid='{user_id}': {e}")
        
        # If no session found, creating new session
        if current_session is None:
            current_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
        else:
            print(f"Existing session '{session_id}'has been found. Resuming session.")

        # Initialize the ADK Runner with our multi-agent pipeline
        runner = Runner(
            app_name=APP_NAME,
            agent=customer_agent.root_agent,
            session_service = session_service,
        )

        print(f"after runner========")
        # New part: Construct the prompt with the JSON data
        user_prompt = (
        "Process the following pre-authorization request by first validating the JSON "
        f"and then triggering the N8N webhook: {request_body.model_dump_json()}"
        )

        # Format the user query as a structured message using the google genais content types
        user_message = types.Content(
            role="user", parts=[types.Part.from_text(text=user_prompt)]
        )
        # print(f"user message : {user_message}")
        # Run the agent asynchronously
        events = runner.run_async(
            user_id = user_id,
            session_id = session_id,
            new_message = user_message,
        )

        # Process events to find the final response  
        final_response = None
        async for event in events:
            # We want to get the result from the tool's output.
            # This is the most reliable way to get the final result.
            if event.is_final_response() and event.content:
                print(f"inside events----------")
                # The content may be a tool's output or a text part, so we check for both.
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
                        break # Exit inner loop once we find the text part
                if final_response:
                    break # Exit outer loop once we have the response

        # Parse the JSON response from agents
        if final_response is None:
            raise HTTPException(status_code=500, detail="No response received from agent.")
        
        # Clean up Markdown code block if it exists
        # This handles responses like: ```json\n{ ... }\n```
        cleaned_response = re.sub(r"^```(?:json)?\n|```$", "", final_response.strip(), flags=re.IGNORECASE)
        print(f"cleaned resp : {cleaned_response}, {type(cleaned_response)}")
        
        # # Loading the cleaned JSON
        # try:
        #     response_data = json.loads(cleaned_response)
        # except json.JSONDecodeError:
        #     raise HTTPException(status_code=500, detail=f"Agent response is not valid JSON. Response was: {cleaned_response}")
        
        # Return the structured response using your Pydantic model
        return PreAuthResponse(
            req_id = unique_id,
            status="yes",
            # suggested_response=response_data.get("suggested_response", "")
            message=cleaned_response
        )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process agent query: {e}")
        
# Include the router in the FastAPI app
app.include_router(router, prefix="/api", tags=["Process Pre Auth Request"])