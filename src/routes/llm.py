from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512

class PersonSearch(BaseModel):
    """Defines the expected input structure from the user."""
    email: str
    first_name: str 
    last_name: str   

# class PersonaProfile(BaseModel):
#     name: str
#     current_job_title: Optional[str] = None
#     company: Optional[str] = None
#     location: Optional[str] = None
#     education: Optional[List[str]] = None
#     skills: Optional[List[str]] = None
#     professional_summary: Optional[str] = None
#     notable_achievements: Optional[List[str]] = None

class SearchRequest(BaseModel):
    queries: List[str]


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None

@router.post("/search_person")
async def search_person_profile(search_data: PersonSearch):
    """
    Searches the Apollo.io database for a person using name and email.
    Uses the People Match endpoint for high-confidence results.
    """
    
    # NEVER hardcode API keys. Use environment variables or a configuration file.
    APOLLO_API_KEY = "" # Replace with secure loading (e.g., os.getenv('APOLLO_API_KEY'))
    
    # 1. Prepare the headers for Apollo.io
    # The API key MUST be in the X-Api-Key header for this endpoint.
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    # 2. Prepare the payload (body) for Apollo.io - ONLY search criteria goes here
    apollo_payload = {}
    
    # Email is a strong identifier, but Apollo Match works best with multiple fields.
    if search_data.email:
        apollo_payload["email"] = search_data.email
    if search_data.first_name:
        apollo_payload["first_name"] = search_data.first_name
    if search_data.last_name:
        apollo_payload["last_name"] = search_data.last_name
    
    # if apollo_payload.get("email"):
    #     domain = apollo_payload["email"].split("@")[-1]
    #     apollo_payload["domain"] = domain
    
    # Ensure at least one search field is present
    if not apollo_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least 'email', or a combination of 'first_name' and 'last_name'."
        )

    try:
        # 3. Make the POST request to the Apollo.io API
        response = requests.post(
            "https://api.apollo.io/api/v1/people/match?reveal_personal_emails=false&reveal_phone_number=false",
            headers=headers, # Use the corrected headers
            json=apollo_payload, # Use the payload (without the api_key)
            timeout=10 
        )
        
        # ... (Steps 3 and 4 for status handling and response processing remain largely the same)
        
        # 4. Handle Apollo.io API response status
        if response.status_code != 200:
            # Raise an HTTP exception if Apollo.io returns an error (e.g., 401 Unauthorized for bad API Key)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Apollo.io API Error: {response.text}"
            )
            
        apollo_result = response.json()
        print("Apollo.io Response:", apollo_result)  # Debug log
        # 5. Process the successful response
        person_data = apollo_result.get("person")

        if person_data:
            return {
                "status": "success",
                "message": "Person profile found.",
                "person": person_data 
            }
        else:
            return {
                "status": "not_found",
                "message": "No matching person found in Apollo.io.",
                "person": None
            }

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Apollo.io API request timed out."
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error connecting to Apollo.io API: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )
