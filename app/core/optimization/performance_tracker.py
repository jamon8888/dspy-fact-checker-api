"""
Performance Tracker

This module tracks and analyzes performance metrics for document processing
pipelines to enable continuous optimization.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .data_models import PerformanceMetrics

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """Aggregates performance metrics over time."""
    
    def __init__(self, window_size: int = 100):
        """Initialize the metrics aggregator."""
        self.window_size = window_size
        self.metrics_history = defaultdict(lambda: deque(maxlen=window_size))
        self.logger = logging.getLogger(__name__ + ".MetricsAggregator")
    
    def add_metrics(self, metrics: PerformanceMetrics):
        """Add new performance metrics."""
        metric_dict = metrics.dict()
        
        for key, value in metric_dict.items():
            if isinstance(value, (int, float)) and value is not None:
                self.metrics_history[key].append({
                    'value': value,
                    'timestamp': metrics.timestamp
                })
    
    def get_aggregated_metrics(self, time_window: Optional[timedelta] = None) -> Dict[str, Dict[str, float]]:
        """Get aggregated metrics over a time window."""
        cutoff_time = datetime.now() - time_window if time_window else None
        aggregated = {}
        
        for metric_name, history in self.metrics_history.items():
            if not history:
                continue
            
            # Filter by time window if specified
            if cutoff_time:
                filtered_values = [
                    item['value'] for item in history 
                    if item['timestamp'] >= cutoff_time
                ]
            else:
                filtered_values = [item['value'] for item in history]
            
            if filtered_values:
                aggregated[metric_name] = {
                    'mean': sum(filtered_values) / len(filtered_values),
                    'min': min(filtered_values),
                    'max': max(filtered_values),
                    'count': len(filtered_values),
                    'latest': filtered_values[-1] if filtered_values else None
                }
        
        return aggregated
    
    def get_trend_analysis(self, metric_name: str, periods: int = 10) -> Dict[str, Any]:
        """Analyze trend for a specific metric."""
        if metric_name not in self.metrics_history:
            return {'trend': 'unknown', 'confidence': 0.0}
        
        history = list(self.metrics_history[metric_name])
        if len(history) < periods:
            return {'trend': 'insufficient_data', 'confidence': 0.0}
        
        # Simple trend analysis
        recent_values = [item['value'] for item in history[-periods:]]
        older_values = [item['value'] for item in history[-periods*2:-periods]] if len(history) >= periods*2 else []
        
        if not older_values:
            return {'trend': 'insufficient_data', 'confidence': 0.0}
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        change_ratio = (recent_avg - older_avg) / older_avg if older_avg != 0 else 0
        
        if abs(change_ratio) < 0.05:
            trend = 'stable'
        elif change_ratio > 0:
            trend = 'improving'
        else:
            trend = 'declining'
        
        confidence = min(1.0, abs(change_ratio) * 10)  # Simple confidence calculation
        
        return {
            'trend': trend,
            'confidence': confidence,
            'change_ratio': change_ratio,
            'recent_avg': recent_avg,
            'older_avg': older_avg
        }


class PerformanceAnalyzer:
    """Analyzes performance patterns and identifies optimization opportunities."""
    
    def __init__(self):
        """Initialize the performance analyzer."""
        self.logger = logging.getLogger(__name__ + ".PerformanceAnalyzer")
    
    async def analyze_performance_patterns(
        self, 
        metrics_history: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze performance patterns in metrics history."""
        try:
            analysis = {
                'performance_summary': {},
                'bottlenecks': [],
                'optimization_opportunities': [],
                'anomalies': []
            }
            
            # Analyze each metric
            for metric_name, history in metrics_history.items():
                if not history:
                    continue
                
                metric_analysis = await self._analyze_single_metric(metric_name, history)
                analysis['performance_summary'][metric_name] = metric_analysis
                
                # Identify bottlenecks
                if metric_analysis.get('is_bottleneck', False):
                    analysis['bottlenecks'].append({
                        'metric': metric_name,
                        'severity': metric_analysis.get('bottleneck_severity', 'medium'),
                        'description': metric_analysis.get('bottleneck_description', '')
                    })
                
                # Identify optimization opportunities
                if metric_analysis.get('optimization_potential', 0) > 0.3:
                    analysis['optimization_opportunities'].append({
                        'metric': metric_name,
                        'potential': metric_analysis.get('optimization_potential', 0),
                        'recommendations': metric_analysis.get('recommendations', [])
                    })
                
                # Identify anomalies
                anomalies = metric_analysis.get('anomalies', [])
                analysis['anomalies'].extend(anomalies)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance patterns: {e}")
            return {'error': str(e)}
    
    async def _analyze_single_metric(
        self, 
        metric_name: str, 
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze a single metric's performance."""
        values = [item['value'] for item in history if 'value' in item]
        
        if not values:
            return {'status': 'no_data'}
        
        # Basic statistics
        mean_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # Variability analysis
        variance = sum((x - mean_value) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        coefficient_of_variation = std_dev / mean_value if mean_value != 0 else 0
        
        # Performance assessment
        analysis = {
            'mean': mean_value,
            'min': min_value,
            'max': max_value,
            'std_dev': std_dev,
            'coefficient_of_variation': coefficient_of_variation,
            'sample_count': len(values)
        }
        
        # Metric-specific analysis
        if metric_name in ['accuracy', 'precision', 'recall', 'f1_score']:
            analysis.update(self._analyze_quality_metric(metric_name, values))
        elif metric_name == 'processing_time':
            analysis.update(self._analyze_latency_metric(values))
        elif metric_name == 'cost':
            analysis.update(self._analyze_cost_metric(values))
        
        return analysis
    
    def _analyze_quality_metric(self, metric_name: str, values: List[float]) -> Dict[str, Any]:
        """Analyze quality metrics (accuracy, precision, etc.)."""
        mean_value = sum(values) / len(values)
        
        # Quality thresholds
        excellent_threshold = 0.9
        good_threshold = 0.8
        acceptable_threshold = 0.7
        
        if mean_value >= excellent_threshold:
            quality_level = 'excellent'
            optimization_potential = 0.1
        elif mean_value >= good_threshold:
            quality_level = 'good'
            optimization_potential = 0.3
        elif mean_value >= acceptable_threshold:
            quality_level = 'acceptable'
            optimization_potential = 0.5
        else:
            quality_level = 'poor'
            optimization_potential = 0.8
        
        recommendations = []
        if mean_value < good_threshold:
            recommendations.append(f"Consider optimizing {metric_name} - current average: {mean_value:.3f}")
        
        return {
            'quality_level': quality_level,
            'optimization_potential': optimization_potential,
            'recommendations': recommendations,
            'is_bottleneck': mean_value < acceptable_threshold
        }
    
    def _analyze_latency_metric(self, values: List[float]) -> Dict[str, Any]:
        """Analyze latency/processing time metrics."""
        mean_value = sum(values) / len(values)
        
        # Latency thresholds (in seconds)
        fast_threshold = 2.0
        acceptable_threshold = 5.0
        slow_threshold = 10.0
        
        if mean_value <= fast_threshold:
            latency_level = 'fast'
            optimization_potential = 0.1
        elif mean_value <= acceptable_threshold:
            latency_level = 'acceptable'
            optimization_potential = 0.3
        elif mean_value <= slow_threshold:
            latency_level = 'slow'
            optimization_potential = 0.6
        else:
            latency_level = 'very_slow'
            optimization_potential = 0.9
        
        recommendations = []
        if mean_value > acceptable_threshold:
            recommendations.append(f"Consider optimizing processing speed - current average: {mean_value:.2f}s")
        
        return {
            'latency_level': latency_level,
            'optimization_potential': optimization_potential,
            'recommendations': recommendations,
            'is_bottleneck': mean_value > slow_threshold,
            'bottleneck_severity': 'high' if mean_value > slow_threshold else 'medium'
        }
    
    def _analyze_cost_metric(self, values: List[float]) -> Dict[str, Any]:
        """Analyze cost metrics."""
        mean_value = sum(values) / len(values)
        
        # Cost thresholds (in dollars)
        low_cost_threshold = 0.01
        moderate_cost_threshold = 0.05
        high_cost_threshold = 0.20
        
        if mean_value <= low_cost_threshold:
            cost_level = 'low'
            optimization_potential = 0.1
        elif mean_value <= moderate_cost_threshold:
            cost_level = 'moderate'
            optimization_potential = 0.3
        elif mean_value <= high_cost_threshold:
            cost_level = 'high'
            optimization_potential = 0.6
        else:
            cost_level = 'very_high'
            optimization_potential = 0.9
        
        recommendations = []
        if mean_value > moderate_cost_threshold:
            recommendations.append(f"Consider cost optimization - current average: ${mean_value:.4f}")
        
        return {
            'cost_level': cost_level,
            'optimization_potential': optimization_potential,
            'recommendations': recommendations,
            'is_bottleneck': mean_value > high_cost_threshold
        }


class PerformanceTracker:
    """Main performance tracking system."""
    
    def __init__(self, window_size: int = 1000):
        """Initialize the performance tracker."""
        self.metrics_aggregator = MetricsAggregator(window_size)
        self.performance_analyzer = PerformanceAnalyzer()
        self.logger = logging.getLogger(__name__ + ".PerformanceTracker")
        
        # Performance tracking state
        self.tracking_enabled = True
        self.alert_thresholds = {
            'accuracy': {'min': 0.7, 'max': 1.0},
            'processing_time': {'min': 0.0, 'max': 10.0},
            'cost': {'min': 0.0, 'max': 0.50}
        }
    
    async def track_performance(self, metrics: PerformanceMetrics):
        """Track new performance metrics."""
        try:
            if not self.tracking_enabled:
                return
            
            # Add to aggregator
            self.metrics_aggregator.add_metrics(metrics)
            
            # Check for alerts
            await self._check_performance_alerts(metrics)
            
            self.logger.debug(f"Tracked performance metrics for {metrics.model_used}")
            
        except Exception as e:
            self.logger.error(f"Error tracking performance: {e}")
    
    async def get_performance_summary(
        self, 
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        try:
            # Get aggregated metrics
            aggregated_metrics = self.metrics_aggregator.get_aggregated_metrics(time_window)
            
            # Get trend analysis for key metrics
            trends = {}
            key_metrics = ['accuracy', 'processing_time', 'cost', 'confidence_score']
            for metric in key_metrics:
                trends[metric] = self.metrics_aggregator.get_trend_analysis(metric)
            
            # Get performance analysis
            metrics_history = {
                name: list(self.metrics_aggregator.metrics_history[name])
                for name in self.metrics_aggregator.metrics_history
            }
            performance_analysis = await self.performance_analyzer.analyze_performance_patterns(
                metrics_history
            )
            
            return {
                'aggregated_metrics': aggregated_metrics,
                'trends': trends,
                'performance_analysis': performance_analysis,
                'tracking_status': {
                    'enabled': self.tracking_enabled,
                    'window_size': self.metrics_aggregator.window_size,
                    'total_samples': sum(
                        len(history) for history in self.metrics_aggregator.metrics_history.values()
                    )
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for performance optimization."""
        try:
            # Get current performance analysis
            metrics_history = {
                name: list(self.metrics_aggregator.metrics_history[name])
                for name in self.metrics_aggregator.metrics_history
            }
            analysis = await self.performance_analyzer.analyze_performance_patterns(metrics_history)
            
            recommendations = []
            
            # Add bottleneck recommendations
            for bottleneck in analysis.get('bottlenecks', []):
                recommendations.append({
                    'type': 'bottleneck',
                    'priority': 'high' if bottleneck['severity'] == 'high' else 'medium',
                    'metric': bottleneck['metric'],
                    'description': f"Address {bottleneck['metric']} bottleneck",
                    'action': f"Optimize {bottleneck['metric']} performance"
                })
            
            # Add optimization opportunity recommendations
            for opportunity in analysis.get('optimization_opportunities', []):
                recommendations.append({
                    'type': 'optimization',
                    'priority': 'high' if opportunity['potential'] > 0.6 else 'medium',
                    'metric': opportunity['metric'],
                    'description': f"Optimization opportunity for {opportunity['metric']}",
                    'action': f"Apply optimization strategies to improve {opportunity['metric']}",
                    'potential_improvement': opportunity['potential']
                })
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting optimization recommendations: {e}")
            return []
    
    async def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts based on thresholds."""
        try:
            alerts = []
            
            # Check accuracy
            if metrics.accuracy is not None:
                thresholds = self.alert_thresholds.get('accuracy', {})
                if metrics.accuracy < thresholds.get('min', 0):
                    alerts.append(f"Low accuracy alert: {metrics.accuracy:.3f}")
            
            # Check processing time
            if metrics.processing_time > self.alert_thresholds.get('processing_time', {}).get('max', 10):
                alerts.append(f"High latency alert: {metrics.processing_time:.2f}s")
            
            # Check cost
            if metrics.cost > self.alert_thresholds.get('cost', {}).get('max', 0.50):
                alerts.append(f"High cost alert: ${metrics.cost:.4f}")
            
            # Log alerts
            for alert in alerts:
                self.logger.warning(alert)
                
        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {e}")
    
    def set_alert_thresholds(self, thresholds: Dict[str, Dict[str, float]]):
        """Set custom alert thresholds."""
        self.alert_thresholds.update(thresholds)
        self.logger.info("Updated alert thresholds")
    
    def enable_tracking(self):
        """Enable performance tracking."""
        self.tracking_enabled = True
        self.logger.info("Performance tracking enabled")
    
    def disable_tracking(self):
        """Disable performance tracking."""
        self.tracking_enabled = False
        self.logger.info("Performance tracking disabled")
