"""
Notification Service

Service for sending notifications about billing, usage, and account events.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.subscription import Subscription, UsageRecord
from app.services.subscription_service import subscription_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications."""
    
    def __init__(self):
        """Initialize the notification service."""
        self.logger = logging.getLogger(__name__ + ".NotificationService")
        
        # Notification thresholds
        self.quota_warning_thresholds = [0.8, 0.9, 0.95]  # 80%, 90%, 95%
        self.billing_warning_days = [7, 3, 1]  # Days before billing
        
        # Email templates (simplified - would use proper template engine)
        self.email_templates = {
            "quota_warning": {
                "subject": "Usage Quota Warning - {usage_type}",
                "body": """
                Dear {user_name},
                
                You have used {percentage}% of your monthly {usage_type} quota.
                
                Current usage: {current_usage} / {limit}
                Remaining: {remaining}
                
                Consider upgrading your plan to avoid service interruption.
                
                Best regards,
                Fact-Checker Team
                """
            },
            "quota_exceeded": {
                "subject": "Usage Quota Exceeded - {usage_type}",
                "body": """
                Dear {user_name},
                
                You have exceeded your monthly {usage_type} quota.
                
                Current usage: {current_usage} / {limit}
                Overage: {overage}
                Additional charges: ${overage_cost:.2f}
                
                Please upgrade your plan or reduce usage.
                
                Best regards,
                Fact-Checker Team
                """
            },
            "billing_reminder": {
                "subject": "Billing Reminder - Payment Due in {days} Days",
                "body": """
                Dear {user_name},
                
                Your subscription payment of ${amount:.2f} is due in {days} days.
                
                Billing date: {billing_date}
                Subscription: {subscription_tier}
                
                Please ensure your payment method is up to date.
                
                Best regards,
                Fact-Checker Team
                """
            },
            "payment_failed": {
                "subject": "Payment Failed - Action Required",
                "body": """
                Dear {user_name},
                
                We were unable to process your payment of ${amount:.2f}.
                
                Please update your payment method to avoid service interruption.
                
                Best regards,
                Fact-Checker Team
                """
            },
            "subscription_cancelled": {
                "subject": "Subscription Cancelled",
                "body": """
                Dear {user_name},
                
                Your subscription has been cancelled as requested.
                
                Your service will continue until {end_date}.
                
                We're sorry to see you go!
                
                Best regards,
                Fact-Checker Team
                """
            }
        }
    
    async def send_quota_warning(
        self,
        db: Session,
        user: User,
        usage_type: str,
        current_usage: int,
        limit: int,
        percentage: float
    ):
        """Send quota warning notification."""
        try:
            remaining = max(0, limit - current_usage)
            
            notification_data = {
                "user_name": user.full_name,
                "usage_type": usage_type.replace("_", " ").title(),
                "percentage": int(percentage * 100),
                "current_usage": current_usage,
                "limit": limit,
                "remaining": remaining
            }
            
            await self._send_email_notification(
                user=user,
                template_key="quota_warning",
                data=notification_data
            )
            
            self.logger.info(f"Quota warning sent to user {user.id} for {usage_type}")
            
        except Exception as e:
            self.logger.error(f"Error sending quota warning: {e}")
    
    async def send_quota_exceeded_notification(
        self,
        db: Session,
        user: User,
        usage_type: str,
        current_usage: int,
        limit: int,
        overage: int,
        overage_cost: float
    ):
        """Send quota exceeded notification."""
        try:
            notification_data = {
                "user_name": user.full_name,
                "usage_type": usage_type.replace("_", " ").title(),
                "current_usage": current_usage,
                "limit": limit,
                "overage": overage,
                "overage_cost": overage_cost
            }
            
            await self._send_email_notification(
                user=user,
                template_key="quota_exceeded",
                data=notification_data
            )
            
            self.logger.info(f"Quota exceeded notification sent to user {user.id} for {usage_type}")
            
        except Exception as e:
            self.logger.error(f"Error sending quota exceeded notification: {e}")
    
    async def send_billing_reminder(
        self,
        db: Session,
        user: User,
        subscription: Subscription,
        days_until_billing: int
    ):
        """Send billing reminder notification."""
        try:
            notification_data = {
                "user_name": user.full_name,
                "days": days_until_billing,
                "amount": float(subscription.effective_price),
                "billing_date": subscription.next_billing_date.strftime("%Y-%m-%d") if subscription.next_billing_date else "TBD",
                "subscription_tier": subscription.tier.value.title()
            }
            
            await self._send_email_notification(
                user=user,
                template_key="billing_reminder",
                data=notification_data
            )
            
            self.logger.info(f"Billing reminder sent to user {user.id}")
            
        except Exception as e:
            self.logger.error(f"Error sending billing reminder: {e}")
    
    async def send_payment_failed_notification(
        self,
        db: Session,
        user: User,
        amount: float
    ):
        """Send payment failed notification."""
        try:
            notification_data = {
                "user_name": user.full_name,
                "amount": amount
            }
            
            await self._send_email_notification(
                user=user,
                template_key="payment_failed",
                data=notification_data
            )
            
            self.logger.info(f"Payment failed notification sent to user {user.id}")
            
        except Exception as e:
            self.logger.error(f"Error sending payment failed notification: {e}")
    
    async def send_subscription_cancelled_notification(
        self,
        db: Session,
        user: User,
        subscription: Subscription
    ):
        """Send subscription cancelled notification."""
        try:
            notification_data = {
                "user_name": user.full_name,
                "end_date": subscription.end_date.strftime("%Y-%m-%d")
            }
            
            await self._send_email_notification(
                user=user,
                template_key="subscription_cancelled",
                data=notification_data
            )
            
            self.logger.info(f"Subscription cancelled notification sent to user {user.id}")
            
        except Exception as e:
            self.logger.error(f"Error sending subscription cancelled notification: {e}")
    
    async def check_and_send_quota_warnings(self, db: Session):
        """Check all users for quota warnings and send notifications."""
        try:
            # Get all active users with subscriptions
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                subscription = await subscription_service.get_active_subscription(db, user.id)
                if not subscription:
                    continue
                
                quota_limits = subscription.get_quota_limits()
                
                for usage_type, limit in quota_limits.items():
                    if limit <= 0:  # Skip unlimited quotas
                        continue
                    
                    current_usage = await subscription_service.get_monthly_usage(db, user.id, usage_type)
                    percentage = current_usage / limit if limit > 0 else 0
                    
                    # Check if we should send a warning
                    for threshold in self.quota_warning_thresholds:
                        if percentage >= threshold:
                            # Check if we already sent this warning
                            if not await self._already_sent_quota_warning(db, user.id, usage_type, threshold):
                                await self.send_quota_warning(
                                    db, user, usage_type, current_usage, limit, percentage
                                )
                                await self._record_quota_warning_sent(db, user.id, usage_type, threshold)
                            break
            
            self.logger.info("Quota warning check completed")
            
        except Exception as e:
            self.logger.error(f"Error checking quota warnings: {e}")
    
    async def check_and_send_billing_reminders(self, db: Session):
        """Check for upcoming billing dates and send reminders."""
        try:
            # Get subscriptions with upcoming billing dates
            upcoming_billing = db.query(Subscription).filter(
                and_(
                    Subscription.status == "active",
                    Subscription.next_billing_date.isnot(None),
                    Subscription.next_billing_date <= datetime.utcnow() + timedelta(days=7)
                )
            ).all()
            
            for subscription in upcoming_billing:
                user = db.query(User).filter(User.id == subscription.user_id).first()
                if not user:
                    continue
                
                days_until_billing = (subscription.next_billing_date - datetime.utcnow()).days
                
                if days_until_billing in self.billing_warning_days:
                    # Check if we already sent this reminder
                    if not await self._already_sent_billing_reminder(db, subscription.id, days_until_billing):
                        await self.send_billing_reminder(db, user, subscription, days_until_billing)
                        await self._record_billing_reminder_sent(db, subscription.id, days_until_billing)
            
            self.logger.info("Billing reminder check completed")
            
        except Exception as e:
            self.logger.error(f"Error checking billing reminders: {e}")
    
    async def _send_email_notification(
        self,
        user: User,
        template_key: str,
        data: Dict[str, Any]
    ):
        """Send email notification to user."""
        try:
            # Check user preferences
            if not user.notification_preferences or "email_notifications" not in user.notification_preferences:
                # Default to enabled if no preferences set
                email_enabled = True
            else:
                import json
                prefs = json.loads(user.notification_preferences)
                email_enabled = prefs.get("email_notifications", True)
            
            if not email_enabled:
                self.logger.info(f"Email notifications disabled for user {user.id}")
                return
            
            template = self.email_templates.get(template_key)
            if not template:
                self.logger.error(f"Email template not found: {template_key}")
                return
            
            subject = template["subject"].format(**data)
            body = template["body"].format(**data)
            
            # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
            # For now, just log the email
            self.logger.info(f"EMAIL TO {user.email}: {subject}")
            self.logger.debug(f"EMAIL BODY: {body}")
            
            # In production, you would send the actual email here:
            # await email_service.send_email(
            #     to=user.email,
            #     subject=subject,
            #     body=body
            # )
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
    
    async def _already_sent_quota_warning(
        self,
        db: Session,
        user_id: int,
        usage_type: str,
        threshold: float
    ) -> bool:
        """Check if quota warning was already sent."""
        # TODO: Implement notification tracking table
        # For now, return False to always send (in production, track sent notifications)
        return False
    
    async def _record_quota_warning_sent(
        self,
        db: Session,
        user_id: int,
        usage_type: str,
        threshold: float
    ):
        """Record that quota warning was sent."""
        # TODO: Implement notification tracking
        pass
    
    async def _already_sent_billing_reminder(
        self,
        db: Session,
        subscription_id: int,
        days_until_billing: int
    ) -> bool:
        """Check if billing reminder was already sent."""
        # TODO: Implement notification tracking
        return False
    
    async def _record_billing_reminder_sent(
        self,
        db: Session,
        subscription_id: int,
        days_until_billing: int
    ):
        """Record that billing reminder was sent."""
        # TODO: Implement notification tracking
        pass


# Global notification service instance
notification_service = NotificationService()
