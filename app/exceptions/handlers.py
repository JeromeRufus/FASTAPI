from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.custom_exception import AppException


# =========================================================
# GLOBAL APPLICATION EXCEPTION HANDLER
# =========================================================

async def app_exception_handler(
    request: Request,
    exc: AppException
):

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.message,
            "path": request.url.path
        }
    )