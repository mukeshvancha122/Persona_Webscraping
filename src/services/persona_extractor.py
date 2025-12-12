import re
from typing import Any, Dict, List, Optional


class PersonaExtractor:
    """Extract structured person persona from Perplexity search results.

    Parses title, full name, image, experience, email, and social media from snippets.
    """

    @staticmethod
    def extract_persona(result: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract persona fields from a single search result.

        Args:
            result: dict with 'title', 'url', 'snippet' keys from Perplexity search

        Returns:
            dict with keys: full_name, job_title, company, image_url, experience, email, social_media, source_url, bio
        """
        persona: Dict[str, Optional[str]] = {
            "full_name": None,
            "job_title": None,
            "company": None,
            "image_url": None,
            "experience": None,
            "email": None,
            "social_media": None,
            "source_url": result.get("url"),
            "bio": result.get("snippet", "")[:500],  # first 500 chars of snippet
        }

        title = result.get("title", "")
        snippet = result.get("snippet", "")
        url = result.get("url", "")

        # Extract full name from title (usually "FirstName LastName | Company/Title")
        if "|" in title:
            name_part = title.split("|")[0].strip()
        else:
            # fallback: first part before " - " or just use whole title
            name_part = title.split(" - ")[0].strip()

        # Clean up the name (remove HTML entities, extra punctuation)
        name_part = re.sub(r"[^\w\s]", "", name_part).strip()
        if name_part:
            persona["full_name"] = name_part

        # Extract job title from title or snippet
        # common patterns: "Title at Company", "Title | Company", "Job Title" in first line
        if "|" in title:
            title_part = title.split("|")[1].strip() if len(title.split("|")) > 1 else ""
            if title_part:
                persona["job_title"] = title_part[:100]  # limit to 100 chars

        # Extract experience from snippet (look for years, "years of", "expertise")
        exp_match = re.search(r"(\d+)\+?\s*(?:years?|year's)\s+(?:of\s+)?(?:experience|expertise)", snippet, re.IGNORECASE)
        if exp_match:
            persona["experience"] = f"{exp_match.group(1)}+ years"

        # Extract email (basic pattern)
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", snippet)
        if email_match:
            persona["email"] = email_match.group(0)

        # Extract social media handles or links (LinkedIn, Twitter, etc.)
        social_patterns = {
            "linkedin": r"(?:linkedin\.com/in/|@\w+.*linkedin)",
            "twitter": r"(?:twitter\.com/|@\w+(?:\s|$))",
            "github": r"github\.com/[\w-]+",
        }
        found_social = []
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, snippet + " " + url, re.IGNORECASE)
            if match:
                found_social.append(f"{platform}: {match.group(0)}")

        if found_social:
            persona["social_media"] = " | ".join(found_social)

        # Try to extract company from snippet (look for "at Company", "from Company")
        company_match = re.search(r"(?:at|from)\s+([A-Z][A-Za-z\s&]+?)(?:\s|,|-|$)", snippet)
        if company_match:
            persona["company"] = company_match.group(1).strip()

        return persona

    @staticmethod
    def extract_personas_from_results(results: List[Dict[str, Any]]) -> List[Dict[str, Optional[str]]]:
        """Extract personas from a list of search results (typically the 0th index).

        Args:
            results: list of result dicts from Perplexity search

        Returns:
            list of persona dicts
        """
        personas = []
        for result in results:
            if isinstance(result, dict):
                personas.append(PersonaExtractor.extract_persona(result))
        return personas
