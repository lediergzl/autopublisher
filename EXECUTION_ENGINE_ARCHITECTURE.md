# Campaign Execution Engine Architecture

## Visión General

El **Campaign Execution Engine** es un módulo desacoplado y modular para ejecutar campañas de publicación en múltiples comunidades de forma independiente, confiable y auditable.

## Principios Arquitectónicos

### 1. **Desacoplamiento**
- El motor de ejecución NO conoce detalles específicos de Telegram
- Se comunica con plataformas via interfaz abstracta `MessageTransport`
- Permite múltiples implementaciones: Telegram, WhatsApp, Email, etc.

### 2. **SOLID**
- **S**ingle Responsibility: Cada clase tiene una responsabilidad única
- **O**pen/Closed: Extensible sin modificar código existente
- **L**iskov Substitution: Interfaces intercambiables
- **I**nterface Segregation: Interfaces mínimas y focalizadas
- **D**ependency Inversion: Depende de abstracciones, no de implementaciones

### 3. **Independencia de Componentes**
- Workers independientes: Pueden ejecutarse en procesos separados
- Colas desacopladas: Cambiar Redis por RabbitMQ sin afectar la lógica
- Transporte pluggable: Nuevos transportes sin modificar manager

## Arquitectura de Colas

```
┌─────────────────────┐
│  CampaignManager    │
│  (Orquestador)      │
└──────────┬──────────┘
           │ Encola tareas
           ▼
┌─────────────────────┐
│  Redis Queue        │
│  (Persistencia)     │
└──────────┬──────────┘
           │ Desencola
           ▼
┌─────────────────────┐
│  Worker 1           │
│  (Procesa tareas)   │
└──────────┬──────────┘
           │ Envía mensaje
           ▼
┌─────────────────────┐
│  MessageTransport   │
│  (Interfaz)         │
└──────────┬──────────┘
           │ Implementación
           ▼
┌─────────────────────┐
│  TelegramTransport  │
│  WhatsAppTransport  │
│  EmailTransport     │
└─────────────────────┘
```

## Módulos

### 1. **app/execution/**
**Núcleo del motor de ejecución**

#### `interfaces.py`
Define contratos abstractos:
- `MessageTransport`: Interface para envío de mensajes
- `ExecutionRepository`: Interface para persistencia
- `QueueBackend`: Interface para colas

#### `manager.py`
Orquestador central:
- `CampaignManager`: Gestiona ciclo de vida de ejecuciones
  - Crear ejecución
  - Iniciar/Pausar/Reanudar/Cancelar
  - Registrar auditoría
  - Controlar estados

#### `models.py`
Estructuras de datos:
- `ExecutionState`: Estados globales (PENDING, PROCESSING, COMPLETED, etc.)
- `TaskState`: Estados de tareas (PENDING, PROCESSING, COMPLETED, FAILED, RETRY)
- `CampaignExecutionTask`: Payload de una tarea
- `ExecutionAuditLog`: Registro de auditoría completo
- `TaskAuditLog`: Registro de auditoría por tarea

#### `exceptions.py`
Excepciones personalizadas:
- `ExecutionEngineException`: Base
- `TransportException`: Errores de transporte
- `TaskProcessingException`: Errores procesando tareas
- `InvalidStateTransitionException`: Transiciones inválidas

### 2. **app/queue/**
**Gestión de colas de trabajo**

#### `manager.py`
- `QueueManager`: Capa de abstracción sobre backend

#### `redis_backend.py`
- `RedisQueueBackend`: Implementación con Redis
  - Almacena tareas como JSON
  - Tracking de estado: pendiente, procesando, completada, fallida
  - Reintentos automáticos
  - Persistencia

### 3. **app/workers/**
**Procesadores independientes de tareas**

#### `task_processor.py`
- `TaskProcessor`: Procesa una tarea
  - Deserializa
  - Valida
  - Marca como procesando
  - Invoca transporte
  - Registra resultado
  - Maneja errores y reintentos

#### `worker.py`
- `Worker`: Proceso que ejecuta tasks
  - Polling a la cola
  - Concurrencia configurable
  - Ciclo de vida (start/stop)
  - Espera a tareas activas al detener

### 4. **app/transports/**
**Implementaciones concretas de transporte**

#### `base.py`
- `BaseMessageTransport`: Clase base para transportes
  - Validaciones comunes
  - Métodos helper

Ejemplos de implementación:
```python
class TelegramTransport(BaseMessageTransport):
    async def send(self, recipient_id, content, metadata=None):
        # Lógica específica de Telegram
        pass

class EmailTransport(BaseMessageTransport):
    async def send(self, recipient_id, content, metadata=None):
        # Lógica específica de Email
        pass
```

## Flujo de Ejecución

### Crear y ejecutar una campaña

```python
# 1. Crear ejecución
execution_id = await campaign_manager.create_execution(
    campaign_id=42,
    user_id=5,
    tasks=[
        CampaignExecutionTask(
            task_id="task-1",
            execution_id="exec-1",
            campaign_id=42,
            user_id=5,
            community_id=10,
            content_id=1,
            recipient_id="123456",
            content="Mensaje a comunidad 1",
        ),
        CampaignExecutionTask(
            task_id="task-2",
            execution_id="exec-1",
            campaign_id=42,
            user_id=5,
            community_id=11,
            content_id=1,
            recipient_id="654321",
            content="Mensaje a comunidad 2",
        ),
    ]
)

# 2. Encolar tareas
for task in tasks:
    await campaign_manager.enqueue_task(execution_id, task)

# 3. Iniciar ejecución
await campaign_manager.start_execution(execution_id)

# 4. Worker procesa tareas
worker = Worker(queue_manager, campaign_manager, task_processor)
await worker.start(execution_id, queue_name)

# 5. Usuario puede pausar/reanudar/cancelar
await campaign_manager.pause_execution(execution_id)
await campaign_manager.resume_execution(execution_id)
await campaign_manager.cancel_execution(execution_id)

# 6. Obtener auditoría
audit_log = await campaign_manager.get_audit_log(execution_id)
print(audit_log.to_dict())
```

## Estados y Transiciones

### Estados de Ejecución
```
PENDING
   ↓
PROCESSING ← → PAUSED
   ↓
┌──────────────────┐
├─ COMPLETED       │
├─ PARTIAL_FAILURE │
├─ FAILED          │
└──────────────────┘

CANCELLED (desde cualquier estado)
```

### Estados de Tarea
```
PENDING
   ↓
PROCESSING
   ├─ COMPLETED
   ├─ FAILED → RETRY → PENDING
   └─ FAILED (permanente)
```

## Auditoría

Cada ejecución registra:

### Auditoría de Ejecución
```json
{
  "execution_id": "exec-789",
  "campaign_id": 42,
  "user_id": 5,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:30Z",
  "duration_ms": 330000,
  "total_tasks": 10,
  "completed_tasks": 9,
  "failed_tasks": 1,
  "status": "partial_failure",
  "task_logs": [...]
}
```

### Auditoría de Tarea
```json
{
  "task_id": "task-123",
  "campaign_id": 42,
  "community_id": 10,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:05Z",
  "duration_ms": 5000,
  "status": "completed",
  "message_id": "msg-456",
  "retry_count": 0,
  "errors": []
}
```

## Manejo de Errores

### Estrategia de Reintentos
1. Tarea falla
2. Se registra error
3. Se incrementa `retry_count`
4. Si `retry_count < max_retries` (default 3): Se reencola
5. Si `retry_count >= max_retries`: Se marca como fallida permanente

### Tipos de Excepción
- `TransportException`: Error al enviar mensaje → Reintenta
- `TaskProcessingException`: Error en validación → Falla permanente
- `CampaignExecutionException`: Error en ejecución → Falla permanente

## Inyección de Dependencias

Todos los componentes reciben sus dependencias via constructor:

```python
# Crear instancias
repository = DatabaseExecutionRepository(db_session)
queue_backend = RedisQueueBackend(redis_url)
queue_manager = QueueManager(queue_backend)
campaign_manager = CampaignManager(repository, queue_backend)

telegram_transport = TelegramTransport(client)
task_processor = TaskProcessor(queue_manager, campaign_manager, telegram_transport)

worker = Worker(queue_manager, campaign_manager, task_processor, concurrency=4)
```

## Testabilidad

Todos los componentes son testables:

```python
# Mocks
mock_repository = AsyncMock(spec=ExecutionRepository)
mock_queue = AsyncMock(spec=QueueBackend)
mock_transport = AsyncMock(spec=MessageTransport)

# Inyectar mocks
manager = CampaignManager(mock_repository, mock_queue)
processor = TaskProcessor(mock_queue, manager, mock_transport)

# Tests
await manager.create_execution(...)
# Verificar calls
mock_repository.create_execution.assert_called_once()
```

## Extensibilidad

### Agregar nuevo transporte

```python
# 1. Implementar MessageTransport
class WhatsAppTransport(BaseMessageTransport):
    async def send(self, recipient_id, content, metadata=None):
        # Implementar lógica específica
        pass
    
    async def validate(self):
        # Validar configuración
        pass

# 2. Inyectar en TaskProcessor
whatsapp_transport = WhatsAppTransport(client)
task_processor = TaskProcessor(queue_manager, campaign_manager, whatsapp_transport)

# 3. No requiere cambios en CampaignManager
```

### Cambiar backend de cola

```python
# Cambiar de Redis a RabbitMQ
class RabbitMQQueueBackend(QueueBackend):
    # Implementar interface
    pass

queue_backend = RabbitMQQueueBackend(rabbitmq_url)
queue_manager = QueueManager(queue_backend)

# El resto del código no cambia
```

## Configuración

### Variables de entorno
```
REDIS_URL=redis://localhost:6379
MAX_RETRIES=3
WORKER_CONCURRENCY=4
TASK_TIMEOUT_SECONDS=30
```

### Configuración de Worker
```python
worker = Worker(
    queue_manager=queue_manager,
    campaign_manager=campaign_manager,
    task_processor=task_processor,
    concurrency=4,           # Tareas simultáneas
    poll_interval_seconds=1, # Intervalo de polling
)
```

## Performance

- **Throughput**: Limitado por velocidad del transporte
- **Latencia**: < 1s por tarea (sin red)
- **Escalabilidad**: Múltiples workers independientes
- **Persistencia**: Redis como buffer

## Seguridad

- ✅ Validación de integridad de tareas
- ✅ Auditoría completa de cada operación
- ✅ Timeout configurable por tarea
- ✅ Manejo de excepciones granular
- ✅ Aislamiento entre ejecuciones

## Ejemplo Completo

Ver `/examples/campaign_execution_example.py` para implementación completa.
