"""
System Metrics

Comprehensive system performance tracking and monitoring for the fact-checking platform.
"""

import logging
import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.database import get_db
from app.models.user import User
from app.models.subscription import UsageRecord

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None


@dataclass
class SystemHealthStatus:
    """System health status."""
    status: str  # healthy, warning, critical
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_connections: int
    error_rate: float
    timestamp: datetime


class MetricsCollector:
    """Collects various system and application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.logger = logging.getLogger(__name__ + ".MetricsCollector")
        self.metrics_buffer = deque(maxlen=10000)
        self.latency_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            memory_total = memory.total
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free
            disk_total = disk.total
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'usage_percent': memory_percent,
                    'available_bytes': memory_available,
                    'total_bytes': memory_total,
                    'used_bytes': memory_total - memory_available
                },
                'disk': {
                    'usage_percent': disk_percent,
                    'free_bytes': disk_free,
                    'total_bytes': disk_total,
                    'used_bytes': disk_total - disk_free
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics."""
        try:
            db = next(get_db())
            
            try:
                # API metrics
                api_metrics = await self._collect_api_metrics(db)
                
                # Processing metrics
                processing_metrics = await self._collect_processing_metrics(db)
                
                # User metrics
                user_metrics = await self._collect_user_metrics(db)
                
                # Error metrics
                error_metrics = await self._collect_error_metrics()
                
                return {
                    'api': api_metrics,
                    'processing': processing_metrics,
                    'users': user_metrics,
                    'errors': error_metrics
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
            return {}
    
    async def _collect_api_metrics(self, db: Session) -> Dict[str, Any]:
        """Collect API performance metrics."""
        try:
            # Get recent usage records
            recent_usage = db.query(UsageRecord).filter(
                UsageRecord.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            # Calculate metrics
            total_requests = len(recent_usage)
            avg_processing_time = 0
            if recent_usage:
                processing_times = [r.processing_time for r in recent_usage if r.processing_time]
                if processing_times:
                    avg_processing_time = sum(processing_times) / len(processing_times)
            
            # Calculate latency percentiles
            latency_p50 = self._calculate_percentile(self.latency_buffer['api'], 50)
            latency_p95 = self._calculate_percentile(self.latency_buffer['api'], 95)
            latency_p99 = self._calculate_percentile(self.latency_buffer['api'], 99)
            
            return {
                'requests_per_hour': total_requests,
                'avg_processing_time': float(avg_processing_time) if avg_processing_time else 0.0,
                'latency': {
                    'p50': latency_p50,
                    'p95': latency_p95,
                    'p99': latency_p99
                },
                'throughput': total_requests / 3600 if total_requests > 0 else 0  # requests per second
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting API metrics: {e}")
            return {}
    
    async def _collect_processing_metrics(self, db: Session) -> Dict[str, Any]:
        """Collect document processing metrics."""
        try:
            # Get processing times by type
            recent_usage = db.query(UsageRecord).filter(
                UsageRecord.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            processing_by_type = defaultdict(list)
            for record in recent_usage:
                if record.processing_time:
                    processing_by_type[record.usage_type].append(float(record.processing_time))
            
            metrics = {}
            for usage_type, times in processing_by_type.items():
                if times:
                    metrics[f'{usage_type}_avg_time'] = sum(times) / len(times)
                    metrics[f'{usage_type}_min_time'] = min(times)
                    metrics[f'{usage_type}_max_time'] = max(times)
                    metrics[f'{usage_type}_count'] = len(times)
                else:
                    metrics[f'{usage_type}_avg_time'] = 0.0
                    metrics[f'{usage_type}_count'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting processing metrics: {e}")
            return {}
    
    async def _collect_user_metrics(self, db: Session) -> Dict[str, Any]:
        """Collect user activity metrics."""
        try:
            # Active users in last 24 hours
            active_users_24h = db.query(User).filter(
                User.last_login >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Active users in last hour
            active_users_1h = db.query(User).filter(
                User.last_login >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            # Total registered users
            total_users = db.query(User).count()
            
            # Users with recent activity
            recent_activity = db.query(UsageRecord.user_id).filter(
                UsageRecord.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).distinct().count()
            
            return {
                'active_users_24h': active_users_24h,
                'active_users_1h': active_users_1h,
                'total_users': total_users,
                'users_with_recent_activity': recent_activity
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting user metrics: {e}")
            return {}
    
    async def _collect_error_metrics(self) -> Dict[str, Any]:
        """Collect error rate metrics."""
        try:
            total_requests = sum(self.request_counts.values())
            total_errors = sum(self.error_counts.values())
            
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'total_errors': total_errors,
                'error_rate_percent': error_rate,
                'error_breakdown': dict(self.error_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting error metrics: {e}")
            return {}
    
    def record_request_latency(self, endpoint: str, latency: float):
        """Record request latency for an endpoint."""
        self.latency_buffer[endpoint].append(latency)
        self.latency_buffer['api'].append(latency)
        self.request_counts[endpoint] += 1
    
    def record_error(self, endpoint: str, error_type: str):
        """Record an error occurrence."""
        self.error_counts[f"{endpoint}:{error_type}"] += 1
        self.error_counts['total'] += 1
    
    def _calculate_percentile(self, values: deque, percentile: int) -> float:
        """Calculate percentile from values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]


class AlertingSystem:
    """System for monitoring metrics and triggering alerts."""
    
    def __init__(self):
        """Initialize alerting system."""
        self.logger = logging.getLogger(__name__ + ".AlertingSystem")
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'error_rate': 5.0,
            'latency_p95': 5000.0,  # 5 seconds
            'latency_p99': 10000.0  # 10 seconds
        }
        self.alert_history = deque(maxlen=1000)
    
    async def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against thresholds and generate alerts."""
        alerts = []
        
        try:
            # System resource alerts
            system_metrics = metrics.get('system', {})
            
            # CPU alert
            cpu_usage = system_metrics.get('cpu', {}).get('usage_percent', 0)
            if cpu_usage > self.alert_thresholds['cpu_usage']:
                alerts.append(self._create_alert(
                    'high_cpu_usage',
                    f"CPU usage is {cpu_usage:.1f}%",
                    'warning' if cpu_usage < 90 else 'critical',
                    {'cpu_usage': cpu_usage}
                ))
            
            # Memory alert
            memory_usage = system_metrics.get('memory', {}).get('usage_percent', 0)
            if memory_usage > self.alert_thresholds['memory_usage']:
                alerts.append(self._create_alert(
                    'high_memory_usage',
                    f"Memory usage is {memory_usage:.1f}%",
                    'warning' if memory_usage < 95 else 'critical',
                    {'memory_usage': memory_usage}
                ))
            
            # Disk alert
            disk_usage = system_metrics.get('disk', {}).get('usage_percent', 0)
            if disk_usage > self.alert_thresholds['disk_usage']:
                alerts.append(self._create_alert(
                    'high_disk_usage',
                    f"Disk usage is {disk_usage:.1f}%",
                    'warning' if disk_usage < 95 else 'critical',
                    {'disk_usage': disk_usage}
                ))
            
            # Application alerts
            app_metrics = metrics.get('application', {})
            
            # Error rate alert
            error_rate = app_metrics.get('errors', {}).get('error_rate_percent', 0)
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append(self._create_alert(
                    'high_error_rate',
                    f"Error rate is {error_rate:.1f}%",
                    'warning' if error_rate < 10 else 'critical',
                    {'error_rate': error_rate}
                ))
            
            # Latency alerts
            api_metrics = app_metrics.get('api', {})
            latency = api_metrics.get('latency', {})
            
            p95_latency = latency.get('p95', 0)
            if p95_latency > self.alert_thresholds['latency_p95']:
                alerts.append(self._create_alert(
                    'high_latency_p95',
                    f"95th percentile latency is {p95_latency:.0f}ms",
                    'warning',
                    {'latency_p95': p95_latency}
                ))
            
            p99_latency = latency.get('p99', 0)
            if p99_latency > self.alert_thresholds['latency_p99']:
                alerts.append(self._create_alert(
                    'high_latency_p99',
                    f"99th percentile latency is {p99_latency:.0f}ms",
                    'critical',
                    {'latency_p99': p99_latency}
                ))
            
            # Store alerts in history
            for alert in alerts:
                self.alert_history.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
            return []
    
    def _create_alert(self, alert_type: str, message: str, severity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert object."""
        return {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification."""
        try:
            # Log the alert
            self.logger.warning(f"ALERT [{alert['severity'].upper()}]: {alert['message']}")
            
            # TODO: Integrate with notification services (Slack, email, PagerDuty, etc.)
            # For now, just log
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")


class SystemMetrics:
    """Main system metrics class for comprehensive monitoring."""
    
    def __init__(self):
        """Initialize system metrics."""
        self.logger = logging.getLogger(__name__ + ".SystemMetrics")
        self.metrics_collector = MetricsCollector()
        self.alerting_system = AlertingSystem()
        self.last_collection_time = None
        
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all system and application metrics."""
        try:
            start_time = time.time()
            
            # Collect system metrics
            system_metrics = await self.metrics_collector.collect_system_metrics()
            
            # Collect application metrics
            application_metrics = await self.metrics_collector.collect_application_metrics()
            
            collection_time = time.time() - start_time
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'collection_time_seconds': collection_time,
                'system': system_metrics,
                'application': application_metrics
            }
            
            self.last_collection_time = datetime.utcnow()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return {}
    
    async def get_system_health(self) -> SystemHealthStatus:
        """Get overall system health status."""
        try:
            metrics = await self.collect_all_metrics()
            
            system_metrics = metrics.get('system', {})
            app_metrics = metrics.get('application', {})
            
            # Extract key health indicators
            cpu_usage = system_metrics.get('cpu', {}).get('usage_percent', 0)
            memory_usage = system_metrics.get('memory', {}).get('usage_percent', 0)
            disk_usage = system_metrics.get('disk', {}).get('usage_percent', 0)
            error_rate = app_metrics.get('errors', {}).get('error_rate_percent', 0)
            
            # Calculate network latency (simplified)
            network_latency = app_metrics.get('api', {}).get('latency', {}).get('p95', 0)
            
            # Determine overall health status
            if (cpu_usage > 90 or memory_usage > 95 or disk_usage > 95 or error_rate > 10):
                status = 'critical'
            elif (cpu_usage > 80 or memory_usage > 85 or disk_usage > 90 or error_rate > 5):
                status = 'warning'
            else:
                status = 'healthy'
            
            return SystemHealthStatus(
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_latency=network_latency,
                active_connections=app_metrics.get('users', {}).get('active_users_1h', 0),
                error_rate=error_rate,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return SystemHealthStatus(
                status='unknown',
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                network_latency=0,
                active_connections=0,
                error_rate=0,
                timestamp=datetime.utcnow()
            )
    
    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle."""
        try:
            # Collect metrics
            metrics = await self.collect_all_metrics()
            
            # Check for alerts
            alerts = await self.alerting_system.check_alerts(metrics)
            
            # Send alerts if any
            for alert in alerts:
                await self.alerting_system.send_alert(alert)
            
            # Log summary
            self.logger.info(f"Monitoring cycle completed. Collected {len(metrics)} metric groups, {len(alerts)} alerts generated")
            
            return {
                'metrics': metrics,
                'alerts': alerts,
                'health_status': await self.get_system_health()
            }
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
            return {}


# Global system metrics instance
system_metrics = SystemMetrics()
