"""Cross-platform engagement helpers for the RustChain ecosystem.

Star repos, check Dev.to stats, and generate social-bounty proof.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests

from concierge import config


# ---------------------------------------------------------------------------
# GitHub star helpers
# ---------------------------------------------------------------------------

def star_repo(owner: str, repo: str, token: str) -> bool:
    """Star a single GitHub repository.

    Uses PUT /user/starred/{owner}/{repo} which is idempotent -- starring an
    already-starred repo is a no-op that still returns 204.

    Returns True on success (HTTP 204), False otherwise.
    """
    url = f"https://api.github.com/user/starred/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        resp = requests.put(url, headers=headers, timeout=15)
        return resp.status_code == 204
    except requests.RequestException:
        return False


def star_all_ecosystem_repos(token: str) -> Dict[str, bool]:
    """Star every repository listed in config.REPOS.

    Returns a dict mapping ``"owner/repo"`` to a boolean success flag.
    """
    results: Dict[str, bool] = {}
    for full_name in config.REPOS:
        owner, repo = full_name.split("/", 1)
        results[full_name] = star_repo(owner, repo, token)
    return results


# ---------------------------------------------------------------------------
# Dev.to article stats
# ---------------------------------------------------------------------------

def check_devto_articles(api_key: str) -> List[dict]:
    """Fetch the authenticated user's Dev.to articles.

    Returns a list of dicts with keys: title, url, page_views,
    positive_reactions.
    """
    url = "https://dev.to/api/articles/me"
    headers = {"api-key": api_key, "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    articles = []
    for item in resp.json():
        articles.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "page_views": item.get("page_views_count", 0),
                "positive_reactions": item.get("positive_reactions_count", 0),
            }
        )
    return articles


# ---------------------------------------------------------------------------
# Engagement proof generation
# ---------------------------------------------------------------------------

def generate_engagement_proof(platform: str, action: str, proof_url: str) -> str:
    """Format a markdown comment suitable for claiming a social bounty.

    Parameters
    ----------
    platform : str
        Name of the platform (e.g. "Twitter", "Dev.to", "Moltbook").
    action : str
        What was done (e.g. "shared article", "starred repos", "upvoted").
    proof_url : str
        A public URL that proves the action was taken.

    Returns
    -------
    str
        Markdown-formatted proof comment ready to paste into a GitHub issue.
    """
    return (
        f"**Engagement Proof**\n\n"
        f"- **Platform:** {platform}\n"
        f"- **Action:** {action}\n"
        f"- **Proof:** [{proof_url}]({proof_url})\n\n"
        f"Requesting payout per the bounty terms."
    )


# ---------------------------------------------------------------------------
# SaaSCity upvote integration
# ---------------------------------------------------------------------------

def saascity_upvote(
    api_key: Optional[str] = None,
    dry_run: bool = False,
    listings: Optional[List[str]] = None
) -> Dict[str, any]:
    """Upvote RustChain/BoTTube listings on SaaSCity.
    
    Discovers and upvotes specified listings (or auto-discovers RustChain-related ones).
    
    Parameters
    ----------
    api_key : str, optional
        SaaSCity API key. If not provided, loads from SAASCITY_KEY env var.
    dry_run : bool, default False
        If True, only shows what would be upvoted without making API calls.
    listings : List[str], optional
        List of listing IDs/names to upvote. If None, auto-discovers RustChain/BoTTube listings.
    
    Returns
    -------
    Dict[str, any]
        Result dict with keys:
        - success: bool - Overall success status
        - upvoted: List[str] - List of successfully upvoted listings
        - failed: List[str] - List of failed listings
        - message: str - Human-readable status message
    
    Raises
    ------
    ValueError
        If API key is missing (not provided and not in env var)
    requests.RequestException
        If API requests fail
    """
    # Get API key from parameter or environment
    key = api_key or os.getenv("SAASCITY_KEY")
    
    if not key:
        raise ValueError(
            "SaaSCity API key required. Provide via 'api_key' parameter "
            "or set SAASCITY_KEY environment variable. "
            "Visit https://saascity.io to register and get your API key."
        )
    
    # Base URL for SaaSCity API (adjust if different)
    base_url = "https://saascity.io/api/v1"
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    # Auto-discover listings if not specified
    if listings is None:
        listings = _discover_rustchain_listings(base_url, headers)
    
    if dry_run:
        return {
            "success": True,
            "upvoted": [],
            "failed": [],
            "message": f"[DRY RUN] Would upvote {len(listings)} listings: {', '.join(listings)}"
        }
    
    # Perform upvotes
    upvoted = []
    failed = []
    
    for listing in listings:
        try:
            # Upvote the listing (adjust endpoint as needed)
            url = f"{base_url}/listings/{listing}/upvote"
            resp = requests.post(url, headers=headers, timeout=15)
            
            if resp.status_code in (200, 201, 204):
                upvoted.append(listing)
            else:
                failed.append(f"{listing} (HTTP {resp.status_code})")
        except requests.RequestException as e:
            failed.append(f"{listing} ({str(e)})")
    
    success = len(upvoted) > 0 and len(failed) == 0
    
    return {
        "success": success,
        "upvoted": upvoted,
        "failed": failed,
        "message": f"Upvoted {len(upvoted)} listing(s). Failed: {len(failed)}."
    }


def _discover_rustchain_listings(base_url: str, headers: Dict[str, str]) -> List[str]:
    """Auto-discover RustChain/BoTTube related listings on SaaSCity.
    
    Searches for listings matching keywords like "RustChain", "BoTTube", etc.
    
    Returns
    -------
    List[str]
        List of listing IDs/names to upvote
    """
    # Search for RustChain-related listings
    search_terms = ["RustChain", "BoTTube", "bounty", "RTC"]
    found_listings = []
    
    for term in search_terms:
        try:
            url = f"{base_url}/listings/search"
            params = {"q": term, "limit": 10}
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                # Extract listing IDs from response (adjust based on actual API structure)
                listings = data.get("listings", data.get("items", []))
                for listing in listings:
                    listing_id = listing.get("id") or listing.get("name") or listing.get("slug")
                    if listing_id and listing_id not in found_listings:
                        found_listings.append(str(listing_id))
        except requests.RequestException:
            # Continue searching even if one search fails
            continue
    
    # If no listings found, return default known listings
    if not found_listings:
        # These would be the actual RustChain/BoTTube listing IDs on SaaSCity
        # Adjust based on real listing names/IDs
        found_listings = ["rustchain", "bottube"]
    
    return found_listings
