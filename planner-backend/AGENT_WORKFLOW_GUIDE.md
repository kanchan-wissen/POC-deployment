# Agent Tools Workflow Documentation

## Overview
This document explains how the Planner Agent should use the API tools to handle preauthorization requests.

## Complete Workflow for Agent

### 1. Initial Request Processing
When a user submits a prompt with payer_id and patient_id:

```
User Input: "Please process preauth for patient PAT123 with Aetna (PAYER001) for MRI scan"
```

**Agent extracts:**
- patient_id: PAT123  
- payer_id: PAYER001
- prompt: "Please process preauth for patient PAT123 with Aetna (PAYER001) for MRI scan"

### 2. Tool Usage Sequence

#### Step 1: Start New Request
```http
POST /api/tools/start-request
{
  "user_id": "extracted_or_provided_user_id",
  "prompt": "Please process preauth for patient PAT123 with Aetna (PAYER001) for MRI scan"
}
```
**Response:** `{"request_id": "abc123", "status": "CREATED"}`

#### Step 2: Check Payer Onboarding
```http
GET /api/tools/check-payer/PAYER001?request_id=abc123
```
**Response:** `{"is_onboarded": true, "payer_details": {...}}`

**If payer not onboarded:** Stop workflow and inform user

#### Step 3: Get Patient Details
```http
POST /api/tools/get-patient-details
{
  "patient_id": "PAT123",
  "request_id": "abc123"
}
```
**Response:** `{"patient_data": {...}, "success": true}`

#### Step 4: Validate JSON
```http
POST /api/tools/validate-json
{
  "patient_data": {...},
  "payer_id": "PAYER001", 
  "request_id": "abc123"
}
```

**If validation fails:**
- Response: `{"is_valid": false, "missing_fields": ["field1", "field2"]}`
- Status becomes "USER_ACTION_REQUIRED"
- Agent should inform user about missing information
- Wait for user to provide additional info via dashboard

**If validation passes:** Continue to next step

#### Step 5: Trigger N8N Workflow
```http
POST /api/tools/trigger-n8n
{
  "request_id": "abc123",
  "user_id": "user123", 
  "patient_id": "PAT123",
  "patient_name": "John Doe",
  "payer_id": "PAYER001",
  "prompt": "original_prompt",
  "validated_json": {...}
}
```
**Response:** `{"workflow_triggered": true, "workflow_id": "n8n_exec_123"}`

#### Step 6: Monitor Progress (Optional)
```http
GET /api/tools/request-status/abc123
```
**Response:** Current status and any pending user actions

## N8N Workflow Integration

### When N8N Needs User Action
N8N calls this endpoint when human interaction is required:

```http
POST /api/n8n/action-required
{
  "requestId": "abc123",
  "payerId": "PAYER001",
  "status": "action_required",
  "message": "Need additional patient insurance information",
  "action_required": true,
  "action_type": "INSURANCE_INFO_REQUIRED",
  "action_details": {
    "required_fields": ["secondary_insurance", "group_number"],
    "form_url": "https://forms.example.com/insurance-info"
  },
  "screenshot_url": "https://storage.example.com/screenshot123.png"
}
```

This will:
1. Update request status to "USER_ACTION_REQUIRED"
2. Create a user action record in database
3. Frontend dashboard will show this to the user

### When User Completes Action
User submits required information through dashboard, which calls:

```http
POST /api/tools/handle-user-action
{
  "request_id": "abc123",
  "action_id": "action_456", 
  "response_data": {
    "secondary_insurance": "Blue Cross",
    "group_number": "GRP789"
  }
}
```

This will:
1. Mark user action as completed
2. Update request status to "PROCESSING"
3. Optionally resume N8N workflow

## Agent Decision Logic

### Handling Validation Failures
```python
validation_result = call_validate_json_tool(patient_data, payer_id, request_id)

if not validation_result["is_valid"]:
    missing_fields = validation_result["missing_fields"]
    
    agent_response = f"""
    Additional information is required to process your preauth request:
    
    Missing fields: {', '.join(missing_fields)}
    
    Please provide this information through your dashboard. 
    I'll continue processing once you've submitted the required details.
    """
    
    # Wait for user action completion
    while True:
        status = call_request_status_tool(request_id)
        if status["status"] == "PROCESSING":
            # User completed action, continue workflow
            break
        elif status["user_actions_pending"] > 0:
            # Still waiting for user
            time.sleep(30)  # Poll every 30 seconds
        else:
            break
```

### Handling N8N Workflow Pauses
```python
# After triggering N8N workflow
workflow_result = call_trigger_n8n_tool(...)

if workflow_result["workflow_triggered"]:
    agent_response = "Your preauth request is being processed. I'll monitor the progress and let you know if any actions are needed."
    
    # Monitor workflow progress
    while True:
        status = call_request_status_tool(request_id)
        
        if status["status"] == "COMPLETED":
            agent_response = "Great! Your preauth request has been completed successfully."
            break
        elif status["status"] == "USER_ACTION_REQUIRED":
            user_actions = call_user_actions_tool(request_id)
            agent_response = f"The workflow needs your attention. Please check your dashboard for required actions: {user_actions}"
            break
        elif status["status"] == "FAILED":
            agent_response = f"Unfortunately, the preauth process failed: {status['remarks']}"
            break
        
        time.sleep(60)  # Poll every minute
```

## Error Handling

### Common Error Scenarios

1. **Payer Not Onboarded**
```python
if not payer_check["is_onboarded"]:
    return f"Sorry, payer {payer_id} is not currently onboarded to our system. Please contact support."
```

2. **Patient Data Not Found**
```python
if not patient_details["success"]:
    return f"Unable to retrieve patient information for {patient_id}. Please verify the patient ID."
```

3. **N8N Workflow Failed**
```python
if not n8n_result["workflow_triggered"]:
    return f"Failed to start the automation workflow: {n8n_result['message']}"
```

## Dashboard Integration

### Frontend Polling
The frontend dashboard should poll these endpoints:

1. **Request Status**: `GET /api/dashboard/requests?user_id=USER123`
2. **User Actions**: `GET /api/dashboard/user-actions?user_id=USER123`
3. **Request Details**: `GET /api/dashboard/request-details/{request_id}`

### User Action Completion
When user completes an action on dashboard:

```http
POST /api/dashboard/mark-action-completed/{action_id}
{
  "metadata": "user_provided_data",
  "fields": {...}
}
```

## Example Complete Agent Flow

```python
async def process_preauth_request(user_input, user_id):
    # Extract information from user input
    extracted_info = extract_ids_from_prompt(user_input)
    
    # Step 1: Start request
    request = await call_start_request_tool(user_id, user_input)
    request_id = request["request_id"]
    
    # Step 2: Check payer
    payer_check = await call_check_payer_tool(extracted_info["payer_id"], request_id)
    if not payer_check["is_onboarded"]:
        return f"Payer {extracted_info['payer_id']} is not onboarded."
    
    # Step 3: Get patient details
    patient_details = await call_get_patient_details_tool(extracted_info["patient_id"], request_id)
    if not patient_details["success"]:
        return f"Could not retrieve patient data: {patient_details['message']}"
    
    # Step 4: Validate JSON
    validation = await call_validate_json_tool(
        patient_details["patient_data"], 
        extracted_info["payer_id"], 
        request_id
    )
    
    if not validation["is_valid"]:
        return f"Additional information needed: {validation['missing_fields']}"
    
    # Step 5: Trigger N8N
    n8n_result = await call_trigger_n8n_tool({
        "request_id": request_id,
        "user_id": user_id,
        "patient_id": extracted_info["patient_id"],
        "patient_name": patient_details["patient_data"]["patient_name"],
        "payer_id": extracted_info["payer_id"],
        "prompt": user_input,
        "validated_json": patient_details["patient_data"]
    })
    
    if n8n_result["workflow_triggered"]:
        return f"Your preauth request is being processed. Request ID: {request_id}"
    else:
        return f"Failed to start workflow: {n8n_result['message']}"
```

## Important Notes

1. **Request IDs**: Always pass request_id between tool calls to maintain context
2. **Error Handling**: Each tool call should be wrapped in try-catch blocks
3. **User Actions**: When status becomes "USER_ACTION_REQUIRED", the agent should inform the user and wait
4. **Polling**: Use reasonable polling intervals (30-60 seconds) to avoid overwhelming the API
5. **Status Transitions**: Monitor status changes to determine next actions

This tool-based approach allows the agent to maintain control over the workflow while using the APIs as individual, atomic operations.
