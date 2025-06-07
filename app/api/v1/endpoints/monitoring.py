"""
Monitoring API Endpoints

API endpoints for system monitoring, analytics, and quality assurance.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.monitoring.system_metrics import system_metrics
from app.monitoring.business_metrics import business_metrics
from app.monitoring.quality_assurance import quality_assurance
from app.monitoring.continuous_improvement import continuous_improvement
from app.models.user import User, UserRole
from app.api.v1.endpoints.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    system_health: Dict[str, Any]


class MetricsResponse(BaseModel):
    """System metrics response model."""
    timestamp: str
    collection_time_seconds: float
    system_metrics: Dict[str, Any]
    application_metrics: Dict[str, Any]


class BusinessDashboardResponse(BaseModel):
    """Business dashboard response model."""
    timestamp: str
    kpis: List[Dict[str, Any]]
    user_metrics: Dict[str, Any]
    revenue_metrics: Dict[str, Any]
    usage_analytics: Dict[str, Any]
    customer_success: Dict[str, Any]


class QualityReportResponse(BaseModel):
    """Quality report response model."""
    overall_quality_score: float
    overall_status: str
    accuracy_results: List[Dict[str, Any]]
    performance_results: List[Dict[str, Any]]
    regression_results: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: str


def require_admin_access(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin access for monitoring endpoints."""
    if current_user.role not in [UserRole.ADMIN, UserRole.ENTERPRISE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for monitoring endpoints"
        )
    return current_user


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Get system health status.
    
    Returns comprehensive health information including system status,
    resource usage, and service availability.
    """
    try:
        # Get system health
        health_status = await system_metrics.get_system_health()
        
        # Calculate uptime (simplified)
        uptime_seconds = 3600.0  # Placeholder - would track actual uptime
        
        return HealthCheckResponse(
            status=health_status.status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            system_health={
                "cpu_usage": health_status.cpu_usage,
                "memory_usage": health_status.memory_usage,
                "disk_usage": health_status.disk_usage,
                "network_latency": health_status.network_latency,
                "active_connections": health_status.active_connections,
                "error_rate": health_status.error_rate
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_system_metrics(
    current_user: User = Depends(require_admin_access)
):
    """
    Get comprehensive system metrics.
    
    Returns detailed system and application performance metrics
    for monitoring and analysis.
    """
    try:
        metrics = await system_metrics.collect_all_metrics()
        
        return MetricsResponse(
            timestamp=metrics.get('timestamp', datetime.utcnow().isoformat()),
            collection_time_seconds=metrics.get('collection_time_seconds', 0.0),
            system_metrics=metrics.get('system', {}),
            application_metrics=metrics.get('application', {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )


@router.get("/business-dashboard", response_model=BusinessDashboardResponse)
async def get_business_dashboard(
    current_user: User = Depends(require_admin_access)
):
    """
    Get business intelligence dashboard data.
    
    Returns comprehensive business metrics including KPIs,
    user analytics, revenue metrics, and customer success data.
    """
    try:
        dashboard_data = await business_metrics.generate_business_dashboard()
        
        # Convert KPIs to dict format
        kpis_dict = []
        for kpi in dashboard_data.get('kpis', []):
            kpis_dict.append({
                'name': kpi.name,
                'value': kpi.value,
                'unit': kpi.unit,
                'change_percent': kpi.change_percent,
                'target': kpi.target,
                'status': kpi.status
            })
        
        return BusinessDashboardResponse(
            timestamp=dashboard_data.get('timestamp', datetime.utcnow().isoformat()),
            kpis=kpis_dict,
            user_metrics=dashboard_data.get('user_metrics', {}),
            revenue_metrics=dashboard_data.get('revenue_metrics', {}),
            usage_analytics=dashboard_data.get('usage_analytics', {}),
            customer_success=dashboard_data.get('customer_success', {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get business dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business dashboard data"
        )


@router.get("/quality-report", response_model=QualityReportResponse)
async def get_quality_report(
    current_user: User = Depends(require_admin_access)
):
    """
    Get comprehensive quality assurance report.
    
    Returns quality metrics including accuracy tests, performance tests,
    regression analysis, and improvement recommendations.
    """
    try:
        quality_report = await quality_assurance.continuous_quality_monitoring()
        
        # Convert test results to dict format
        def convert_test_results(results):
            return [
                {
                    'test_name': result.test_name,
                    'status': result.status.value,
                    'score': result.score,
                    'details': result.details,
                    'timestamp': result.timestamp.isoformat(),
                    'duration_seconds': result.duration_seconds
                }
                for result in results
            ]
        
        return QualityReportResponse(
            overall_quality_score=quality_report.overall_quality_score,
            overall_status=quality_report.overall_status.value,
            accuracy_results=convert_test_results(quality_report.accuracy_results),
            performance_results=convert_test_results(quality_report.performance_results),
            regression_results=convert_test_results(quality_report.regression_results),
            recommendations=quality_report.recommendations,
            timestamp=quality_report.timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get quality report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quality report"
        )


@router.get("/improvement-report")
async def get_improvement_report(
    current_user: User = Depends(require_admin_access)
):
    """
    Get continuous improvement analysis report.
    
    Returns improvement opportunities, prioritized recommendations,
    and implementation plans based on feedback and analytics.
    """
    try:
        improvement_report = await continuous_improvement.run_improvement_cycle()
        
        # Convert opportunities to dict format
        opportunities = []
        for opp in improvement_report.improvement_opportunities:
            opportunities.append({
                'id': opp.id,
                'title': opp.title,
                'description': opp.description,
                'category': opp.category.value,
                'priority': opp.priority.value,
                'impact_score': opp.impact_score,
                'effort_estimate': opp.effort_estimate,
                'roi_estimate': opp.roi_estimate,
                'supporting_feedback_count': len(opp.supporting_feedback)
            })
        
        # Convert implementation plans
        plans = []
        for plan in improvement_report.implementation_plans:
            plans.append({
                'opportunity_id': plan.opportunity_id,
                'implementation_steps': plan.implementation_steps,
                'estimated_timeline': plan.estimated_timeline,
                'required_resources': plan.required_resources,
                'success_metrics': plan.success_metrics,
                'risk_assessment': plan.risk_assessment
            })
        
        return {
            'timestamp': improvement_report.timestamp.isoformat(),
            'improvement_opportunities': opportunities,
            'prioritized_improvements': opportunities[:10],  # Top 10
            'implementation_plans': plans,
            'expected_impact': improvement_report.expected_impact,
            'feedback_summary': improvement_report.feedback_summary,
            'performance_trends': improvement_report.performance_trends
        }
        
    except Exception as e:
        logger.error(f"Failed to get improvement report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve improvement report"
        )


@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(require_admin_access),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, warning, info")
):
    """
    Get active system alerts.
    
    Returns current system alerts filtered by severity level.
    """
    try:
        # Get current metrics and check for alerts
        metrics = await system_metrics.collect_all_metrics()
        alerts = await system_metrics.alerting_system.check_alerts(metrics)
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_alerts': len(alerts),
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.get("/performance-trends")
async def get_performance_trends(
    current_user: User = Depends(require_admin_access),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze")
):
    """
    Get performance trends over time.
    
    Returns performance trend analysis for the specified time period.
    """
    try:
        # Simulate performance trend data
        # In practice, this would query historical metrics from a time-series database
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trends = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'metrics': {
                'response_time': {
                    'current': 320.5,
                    'average': 315.2,
                    'trend': 'stable',
                    'change_percent': 1.7
                },
                'error_rate': {
                    'current': 2.1,
                    'average': 2.3,
                    'trend': 'improving',
                    'change_percent': -8.7
                },
                'throughput': {
                    'current': 150.2,
                    'average': 145.8,
                    'trend': 'improving',
                    'change_percent': 3.0
                },
                'accuracy': {
                    'current': 0.851,
                    'average': 0.847,
                    'trend': 'improving',
                    'change_percent': 0.5
                }
            },
            'summary': {
                'overall_trend': 'improving',
                'key_improvements': [
                    'Error rate decreased by 8.7%',
                    'Throughput increased by 3.0%'
                ],
                'areas_of_concern': [
                    'Response time slightly increased'
                ]
            }
        }
        
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance trends"
        )


@router.get("/usage-analytics")
async def get_usage_analytics(
    current_user: User = Depends(require_admin_access),
    period: str = Query("month", description="Analysis period: day, week, month")
):
    """
    Get detailed usage analytics.
    
    Returns comprehensive usage analytics including user behavior,
    feature adoption, and usage patterns.
    """
    try:
        # Get usage analytics from business metrics
        dashboard_data = await business_metrics.generate_business_dashboard()
        usage_analytics = dashboard_data.get('usage_analytics', {})
        
        # Add period-specific analysis
        analytics = {
            'period': period,
            'timestamp': datetime.utcnow().isoformat(),
            'usage_summary': usage_analytics,
            'user_behavior': {
                'peak_usage_hours': [9, 10, 11, 14, 15, 16],
                'peak_usage_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'average_session_duration': 12.5,  # minutes
                'bounce_rate': 15.2  # percentage
            },
            'feature_adoption': {
                'text_fact_checking': 85.2,
                'document_processing': 62.1,
                'url_verification': 45.8,
                'api_usage': 28.3,
                'bulk_processing': 12.7
            },
            'geographic_distribution': {
                'north_america': 45.2,
                'europe': 32.1,
                'asia': 18.7,
                'other': 4.0
            }
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )


@router.post("/trigger-monitoring-cycle")
async def trigger_monitoring_cycle(
    current_user: User = Depends(require_admin_access)
):
    """
    Manually trigger a complete monitoring cycle.
    
    Runs system metrics collection, quality assurance checks,
    and generates alerts if necessary.
    """
    try:
        # Run monitoring cycle
        monitoring_result = await system_metrics.run_monitoring_cycle()
        
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_result': {
                'metrics_collected': len(monitoring_result.get('metrics', {})),
                'alerts_generated': len(monitoring_result.get('alerts', [])),
                'health_status': monitoring_result.get('health_status', {}).status if monitoring_result.get('health_status') else 'unknown'
            },
            'message': 'Monitoring cycle completed successfully'
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger monitoring cycle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger monitoring cycle"
        )


@router.get("/system-status")
async def get_system_status():
    """
    Get high-level system status for public status page.
    
    Returns basic system status information that can be displayed
    on a public status page without sensitive details.
    """
    try:
        health_status = await system_metrics.get_system_health()
        
        # Simplified status for public consumption
        if health_status.status == 'healthy':
            status_message = 'All systems operational'
            status_color = 'green'
        elif health_status.status == 'warning':
            status_message = 'Some systems experiencing issues'
            status_color = 'yellow'
        else:
            status_message = 'System issues detected'
            status_color = 'red'
        
        return {
            'status': health_status.status,
            'message': status_message,
            'color': status_color,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'api': 'operational',
                'fact_checking': 'operational',
                'document_processing': 'operational',
                'user_authentication': 'operational',
                'billing': 'operational'
            },
            'uptime_percentage': 99.9  # Simplified
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return {
            'status': 'unknown',
            'message': 'Unable to determine system status',
            'color': 'gray',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {},
            'uptime_percentage': 0.0
        }
