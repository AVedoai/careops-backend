from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums
class FormType(str, Enum):
    CUSTOM = "CUSTOM"
    DOCUMENT = "DOCUMENT"
    EXTERNAL_LINK = "EXTERNAL_LINK"

class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    TIME = "time"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    SIGNATURE = "signature"
    RATING = "rating"
    SECTION = "section"

class SubmissionStatus(str, Enum):
    NEW = "NEW"
    REVIEWED = "REVIEWED"
    CONTACTED = "CONTACTED"
    CONVERTED = "CONVERTED"

# Form Field Configuration
class ValidationRule(BaseModel):
    type: str  # min, max, pattern, custom
    value: Any
    message: str

class ConditionalRule(BaseModel):
    condition: str  # show, hide, require
    when: Dict[str, Any]  # {field: "field_id", operator: "equals", value: "some_value"}

class FormField(BaseModel):
    id: str
    type: FieldType
    label: str
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    required: bool = False
    validation: List[ValidationRule] = []
    options: List[str] = []  # For select, radio, checkbox
    conditional_logic: List[ConditionalRule] = []
    order: int
    properties: Dict[str, Any] = {}  # Additional field-specific properties

class FormSettings(BaseModel):
    notifications: Dict[str, Any] = {
        "email": False,
        "email_to": ""
    }
    redirect: Dict[str, Any] = {
        "enabled": False,
        "url": ""
    }
    thank_you_message: str = "Thank you for your submission!"
    allow_multiple_submissions: bool = False
    require_email: bool = False
    enable_captcha: bool = False
    expiry_date: Optional[datetime] = None

# Form Schemas
class FormBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: FormType = FormType.CUSTOM

class FormCreateCustom(FormBase):
    type: FormType = FormType.CUSTOM
    fields: List[FormField] = []
    settings: FormSettings = FormSettings()

class FormCreateExternal(FormBase):
    type: FormType = FormType.EXTERNAL_LINK
    external_url: str

class FormCreateDocument(FormBase):
    type: FormType = FormType.DOCUMENT
    # file will be uploaded separately

# Legacy schema for backward compatibility
class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    file_url: str

class FormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[List[FormField]] = None
    settings: Optional[FormSettings] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None

class FormResponse(BaseModel):
    id: int
    workspace_id: int
    created_by: Optional[int] = None
    name: str
    description: Optional[str] = None
    type: FormType
    file_url: Optional[str] = None
    external_url: Optional[str] = None
    fields: Optional[List[FormField]] = None
    settings: Optional[FormSettings] = None
    is_active: bool
    is_published: bool
    share_link: Optional[str] = None
    embed_code: Optional[str] = None
    views_count: int
    submissions_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class FormListResponse(BaseModel):
    forms: List[FormResponse]
    total: int
    page: int
    per_page: int

# Public Form (no sensitive data)
class PublicFormResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    fields: List[FormField]
    settings: FormSettings
    workspace_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Form Submission Schemas
class FormSubmissionCreate(BaseModel):
    submitted_data: Dict[str, Any]  # Field ID -> Value mapping
    submitter_email: Optional[str] = None
    submitter_name: Optional[str] = None
    submitter_phone: Optional[str] = None

class FormSubmissionUpdate(BaseModel):
    status: Optional[SubmissionStatus] = None
    notes: Optional[str] = None
    assigned_to: Optional[int] = None
    is_read: Optional[bool] = None

class FormSubmissionResponse(BaseModel):
    id: int
    booking_id: int
    form_id: int
    status: str
    submission_url: Optional[str] = None
    due_date: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CustomFormSubmissionResponse(BaseModel):
    id: int
    form_id: int
    workspace_id: int
    submitted_data: Dict[str, Any]
    submitter_email: Optional[str] = None
    submitter_name: Optional[str] = None
    submitter_phone: Optional[str] = None
    status: str
    is_read: bool
    notes: Optional[str] = None
    assigned_to: Optional[int] = None
    converted_to_booking_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    form_name: Optional[str] = None
    assigned_user_name: Optional[str] = None

    class Config:
        from_attributes = True

class FormSubmissionListResponse(BaseModel):
    submissions: List[CustomFormSubmissionResponse]
    total: int
    page: int
    per_page: int

# Analytics
class FormAnalytics(BaseModel):
    form_id: int
    views: int
    submissions: int
    completion_rate: float
    average_time: Optional[float] = None  # Average completion time in seconds
    top_exit_fields: List[str] = []  # Fields where users most commonly exit

class FormPerformanceResponse(BaseModel):
    total_forms: int
    total_submissions: int
    total_views: int
    average_completion_rate: float
    recent_submissions: List[CustomFormSubmissionResponse]