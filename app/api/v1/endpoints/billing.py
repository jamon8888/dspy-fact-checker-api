"""
Billing API Endpoints

API endpoints for subscription management, billing, and usage tracking.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.services.subscription_service import subscription_service
from app.models.subscription import SubscriptionTier, BillingCycle
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class SubscriptionRequest(BaseModel):
    """Subscription creation request model."""
    
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    billing_cycle: BillingCycle = Field(default=BillingCycle.MONTHLY, description="Billing cycle")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    trial_days: Optional[int] = Field(None, ge=0, le=30, description="Trial period in days")


class SubscriptionUpgradeRequest(BaseModel):
    """Subscription upgrade request model."""
    
    new_tier: SubscriptionTier = Field(..., description="New subscription tier")
    billing_cycle: Optional[BillingCycle] = Field(None, description="New billing cycle")


class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    
    id: int
    tier: str
    status: str
    billing_cycle: str
    base_price: float
    effective_price: float
    currency: str
    start_date: str
    end_date: str
    next_billing_date: Optional[str]
    trial_end_date: Optional[str]
    is_active: bool
    is_trial: bool
    days_remaining: int
    quota_limits: Dict[str, int]


class UsageResponse(BaseModel):
    """Usage response model."""
    
    period: str
    start_date: str
    end_date: str
    subscription_tier: Optional[str]
    usage: Dict[str, Dict[str, Any]]
    overage: Dict[str, float]
    estimated_total: float


class QuotaCheckResponse(BaseModel):
    """Quota check response model."""
    
    allowed: bool
    within_quota: bool
    current_usage: int
    limit: int
    remaining: int
    overage: int
    overage_cost: float


class InvoiceResponse(BaseModel):
    """Invoice response model."""
    
    id: int
    invoice_number: str
    status: str
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str
    billing_period_start: str
    billing_period_end: str
    issue_date: str
    due_date: str
    paid_date: Optional[str]
    is_overdue: bool
    line_items: List[Dict[str, Any]]


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create or update a subscription for the current user.
    
    Creates a new subscription with the specified tier and billing cycle.
    """
    try:
        subscription = await subscription_service.create_subscription(
            db=db,
            user_id=current_user.id,
            tier=request.tier,
            billing_cycle=request.billing_cycle,
            payment_method_id=request.payment_method_id,
            trial_days=request.trial_days
        )
        
        quota_limits = subscription.get_quota_limits()
        
        return SubscriptionResponse(
            id=subscription.id,
            tier=subscription.tier.value,
            status=subscription.status.value,
            billing_cycle=subscription.billing_cycle.value,
            base_price=float(subscription.base_price),
            effective_price=float(subscription.effective_price),
            currency=subscription.currency,
            start_date=subscription.start_date.isoformat(),
            end_date=subscription.end_date.isoformat(),
            next_billing_date=subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            trial_end_date=subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            is_active=subscription.is_active,
            is_trial=subscription.is_trial,
            days_remaining=subscription.days_remaining,
            quota_limits=quota_limits
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription creation failed"
        )


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's active subscription.
    """
    try:
        subscription = await subscription_service.get_active_subscription(db, current_user.id)
        
        if not subscription:
            return None
        
        quota_limits = subscription.get_quota_limits()
        
        return SubscriptionResponse(
            id=subscription.id,
            tier=subscription.tier.value,
            status=subscription.status.value,
            billing_cycle=subscription.billing_cycle.value,
            base_price=float(subscription.base_price),
            effective_price=float(subscription.effective_price),
            currency=subscription.currency,
            start_date=subscription.start_date.isoformat(),
            end_date=subscription.end_date.isoformat(),
            next_billing_date=subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            trial_end_date=subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            is_active=subscription.is_active,
            is_trial=subscription.is_trial,
            days_remaining=subscription.days_remaining,
            quota_limits=quota_limits
        )
        
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upgrade subscription to a higher tier.
    """
    try:
        subscription = await subscription_service.upgrade_subscription(
            db=db,
            user_id=current_user.id,
            new_tier=request.new_tier,
            billing_cycle=request.billing_cycle
        )
        
        quota_limits = subscription.get_quota_limits()
        
        return SubscriptionResponse(
            id=subscription.id,
            tier=subscription.tier.value,
            status=subscription.status.value,
            billing_cycle=subscription.billing_cycle.value,
            base_price=float(subscription.base_price),
            effective_price=float(subscription.effective_price),
            currency=subscription.currency,
            start_date=subscription.start_date.isoformat(),
            end_date=subscription.end_date.isoformat(),
            next_billing_date=subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            trial_end_date=subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            is_active=subscription.is_active,
            is_trial=subscription.is_trial,
            days_remaining=subscription.days_remaining,
            quota_limits=quota_limits
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription upgrade failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription upgrade failed"
        )


@router.post("/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel current subscription.
    
    If immediate=True, cancels immediately. Otherwise, cancels at end of billing period.
    """
    try:
        success = await subscription_service.cancel_subscription(
            db=db,
            user_id=current_user.id,
            immediate=immediate
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        return {
            "message": "Subscription cancelled successfully",
            "immediate": immediate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription cancellation failed"
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    period: str = "current",  # current, previous, or YYYY-MM
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for the current user.
    """
    try:
        # Determine date range based on period
        now = datetime.utcnow()
        if period == "current":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = start_date.replace(year=now.year + 1, month=1)
            else:
                end_date = start_date.replace(month=now.month + 1)
        elif period == "previous":
            if now.month == 1:
                start_date = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Parse YYYY-MM format
            try:
                year, month = map(int, period.split('-'))
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid period format. Use 'current', 'previous', or 'YYYY-MM'"
                )
        
        # Get subscription details
        subscription = await subscription_service.get_active_subscription(db, current_user.id)
        
        # Get usage data
        usage_data = await subscription_service.get_monthly_usage(db, current_user.id)
        
        # Get quota limits
        if subscription:
            quota_limits = subscription.get_quota_limits()
            subscription_tier = subscription.tier.value
        else:
            quota_limits = {
                "text_requests": 100,
                "document_requests": 10,
                "url_requests": 50,
                "api_calls": 1000
            }
            subscription_tier = "free"
        
        # Calculate usage percentages and overage
        usage_response = {}
        overage_response = {}
        total_overage = 0.0
        
        for usage_type, limit in quota_limits.items():
            used = usage_data.get(usage_type, 0)
            
            if limit == -1:  # Unlimited
                percentage = 0.0
                overage = 0
            else:
                percentage = (used / limit * 100) if limit > 0 else 0
                overage = max(0, used - limit)
            
            usage_response[usage_type] = {
                "used": used,
                "limit": limit,
                "percentage": percentage,
                "remaining": max(0, limit - used) if limit > 0 else -1
            }
            
            # Calculate overage cost
            overage_cost = 0.0
            if overage > 0:
                overage_rates = {
                    "text_requests": 0.01,
                    "document_requests": 0.10,
                    "url_requests": 0.02,
                    "api_calls": 0.001
                }
                overage_cost = overage * overage_rates.get(usage_type, 0.0)
                total_overage += overage_cost
            
            overage_response[usage_type] = overage_cost
        
        # Calculate estimated total
        base_cost = float(subscription.effective_price) if subscription else 0.0
        estimated_total = base_cost + total_overage
        
        return UsageResponse(
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            subscription_tier=subscription_tier,
            usage=usage_response,
            overage=overage_response,
            estimated_total=estimated_total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage data"
        )


@router.get("/quota-check/{usage_type}", response_model=QuotaCheckResponse)
async def check_quota(
    usage_type: str,
    requested_usage: int = 1,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check quota limits for a specific usage type.
    """
    try:
        quota_check = await subscription_service.check_quota_limits(
            db=db,
            user_id=current_user.id,
            usage_type=usage_type,
            requested_usage=requested_usage
        )
        
        return QuotaCheckResponse(**quota_check)
        
    except Exception as e:
        logger.error(f"Error checking quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check quota"
        )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's invoices.
    """
    try:
        from app.models.subscription import Invoice
        import json
        
        invoices = db.query(Invoice).filter(
            Invoice.user_id == current_user.id
        ).order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()
        
        invoice_responses = []
        for invoice in invoices:
            line_items = json.loads(invoice.line_items) if invoice.line_items else []
            
            invoice_responses.append(InvoiceResponse(
                id=invoice.id,
                invoice_number=invoice.invoice_number,
                status=invoice.status.value,
                subtotal=float(invoice.subtotal),
                tax_amount=float(invoice.tax_amount),
                total_amount=float(invoice.total_amount),
                currency=invoice.currency,
                billing_period_start=invoice.billing_period_start.isoformat(),
                billing_period_end=invoice.billing_period_end.isoformat(),
                issue_date=invoice.issue_date.isoformat(),
                due_date=invoice.due_date.isoformat(),
                paid_date=invoice.paid_date.isoformat() if invoice.paid_date else None,
                is_overdue=invoice.is_overdue,
                line_items=line_items
            ))
        
        return invoice_responses
        
    except Exception as e:
        logger.error(f"Error getting invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get invoices"
        )


@router.get("/pricing")
async def get_pricing():
    """
    Get subscription tier pricing information.
    """
    try:
        pricing = {
            "tiers": {
                "free": {
                    "name": "Free",
                    "price": {"monthly": 0, "quarterly": 0, "yearly": 0},
                    "features": [
                        "100 text fact-checks per month",
                        "10 document fact-checks per month",
                        "50 URL fact-checks per month",
                        "Basic fact-checking models",
                        "Email support"
                    ],
                    "limits": {
                        "text_requests": 100,
                        "document_requests": 10,
                        "url_requests": 50,
                        "api_calls": 1000,
                        "storage_gb": 1
                    }
                },
                "starter": {
                    "name": "Starter",
                    "price": {"monthly": 29, "quarterly": 79, "yearly": 290},
                    "features": [
                        "1,000 text fact-checks per month",
                        "100 document fact-checks per month",
                        "500 URL fact-checks per month",
                        "Advanced fact-checking models",
                        "API access",
                        "Priority email support"
                    ],
                    "limits": {
                        "text_requests": 1000,
                        "document_requests": 100,
                        "url_requests": 500,
                        "api_calls": 10000,
                        "storage_gb": 5
                    }
                },
                "professional": {
                    "name": "Professional",
                    "price": {"monthly": 99, "quarterly": 267, "yearly": 990},
                    "features": [
                        "10,000 text fact-checks per month",
                        "1,000 document fact-checks per month",
                        "5,000 URL fact-checks per month",
                        "All fact-checking models",
                        "Bulk processing",
                        "Advanced analytics",
                        "Phone & email support"
                    ],
                    "limits": {
                        "text_requests": 10000,
                        "document_requests": 1000,
                        "url_requests": 5000,
                        "api_calls": 100000,
                        "storage_gb": 50
                    }
                },
                "enterprise": {
                    "name": "Enterprise",
                    "price": {"monthly": 299, "quarterly": 807, "yearly": 2990},
                    "features": [
                        "Unlimited fact-checks",
                        "Custom model training",
                        "White-label solution",
                        "Dedicated support",
                        "SLA guarantee",
                        "Custom integrations"
                    ],
                    "limits": {
                        "text_requests": -1,
                        "document_requests": -1,
                        "url_requests": -1,
                        "api_calls": -1,
                        "storage_gb": 500
                    }
                }
            },
            "overage_pricing": {
                "text_requests": 0.01,
                "document_requests": 0.10,
                "url_requests": 0.02,
                "api_calls": 0.001
            },
            "currency": "USD"
        }
        
        return pricing
        
    except Exception as e:
        logger.error(f"Error getting pricing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pricing information"
        )
