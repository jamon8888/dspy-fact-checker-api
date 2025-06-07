"""
Monitoring Dashboard

Comprehensive monitoring dashboard for the fact-checking platform.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.monitoring.system_metrics import system_metrics
from app.monitoring.business_metrics import business_metrics
from app.monitoring.quality_assurance import quality_assurance
from app.monitoring.continuous_improvement import continuous_improvement

logger = logging.getLogger(__name__)


@dataclass
class DashboardData:
    """Complete dashboard data structure."""
    timestamp: datetime
    system_health: Dict[str, Any]
    key_metrics: Dict[str, Any]
    business_kpis: List[Dict[str, Any]]
    quality_status: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    improvement_opportunities: List[Dict[str, Any]]


class MonitoringDashboard:
    """Main monitoring dashboard class."""
    
    def __init__(self):
        """Initialize monitoring dashboard."""
        self.logger = logging.getLogger(__name__ + ".MonitoringDashboard")
        self.last_update = None
        self.cached_data = None
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
    
    async def get_dashboard_data(self, force_refresh: bool = False) -> DashboardData:
        """Get comprehensive dashboard data."""
        try:
            # Check cache
            if (not force_refresh and 
                self.cached_data and 
                self.last_update and 
                datetime.utcnow() - self.last_update < self.cache_duration):
                return self.cached_data
            
            self.logger.info("Refreshing dashboard data")
            
            # Collect all monitoring data in parallel
            tasks = [
                self._get_system_health(),
                self._get_key_metrics(),
                self._get_business_kpis(),
                self._get_quality_status(),
                self._get_active_alerts(),
                self._get_performance_trends(),
                self._get_improvement_opportunities()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract results (handle exceptions)
            system_health = results[0] if not isinstance(results[0], Exception) else {}
            key_metrics = results[1] if not isinstance(results[1], Exception) else {}
            business_kpis = results[2] if not isinstance(results[2], Exception) else []
            quality_status = results[3] if not isinstance(results[3], Exception) else {}
            alerts = results[4] if not isinstance(results[4], Exception) else []
            performance_trends = results[5] if not isinstance(results[5], Exception) else {}
            improvement_opportunities = results[6] if not isinstance(results[6], Exception) else []
            
            # Create dashboard data
            dashboard_data = DashboardData(
                timestamp=datetime.utcnow(),
                system_health=system_health,
                key_metrics=key_metrics,
                business_kpis=business_kpis,
                quality_status=quality_status,
                alerts=alerts,
                performance_trends=performance_trends,
                improvement_opportunities=improvement_opportunities
            )
            
            # Update cache
            self.cached_data = dashboard_data
            self.last_update = datetime.utcnow()
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            # Return empty dashboard data on error
            return DashboardData(
                timestamp=datetime.utcnow(),
                system_health={},
                key_metrics={},
                business_kpis=[],
                quality_status={},
                alerts=[],
                performance_trends={},
                improvement_opportunities=[]
            )
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            health_status = await system_metrics.get_system_health()
            
            return {
                'status': health_status.status,
                'cpu_usage': health_status.cpu_usage,
                'memory_usage': health_status.memory_usage,
                'disk_usage': health_status.disk_usage,
                'network_latency': health_status.network_latency,
                'active_connections': health_status.active_connections,
                'error_rate': health_status.error_rate,
                'timestamp': health_status.timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {}
    
    async def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key system metrics."""
        try:
            metrics = await system_metrics.collect_all_metrics()
            
            # Extract key metrics
            system_data = metrics.get('system', {})
            app_data = metrics.get('application', {})
            
            return {
                'requests_per_hour': app_data.get('api', {}).get('requests_per_hour', 0),
                'avg_response_time': app_data.get('api', {}).get('avg_processing_time', 0),
                'error_rate': app_data.get('errors', {}).get('error_rate_percent', 0),
                'active_users': app_data.get('users', {}).get('active_users_1h', 0),
                'cpu_usage': system_data.get('cpu', {}).get('usage_percent', 0),
                'memory_usage': system_data.get('memory', {}).get('usage_percent', 0),
                'disk_usage': system_data.get('disk', {}).get('usage_percent', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting key metrics: {e}")
            return {}
    
    async def _get_business_kpis(self) -> List[Dict[str, Any]]:
        """Get business KPIs."""
        try:
            dashboard_data = await business_metrics.generate_business_dashboard()
            kpis = dashboard_data.get('kpis', [])
            
            # Convert KPI objects to dictionaries
            kpi_list = []
            for kpi in kpis:
                kpi_list.append({
                    'name': kpi.name,
                    'value': kpi.value,
                    'unit': kpi.unit,
                    'change_percent': kpi.change_percent,
                    'target': kpi.target,
                    'status': kpi.status
                })
            
            return kpi_list
            
        except Exception as e:
            self.logger.error(f"Error getting business KPIs: {e}")
            return []
    
    async def _get_quality_status(self) -> Dict[str, Any]:
        """Get quality assurance status."""
        try:
            quality_report = await quality_assurance.continuous_quality_monitoring()
            
            return {
                'overall_score': quality_report.overall_quality_score,
                'overall_status': quality_report.overall_status.value,
                'accuracy_tests': len(quality_report.accuracy_results),
                'performance_tests': len(quality_report.performance_results),
                'regression_tests': len(quality_report.regression_results),
                'recommendations_count': len(quality_report.recommendations),
                'last_check': quality_report.timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting quality status: {e}")
            return {}
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts."""
        try:
            metrics = await system_metrics.collect_all_metrics()
            alerts = await system_metrics.alerting_system.check_alerts(metrics)
            
            # Sort alerts by severity
            severity_order = {'critical': 0, 'warning': 1, 'info': 2}
            alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'info'), 3))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends."""
        try:
            # Simulate performance trends
            # In practice, this would query historical data
            
            trends = {
                'response_time': {
                    'current': 320.5,
                    'trend': 'stable',
                    'change_percent': 1.7,
                    'sparkline': [315, 318, 322, 320, 325, 318, 320]  # Last 7 data points
                },
                'error_rate': {
                    'current': 2.1,
                    'trend': 'improving',
                    'change_percent': -8.7,
                    'sparkline': [2.8, 2.6, 2.4, 2.3, 2.2, 2.0, 2.1]
                },
                'throughput': {
                    'current': 150.2,
                    'trend': 'improving',
                    'change_percent': 3.0,
                    'sparkline': [145, 147, 148, 149, 151, 152, 150]
                },
                'user_satisfaction': {
                    'current': 4.2,
                    'trend': 'improving',
                    'change_percent': 2.4,
                    'sparkline': [4.0, 4.1, 4.1, 4.2, 4.3, 4.2, 4.2]
                }
            }
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting performance trends: {e}")
            return {}
    
    async def _get_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Get top improvement opportunities."""
        try:
            improvement_report = await continuous_improvement.run_improvement_cycle()
            
            # Get top 5 prioritized improvements
            opportunities = []
            for opp in improvement_report.prioritized_improvements[:5]:
                opportunities.append({
                    'id': opp.id,
                    'title': opp.title,
                    'category': opp.category.value,
                    'priority': opp.priority.value,
                    'impact_score': opp.impact_score,
                    'roi_estimate': opp.roi_estimate
                })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting improvement opportunities: {e}")
            return []
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary for quick overview."""
        try:
            dashboard_data = await self.get_dashboard_data()
            
            # Calculate summary statistics
            total_alerts = len(dashboard_data.alerts)
            critical_alerts = len([a for a in dashboard_data.alerts if a.get('severity') == 'critical'])
            
            system_status = dashboard_data.system_health.get('status', 'unknown')
            quality_score = dashboard_data.quality_status.get('overall_score', 0)
            
            # Get key metrics
            key_metrics = dashboard_data.key_metrics
            
            return {
                'timestamp': dashboard_data.timestamp.isoformat(),
                'system_status': system_status,
                'quality_score': quality_score,
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'key_metrics': {
                    'requests_per_hour': key_metrics.get('requests_per_hour', 0),
                    'avg_response_time': key_metrics.get('avg_response_time', 0),
                    'error_rate': key_metrics.get('error_rate', 0),
                    'active_users': key_metrics.get('active_users', 0)
                },
                'top_kpis': dashboard_data.business_kpis[:3],  # Top 3 KPIs
                'urgent_improvements': len([
                    opp for opp in dashboard_data.improvement_opportunities 
                    if opp.get('priority') in ['critical', 'high']
                ])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard summary: {e}")
            return {}
    
    async def export_dashboard_data(self, format: str = 'json') -> Dict[str, Any]:
        """Export dashboard data in specified format."""
        try:
            dashboard_data = await self.get_dashboard_data()
            
            if format.lower() == 'json':
                return {
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'format': 'json',
                    'data': {
                        'timestamp': dashboard_data.timestamp.isoformat(),
                        'system_health': dashboard_data.system_health,
                        'key_metrics': dashboard_data.key_metrics,
                        'business_kpis': dashboard_data.business_kpis,
                        'quality_status': dashboard_data.quality_status,
                        'alerts': dashboard_data.alerts,
                        'performance_trends': dashboard_data.performance_trends,
                        'improvement_opportunities': dashboard_data.improvement_opportunities
                    }
                }
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting dashboard data: {e}")
            return {}
    
    def clear_cache(self):
        """Clear dashboard cache to force refresh."""
        self.cached_data = None
        self.last_update = None
        self.logger.info("Dashboard cache cleared")


# Global dashboard instance
monitoring_dashboard = MonitoringDashboard()
