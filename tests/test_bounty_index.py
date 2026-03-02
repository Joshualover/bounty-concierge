"""Test suite for bounty index RTC parsing and aggregation."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concierge.bounty_index import (
    parse_reward,
    estimate_difficulty,
    tag_skills,
    format_markdown,
    _RTC_PATTERN,
)


class TestParseReward:
    """Test the parse_reward function for extracting RTC amounts."""

    def test_simple_amount(self):
        """Test parsing simple RTC amount."""
        reward = parse_reward("Test bounty 10 RTC", "")
        assert reward == 10.0

    def test_amount_in_body(self):
        """Test parsing amount from body when not in title."""
        reward = parse_reward("Test bounty", "This bounty pays 50 RTC")
        assert reward == 50.0

    def test_title_priority(self):
        """Test that title takes priority over body."""
        reward = parse_reward("100 RTC bounty", "Also mentions 50 RTC")
        assert reward == 100.0

    def test_decimal_amount(self):
        """Test parsing decimal RTC amounts."""
        reward = parse_reward("Test 0.5 RTC", "")
        assert reward == 0.5

    def test_comma_separator(self):
        """Test parsing amounts with comma separators."""
        reward = parse_reward("Test 1,000 RTC", "")
        assert reward == 1000.0

    def test_no_reward(self):
        """Test handling of text without RTC amount."""
        reward = parse_reward("Test bounty", "No reward mentioned")
        assert reward == 0.0

    def test_first_match_only(self):
        """Test that only first RTC amount is extracted."""
        reward = parse_reward("10 RTC and 20 RTC", "")
        assert reward == 10.0

    def test_case_insensitive(self):
        """Test that rtc is matched case-insensitively."""
        reward = parse_reward("Test 15 rtc", "")
        assert reward == 15.0

    def test_bounded_by_non_alphanumeric(self):
        """Test that RTC must be bounded by non-alphanumeric."""
        # Should match - space before number
        reward1 = parse_reward("Test 10 RTC", "")
        assert reward1 == 10.0
        
        # Should NOT match - part of another word
        reward2 = parse_reward("Test X10RTC value", "")
        assert reward2 == 0.0


class TestEstimateDifficulty:
    """Test the estimate_difficulty function."""

    def test_micro_tier(self):
        """Test micro difficulty tier."""
        assert estimate_difficulty("Test", [], 5) == "micro"
        assert estimate_difficulty("Test", [], 0) == "micro"

    def test_standard_tier(self):
        """Test standard difficulty tier."""
        assert estimate_difficulty("Test", [], 10) == "standard"
        assert estimate_difficulty("Test", [], 49) == "standard"

    def test_major_tier(self):
        """Test major difficulty tier."""
        assert estimate_difficulty("Test", [], 50) == "major"
        assert estimate_difficulty("Test", [], 199) == "major"

    def test_critical_tier(self):
        """Test critical difficulty tier."""
        assert estimate_difficulty("Test", [], 201) == "critical"

    def test_label_override(self):
        """Test that labels override reward-based estimation."""
        # Reward suggests standard but label says critical
        assert estimate_difficulty("Test", ["critical"], 10) == "critical"
        assert estimate_difficulty("Test", ["micro"], 200) == "micro"

    def test_label_case_insensitive(self):
        """Test that label matching is case-insensitive."""
        assert estimate_difficulty("Test", ["CRITICAL"], 10) == "critical"
        assert estimate_difficulty("Test", ["Micro"], 200) == "micro"


class TestTagSkills:
    """Test the tag_skills function."""

    def test_python_detection(self):
        """Test Python skill detection."""
        skills = tag_skills("Python script for .py file", "")
        assert "python" in skills

    def test_rust_detection(self):
        """Test Rust skill detection."""
        skills = tag_skills("Rust cargo crate .rs", "")
        assert "rust" in skills

    def test_javascript_detection(self):
        """Test JavaScript skill detection."""
        skills = tag_skills("React component .js typescript", "")
        assert "javascript" in skills

    def test_docker_detection(self):
        """Test Docker skill detection."""
        skills = tag_skills("Docker container dockerfile", "")
        assert "docker" in skills

    def test_documentation_detection(self):
        """Test documentation skill detection."""
        skills = tag_skills("Write README documentation", "")
        assert "documentation" in skills

    def test_security_detection(self):
        """Test security skill detection."""
        skills = tag_skills("Security audit vulnerability", "")
        assert "security" in skills

    def test_social_media_detection(self):
        """Test social media skill detection."""
        skills = tag_skills("Twitter bottube youtube", "")
        assert "social-media" in skills

    def test_multiple_skills(self):
        """Test detection of multiple skills."""
        skills = tag_skills("Python script with Docker container", "")
        assert "python" in skills
        assert "docker" in skills

    def test_no_skills(self):
        """Test when no skills match."""
        skills = tag_skills("Random task xyz", "")
        assert skills == []


class TestFormatMarkdown:
    """Test the format_markdown function."""

    def test_empty_list(self):
        """Test formatting empty bounty list."""
        result = format_markdown([])
        assert "| # | Repo | Title | RTC | Tier | Skills |" in result

    def test_single_bounty(self):
        """Test formatting single bounty."""
        bounties = [{
            "number": 1,
            "repo": "Scottcjn/test",
            "title": "Test Bounty",
            "reward_rtc": 10.0,
            "difficulty": "standard",
            "skills": ["python"],
        }]
        result = format_markdown(bounties)
        assert "1" in result
        assert "test" in result
        assert "Test Bounty" in result
        assert "10.0" in result

    def test_skills_formatting(self):
        """Test skills are formatted correctly."""
        bounties = [{
            "number": 1,
            "repo": "Scottcjn/test",
            "title": "Test",
            "reward_rtc": 10.0,
            "difficulty": "standard",
            "skills": ["python", "docker"],
        }]
        result = format_markdown(bounties)
        assert "python, docker" in result

    def test_no_skills_formatting(self):
        """Test empty skills are shown as dash."""
        bounties = [{
            "number": 1,
            "repo": "Scottcjn/test",
            "title": "Test",
            "reward_rtc": 10.0,
            "difficulty": "standard",
            "skills": [],
        }]
        result = format_markdown(bounties)
        assert "| - |" in result or "- |" in result


class TestRtcPattern:
    """Test the RTC regex pattern."""

    def test_valid_patterns(self):
        """Test valid RTC patterns match."""
        assert _RTC_PATTERN.search("10 RTC") is not None
        assert _RTC_PATTERN.search("1,000 RTC") is not None
        assert _RTC_PATTERN.search("0.5 rtc") is not None

    def test_invalid_patterns(self):
        """Test invalid patterns don't match."""
        assert _RTC_PATTERN.search("X10RTC") is None
        assert _RTC_PATTERN.search("RTC10") is None
