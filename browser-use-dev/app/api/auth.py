import os
import jwt
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# 🔐 JWT secret
JWT_SECRET = os.getenv("SECRET_KEY", "super-secret-key")
JWT_ALGORITHM = "HS256"

@router.post("/login")
async def login(request: Request):
    """
    Simple local login - generates JWT token for any request
    This is a simplified version without external OAuth
    """
    try:
        # For simplicity, we'll create a default user
        # In a real application, you would validate credentials here
        payload = {
            "email": "user@local.com",
            "name": "Local User",
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return JSONResponse({
            "success": True,
            "token": jwt_token,
            "message": "Login successful"
        })
    except Exception as e:
        print("Login error:", str(e))
        raise HTTPException(status_code=400, detail="Authentication failed")

@router.get("/me")
async def get_user_info(Authorization: str = Header(...)):
    """
    Return user info from JWT token
    """
    try:
        scheme, token = Authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError("Invalid token scheme")

        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"email": decoded.get("email"), "name": decoded.get("name")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

