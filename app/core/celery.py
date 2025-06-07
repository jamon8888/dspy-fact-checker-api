"""
Celery configuration and task management for the DSPy-Enhanced Fact-Checker API Platform.
"""

import os
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from celery import Celery, Task
from celery.signals import worker_ready, worker_shutting_down, task_prerun, task_postrun
from kombu import Queue

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "fact_checker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_processing",
        "app.tasks.fact_checking",
        "app.tasks.maintenance",
        "app.tasks.monitoring"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.document_processing.*": {"queue": "document_processing"},
        "app.tasks.fact_checking.*": {"queue": "fact_checking"},
        "app.tasks.maintenance.*": {"queue": "maintenance"},
        "app.tasks.monitoring.*": {"queue": "monitoring"},
    },
    
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("document_processing", routing_key="document_processing"),
        Queue("fact_checking", routing_key="fact_checking"),
        Queue("maintenance", routing_key="maintenance"),
        Queue("monitoring", routing_key="monitoring"),
        Queue("high_priority", routing_key="high_priority"),
    ),
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Monitoring
    worker_hijack_root_logger=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.tasks.maintenance.cleanup_expired_sessions",
            "schedule": timedelta(hours=1),
        },
        "cleanup-old-results": {
            "task": "app.tasks.maintenance.cleanup_old_results",
            "schedule": timedelta(hours=6),
        },
        "system-health-check": {
            "task": "app.tasks.monitoring.system_health_check",
            "schedule": timedelta(minutes=5),
        },
        "database-maintenance": {
            "task": "app.tasks.maintenance.database_maintenance",
            "schedule": timedelta(days=1),
        },
    },
    beat_schedule_filename="celerybeat-schedule",
)


class CallbackTask(Task):
    """Base task class with callbacks and error handling."""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called when task succeeds."""
        logger.info(f"Task {self.name}[{task_id}] succeeded: {retval}")
    
    def on_failure(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: dict, 
        einfo: Any
    ) -> None:
        """Called when task fails."""
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        
        # Store failure information for monitoring
        from app.core.redis import cache
        import asyncio
        
        try:
            failure_info = {
                "task_name": self.name,
                "task_id": task_id,
                "error": str(exc),
                "args": args,
                "kwargs": kwargs,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Use asyncio to run async cache operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                cache.set(f"task_failure:{task_id}", failure_info, ttl=86400)
            )
            loop.close()
            
        except Exception as e:
            logger.error(f"Failed to store task failure info: {e}")
    
    def on_retry(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: dict, 
        einfo: Any
    ) -> None:
        """Called when task is retried."""
        logger.warning(f"Task {self.name}[{task_id}] retry: {exc}")


# Set default task base class
celery_app.Task = CallbackTask


class TaskManager:
    """Task management utilities."""
    
    @staticmethod
    def get_task_info(task_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a task."""
        try:
            result = celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result,
                "traceback": result.traceback,
                "date_done": result.date_done,
                "successful": result.successful(),
                "failed": result.failed(),
            }
        except Exception as e:
            logger.error(f"Failed to get task info for {task_id}: {e}")
            return None
    
    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """Cancel a running task."""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    @staticmethod
    def get_active_tasks() -> List[Dict[str, Any]]:
        """Get list of active tasks."""
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            
            if active_tasks:
                all_tasks = []
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        task["worker"] = worker
                        all_tasks.append(task)
                return all_tasks
            return []
            
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return []
    
    @staticmethod
    def get_worker_stats() -> Dict[str, Any]:
        """Get worker statistics."""
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            return stats or {}
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {}
    
    @staticmethod
    def get_queue_lengths() -> Dict[str, int]:
        """Get queue lengths."""
        try:
            inspect = celery_app.control.inspect()
            
            # Get reserved tasks (being processed)
            reserved = inspect.reserved()
            
            # Get scheduled tasks
            scheduled = inspect.scheduled()
            
            # Get active tasks
            active = inspect.active()
            
            queue_info = {}
            
            # Count tasks by queue
            for worker_data in [reserved, scheduled, active]:
                if worker_data:
                    for worker, tasks in worker_data.items():
                        for task in tasks:
                            queue = task.get("delivery_info", {}).get("routing_key", "default")
                            queue_info[queue] = queue_info.get(queue, 0) + 1
            
            return queue_info
            
        except Exception as e:
            logger.error(f"Failed to get queue lengths: {e}")
            return {}


class TaskPriority:
    """Task priority levels."""
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 15


def create_task_with_priority(
    func: callable,
    priority: int = TaskPriority.NORMAL,
    queue: str = "default",
    **kwargs
) -> Any:
    """Create a task with specific priority and queue."""
    return func.apply_async(
        queue=queue,
        priority=priority,
        **kwargs
    )


# Celery signals
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Called when worker is ready."""
    logger.info(f"Celery worker {sender} is ready")


@worker_shutting_down.connect
def worker_shutting_down_handler(sender=None, **kwargs):
    """Called when worker is shutting down."""
    logger.info(f"Celery worker {sender} is shutting down")


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Called before task execution."""
    logger.debug(f"Starting task {task.name}[{task_id}]")


@task_postrun.connect
def task_postrun_handler(
    sender=None, 
    task_id=None, 
    task=None, 
    args=None, 
    kwargs=None, 
    retval=None, 
    state=None, 
    **kwds
):
    """Called after task execution."""
    logger.debug(f"Finished task {task.name}[{task_id}] with state {state}")


# Health check function
async def check_celery_health() -> Dict[str, Any]:
    """Check Celery health status."""
    try:
        # Check if broker is accessible
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            active_workers = len(stats)
            total_tasks = sum(
                worker_stats.get("total", {}).values() 
                for worker_stats in stats.values()
            )
            
            return {
                "status": "healthy",
                "active_workers": active_workers,
                "total_tasks_processed": total_tasks,
                "broker_url": settings.CELERY_BROKER_URL,
                "backend_url": settings.CELERY_RESULT_BACKEND,
            }
        else:
            return {
                "status": "unhealthy",
                "error": "No active workers found",
                "broker_url": settings.CELERY_BROKER_URL,
                "backend_url": settings.CELERY_RESULT_BACKEND,
            }
            
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "broker_url": settings.CELERY_BROKER_URL,
            "backend_url": settings.CELERY_RESULT_BACKEND,
        }


# Global task manager instance
task_manager = TaskManager()


# FastAPI dependency
def get_task_manager() -> TaskManager:
    """FastAPI dependency for task manager."""
    return task_manager
