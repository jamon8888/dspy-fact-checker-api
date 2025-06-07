"""
Subscription Service

Service for managing user subscriptions, billing, and usage tracking.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.subscription import (
    Subscription, SubscriptionTier, SubscriptionStatus, BillingCycle,
    UsageRecord, Invoice, PaymentStatus, PaymentMethod, BillingAddress
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription and billing management."""
    
    def __init__(self):
        """Initialize the subscription service."""
        self.logger = logging.getLogger(__name__ + ".SubscriptionService")
        
        # Tier pricing (monthly)
        self.tier_pricing = {
            SubscriptionTier.FREE: {
                "monthly": Decimal("0.00"),
                "quarterly": Decimal("0.00"),
                "yearly": Decimal("0.00")
            },
            SubscriptionTier.STARTER: {
                "monthly": Decimal("29.00"),
                "quarterly": Decimal("79.00"),  # 10% discount
                "yearly": Decimal("290.00")     # 17% discount
            },
            SubscriptionTier.PROFESSIONAL: {
                "monthly": Decimal("99.00"),
                "quarterly": Decimal("267.00"), # 10% discount
                "yearly": Decimal("990.00")     # 17% discount
            },
            SubscriptionTier.ENTERPRISE: {
                "monthly": Decimal("299.00"),
                "quarterly": Decimal("807.00"), # 10% discount
                "yearly": Decimal("2990.00")    # 17% discount
            }
        }
        
        # Overage pricing per unit
        self.overage_pricing = {
            "text_requests": Decimal("0.01"),      # $0.01 per request
            "document_requests": Decimal("0.10"),  # $0.10 per document
            "url_requests": Decimal("0.02"),       # $0.02 per URL
            "api_calls": Decimal("0.001")          # $0.001 per API call
        }
    
    async def get_active_subscription(self, db: Session, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        try:
            subscription = db.query(Subscription).filter(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date > datetime.utcnow()
                )
            ).first()
            
            return subscription
            
        except Exception as e:
            self.logger.error(f"Error getting active subscription: {e}")
            return None
    
    async def create_subscription(
        self,
        db: Session,
        user_id: int,
        tier: SubscriptionTier,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        payment_method_id: Optional[str] = None,
        trial_days: Optional[int] = None
    ) -> Subscription:
        """Create a new subscription for user."""
        try:
            # Check if user already has an active subscription
            existing_subscription = await self.get_active_subscription(db, user_id)
            if existing_subscription:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has an active subscription"
                )
            
            # Calculate pricing
            price = self.tier_pricing[tier][billing_cycle.value]
            
            # Calculate dates
            start_date = datetime.utcnow()
            if billing_cycle == BillingCycle.MONTHLY:
                end_date = start_date + timedelta(days=30)
            elif billing_cycle == BillingCycle.QUARTERLY:
                end_date = start_date + timedelta(days=90)
            else:  # YEARLY
                end_date = start_date + timedelta(days=365)
            
            # Handle trial period
            trial_end_date = None
            subscription_status = SubscriptionStatus.ACTIVE
            if trial_days and trial_days > 0:
                trial_end_date = start_date + timedelta(days=trial_days)
                subscription_status = SubscriptionStatus.TRIALING
            
            # Create subscription
            subscription = Subscription(
                user_id=user_id,
                tier=tier,
                status=subscription_status,
                billing_cycle=billing_cycle,
                base_price=price,
                start_date=start_date,
                end_date=end_date,
                trial_end_date=trial_end_date,
                next_billing_date=trial_end_date or end_date,
                payment_method_id=payment_method_id
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            self.logger.info(f"Subscription created for user {user_id}: {tier.value}")
            
            return subscription
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating subscription: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subscription"
            )
    
    async def upgrade_subscription(
        self,
        db: Session,
        user_id: int,
        new_tier: SubscriptionTier,
        billing_cycle: Optional[BillingCycle] = None
    ) -> Subscription:
        """Upgrade user's subscription to a higher tier."""
        try:
            current_subscription = await self.get_active_subscription(db, user_id)
            if not current_subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found"
                )
            
            # Validate upgrade path
            tier_levels = {
                SubscriptionTier.FREE: 0,
                SubscriptionTier.STARTER: 1,
                SubscriptionTier.PROFESSIONAL: 2,
                SubscriptionTier.ENTERPRISE: 3
            }
            
            if tier_levels[new_tier] <= tier_levels[current_subscription.tier]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New tier must be higher than current tier"
                )
            
            # Use current billing cycle if not specified
            if not billing_cycle:
                billing_cycle = current_subscription.billing_cycle
            
            # Calculate new pricing
            new_price = self.tier_pricing[new_tier][billing_cycle.value]
            
            # Calculate prorated amount
            days_remaining = (current_subscription.end_date - datetime.utcnow()).days
            prorated_amount = await self._calculate_prorated_amount(
                current_subscription.base_price,
                new_price,
                days_remaining,
                billing_cycle
            )
            
            # Update subscription
            current_subscription.tier = new_tier
            current_subscription.base_price = new_price
            current_subscription.billing_cycle = billing_cycle
            current_subscription.status = SubscriptionStatus.ACTIVE
            
            db.commit()
            
            self.logger.info(f"Subscription upgraded for user {user_id}: {new_tier.value}")
            
            return current_subscription
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error upgrading subscription: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upgrade subscription"
            )
    
    async def cancel_subscription(
        self,
        db: Session,
        user_id: int,
        immediate: bool = False
    ) -> bool:
        """Cancel user's subscription."""
        try:
            subscription = await self.get_active_subscription(db, user_id)
            if not subscription:
                return False
            
            if immediate:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.end_date = datetime.utcnow()
            else:
                # Cancel at end of billing period
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.utcnow()
            
            db.commit()
            
            self.logger.info(f"Subscription cancelled for user {user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling subscription: {e}")
            return False
    
    async def track_usage(
        self,
        db: Session,
        user_id: int,
        usage_type: str,
        usage_count: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        """Track usage for billing and quota management."""
        try:
            # Get current subscription
            subscription = await self.get_active_subscription(db, user_id)
            
            # Get current billing period
            now = datetime.utcnow()
            billing_period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                billing_period_end = billing_period_start.replace(year=now.year + 1, month=1)
            else:
                billing_period_end = billing_period_start.replace(month=now.month + 1)
            
            # Calculate costs
            base_cost = Decimal("0.00")
            overage_cost = Decimal("0.00")
            
            if subscription:
                quota_limits = subscription.get_quota_limits()
                current_usage = await self.get_monthly_usage(db, user_id, usage_type)
                
                if quota_limits.get(usage_type, 0) > 0:  # Not unlimited
                    if current_usage >= quota_limits[usage_type]:
                        # This is overage usage
                        overage_cost = self.overage_pricing.get(usage_type, Decimal("0.00")) * usage_count
            
            total_cost = base_cost + overage_cost
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                subscription_id=subscription.id if subscription else None,
                usage_type=usage_type,
                usage_count=usage_count,
                base_cost=base_cost,
                overage_cost=overage_cost,
                total_cost=total_cost,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            db.add(usage_record)
            db.commit()
            
            return usage_record
            
        except Exception as e:
            self.logger.error(f"Error tracking usage: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track usage"
            )
    
    async def get_monthly_usage(
        self,
        db: Session,
        user_id: int,
        usage_type: Optional[str] = None
    ) -> Dict[str, int]:
        """Get monthly usage for user."""
        try:
            # Get current billing period
            now = datetime.utcnow()
            billing_period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            query = db.query(
                UsageRecord.usage_type,
                func.sum(UsageRecord.usage_count).label('total_usage')
            ).filter(
                and_(
                    UsageRecord.user_id == user_id,
                    UsageRecord.created_at >= billing_period_start
                )
            )
            
            if usage_type:
                query = query.filter(UsageRecord.usage_type == usage_type)
                result = query.first()
                return int(result.total_usage) if result and result.total_usage else 0
            else:
                results = query.group_by(UsageRecord.usage_type).all()
                return {result.usage_type: int(result.total_usage) for result in results}
            
        except Exception as e:
            self.logger.error(f"Error getting monthly usage: {e}")
            return {} if not usage_type else 0
    
    async def check_quota_limits(
        self,
        db: Session,
        user_id: int,
        usage_type: str,
        requested_usage: int = 1
    ) -> Dict[str, Any]:
        """Check if user can perform requested usage within quota limits."""
        try:
            subscription = await self.get_active_subscription(db, user_id)
            if not subscription:
                # Free tier limits
                quota_limits = {
                    "text_requests": 100,
                    "document_requests": 10,
                    "url_requests": 50,
                    "api_calls": 1000
                }
                limit = quota_limits.get(usage_type, 0)
            else:
                quota_limits = subscription.get_quota_limits()
                limit = quota_limits.get(usage_type, 0)
            
            # Unlimited usage
            if limit == -1:
                return {
                    "allowed": True,
                    "within_quota": True,
                    "current_usage": 0,
                    "limit": -1,
                    "overage": 0
                }
            
            current_usage = await self.get_monthly_usage(db, user_id, usage_type)
            remaining = max(0, limit - current_usage)
            
            # Check if request exceeds remaining quota
            overage = max(0, requested_usage - remaining)
            within_quota = overage == 0
            
            # Allow overage for paid plans
            allowed = within_quota or (subscription and subscription.tier != SubscriptionTier.FREE)
            
            return {
                "allowed": allowed,
                "within_quota": within_quota,
                "current_usage": current_usage,
                "limit": limit,
                "remaining": remaining,
                "overage": overage,
                "overage_cost": self.overage_pricing.get(usage_type, Decimal("0.00")) * overage
            }
            
        except Exception as e:
            self.logger.error(f"Error checking quota limits: {e}")
            return {
                "allowed": False,
                "within_quota": False,
                "current_usage": 0,
                "limit": 0,
                "overage": requested_usage
            }
    
    async def generate_invoice(
        self,
        db: Session,
        user_id: int,
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> Invoice:
        """Generate invoice for user's usage in billing period."""
        try:
            subscription = await self.get_active_subscription(db, user_id)
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found"
                )
            
            # Calculate subscription amount
            subtotal = subscription.effective_price
            
            # Calculate overage charges
            usage_records = db.query(UsageRecord).filter(
                and_(
                    UsageRecord.user_id == user_id,
                    UsageRecord.billing_period_start == billing_period_start,
                    UsageRecord.overage_cost > 0
                )
            ).all()
            
            overage_total = sum(record.overage_cost for record in usage_records)
            subtotal += overage_total
            
            # Calculate tax (simplified - would integrate with tax service)
            tax_rate = Decimal("0.08")  # 8% tax
            tax_amount = subtotal * tax_rate
            
            total_amount = subtotal + tax_amount
            
            # Generate invoice number
            invoice_count = db.query(Invoice).filter(Invoice.user_id == user_id).count()
            invoice_number = f"INV-{user_id:06d}-{invoice_count + 1:04d}"
            
            # Create line items
            line_items = [
                {
                    "description": f"{subscription.tier.value.title()} Subscription",
                    "quantity": 1,
                    "unit_price": float(subscription.effective_price),
                    "total": float(subscription.effective_price)
                }
            ]
            
            if overage_total > 0:
                line_items.append({
                    "description": "Usage Overages",
                    "quantity": 1,
                    "unit_price": float(overage_total),
                    "total": float(overage_total)
                })
            
            # Create invoice
            invoice = Invoice(
                user_id=user_id,
                subscription_id=subscription.id,
                invoice_number=invoice_number,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                due_date=datetime.utcnow() + timedelta(days=30),
                line_items=json.dumps(line_items)
            )
            
            db.add(invoice)
            db.commit()
            db.refresh(invoice)
            
            self.logger.info(f"Invoice generated for user {user_id}: {invoice_number}")
            
            return invoice
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error generating invoice: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate invoice"
            )
    
    async def _calculate_prorated_amount(
        self,
        current_price: Decimal,
        new_price: Decimal,
        days_remaining: int,
        billing_cycle: BillingCycle
    ) -> Decimal:
        """Calculate prorated amount for subscription upgrade."""
        if billing_cycle == BillingCycle.MONTHLY:
            total_days = 30
        elif billing_cycle == BillingCycle.QUARTERLY:
            total_days = 90
        else:  # YEARLY
            total_days = 365
        
        # Calculate daily rates
        current_daily_rate = current_price / total_days
        new_daily_rate = new_price / total_days
        
        # Calculate prorated amount
        prorated_amount = (new_daily_rate - current_daily_rate) * days_remaining
        
        return max(Decimal("0.00"), prorated_amount)


# Global subscription service instance
subscription_service = SubscriptionService()
