from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    Float,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResponseStatus(str, enum.Enum):
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"


class LogType(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    domain = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    categories = relationship("Category", back_populates="user")
    documents = relationship("Document", back_populates="user")
    mailbox_configs = relationship("MailboxConfig", back_populates="user")
    emails = relationship("Email", back_populates="user")
    auto_reply_rules = relationship("AutoReplyRule", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    tone = Column(String, default="professional")
    template = Column(Text)
    custom_prompt = Column(Text)
    color = Column(String, default="bg-blue-500")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="categories")
    document_categories = relationship("DocumentCategory", back_populates="category")
    emails = relationship("Email", back_populates="category")
    auto_reply_rule_categories = relationship(
        "AutoReplyRuleCategory", back_populates="category"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    size = Column(Integer)
    content = Column(Text)
    content_preview = Column(Text)
    processing_status = Column(Enum(EmailStatus), default=EmailStatus.PENDING)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    document_metadata = Column(JSON)

    user = relationship("User", back_populates="documents")
    document_categories = relationship("DocumentCategory", back_populates="document")


class DocumentCategory(Base):
    __tablename__ = "document_categories"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    document = relationship("Document", back_populates="document_categories")
    category = relationship("Category", back_populates="document_categories")


class MailboxConfig(Base):
    __tablename__ = "mailbox_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    app_password = Column(String, nullable=False)
    auto_reply_emails = Column(JSON)
    confidence_threshold = Column(Float, default=0.8)
    enabled = Column(Boolean, default=True)
    connection_status = Column(String, default="disconnected")
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="mailbox_configs")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    from_email = Column(String, nullable=False)
    from_name = Column(String)
    to_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text)
    html_body = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False)
    priority = Column(String, default="normal")
    labels = Column(JSON)
    thread_id = Column(String)
    ai_analysis = Column(JSON)

    user = relationship("User", back_populates="emails")
    category = relationship("Category", back_populates="emails")
    attachments = relationship("EmailAttachment", back_populates="email")
    ai_responses = relationship("AIResponse", back_populates="email")


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    name = Column(String, nullable=False)
    size = Column(Integer)
    type = Column(String)
    file_path = Column(String)

    email = relationship("Email", back_populates="attachments")


class AIResponse(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    suggestion = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    tone = Column(String, default="professional")
    reasoning = Column(Text)
    alternative_suggestions = Column(JSON)
    used_documents = Column(JSON)
    processing_time_ms = Column(Integer)
    status = Column(Enum(ResponseStatus), default=ResponseStatus.GENERATED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    edited_content = Column(Text)
    rejection_reason = Column(String)
    rejection_feedback = Column(Text)

    email = relationship("Email", back_populates="ai_responses")


class AutoReplyRule(Base):
    __tablename__ = "auto_reply_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_address = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    confidence_threshold = Column(Float, default=0.8)
    keywords = Column(JSON)
    schedule = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="auto_reply_rules")
    auto_reply_rule_categories = relationship(
        "AutoReplyRuleCategory", back_populates="auto_reply_rule"
    )


class AutoReplyRuleCategory(Base):
    __tablename__ = "auto_reply_rule_categories"

    id = Column(Integer, primary_key=True, index=True)
    auto_reply_rule_id = Column(Integer, ForeignKey("auto_reply_rules.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    auto_reply_rule = relationship(
        "AutoReplyRule", back_populates="auto_reply_rule_categories"
    )
    category = relationship("Category", back_populates="auto_reply_rule_categories")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(Enum(LogType), nullable=False)
    email = Column(String)
    subject = Column(String)
    confidence = Column(Float)
    action = Column(String, nullable=False)
    category = Column(String)
    response_time_ms = Column(Integer)
    user_action = Column(String)
    log_metadata = Column(JSON)

    user = relationship("User", back_populates="activity_logs")


class SentEmail(Base):
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True, index=True)
    original_email_id = Column(Integer, ForeignKey("emails.id"))
    message_id = Column(String)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="sent")
    recipients = Column(JSON)
    delivery_status = Column(String, default="pending")
    content = Column(Text)
    html_content = Column(Text)


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)
    secret = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
