"""
DSPy modules for document-aware fact-checking.

This module contains DSPy signatures and modules for advanced fact-checking
with document context preservation and specialized analysis.
"""

# Import core data models
try:
    from .data_models import (
        DocumentClaim, Evidence, ClaimVerificationResult,
        DocumentFactCheckResult, ProcessingOptions, UncertaintyMetrics,
        ClaimType, VerificationResult, DocumentType, EvidenceType
    )
    DATA_MODELS_AVAILABLE = True
except ImportError as e:
    DATA_MODELS_AVAILABLE = False
    DocumentClaim = None
    Evidence = None
    ClaimVerificationResult = None
    DocumentFactCheckResult = None
    ProcessingOptions = None
    UncertaintyMetrics = None
    ClaimType = None
    VerificationResult = None
    DocumentType = None
    EvidenceType = None

# Import DSPy signatures
try:
    from .signatures import (
        DocumentClaimExtraction, DocumentClaimVerification, DocumentFactSynthesis
    )
    SIGNATURES_AVAILABLE = True
except ImportError as e:
    SIGNATURES_AVAILABLE = False
    DocumentClaimExtraction = None
    DocumentClaimVerification = None
    DocumentFactSynthesis = None

# Import DSPy modules
try:
    from .modules import (
        DocumentAwareFactChecker, UncertaintyEstimator
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    DocumentAwareFactChecker = None
    UncertaintyEstimator = None

# Import specialized modules
try:
    from .specialized import (
        AcademicCitationVerifier, MethodologyAnalyzer,
        NewsSourceCredibilityAnalyzer, NewsBiasDetector,
        LegalPrecedentChecker, StatuteVerifier
    )
    SPECIALIZED_AVAILABLE = True
except ImportError as e:
    SPECIALIZED_AVAILABLE = False
    AcademicCitationVerifier = None
    MethodologyAnalyzer = None
    NewsSourceCredibilityAnalyzer = None
    NewsBiasDetector = None
    LegalPrecedentChecker = None
    StatuteVerifier = None

__all__ = [
    # Data models
    "DocumentClaim",
    "Evidence",
    "ClaimVerificationResult",
    "DocumentFactCheckResult",
    "ProcessingOptions",
    "UncertaintyMetrics",
    "ClaimType",
    "VerificationResult",
    "DocumentType",
    "EvidenceType",

    # DSPy signatures
    "DocumentClaimExtraction",
    "DocumentClaimVerification",
    "DocumentFactSynthesis",

    # DSPy modules
    "DocumentAwareFactChecker",
    "UncertaintyEstimator",

    # Specialized modules
    "AcademicCitationVerifier",
    "MethodologyAnalyzer",
    "NewsSourceCredibilityAnalyzer",
    "NewsBiasDetector",
    "LegalPrecedentChecker",
    "StatuteVerifier",

    # Availability flags
    "DATA_MODELS_AVAILABLE",
    "SIGNATURES_AVAILABLE",
    "MODULES_AVAILABLE",
    "SPECIALIZED_AVAILABLE"
]