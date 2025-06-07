"""
Tests for monitoring, analytics, and quality assurance systems.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.monitoring.system_metrics import SystemMetrics, MetricsCollector, AlertingSystem
from app.monitoring.business_metrics import BusinessMetrics, BusinessMetricsCollector
from app.monitoring.quality_assurance import QualityAssuranceSystem, AccuracyMonitor, PerformanceTester
from app.monitoring.continuous_improvement import ContinuousImprovementSystem, FeedbackCollector
from app.monitoring.dashboard import MonitoringDashboard


class TestSystemMetrics:
    """Test system metrics collection and alerting."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector instance."""
        return MetricsCollector()
    
    @pytest.fixture
    def alerting_system(self):
        """Create alerting system instance."""
        return AlertingSystem()
    
    @pytest.fixture
    def system_metrics(self):
        """Create system metrics instance."""
        return SystemMetrics()
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, metrics_collector):
        """Test system metrics collection."""
        with patch('psutil.cpu_percent', return_value=45.2), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_network:
            
            # Mock system data
            mock_memory.return_value = Mock(percent=67.8, available=2147483648, total=8589934592)
            mock_disk.return_value = Mock(percent=23.1, free=107374182400, total=137438953472)
            mock_network.return_value = Mock(bytes_sent=1048576, bytes_recv=2097152, packets_sent=1000, packets_recv=1500)
            
            metrics = await metrics_collector.collect_system_metrics()
            
            assert 'cpu' in metrics
            assert 'memory' in metrics
            assert 'disk' in metrics
            assert 'network' in metrics
            assert metrics['cpu']['usage_percent'] == 45.2
            assert metrics['memory']['usage_percent'] == 67.8
    
    @pytest.mark.asyncio
    async def test_collect_application_metrics(self, metrics_collector):
        """Test application metrics collection."""
        with patch('app.monitoring.system_metrics.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__next__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            mock_db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 0
            
            metrics = await metrics_collector.collect_application_metrics()
            
            assert 'api' in metrics
            assert 'processing' in metrics
            assert 'users' in metrics
            assert 'errors' in metrics
    
    @pytest.mark.asyncio
    async def test_alerting_system(self, alerting_system):
        """Test alert generation."""
        # Mock metrics with high CPU usage
        metrics = {
            'system': {
                'cpu': {'usage_percent': 95.0},
                'memory': {'usage_percent': 70.0},
                'disk': {'usage_percent': 50.0}
            },
            'application': {
                'errors': {'error_rate_percent': 2.0},
                'api': {'latency': {'p95': 300, 'p99': 500}}
            }
        }
        
        alerts = await alerting_system.check_alerts(metrics)
        
        # Should generate CPU alert
        assert len(alerts) > 0
        cpu_alerts = [a for a in alerts if a['type'] == 'high_cpu_usage']
        assert len(cpu_alerts) == 1
        assert cpu_alerts[0]['severity'] in ['warning', 'critical']
    
    @pytest.mark.asyncio
    async def test_system_health_status(self, system_metrics):
        """Test system health status calculation."""
        with patch.object(system_metrics, 'collect_all_metrics') as mock_collect:
            mock_collect.return_value = {
                'system': {
                    'cpu': {'usage_percent': 45.0},
                    'memory': {'usage_percent': 60.0},
                    'disk': {'usage_percent': 30.0}
                },
                'application': {
                    'errors': {'error_rate_percent': 1.5},
                    'api': {'latency': {'p95': 200}},
                    'users': {'active_users_1h': 25}
                }
            }
            
            health = await system_metrics.get_system_health()
            
            assert health.status == 'healthy'
            assert health.cpu_usage == 45.0
            assert health.memory_usage == 60.0
            assert health.error_rate == 1.5


class TestBusinessMetrics:
    """Test business metrics and analytics."""
    
    @pytest.fixture
    def business_metrics_collector(self):
        """Create business metrics collector instance."""
        return BusinessMetricsCollector()
    
    @pytest.fixture
    def business_metrics(self):
        """Create business metrics instance."""
        return BusinessMetrics()
    
    @pytest.mark.asyncio
    async def test_collect_user_metrics(self, business_metrics_collector):
        """Test user metrics collection."""
        with patch('app.monitoring.business_metrics.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__next__.return_value = mock_db
            
            # Mock user queries
            mock_db.query.return_value.filter.return_value.count.return_value = 100
            
            metrics = await business_metrics_collector.collect_user_metrics()
            
            assert 'daily_active_users' in metrics
            assert 'monthly_active_users' in metrics
            assert 'user_retention_rate' in metrics
            assert 'feature_adoption' in metrics
    
    @pytest.mark.asyncio
    async def test_collect_revenue_metrics(self, business_metrics_collector):
        """Test revenue metrics collection."""
        with patch('app.monitoring.business_metrics.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__next__.return_value = mock_db
            
            # Mock subscription data
            mock_subscription = Mock()
            mock_subscription.effective_price = 99.0
            mock_subscription.billing_cycle.value = 'monthly'
            mock_subscription.tier.value = 'professional'
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_subscription]
            mock_db.query.return_value.filter.return_value.scalar.return_value = 2970.0  # Monthly revenue
            mock_db.query.return_value.filter.return_value.count.return_value = 5
            
            metrics = await business_metrics_collector.collect_revenue_metrics()
            
            assert 'monthly_recurring_revenue' in metrics
            assert 'annual_recurring_revenue' in metrics
            assert 'paying_customers' in metrics
            assert 'churn_rate' in metrics
    
    @pytest.mark.asyncio
    async def test_generate_business_dashboard(self, business_metrics):
        """Test business dashboard generation."""
        with patch.object(business_metrics.collector, 'collect_user_metrics') as mock_user, \
             patch.object(business_metrics.collector, 'collect_revenue_metrics') as mock_revenue, \
             patch.object(business_metrics.collector, 'collect_usage_analytics') as mock_usage, \
             patch.object(business_metrics.collector, 'collect_customer_success_metrics') as mock_success:
            
            mock_user.return_value = {'monthly_active_users': 500}
            mock_revenue.return_value = {'monthly_recurring_revenue': 15000}
            mock_usage.return_value = {'total_requests_month': 50000}
            mock_success.return_value = {'customer_satisfaction_score': 4.2}
            
            dashboard = await business_metrics.generate_business_dashboard()
            
            assert 'timestamp' in dashboard
            assert 'kpis' in dashboard
            assert 'user_metrics' in dashboard
            assert 'revenue_metrics' in dashboard
            assert len(dashboard['kpis']) > 0


class TestQualityAssurance:
    """Test quality assurance system."""
    
    @pytest.fixture
    def accuracy_monitor(self):
        """Create accuracy monitor instance."""
        return AccuracyMonitor()
    
    @pytest.fixture
    def performance_tester(self):
        """Create performance tester instance."""
        return PerformanceTester()
    
    @pytest.fixture
    def quality_assurance(self):
        """Create quality assurance system instance."""
        return QualityAssuranceSystem()
    
    @pytest.mark.asyncio
    async def test_accuracy_monitoring(self, accuracy_monitor):
        """Test accuracy monitoring."""
        results = await accuracy_monitor.run_accuracy_tests()
        
        assert len(results) > 0
        for result in results:
            assert hasattr(result, 'test_name')
            assert hasattr(result, 'status')
            assert hasattr(result, 'score')
            assert 0 <= result.score <= 1
    
    @pytest.mark.asyncio
    async def test_performance_testing(self, performance_tester):
        """Test performance testing."""
        results = await performance_tester.run_performance_tests()
        
        assert len(results) > 0
        for result in results:
            assert hasattr(result, 'test_name')
            assert hasattr(result, 'status')
            assert hasattr(result, 'score')
            assert result.duration_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_quality_monitoring_cycle(self, quality_assurance):
        """Test complete quality monitoring cycle."""
        report = await quality_assurance.continuous_quality_monitoring()
        
        assert hasattr(report, 'overall_quality_score')
        assert hasattr(report, 'overall_status')
        assert hasattr(report, 'accuracy_results')
        assert hasattr(report, 'performance_results')
        assert hasattr(report, 'recommendations')
        assert 0 <= report.overall_quality_score <= 1


class TestContinuousImprovement:
    """Test continuous improvement system."""
    
    @pytest.fixture
    def feedback_collector(self):
        """Create feedback collector instance."""
        return FeedbackCollector()
    
    @pytest.fixture
    def continuous_improvement(self):
        """Create continuous improvement system instance."""
        return ContinuousImprovementSystem()
    
    @pytest.mark.asyncio
    async def test_feedback_collection(self, feedback_collector):
        """Test feedback collection."""
        feedback = await feedback_collector.collect_all_feedback()
        
        assert isinstance(feedback, list)
        for item in feedback:
            assert hasattr(item, 'source')
            assert hasattr(item, 'category')
            assert hasattr(item, 'description')
            assert hasattr(item, 'impact_score')
            assert 0 <= item.impact_score <= 1
    
    @pytest.mark.asyncio
    async def test_improvement_cycle(self, continuous_improvement):
        """Test improvement cycle."""
        report = await continuous_improvement.run_improvement_cycle()
        
        assert hasattr(report, 'improvement_opportunities')
        assert hasattr(report, 'prioritized_improvements')
        assert hasattr(report, 'implementation_plans')
        assert hasattr(report, 'expected_impact')
        assert isinstance(report.improvement_opportunities, list)


class TestMonitoringDashboard:
    """Test monitoring dashboard."""
    
    @pytest.fixture
    def dashboard(self):
        """Create monitoring dashboard instance."""
        return MonitoringDashboard()
    
    @pytest.mark.asyncio
    async def test_dashboard_data_collection(self, dashboard):
        """Test dashboard data collection."""
        with patch.object(dashboard, '_get_system_health') as mock_health, \
             patch.object(dashboard, '_get_key_metrics') as mock_metrics, \
             patch.object(dashboard, '_get_business_kpis') as mock_kpis, \
             patch.object(dashboard, '_get_quality_status') as mock_quality, \
             patch.object(dashboard, '_get_active_alerts') as mock_alerts, \
             patch.object(dashboard, '_get_performance_trends') as mock_trends, \
             patch.object(dashboard, '_get_improvement_opportunities') as mock_improvements:
            
            mock_health.return_value = {'status': 'healthy'}
            mock_metrics.return_value = {'requests_per_hour': 1000}
            mock_kpis.return_value = [{'name': 'MRR', 'value': 15000}]
            mock_quality.return_value = {'overall_score': 0.85}
            mock_alerts.return_value = []
            mock_trends.return_value = {'response_time': {'current': 200}}
            mock_improvements.return_value = []
            
            data = await dashboard.get_dashboard_data()
            
            assert hasattr(data, 'timestamp')
            assert hasattr(data, 'system_health')
            assert hasattr(data, 'key_metrics')
            assert hasattr(data, 'business_kpis')
            assert hasattr(data, 'quality_status')
            assert data.system_health['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_dashboard_summary(self, dashboard):
        """Test dashboard summary generation."""
        with patch.object(dashboard, 'get_dashboard_data') as mock_data:
            mock_dashboard_data = Mock()
            mock_dashboard_data.timestamp = datetime.utcnow()
            mock_dashboard_data.system_health = {'status': 'healthy'}
            mock_dashboard_data.quality_status = {'overall_score': 0.85}
            mock_dashboard_data.alerts = []
            mock_dashboard_data.key_metrics = {'requests_per_hour': 1000}
            mock_dashboard_data.business_kpis = [{'name': 'MRR', 'value': 15000}]
            mock_dashboard_data.improvement_opportunities = []
            
            mock_data.return_value = mock_dashboard_data
            
            summary = await dashboard.get_dashboard_summary()
            
            assert 'timestamp' in summary
            assert 'system_status' in summary
            assert 'quality_score' in summary
            assert 'key_metrics' in summary
            assert summary['system_status'] == 'healthy'
    
    def test_cache_functionality(self, dashboard):
        """Test dashboard caching."""
        # Clear cache
        dashboard.clear_cache()
        assert dashboard.cached_data is None
        assert dashboard.last_update is None
    
    @pytest.mark.asyncio
    async def test_export_functionality(self, dashboard):
        """Test dashboard data export."""
        with patch.object(dashboard, 'get_dashboard_data') as mock_data:
            mock_dashboard_data = Mock()
            mock_dashboard_data.timestamp = datetime.utcnow()
            mock_dashboard_data.system_health = {'status': 'healthy'}
            mock_dashboard_data.key_metrics = {'requests_per_hour': 1000}
            mock_dashboard_data.business_kpis = []
            mock_dashboard_data.quality_status = {'overall_score': 0.85}
            mock_dashboard_data.alerts = []
            mock_dashboard_data.performance_trends = {}
            mock_dashboard_data.improvement_opportunities = []
            
            mock_data.return_value = mock_dashboard_data
            
            export_data = await dashboard.export_dashboard_data('json')
            
            assert 'export_timestamp' in export_data
            assert 'format' in export_data
            assert 'data' in export_data
            assert export_data['format'] == 'json'


@pytest.mark.integration
class TestMonitoringIntegration:
    """Integration tests for monitoring system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring(self):
        """Test end-to-end monitoring workflow."""
        # This would test the complete monitoring pipeline
        # from data collection to dashboard display
        pass
    
    @pytest.mark.asyncio
    async def test_alert_workflow(self):
        """Test alert generation and notification workflow."""
        # This would test the complete alert pipeline
        # from threshold breach to notification delivery
        pass
    
    @pytest.mark.asyncio
    async def test_quality_improvement_cycle(self):
        """Test quality monitoring and improvement cycle."""
        # This would test the complete quality assurance
        # and continuous improvement workflow
        pass


if __name__ == "__main__":
    pytest.main([__file__])
