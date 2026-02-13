from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.websockets.manager import socket_app
from app.api.v1 import (
    auth,
    workspaces,
    onboarding,
    contacts,
    conversations,
    bookings,
    services,
    forms,
    form_builder,
    public_forms,
    inventory,
    integrations,
    alerts,
    public
)
from app.utils.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ValidationException
)

app = FastAPI(
    title="CareOps API",
    description="Unified operations platform for service-based businesses",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )

@app.exception_handler(ForbiddenException)
async def forbidden_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)}
    )

@app.exception_handler(NotFoundException)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

@app.exception_handler(ValidationException)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CareOps API", 
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["contacts"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(forms.router, prefix="/api/v1/forms", tags=["forms-legacy"])  # Legacy document forms
app.include_router(form_builder.router, prefix="/api/v1/form-builder", tags=["form-builder"])  # New form builder
app.include_router(public_forms.router, prefix="/api/public", tags=["public-forms"])  # Public form submissions
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(public.router, prefix="/api/v1/public", tags=["public"])

# Mount Socket.IO
app.mount("/socket.io", socket_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)