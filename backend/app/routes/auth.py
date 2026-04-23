from fastapi import APIRouter

router = APIRouter()

@router.get("/auth")
def register():
    return {"status": "ok",
            "message":"Registration endpoint is working"
    }