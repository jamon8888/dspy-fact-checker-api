"""Data models for claim verification.

All the structured types used throughout the verification workflow.
"""

from enum import Enum
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from claim_extractor.schemas import ValidatedClaim
from operator import add


class VerificationResult(str, Enum):
    """Possible outcomes of a fact-checking verification."""

    SUPPORTED = "Supported"
    REFUTED = "Refuted"
    INSUFFICIENT_INFORMATION = "Insufficient Information"
    CONFLICTING_EVIDENCE = "Conflicting Evidence"


class Evidence(BaseModel):
    """A single piece of evidence retrieved from a search."""

    url: str = Field(description="The URL of the evidence source")
    text: str = Field(description="The text snippet of the evidence")
    title: Optional[str] = Field(
        default=None, description="The title of the source page"
    )


class Verdict(BaseModel):
    """The result of fact-checking a single claim."""

    claim_text: str = Field(description="The text of the claim that was checked")
    disambiguated_sentence: str = Field(
        description="The disambiguated sentence from which the claim was derived"
    )
    original_sentence: str = Field(
        description="The original sentence from which the claim was derived"
    )
    original_index: int = Field(
        description="The index of the original sentence in the source text"
    )
    result: VerificationResult = Field(
        description="The fact-checking verdict (Supported, Refuted, etc.)"
    )
    reasoning: str = Field(description="Brief explanation of the verdict")
    sources: List[Evidence] = Field(
        default_factory=list, description="List of evidence sources"
    )


class RetrieveEvidenceInput(BaseModel):
    """Input for the retrieve evidence node."""

    query: str = Field(description="The search query to retrieve evidence")


class ClaimVerifierState(BaseModel):
    """The workflow graph state for claim verification."""

    claim: ValidatedClaim = Field(description="The claim being verified")
    queries: List[str] = Field(
        default_factory=list, description="Generated search queries"
    )
    evidence: Annotated[List[Evidence], add] = Field(default_factory=list)
    verdict: Optional[Verdict] = Field(
        default=None, description="Final verification result"
    )
    retry_count: int = Field(
        default=0, description="Number of retry attempts for insufficient information"
    )
