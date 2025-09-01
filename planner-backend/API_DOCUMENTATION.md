# Preauth Agent API Documentation

## Overview
This API system provides comprehensive REST endpoints for handling preauthorization requests with automated processing and user interaction workflows.

## Base URL
```
http://host.docker.internal:8001
```

## API Endpoints

### 1. Preauth Management APIs

#### POST `/api/preauth/initiate`
**Main endpoint to initiate preauthorization process**

**Request Body:**
```json
{
  "user_id": "string",
  "payer_id": "string", 
  "patient_id": "string",
  "patient_name": "string",
  "prompt": "string"
}
```

**Response:**
```json
{
  "request_id": "string",
  "status": "string",
  "message": "string",
  "http_status": "enum"
}
```

**Workflow:**
1. Validates payer onboarding status
2. Fetches patient details from external systems
3. Validates JSON against payer-specific rules
4. Triggers N8N webhook if validation passes
5. Creates user action records if additional info needed

#### GET `/api/preauth/status/{request_id}`
**Get current status of preauth request**

**Response:**
```json
{
  "request_id": "string",
  "status": "string",
  "last_updated": "datetime",
  "remarks": "string",
  "http_status": "enum"
}
```

#### GET `/api/preauth/user-actions/{request_id}`
**Get user actions required for a specific request**

**Response:**
```json
{
  "request_id": "string",
  "user_actions": [
    {
      "id": "string",
      "actionType": "string",
      "actionStatus": "string",
      "requestedAt": "datetime",
      "metadata": "string"
    }
  ],
  "http_status": "enum"
}
```

#### POST `/api/preauth/user-action/{request_id}`
**Submit user action response (additional information)**

**Request Body:**
```json
{
  "field_name": "value",
  "additional_info": "string"
}
```

### 2. N8N Callback APIs

#### POST `/api/n8n/callback`
**Callback endpoint for N8N to send updates back to the system**

**Request Body:**
```json
{
  "request_id": "string",
  "status": "string",
  "action_type": "string",
  "message": "string",
  "metadata": {},
  "screenshot_url": "string",
  "user_action_required": true,
  "workflow_step": "string"
}
```

#### POST `/api/n8n/workflow-status/{request_id}`
**Update workflow status with detailed information**

#### POST `/api/n8n/screenshot/{request_id}`
**Save screenshot URLs or data from N8N**

#### GET `/api/n8n/workflow-info/{request_id}`
**Get information about a specific workflow/request**

#### POST `/api/n8n/complete/{request_id}`
**Mark a workflow as completed**

### 3. Dashboard APIs

#### GET `/api/dashboard/stats`
**Get dashboard statistics**

**Query Parameters:**
- `days` (optional): Number of days to look back (default: 7)

**Response:**
```json
{
  "total_requests": 100,
  "pending_requests": 15,
  "completed_requests": 70,
  "failed_requests": 10,
  "user_action_required": 5,
  "success_rate": 75.5
}
```

#### GET `/api/dashboard/requests`
**Get recent preauth requests with summary information**

**Query Parameters:**
- `limit` (optional): Number of requests to return (default: 20)
- `status` (optional): Filter by status
- `user_id` (optional): Filter by user ID

**Response:**
```json
[
  {
    "request_id": "string",
    "patient_name": "string",
    "payer_id": "string",
    "status": "string",
    "created_at": "datetime",
    "last_updated": "datetime",
    "current_step": "string",
    "user_actions_pending": 0
  }
]
```

#### GET `/api/dashboard/user-actions`
**Get pending user actions that require attention**

#### GET `/api/dashboard/request-details/{request_id}`
**Get detailed information about a specific request**

#### GET `/api/dashboard/payer-stats`
**Get statistics grouped by payer**

#### POST `/api/dashboard/mark-action-completed/{action_id}`
**Mark a user action as completed from the dashboard**

### 4. Payer Management APIs

#### GET `/api/payers/{payer_id}`
**Retrieve payer information and validate onboarding**

**Query Parameters:**
- `request_id`: Request ID for validation

### 5. Validation APIs

#### POST `/api/validate-json`
**Validate JSON payload against payer-specific rules**

### 6. System APIs

#### GET `/health`
**Health check endpoint**

#### GET `/`
**Root endpoint with API information**

## Status Codes

### Request Status Enum
- `CREATED`: Request created
- `PROCESSING`: Being processed
- `IN_PROGRESS`: Workflow in progress
- `USER_ACTION_REQUIRED`: Waiting for user input
- `COMPLETED`: Successfully completed
- `FAILED`: Failed

### User Action Types
- `INFO_REQUIRED`: Additional information needed
- `SCREENSHOT_CAPTURE`: Screenshot captured
- `WORKFLOW_COMPLETED`: Workflow completed

## Environment Variables

```bash
# Database Configuration
MONGODB_URL=mongodb://host.docker.internal:27017
DATABASE_NAME=preauth_db

# External Services
N8N_WEBHOOK_URL=http://n8n-instance/webhook/preauth
AGENT_URL=http://agent-service/process
PATIENT_API_URL=http://patient-service/api
BASE_URL=http://host.docker.internal:8001

# Authentication (if needed)
API_KEY=your-api-key
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Usage Examples

### 1. Initiate Preauth Request

```bash
curl -X POST "http://host.docker.internal:8001/api/preauth/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "payer_id": "PAYER001", 
    "patient_id": "PAT456",
    "patient_name": "John Doe",
    "prompt": "Request preauth for MRI scan"
  }'
```

### 2. Check Request Status

```bash
curl -X GET "http://host.docker.internal:8001/api/preauth/status/abc123"
```

### 3. Get Dashboard Stats

```bash
curl -X GET "http://host.docker.internal:8001/api/dashboard/stats?days=30"
```

### 4. N8N Callback Example

```bash
curl -X POST "http://host.docker.internal:8001/api/n8n/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "abc123",
    "status": "waiting_for_user",
    "action_type": "FORM_FILL_REQUIRED",
    "message": "Need additional patient information",
    "user_action_required": true,
    "workflow_step": "form_validation"
  }'
```

## Frontend Integration

The dashboard APIs are designed to be consumed by a frontend dashboard application. Key features:

1. **Real-time Updates**: Poll status endpoints for live updates
2. **User Action Management**: Handle user input requirements
3. **Progress Tracking**: Visual workflow progress
4. **Statistics Dashboard**: Analytics and reporting

## Database Collections

### Core Collections:
- `requestProgress`: Track request status and progress
- `priorAuthRequest`: Store original preauth requests
- `priorAuthUserAction`: Track user actions and responses
- `priorAuthPayers`: Onboarded payer information
- `conversationHistory`: Chat/interaction history

### Sample Documents:

**requestProgress:**
```json
{
  "requestId": "abc123",
  "status": "IN_PROGRESS",
  "lastUpdatedAt": "2025-01-01T10:00:00Z",
  "remarks": "Processing patient validation",
  "workflowStep": "patient_data_fetch",
  "metadata": {}
}
```

**priorAuthRequest:**
```json
{
  "requestId": "abc123",
  "userId": "user123",
  "patientId": "PAT456",
  "patientName": "John Doe",
  "payerId": "PAYER001",
  "createdAt": "2025-01-01T09:00:00Z",
  "lastUpdatedAt": "2025-01-01T10:00:00Z"
}
```

This API system provides a complete solution for managing preauthorization workflows with real-time updates, user interaction handling, and comprehensive dashboard functionality.
