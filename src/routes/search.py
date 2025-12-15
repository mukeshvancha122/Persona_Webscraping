import os
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field, model_validator

from src.services.orchestrator import spin_up_orchestrator, spin_up_orchestrator_anthropic
from src.services.search import SearchService
from src.types.orchestrator_plan import OrchestratorPlan, SearchResult


DEFAULT_SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "brave")
SUPPORTED_PLAN_PROVIDERS = {"google", "anthropic"}


class PersonSearchRequest(BaseModel):
    """Request payload when searching for a person by name/email."""

    name: Optional[str] = Field(None, description="Full name of the person to search for")
    email: Optional[EmailStr] = Field(None, description="Email address belonging to the target person")
    search_providers: Optional[List[str]] = Field(
        None,
        description="List of search providers to query (e.g. ['brave', 'serpapi'])",
    )
    include_plan: bool = Field(True, description="Whether to include the orchestrator plan in the response")
    plan_provider: Literal["google", "anthropic"] = Field(
        "google",
        description="LLM provider for generating the orchestrator plan",
    )
    extra_context: Optional[str] = Field(
        None,
        description="Additional context appended to the search query and plan prompt",
    )

    @model_validator(mode="before")
    def ensure_contact_info(cls, values):
        name = values.get("name")
        email = values.get("email")
        if not name and not email:
            raise ValueError("At least one of 'name' or 'email' is required")
        return values


class ProviderSearchResults(BaseModel):
    provider: str
    results: List[SearchResult]


class PersonSearchResponse(BaseModel):
    """Response shape for the person search endpoint."""

    query: str
    name: Optional[str]
    email: Optional[EmailStr]
    plan_provider: Literal["google", "anthropic"]
    orchestrator_plan: Optional[OrchestratorPlan]
    search_results: List[ProviderSearchResults]


router = APIRouter()


async def _generate_plan(query: str, provider: str) -> OrchestratorPlan:
    provider = provider.lower()
    if provider == "anthropic":
        return await spin_up_orchestrator_anthropic(query)
    return await spin_up_orchestrator(query)


@router.post("/person", response_model=PersonSearchResponse)
async def person_search(request_body: PersonSearchRequest):
    """Search for a person using name/email and return provider results + plan."""
    parts = [request_body.name, request_body.email, request_body.extra_context]
    query = " ".join(part.strip() for part in parts if part and part.strip())
    if not query:
        raise HTTPException(status_code=400, detail="Unable to construct a query from the request data")

    providers = request_body.search_providers or [DEFAULT_SEARCH_PROVIDER]
    normalized_providers = []
    for provider in providers:
        if not provider:
            continue
        normalized = provider.strip().lower()
        if normalized and normalized not in normalized_providers:
            normalized_providers.append(normalized)
    if not normalized_providers:
        normalized_providers.append(DEFAULT_SEARCH_PROVIDER)

    provider_results: List[ProviderSearchResults] = []
    for provider in normalized_providers:
        results = await SearchService.search(query, provider_override=provider)
        provider_results.append(ProviderSearchResults(provider=provider, results=results))

    plan = None
    if request_body.include_plan:
        plan_provider = request_body.plan_provider.lower()
        if plan_provider not in SUPPORTED_PLAN_PROVIDERS:
            raise HTTPException(status_code=400, detail="Unsupported plan provider")
        try:
            plan = await _generate_plan(query, plan_provider)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to generate orchestrator plan: {exc}")

    return PersonSearchResponse(
        query=query,
        name=request_body.name,
        email=request_body.email,
        plan_provider=request_body.plan_provider,
        orchestrator_plan=plan,
        search_results=provider_results,
    )

