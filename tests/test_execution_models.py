"""
Tests para modelos de ejecución.
"""

import pytest
from datetime import datetime
from app.execution.models import (
    ExecutionState,
    TaskState,
    TaskAuditLog,
    ExecutionAuditLog,
    CampaignExecutionTask,
)


class TestExecutionState:
    """Tests para ExecutionState enum."""

    def test_states_exist(self):
        """Verifica que todos los estados existen."""
        assert hasattr(ExecutionState, 'PENDING')
        assert hasattr(ExecutionState, 'PROCESSING')
        assert hasattr(ExecutionState, 'COMPLETED')
        assert hasattr(ExecutionState, 'FAILED')


class TestTaskState:
    """Tests para TaskState enum."""

    def test_states_exist(self):
        """Verifica que todos los estados existen."""
        assert hasattr(TaskState, 'PENDING')
        assert hasattr(TaskState, 'PROCESSING')
        assert hasattr(TaskState, 'COMPLETED')
        assert hasattr(TaskState, 'FAILED')


class TestTaskAuditLog:
    """Tests para TaskAuditLog."""

    def test_creation(self):
        """Verifica creación de log de tarea."""
        log = TaskAuditLog(
            task_id="task-1",
            campaign_id=42,
            community_id=10,
            status="completed",
        )
        assert log.task_id == "task-1"
        assert log.campaign_id == 42
        assert log.community_id == 10
        assert log.status == "completed"

    def test_to_dict(self):
        """Verifica serialización a dict."""
        log = TaskAuditLog(
            task_id="task-1",
            campaign_id=42,
            community_id=10,
            started_at=datetime.utcnow(),
            status="completed",
        )
        data = log.to_dict()
        assert data["task_id"] == "task-1"
        assert "started_at" in data
        assert isinstance(data["started_at"], str)


class TestCampaignExecutionTask:
    """Tests para CampaignExecutionTask."""

    def test_creation(self):
        """Verifica creación de tarea."""
        task = CampaignExecutionTask(
            task_id="t-1",
            execution_id="exec-1",
            campaign_id=42,
            user_id=5,
            community_id=10,
            content_id=1,
            recipient_id="123456",
            content="Test message",
        )
        assert task.task_id == "t-1"
        assert task.campaign_id == 42
        assert task.content == "Test message"

    def test_to_dict(self):
        """Verifica serialización."""
        task = CampaignExecutionTask(
            task_id="t-1",
            execution_id="exec-1",
            campaign_id=42,
            user_id=5,
            community_id=10,
            content_id=1,
            recipient_id="123456",
            content="Test message",
        )
        data = task.to_dict()
        assert data["task_id"] == "t-1"
        assert data["content"] == "Test message"

    def test_from_dict(self):
        """Verifica deserialización."""
        data = {
            "task_id": "t-1",
            "execution_id": "exec-1",
            "campaign_id": 42,
            "user_id": 5,
            "community_id": 10,
            "content_id": 1,
            "recipient_id": "123456",
            "content": "Test message",
        }
        task = CampaignExecutionTask.from_dict(data)
        assert task.task_id == "t-1"
        assert task.campaign_id == 42
