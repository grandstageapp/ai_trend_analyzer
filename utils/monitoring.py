"""
Task monitoring and recovery mechanisms
"""
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"

@dataclass
class TaskMetrics:
    task_id: str
    task_type: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    posts_processed: int = 0
    trends_created: int = 0
    error_message: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat() if self.start_time else None
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        return data

class TaskMonitor:
    """Monitor and track background task execution"""
    
    def __init__(self, log_file: str = "task_monitor.log"):
        self.log_file = Path(log_file)
        self.current_tasks: Dict[str, TaskMetrics] = {}
        
    def start_task(self, task_id: str, task_type: str, correlation_id: str) -> TaskMetrics:
        """Start monitoring a task"""
        metrics = TaskMetrics(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.RUNNING,
            start_time=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        self.current_tasks[task_id] = metrics
        self._log_task_event(metrics, "Task started")
        
        logger.info(f"[{correlation_id}] Started monitoring task {task_id} ({task_type})")
        return metrics
    
    def complete_task(self, task_id: str, posts_processed: int = 0, trends_created: int = 0):
        """Mark task as completed"""
        if task_id not in self.current_tasks:
            logger.warning(f"Task {task_id} not found in current tasks")
            return
        
        metrics = self.current_tasks[task_id]
        metrics.status = TaskStatus.COMPLETED
        metrics.end_time = datetime.utcnow()
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.posts_processed = posts_processed
        metrics.trends_created = trends_created
        
        self._log_task_event(metrics, "Task completed successfully")
        self._archive_task(task_id)
        
        logger.info(f"[{metrics.correlation_id}] Task {task_id} completed in {metrics.duration_seconds:.2f}s")
    
    def fail_task(self, task_id: str, error_message: str):
        """Mark task as failed"""
        if task_id not in self.current_tasks:
            logger.warning(f"Task {task_id} not found in current tasks")
            return
        
        metrics = self.current_tasks[task_id]
        metrics.status = TaskStatus.FAILED
        metrics.end_time = datetime.utcnow()
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.error_message = error_message
        
        self._log_task_event(metrics, f"Task failed: {error_message}")
        self._archive_task(task_id)
        
        logger.error(f"[{metrics.correlation_id}] Task {task_id} failed after {metrics.duration_seconds:.2f}s: {error_message}")
    
    def get_task_status(self, task_id: str) -> Optional[TaskMetrics]:
        """Get current status of a task"""
        return self.current_tasks.get(task_id)
    
    def get_running_tasks(self) -> Dict[str, TaskMetrics]:
        """Get all currently running tasks"""
        return {k: v for k, v in self.current_tasks.items() if v.status == TaskStatus.RUNNING}
    
    def cleanup_stale_tasks(self, max_age_hours: int = 24):
        """Clean up tasks that have been running too long"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale_tasks = []
        
        for task_id, metrics in self.current_tasks.items():
            if metrics.start_time < cutoff_time and metrics.status == TaskStatus.RUNNING:
                stale_tasks.append(task_id)
        
        for task_id in stale_tasks:
            self.fail_task(task_id, f"Task exceeded maximum runtime of {max_age_hours} hours")
            logger.warning(f"Cleaned up stale task: {task_id}")
        
        return len(stale_tasks)
    
    def _log_task_event(self, metrics: TaskMetrics, event: str):
        """Log task event to file"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event,
                "task_metrics": metrics.to_dict()
            }
            
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to log task event: {e}")
    
    def _archive_task(self, task_id: str):
        """Move task from current to archived"""
        if task_id in self.current_tasks:
            del self.current_tasks[task_id]

# Global task monitor instance
task_monitor = TaskMonitor()