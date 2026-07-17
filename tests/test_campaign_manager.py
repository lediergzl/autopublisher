"""
Tests para CampaignManager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.execution.manager import CampaignManager
from app.execution.models import ExecutionState, CampaignExecutionTask
from app.execution.exceptions import (
    InvalidStateTransitionException,
    ExecutionNotFoundException,
)


@pytest.fixture
def mock_repository():
    """Mock de repository."""
    return AsyncMock()


@pytest.fixture
def mock_queue_backend():
    """Mock de queue backend."""
    return AsyncMock()


@pytest.fixture
def campaign_manager(mock_repository, mock_queue_backend):
    """Fixture de CampaignManager."""
    return CampaignManager(mock_repository, mock_queue_backend)


@pytest.mark.asyncio
async def test_create_execution(campaign_manager, mock_repository):
    """Tests creación de ejecución."""
    # Arrange
    mock_repository.create_execution = AsyncMock()
    tasks = [
        CampaignExecutionTask(
            task_id="t-1",
            execution_id="exec-1",
            campaign_id=42,
            user_id=5,
            community_id=10,
            content_id=1,
            recipient_id="123456",
            content="Test",
        )
    ]

    # Act
    execution_id = await campaign_manager.create_execution(
        campaign_id=42,
        user_id=5,
        tasks=tasks,
    )

    # Assert
    assert execution_id is not None
    assert len(execution_id) > 0
    mock_repository.create_execution.assert_called_once()


@pytest.mark.asyncio
async def test_start_execution(campaign_manager, mock_repository):
    """Tests inicio de ejecución."""
    # Arrange
    execution_id = "exec-123"
    campaign_manager._executions_state[execution_id] = ExecutionState.PENDING
    mock_repository.update_execution_state = AsyncMock()

    # Act
    await campaign_manager.start_execution(execution_id)

    # Assert
    assert campaign_manager._executions_state[execution_id] == ExecutionState.PROCESSING
    mock_repository.update_execution_state.assert_called_once()


@pytest.mark.asyncio
async def test_start_execution_invalid_state(campaign_manager):
    """Tests que no se puede iniciar en estado incorrecto."""
    # Arrange
    execution_id = "exec-123"
    campaign_manager._executions_state[execution_id] = ExecutionState.COMPLETED

    # Act & Assert
    with pytest.raises(InvalidStateTransitionException):
        await campaign_manager.start_execution(execution_id)


@pytest.mark.asyncio
async def test_pause_execution(campaign_manager, mock_repository):
    """Tests pausa de ejecución."""
    # Arrange
    execution_id = "exec-123"
    campaign_manager._executions_state[execution_id] = ExecutionState.PROCESSING
    mock_repository.update_execution_state = AsyncMock()

    # Act
    await campaign_manager.pause_execution(execution_id)

    # Assert
    assert campaign_manager._executions_state[execution_id] == ExecutionState.PAUSED


@pytest.mark.asyncio
async def test_execution_not_found(campaign_manager):
    """Tests que se lanza excepción si no existe ejecución."""
    with pytest.raises(ExecutionNotFoundException):
        await campaign_manager.get_execution_state("nonexistent")
