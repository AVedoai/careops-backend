from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.form import (
    PublicFormResponse, FormSubmissionCreate, CustomFormSubmissionResponse
)
from app.services.form_builder_service import FormBuilderService

router = APIRouter()
form_service = FormBuilderService()

@router.get("/forms/{share_link}", response_model=PublicFormResponse)
async def get_public_form(
    share_link: str,
    db: Session = Depends(get_db)
):
    """Get form by public share link (no authentication required)"""
    share_link = f"/f/{share_link}"  # Ensure proper format
    return await form_service.get_public_form(db, share_link)

@router.post("/forms/{share_link}/submit", response_model=CustomFormSubmissionResponse)
async def submit_form(
    share_link: str,
    submission_data: FormSubmissionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit form response (no authentication required)"""
    share_link = f"/f/{share_link}"  # Ensure proper format
    
    # Get client IP and user agent for tracking
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await form_service.submit_form(
        db, share_link, submission_data, ip_address, user_agent
    )

@router.get("/forms/{share_link}/track")
async def track_form_view(
    share_link: str,
    db: Session = Depends(get_db)
):
    """Track form view for analytics (called when form loads)"""
    share_link = f"/f/{share_link}"
    
    # This endpoint just increments the view count
    # The actual increment happens in get_public_form
    return {"tracked": True}

# Form validation endpoint (optional - for real-time validation)
@router.post("/forms/{share_link}/validate")
async def validate_form_field(
    share_link: str,
    field_data: dict,  # {field_id: value}
    db: Session = Depends(get_db)
):
    """Validate specific form field (for real-time validation)"""
    share_link = f"/f/{share_link}"
    
    # Get form to access validation rules
    try:
        form = await form_service.get_public_form(db, share_link)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Validate field against form rules
    errors = {}
    for field_id, value in field_data.items():
        # Find field in form
        field_config = None
        for field in form.fields:
            if field["id"] == field_id:
                field_config = field
                break
        
        if not field_config:
            continue
        
        # Validate required fields
        if field_config.get("required", False) and not value:
            errors[field_id] = "This field is required"
        
        # Validate field-specific rules
        validation_rules = field_config.get("validation", [])
        for rule in validation_rules:
            if rule["type"] == "min" and len(str(value)) < rule["value"]:
                errors[field_id] = rule["message"]
            elif rule["type"] == "max" and len(str(value)) > rule["value"]:
                errors[field_id] = rule["message"]
            elif rule["type"] == "pattern":
                import re
                if not re.match(rule["value"], str(value)):
                    errors[field_id] = rule["message"]
    
    return {"valid": len(errors) == 0, "errors": errors}

# Embed endpoint (for iframe embedding)
@router.get("/forms/{share_link}/embed")
async def get_embed_form(
    share_link: str,
    db: Session = Depends(get_db)
):
    """Get embeddable form HTML (for iframe)"""
    share_link = f"/f/{share_link}"
    
    form = await form_service.get_public_form(db, share_link)
    
    # Return minimal HTML for embedding
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{form.name}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .form-container {{ max-width: 600px; margin: 0 auto; }}
            .form-field {{ margin-bottom: 20px; }}
            .form-label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .form-input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
            .form-button {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }}
            .form-button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="form-container">
            <h2>{form.name}</h2>
            {f'<p>{form.description}</p>' if form.description else ''}
            <form id="embedded-form" action="/api/public/forms/{share_link.split('/')[-1]}/submit" method="POST">
                <!-- Form fields will be rendered here dynamically -->
            </form>
        </div>
        <script>
            // Add JavaScript for form rendering and submission
            // This is a basic example - you'd implement full form rendering
            document.getElementById('embedded-form').innerHTML = '<p>Form will be rendered here</p>';
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)