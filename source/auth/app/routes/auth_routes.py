from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse
import app.schemas.auth_schema
from app.services.auth_service import register_user, login_user
from app.services.jwt_service import verify_token

security = HTTPBearer()
router = APIRouter()


@router.post("/register")
def register(data: RegisterRequest):

    try:
        user_id = register_user(
            data.first_name,
            data.last_name,
            data.email,
            data.password
        )
        return {"user_id": user_id}

    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):

    token = login_user(data.email, data.password)

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {"access_token": token}


@router.get("/me")
def get_me(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

@router.put("/me")
def update_me(data: app.schemas.auth_schema.UpdateProfileRequest, credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    from app.services.auth_service import update_user_profile
    try:
        relogin_required = update_user_profile(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password=data.password
        )
        return {"status": "success", "relogin_required": relogin_required}
    except Exception as e:
        if str(e) == "Email already exists":
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=500, detail=str(e))