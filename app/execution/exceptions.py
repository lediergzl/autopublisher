"""
Excepciones personalizadas del motor de ejecución.

Permite manejo granular de errores.
"""


class ExecutionEngineException(Exception):
    """
    Excepción base para el motor de ejecución.
    """
    pass


class TransportException(ExecutionEngineException):
    """
    Error en el transporte de mensajes.
    """
    pass


class TransportValidationException(TransportException):
    """
    Error en la validación del transporte.
    """
    pass


class TaskProcessingException(ExecutionEngineException):
    """
    Error procesando una tarea.
    """
    pass


class CampaignExecutionException(ExecutionEngineException):
    """
    Error en la ejecución de campaña.
    """
    pass


class InvalidStateTransitionException(ExecutionEngineException):
    """
    Transición de estado inválida.
    """
    pass


class QueueException(ExecutionEngineException):
    """
    Error en operaciones de cola.
    """
    pass


class ExecutionNotFoundException(ExecutionEngineException):
    """
    Ejecución no encontrada.
    """
    pass
