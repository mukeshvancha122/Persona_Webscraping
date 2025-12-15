# import requests
# # R2MT-LnoEmJm2S4jXVIhDg
# url = "https://api.apollo.io/api/v1/people/match?reveal_personal_emails=false&reveal_phone_number=false"

# headers = {
#     "accept": "application/json",
#     "Cache-Control": "no-cache",
#     "Content-Type": "application/json",
#     "x-api-key": ""
# }

# response = requests.post(url, headers=headers)

# print(response.text)
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import requests
import os

# --- Configuration ---
# NOTE: It is best practice to load the API key from environment variables.
# You must set this variable in your environment (e.g., in a .env file or shell export)
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_PEOPLE_MATCH_URL = "https://api.apollo.io/v1/people/match"

if not APOLLO_API_KEY:
    raise ValueError("APOLLO_API_KEY environment variable not set.")

app = FastAPI(title="Apollo.io Search Proxy")

# --- Pydantic Schema for Request Body ---
class PersonSearch(BaseModel):
    """Defines the expected input structure from the user."""
    email: str
    first_name: str | None = None  # Optional field
    last_name: str | None = None   # Optional field

# --- API Endpoint ---
@app.post("/api/v1/search_person")
async def search_person_profile(search_data: PersonSearch):
    """
    Searches the Apollo.io database for a person using email and name.
    Uses the People Match endpoint for high-confidence results.
    """
    
    # 1. Prepare the payload for Apollo.io
    # The 'people/match' endpoint prefers a combination of fields for a strong match.
    apollo_payload = {
        "api_key": APOLLO_API_KEY,
        "email": search_data.email
    }
    
    # Add optional name fields if provided
    if search_data.first_name:
        apollo_payload["first_name"] = search_data.first_name
    if search_data.last_name:
        apollo_payload["last_name"] = search_data.last_name

    try:
        # 2. Make the POST request to the Apollo.io API
        response = requests.post(
            APOLLO_PEOPLE_MATCH_URL,
            json=apollo_payload,
            timeout=10 # Set a timeout for the external API call
        )
        
        # 3. Handle Apollo.io API response status
        if response.status_code != 200:
            # Raise an HTTP exception if Apollo.io returns an error
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Apollo.io API Error: {response.text}"
            )
            
        apollo_result = response.json()
        
        # 4. Process the successful response
        person_data = apollo_result.get("person")

        if person_data:
            return {
                "status": "success",
                "message": "Person profile found.",
                "person": person_data # Returns the full person object from Apollo
            }
        else:
            # Apollo.io returns 200 even for no match, but the 'person' field is null/empty
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
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )