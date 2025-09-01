import json
import os
from datetime import datetime

from jsonschema import validate, ValidationError
from fastapi import APIRouter, HTTPException

from db.config.connection import get_db
from db.models.dbmodels.requestProgress import RequestStatus
from db.models.requestModels.validationRequest import ValidationRequest
from db.models.requestModels.jsonValidatorRequest import JsonValidatorRequest
from db.models.responseModels.jsonValidatorResponse import JsonValidatorResponse
from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum

router = APIRouter()

def load_validation_rules():
    """Load validation rules from all_rules.json"""
    try:
        rules_path = os.path.join(os.path.dirname(__file__), '..', 'rulesets', 'all_rules.json')
        with open(rules_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load validation rules: {str(e)}")

def get_payer_id_from_json(json_data):
    """Extract payer ID from JSON data"""
    try:
        if isinstance(json_data, dict) and 'response' in json_data:
            if isinstance(json_data['response'], list) and len(json_data['response']) > 0:
                return json_data['response'][0].get('payerid')
    except Exception:
        pass
    return None

@router.post("/validate-json")
async def validate_json_payload(req: JsonValidatorRequest):
    """
    Endpoint to validate JSON payload against payer-specific rules.
    This API is called after the planner-agent API and after JSON is fetched using get_patientdetails.
    """
    try:
        # Load validation rules
        all_rules = load_validation_rules()
        
        # Extract payer ID from the JSON data
        payer_id = get_payer_id_from_json(req.json_data)
        
        if not payer_id:
            return JsonValidatorResponse(
                is_valid=False,
                http_status=HttpResponseEnum.BAD_REQUEST,
                error_message="Unable to extract payer ID from JSON data"
            )
        
        # Check if we have validation rules for this payer
        if payer_id not in all_rules:
            return JsonValidatorResponse(
                is_valid=False,
                http_status=HttpResponseEnum.BAD_REQUEST,
                error_message=f"No validation rules found for payer ID: {payer_id}"
            )
        
        # Get the validation schema for this payer
        payer_schema = all_rules[payer_id]
        
        # Validate the JSON data against the schema
        try:
            validate(instance=req.json_data, schema=payer_schema)
            
            # If validation passes
            return JsonValidatorResponse(
                is_valid=True,
                http_status=HttpResponseEnum.OK,
                error_message=None
            )
            
        except ValidationError as ve:
            # If validation fails
            return JsonValidatorResponse(
                is_valid=False,
                http_status=HttpResponseEnum.BAD_REQUEST,
                error_message=f"JSON validation failed: {ve.message}"
            )
    
    except Exception as e:
        # Handle any other exceptions
        return JsonValidatorResponse(
            is_valid=False,
            http_status=HttpResponseEnum.INTERNAL_SERVER_ERROR,
            error_message=f"Internal server error during validation: {str(e)}"
        )

@router.post("/payers/{payer_id}/validate")
async def validate_payer(req:ValidationRequest):

    db = get_db()
    try:

        payer = await db.collections("priorAuthPayers").find_one({"id": req.payer_id})
        if payer:
            await db["requestProgress"].update_one(
                {"requestId": req.request_id},
                {
                    "$set": {
                        "status": RequestStatus.VALIDATED,
                        "lastUpdatedAt": datetime.now(),
                        "remarks": "Payer info reterived successfully"
                    }
                }
            )
            return {"status": HttpResponseEnum.OK, "message": "Payer validated successfully"}
        else:
            return {"status": HttpResponseEnum.NOT_FOUND, "message": "Payer not found"}
    except Exception as e:
        await db["requestProgress"].update_one(
            {"requestId": req.request_id},
            {
                "$set": {
                    "status": RequestStatus.FAILED,
                    "lastUpdatedAt": datetime.now(),
                    "remarks": str(e)
                }
            }
        )
        return {"status": HttpResponseEnum.INTERNAL_SERVER_ERROR, "message": str(e)}
