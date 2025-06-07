"""
Business Metrics

Business performance and user behavior analytics for the fact-checking platform.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionTier, UsageRecord, Invoice, PaymentStatus

logger = logging.getLogger(__name__)


@dataclass
class BusinessKPI:
    """Business KPI data structure."""
    name: str
    value: float
    unit: str
    change_percent: Optional[float] = None
    target: Optional[float] = None
    status: str = "normal"  # normal, warning, critical


@dataclass
class RevenueMetrics:
    """Revenue metrics data structure."""
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    total_revenue: float
    revenue_growth_rate: float
    average_revenue_per_user: float
    customer_lifetime_value: float


@dataclass
class UserEngagementMetrics:
    """User engagement metrics data structure."""
    daily_active_users: int
    monthly_active_users: int
    weekly_active_users: int
    user_retention_rate: float
    feature_adoption_rate: Dict[str, float]
    session_duration_avg: float


class BusinessMetricsCollector:
    """Collects business and user analytics metrics."""
    
    def __init__(self):
        """Initialize business metrics collector."""
        self.logger = logging.getLogger(__name__ + ".BusinessMetricsCollector")
    
    async def collect_user_metrics(self) -> Dict[str, Any]:
        """Collect user engagement and behavior metrics."""
        try:
            db = next(get_db())
            
            try:
                now = datetime.utcnow()
                
                # Daily Active Users (last 24 hours)
                dau = db.query(User).filter(
                    User.last_login >= now - timedelta(days=1)
                ).count()
                
                # Weekly Active Users (last 7 days)
                wau = db.query(User).filter(
                    User.last_login >= now - timedelta(days=7)
                ).count()
                
                # Monthly Active Users (last 30 days)
                mau = db.query(User).filter(
                    User.last_login >= now - timedelta(days=30)
                ).count()
                
                # Total registered users
                total_users = db.query(User).count()
                
                # New users this month
                new_users_month = db.query(User).filter(
                    User.created_at >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                ).count()
                
                # User retention rate (simplified - users who logged in this month and last month)
                last_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
                last_month_end = now.replace(day=1)
                this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                last_month_users = db.query(User.id).filter(
                    and_(
                        User.last_login >= last_month_start,
                        User.last_login < last_month_end
                    )
                ).subquery()
                
                retained_users = db.query(User).filter(
                    and_(
                        User.id.in_(last_month_users),
                        User.last_login >= this_month_start
                    )
                ).count()
                
                last_month_user_count = db.query(User).filter(
                    and_(
                        User.last_login >= last_month_start,
                        User.last_login < last_month_end
                    )
                ).count()
                
                retention_rate = (retained_users / last_month_user_count * 100) if last_month_user_count > 0 else 0
                
                # Feature adoption rates
                feature_adoption = await self._calculate_feature_adoption(db)
                
                return {
                    'daily_active_users': dau,
                    'weekly_active_users': wau,
                    'monthly_active_users': mau,
                    'total_users': total_users,
                    'new_users_month': new_users_month,
                    'user_retention_rate': retention_rate,
                    'feature_adoption': feature_adoption,
                    'user_growth_rate': (new_users_month / max(total_users - new_users_month, 1) * 100)
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error collecting user metrics: {e}")
            return {}
    
    async def collect_revenue_metrics(self) -> Dict[str, Any]:
        """Collect revenue and subscription metrics."""
        try:
            db = next(get_db())
            
            try:
                now = datetime.utcnow()
                
                # Monthly Recurring Revenue (MRR)
                active_subscriptions = db.query(Subscription).filter(
                    Subscription.status == 'active'
                ).all()
                
                mrr = sum(float(sub.effective_price) for sub in active_subscriptions 
                         if sub.billing_cycle.value == 'monthly')
                
                # Add quarterly and yearly subscriptions normalized to monthly
                for sub in active_subscriptions:
                    if sub.billing_cycle.value == 'quarterly':
                        mrr += float(sub.effective_price) / 3
                    elif sub.billing_cycle.value == 'yearly':
                        mrr += float(sub.effective_price) / 12
                
                # Annual Recurring Revenue
                arr = mrr * 12
                
                # Total revenue this month
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                monthly_revenue = db.query(func.sum(Invoice.total_amount)).filter(
                    and_(
                        Invoice.status == PaymentStatus.COMPLETED,
                        Invoice.paid_date >= month_start
                    )
                ).scalar() or 0
                
                # Revenue growth rate (compare to last month)
                last_month_start = (month_start - timedelta(days=1)).replace(day=1)
                last_month_revenue = db.query(func.sum(Invoice.total_amount)).filter(
                    and_(
                        Invoice.status == PaymentStatus.COMPLETED,
                        Invoice.paid_date >= last_month_start,
                        Invoice.paid_date < month_start
                    )
                ).scalar() or 0
                
                revenue_growth_rate = 0
                if last_month_revenue > 0:
                    revenue_growth_rate = ((float(monthly_revenue) - float(last_month_revenue)) / float(last_month_revenue)) * 100
                
                # Average Revenue Per User (ARPU)
                paying_customers = len([sub for sub in active_subscriptions if sub.tier != SubscriptionTier.FREE])
                arpu = mrr / paying_customers if paying_customers > 0 else 0
                
                # Customer Lifetime Value (simplified)
                avg_subscription_length = 12  # months (simplified assumption)
                clv = arpu * avg_subscription_length
                
                # Subscription tier distribution
                tier_distribution = {}
                for tier in SubscriptionTier:
                    count = len([sub for sub in active_subscriptions if sub.tier == tier])
                    tier_distribution[tier.value] = count
                
                # Churn rate (simplified)
                cancelled_this_month = db.query(Subscription).filter(
                    and_(
                        Subscription.cancelled_at >= month_start,
                        Subscription.cancelled_at.isnot(None)
                    )
                ).count()
                
                total_active_start_month = len(active_subscriptions) + cancelled_this_month
                churn_rate = (cancelled_this_month / total_active_start_month * 100) if total_active_start_month > 0 else 0
                
                return {
                    'monthly_recurring_revenue': mrr,
                    'annual_recurring_revenue': arr,
                    'monthly_revenue': float(monthly_revenue),
                    'revenue_growth_rate': revenue_growth_rate,
                    'average_revenue_per_user': arpu,
                    'customer_lifetime_value': clv,
                    'paying_customers': paying_customers,
                    'churn_rate': churn_rate,
                    'tier_distribution': tier_distribution
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error collecting revenue metrics: {e}")
            return {}
    
    async def collect_usage_analytics(self) -> Dict[str, Any]:
        """Collect usage analytics and patterns."""
        try:
            db = next(get_db())
            
            try:
                now = datetime.utcnow()
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Total usage this month
                monthly_usage = db.query(UsageRecord).filter(
                    UsageRecord.created_at >= month_start
                ).all()
                
                # Usage by type
                usage_by_type = {}
                for usage_type in ['text_requests', 'document_requests', 'url_requests', 'api_calls']:
                    count = len([u for u in monthly_usage if u.usage_type == usage_type])
                    usage_by_type[usage_type] = count
                
                # Average requests per user
                active_users = db.query(User).filter(
                    User.last_login >= month_start
                ).count()
                
                avg_requests_per_user = len(monthly_usage) / active_users if active_users > 0 else 0
                
                # Peak usage analysis
                peak_usage_analysis = await self._analyze_peak_usage(db, monthly_usage)
                
                # Popular document formats (simplified)
                popular_formats = {
                    'pdf': len([u for u in monthly_usage if 'pdf' in str(u.metadata or '').lower()]),
                    'doc': len([u for u in monthly_usage if 'doc' in str(u.metadata or '').lower()]),
                    'txt': len([u for u in monthly_usage if 'txt' in str(u.metadata or '').lower()]),
                    'url': len([u for u in monthly_usage if u.usage_type == 'url_requests'])
                }
                
                # Model usage distribution
                model_usage = {}
                for record in monthly_usage:
                    if record.model_used:
                        model_usage[record.model_used] = model_usage.get(record.model_used, 0) + 1
                
                return {
                    'total_requests_month': len(monthly_usage),
                    'usage_by_type': usage_by_type,
                    'avg_requests_per_user': avg_requests_per_user,
                    'peak_usage_analysis': peak_usage_analysis,
                    'popular_formats': popular_formats,
                    'model_usage_distribution': model_usage
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error collecting usage analytics: {e}")
            return {}
    
    async def collect_customer_success_metrics(self) -> Dict[str, Any]:
        """Collect customer success and support metrics."""
        try:
            # Simplified customer success metrics
            # In a real implementation, these would come from support ticket systems, surveys, etc.
            
            return {
                'support_ticket_volume': 25,  # Simulated
                'avg_resolution_time_hours': 4.5,  # Simulated
                'customer_satisfaction_score': 4.2,  # Out of 5, simulated
                'net_promoter_score': 65,  # Simulated
                'first_response_time_hours': 1.2,  # Simulated
                'ticket_resolution_rate': 95.5  # Percentage, simulated
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting customer success metrics: {e}")
            return {}
    
    async def _calculate_feature_adoption(self, db: Session) -> Dict[str, float]:
        """Calculate feature adoption rates."""
        try:
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get active users this month
            active_users = db.query(User.id).filter(
                User.last_login >= month_start
            ).all()
            active_user_ids = [user.id for user in active_users]
            total_active = len(active_user_ids)
            
            if total_active == 0:
                return {}
            
            # Feature usage (based on usage records)
            feature_usage = {}
            
            # Text fact-checking
            text_users = db.query(UsageRecord.user_id).filter(
                and_(
                    UsageRecord.usage_type == 'text_requests',
                    UsageRecord.created_at >= month_start,
                    UsageRecord.user_id.in_(active_user_ids)
                )
            ).distinct().count()
            feature_usage['text_fact_checking'] = (text_users / total_active) * 100
            
            # Document processing
            doc_users = db.query(UsageRecord.user_id).filter(
                and_(
                    UsageRecord.usage_type == 'document_requests',
                    UsageRecord.created_at >= month_start,
                    UsageRecord.user_id.in_(active_user_ids)
                )
            ).distinct().count()
            feature_usage['document_processing'] = (doc_users / total_active) * 100
            
            # URL fact-checking
            url_users = db.query(UsageRecord.user_id).filter(
                and_(
                    UsageRecord.usage_type == 'url_requests',
                    UsageRecord.created_at >= month_start,
                    UsageRecord.user_id.in_(active_user_ids)
                )
            ).distinct().count()
            feature_usage['url_fact_checking'] = (url_users / total_active) * 100
            
            # API usage
            api_users = db.query(UsageRecord.user_id).filter(
                and_(
                    UsageRecord.usage_type == 'api_calls',
                    UsageRecord.created_at >= month_start,
                    UsageRecord.user_id.in_(active_user_ids)
                )
            ).distinct().count()
            feature_usage['api_usage'] = (api_users / total_active) * 100
            
            return feature_usage
            
        except Exception as e:
            self.logger.error(f"Error calculating feature adoption: {e}")
            return {}
    
    async def _analyze_peak_usage(self, db: Session, usage_records: List) -> Dict[str, Any]:
        """Analyze peak usage patterns."""
        try:
            if not usage_records:
                return {}
            
            # Group by hour of day
            hourly_usage = {}
            for record in usage_records:
                hour = record.created_at.hour
                hourly_usage[hour] = hourly_usage.get(hour, 0) + 1
            
            # Find peak hours
            peak_hour = max(hourly_usage.items(), key=lambda x: x[1]) if hourly_usage else (0, 0)
            
            # Group by day of week
            daily_usage = {}
            for record in usage_records:
                day = record.created_at.strftime('%A')
                daily_usage[day] = daily_usage.get(day, 0) + 1
            
            # Find peak day
            peak_day = max(daily_usage.items(), key=lambda x: x[1]) if daily_usage else ('Monday', 0)
            
            return {
                'peak_hour': {'hour': peak_hour[0], 'requests': peak_hour[1]},
                'peak_day': {'day': peak_day[0], 'requests': peak_day[1]},
                'hourly_distribution': hourly_usage,
                'daily_distribution': daily_usage
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing peak usage: {e}")
            return {}


class BusinessMetrics:
    """Main business metrics class for comprehensive business intelligence."""
    
    def __init__(self):
        """Initialize business metrics."""
        self.logger = logging.getLogger(__name__ + ".BusinessMetrics")
        self.collector = BusinessMetricsCollector()
    
    async def generate_business_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive business dashboard data."""
        try:
            # Collect all business metrics
            user_metrics = await self.collector.collect_user_metrics()
            revenue_metrics = await self.collector.collect_revenue_metrics()
            usage_analytics = await self.collector.collect_usage_analytics()
            customer_success = await self.collector.collect_customer_success_metrics()
            
            # Calculate key KPIs
            kpis = await self._calculate_key_kpis(user_metrics, revenue_metrics, usage_analytics)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'kpis': kpis,
                'user_metrics': user_metrics,
                'revenue_metrics': revenue_metrics,
                'usage_analytics': usage_analytics,
                'customer_success': customer_success
            }
            
        except Exception as e:
            self.logger.error(f"Error generating business dashboard: {e}")
            return {}
    
    async def _calculate_key_kpis(
        self, 
        user_metrics: Dict[str, Any], 
        revenue_metrics: Dict[str, Any], 
        usage_analytics: Dict[str, Any]
    ) -> List[BusinessKPI]:
        """Calculate key business KPIs."""
        try:
            kpis = []
            
            # Revenue KPIs
            mrr = revenue_metrics.get('monthly_recurring_revenue', 0)
            kpis.append(BusinessKPI(
                name='Monthly Recurring Revenue',
                value=mrr,
                unit='USD',
                change_percent=revenue_metrics.get('revenue_growth_rate', 0),
                target=10000,  # $10k target
                status='normal' if mrr >= 5000 else 'warning'
            ))
            
            # User KPIs
            mau = user_metrics.get('monthly_active_users', 0)
            kpis.append(BusinessKPI(
                name='Monthly Active Users',
                value=mau,
                unit='users',
                target=1000,
                status='normal' if mau >= 500 else 'warning'
            ))
            
            # Retention KPI
            retention = user_metrics.get('user_retention_rate', 0)
            kpis.append(BusinessKPI(
                name='User Retention Rate',
                value=retention,
                unit='%',
                target=80,
                status='normal' if retention >= 70 else 'warning'
            ))
            
            # Usage KPI
            total_requests = usage_analytics.get('total_requests_month', 0)
            kpis.append(BusinessKPI(
                name='Monthly Requests',
                value=total_requests,
                unit='requests',
                target=50000,
                status='normal' if total_requests >= 25000 else 'warning'
            ))
            
            # Customer Success KPI
            csat = customer_success.get('customer_satisfaction_score', 0)
            kpis.append(BusinessKPI(
                name='Customer Satisfaction',
                value=csat,
                unit='score',
                target=4.5,
                status='normal' if csat >= 4.0 else 'warning'
            ))
            
            return kpis
            
        except Exception as e:
            self.logger.error(f"Error calculating KPIs: {e}")
            return []


# Global business metrics instance
business_metrics = BusinessMetrics()
