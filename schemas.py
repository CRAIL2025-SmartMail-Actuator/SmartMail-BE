from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import UserRole, EmailStatus, LogType


# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    domain: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    domain: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    tone: str = "professional"
    template: Optional[str] = None
    custom_prompt: Optional[str] = None
    color: str = "bg-blue-500"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Document Schemas
class DocumentBase(BaseModel):
    name: str
    type: str
    size: Optional[int] = None


class DocumentUpload(BaseModel):
    categories: List[str] = []


class DocumentResponse(DocumentBase):
    id: int
    processing_status: EmailStatus
    upload_date: datetime
    categories: List[str] = []
    content_preview: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentContent(BaseModel):
    id: int
    name: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


# Email Schemas
class EmailBase(BaseModel):
    from_email: str = Field(..., alias="from")
    from_name: Optional[str] = None
    to_email: str = Field(..., alias="to")
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailResponse(EmailBase):
    id: int
    timestamp: datetime
    is_read: bool = False
    is_starred: bool = False
    has_attachments: bool = False
    priority: str = "normal"
    category: Optional[str] = None
    labels: List[str] = []
    thread_id: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class EmailList(BaseModel):
    emails: List[EmailResponse]
    pagination: Dict[str, Any]


# AI Response Schemas
class AIResponseRequest(BaseModel):
    email_id: int
    context: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class AIResponseData(BaseModel):
    response_id: str
    suggestion: str
    confidence: float
    category: str
    tone: str
    reasoning: str
    alternative_suggestions: List[Dict[str, Any]] = []
    used_documents: List[str] = []
    processing_time_ms: int


class AIResponseResponse(BaseModel):
    success: bool
    data: AIResponseData


# Auto Reply Schemas
class AutoReplyRuleBase(BaseModel):
    email_address: str
    enabled: bool = True
    categories: List[str] = []
    confidence_threshold: float = 0.8
    keywords: List[str] = []
    schedule: Optional[Dict[str, Any]] = None


class AutoReplyRuleCreate(AutoReplyRuleBase):
    pass


class AutoReplyRuleResponse(AutoReplyRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Mailbox Config Schemas
class MailboxConfigBase(BaseModel):
    email: str
    app_password: str
    auto_reply_emails: List[str] = []
    confidence_threshold: float = 0.8
    enabled: bool = True


class MailboxConfigCreate(MailboxConfigBase):
    pass


class MailboxConnectionTest(BaseModel):
    email: str
    app_password: str


class MailboxConfigResponse(BaseModel):
    id: int
    email: str
    connection_status: str
    last_sync: Optional[datetime]
    auto_reply_emails: List[str]
    confidence_threshold: float
    enabled: bool

    class Config:
        from_attributes = True


# Activity Log Schemas
class ActivityLogResponse(BaseModel):
    id: int
    timestamp: datetime
    type: LogType
    email: Optional[str]
    subject: Optional[str]
    confidence: Optional[float]
    action: str
    category: Optional[str]
    response_time_ms: Optional[int]
    user_action: Optional[str]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ActivityLogList(BaseModel):
    logs: List[ActivityLogResponse]
    pagination: Dict[str, Any]


# Analytics Schemas
class AnalyticsSummary(BaseModel):
    total_emails: int
    ai_responses_generated: int
    auto_sent: int
    manually_approved: int
    success_rate: float
    average_confidence: float
    average_response_time_ms: int


class AnalyticsTrend(BaseModel):
    date: str
    emails_received: int
    responses_sent: int
    success_rate: float


class CategoryBreakdown(BaseModel):
    category: str
    count: int
    success_rate: float
    average_confidence: float


class ConfidenceDistribution(BaseModel):
    high: int
    medium: int
    low: int


class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    trends: List[AnalyticsTrend]
    category_breakdown: List[CategoryBreakdown]
    confidence_distribution: ConfidenceDistribution


# Standard API Response
class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class ReplyData(BaseModel):
    to: Optional[EmailStr] = None
    subject: str
    body: str
