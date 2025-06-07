"""Data models for the fact checker system.

All the structured types used throughout the orchestration workflow.
"""

from datetime import datetime
from typing import Annotated, List, Optional

from operator import add
from pydantic import BaseModel, Field

from claim_extractor import ValidatedClaim
from claim_verifier import Verdict


class FactCheckReport(BaseModel):
    """The final output of the fact-checking process."""

    question: str = Field(description="The question that was fact-checked")
    answer: str = Field(description="The answer to the question")
    claims_verified: int = Field(description="Number of claims that were verified")
    verified_claims: List[Verdict] = Field(
        description="Results for each verified claim"
    )
    summary: str = Field(description="A concise summary of the fact-checking results")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the fact-check was performed"
    )


class FactCheckerState(BaseModel):
    """The state for the main fact checker workflow."""

    question: str = Field(description="The question to fact-check")
    answer: str = Field(description="The answer to the question")
    extracted_claims: List[ValidatedClaim] = Field(
        default_factory=list, description="Claims extracted from the answer"
    )
    verification_results: Annotated[List[Verdict], add] = Field(
        default_factory=list, description="Verification results for each claim"
    )
    final_report: Optional[FactCheckReport] = Field(
        default=None, description="The final fact-checking report"
    )
