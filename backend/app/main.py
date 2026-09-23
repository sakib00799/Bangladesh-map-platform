import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.geocoding import router as geocoding_router
from app.api.map_config import router as map_config_router
from app.api.nearby import router as nearby_router

app = FastAPI(title="Bangladesh Map Platform API", version="0.1.0")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(geocoding_router)
app.include_router(nearby_router)
app.include_router(map_config_router)


def error_payload(
    code: str,
    message: str,
    details: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in item["loc"] if part != "query"),
            "message": item["msg"],
            "type": item["type"],
        }
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_payload(
            "VALIDATION_ERROR",
            "Request validation failed.",
            details,
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, error: StarletteHTTPException
) -> JSONResponse:
    codes = {
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    message = error.detail if isinstance(error.detail, str) else "Request failed."
    return JSONResponse(
        status_code=error.status_code,
        content=error_payload(codes.get(error.status_code, "HTTP_ERROR"), message),
        headers=error.headers,
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_payload(
            "INTERNAL_ERROR",
            "An unexpected server error occurred.",
        ),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
