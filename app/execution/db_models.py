"""
Database models for campaign execution auditing.

Stores execution state, task logs, and audit trails in PostgreSQL.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class ExecutionStateEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStateEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class CampaignExecution(Base):
    """
    Stores execution metadata and status.
    
    One row per campaign publication attempt.
    """
    __tablename__ = "campaign_executions"
    
    id = Column(String(36), primary_key=True)  # UUID
    campaign_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(SQLEnum(ExecutionStateEnum), default=ExecutionStateEnum.PENDING)
    
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)  # milliseconds
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    metadata = Column(JSON, default={})


class TaskAuditLog(Base):
    """
    Stores individual task execution details.
    
    One row per task within a campaign execution.
    """
    __tablename__ = "task_audit_logs"
    
    id = Column(String(36), primary_key=True)  # UUID
    execution_id = Column(String(36), ForeignKey("campaign_executions.id"), nullable=False, index=True)
    task_id = Column(String(36), nullable=False, index=True)
    
    campaign_id = Column(Integer, nullable=False)
    community_id = Column(Integer, nullable=False)
    
    status = Column(SQLEnum(TaskStateEnum), default=TaskStateEnum.PENDING)
    message_id = Column(String(255), nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    
    retry_count = Column(Integer, default=0)
    errors = Column(JSON, default=[])  # List of error objects
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
