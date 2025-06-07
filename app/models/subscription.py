"""
Subscription and Billing Models

Database models for subscription management, billing, and usage tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
from decimal import Decimal as PyDecimal

from app.db.base_class import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tier levels."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PENDING = "pending"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class BillingCycle(str, enum.Enum):
    """Billing cycle options."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Subscription(Base):
    """Subscription model for managing user subscriptions."""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Subscription details
    tier = Column(SQLEnum(SubscriptionTier), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    billing_cycle = Column(SQLEnum(BillingCycle), default=BillingCycle.MONTHLY, nullable=False)
    
    # Pricing
    base_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)
    
    # Billing dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    next_billing_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Payment integration
    external_subscription_id = Column(String(255), nullable=True)  # Stripe/PayPal ID
    external_customer_id = Column(String(255), nullable=True)
    payment_method_id = Column(String(255), nullable=True)
    
    # Quota and usage limits
    monthly_text_requests = Column(Integer, default=0, nullable=False)
    monthly_document_requests = Column(Integer, default=0, nullable=False)
    monthly_url_requests = Column(Integer, default=0, nullable=False)
    monthly_api_calls = Column(Integer, default=0, nullable=False)
    storage_limit_gb = Column(Integer, default=1, nullable=False)
    
    # Features
    features = Column(Text, nullable=True)  # JSON array of enabled features
    custom_models_enabled = Column(Boolean, default=False, nullable=False)
    priority_support = Column(Boolean, default=False, nullable=False)
    white_label_enabled = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    notes = Column(Text, nullable=True)
    subscription_metadata = Column(Text, nullable=True)  # JSON for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier}', status='{self.status}')>"
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            datetime.utcnow() <= self.end_date
        )
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period."""
        return (
            self.status == SubscriptionStatus.TRIALING and
            self.trial_end_date and
            datetime.utcnow() <= self.trial_end_date
        )
    
    @property
    def days_remaining(self):
        """Get days remaining in current billing period."""
        if self.end_date:
            delta = self.end_date - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    @property
    def effective_price(self):
        """Get effective price after discounts."""
        discount_amount = self.base_price * (self.discount_percentage / 100)
        return self.base_price - discount_amount
    
    def get_quota_limits(self):
        """Get quota limits for this subscription tier."""
        tier_limits = {
            SubscriptionTier.FREE: {
                "text_requests": 100,
                "document_requests": 10,
                "url_requests": 50,
                "api_calls": 1000,
                "storage_gb": 1
            },
            SubscriptionTier.STARTER: {
                "text_requests": 1000,
                "document_requests": 100,
                "url_requests": 500,
                "api_calls": 10000,
                "storage_gb": 5
            },
            SubscriptionTier.PROFESSIONAL: {
                "text_requests": 10000,
                "document_requests": 1000,
                "url_requests": 5000,
                "api_calls": 100000,
                "storage_gb": 50
            },
            SubscriptionTier.ENTERPRISE: {
                "text_requests": -1,  # Unlimited
                "document_requests": -1,
                "url_requests": -1,
                "api_calls": -1,
                "storage_gb": 500
            }
        }
        
        # Use custom limits if set, otherwise use tier defaults
        defaults = tier_limits.get(self.tier, tier_limits[SubscriptionTier.FREE])
        return {
            "text_requests": self.monthly_text_requests or defaults["text_requests"],
            "document_requests": self.monthly_document_requests or defaults["document_requests"],
            "url_requests": self.monthly_url_requests or defaults["url_requests"],
            "api_calls": self.monthly_api_calls or defaults["api_calls"],
            "storage_gb": self.storage_limit_gb or defaults["storage_gb"]
        }


class UsageRecord(Base):
    """Usage tracking model for billing and quota management."""
    
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True, index=True)
    
    # Usage details
    usage_type = Column(String(50), nullable=False, index=True)  # text, document, url, api
    usage_count = Column(Integer, default=1, nullable=False)
    usage_amount = Column(Numeric(10, 4), nullable=True)  # For usage-based billing

    # Request details
    endpoint = Column(String(100), nullable=True)
    model_used = Column(String(50), nullable=True)
    tokens_processed = Column(Integer, nullable=True)
    processing_time = Column(Numeric(8, 3), nullable=True)  # seconds

    # Cost tracking
    base_cost = Column(Numeric(10, 6), nullable=True)
    overage_cost = Column(Numeric(10, 6), nullable=True)
    total_cost = Column(Numeric(10, 6), nullable=True)
    
    # Metadata
    request_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_metadata = Column(Text, nullable=True)  # JSON for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    billing_period_start = Column(DateTime, nullable=False, index=True)
    billing_period_end = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
    subscription = relationship("Subscription", back_populates="usage_records")
    
    def __repr__(self):
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, type='{self.usage_type}', count={self.usage_count})>"


class Invoice(Base):
    """Invoice model for billing management."""
    
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True, index=True)
    
    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Billing period
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    
    # Payment details
    payment_method = Column(String(50), nullable=True)
    external_invoice_id = Column(String(255), nullable=True)  # Stripe/PayPal invoice ID
    payment_intent_id = Column(String(255), nullable=True)
    
    # Dates
    issue_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    paid_date = Column(DateTime, nullable=True)
    
    # Invoice content
    line_items = Column(Text, nullable=True)  # JSON array of line items
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount}, status='{self.status}')>"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        return (
            self.status == PaymentStatus.PENDING and
            datetime.utcnow() > self.due_date
        )
    
    @property
    def days_overdue(self):
        """Get number of days overdue."""
        if self.is_overdue:
            delta = datetime.utcnow() - self.due_date
            return delta.days
        return 0


class PaymentMethod(Base):
    """Payment method model for storing user payment information."""
    
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Payment method details
    type = Column(String(20), nullable=False)  # card, bank_account, paypal
    provider = Column(String(20), nullable=False)  # stripe, paypal, etc.
    external_id = Column(String(255), nullable=False)  # Provider's payment method ID
    
    # Card details (if applicable)
    card_brand = Column(String(20), nullable=True)  # visa, mastercard, etc.
    card_last_four = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    
    # Bank account details (if applicable)
    bank_name = Column(String(100), nullable=True)
    account_last_four = Column(String(4), nullable=True)
    
    # Status and preferences
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, user_id={self.user_id}, type='{self.type}')>"
    
    @property
    def display_name(self):
        """Get display name for payment method."""
        if self.type == "card":
            return f"{self.card_brand.title()} ending in {self.card_last_four}"
        elif self.type == "bank_account":
            return f"{self.bank_name} ending in {self.account_last_four}"
        else:
            return f"{self.type.title()} account"


class BillingAddress(Base):
    """Billing address model for invoicing."""
    
    __tablename__ = "billing_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Address details
    company_name = Column(String(200), nullable=True)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    
    # Tax information
    tax_id = Column(String(50), nullable=True)  # VAT number, etc.
    
    # Status
    is_default = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<BillingAddress(id={self.id}, user_id={self.user_id}, country='{self.country}')>"
    
    @property
    def formatted_address(self):
        """Get formatted address string."""
        lines = []
        if self.company_name:
            lines.append(self.company_name)
        lines.append(self.address_line_1)
        if self.address_line_2:
            lines.append(self.address_line_2)
        
        city_line = self.city
        if self.state:
            city_line += f", {self.state}"
        city_line += f" {self.postal_code}"
        lines.append(city_line)
        lines.append(self.country)
        
        return "\n".join(lines)
