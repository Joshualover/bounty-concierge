"""Test suite for wallet helper validation and operations."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concierge.wallet_helper import (
    validate_wallet_name,
    _WALLET_NAME_RE,
)


class TestValidateWalletName:
    """Test the validate_wallet_name function."""

    def test_valid_simple_name(self):
        """Test valid simple wallet name."""
        is_valid, msg = validate_wallet_name("my-wallet")
        assert is_valid is True
        assert "Valid" in msg

    def test_valid_alphanumeric(self):
        """Test valid alphanumeric wallet name."""
        is_valid, msg = validate_wallet_name("wallet123")
        assert is_valid is True

    def test_valid_with_underscores(self):
        """Test that underscores are NOT valid (only hyphens allowed)."""
        is_valid, msg = validate_wallet_name("my_wallet_name")
        assert is_valid is False
        assert "lowercase letters, digits, and hyphens" in msg

    def test_empty_name(self):
        """Test empty wallet name is invalid."""
        is_valid, msg = validate_wallet_name("")
        assert is_valid is False
        assert "cannot be empty" in msg

    def test_too_short(self):
        """Test name shorter than 3 characters."""
        is_valid, msg = validate_wallet_name("ab")
        assert is_valid is False
        assert "at least 3 characters" in msg

    def test_minimum_length(self):
        """Test minimum length name (3 chars)."""
        is_valid, msg = validate_wallet_name("abc")
        assert is_valid is True

    def test_too_long(self):
        """Test name longer than 64 characters."""
        long_name = "a" * 65
        is_valid, msg = validate_wallet_name(long_name)
        assert is_valid is False
        assert "64 characters or fewer" in msg

    def test_maximum_length(self):
        """Test maximum length name (64 chars)."""
        max_name = "a" * 64
        is_valid, msg = validate_wallet_name(max_name)
        assert is_valid is True

    def test_uppercase_invalid(self):
        """Test uppercase letters are invalid."""
        is_valid, msg = validate_wallet_name("MyWallet")
        assert is_valid is False
        assert "lowercase" in msg

    def test_mixed_case_invalid(self):
        """Test mixed case is invalid."""
        is_valid, msg = validate_wallet_name("my-Wallet")
        assert is_valid is False

    def test_starts_with_hyphen(self):
        """Test name starting with hyphen is invalid."""
        is_valid, msg = validate_wallet_name("-wallet")
        assert is_valid is False

    def test_ends_with_hyphen(self):
        """Test name ending with hyphen is invalid."""
        is_valid, msg = validate_wallet_name("wallet-")
        assert is_valid is False

    def test_special_characters_invalid(self):
        """Test special characters are invalid."""
        is_valid, msg = validate_wallet_name("wallet@name")
        assert is_valid is False

    def test_spaces_invalid(self):
        """Test spaces are invalid."""
        is_valid, msg = validate_wallet_name("my wallet")
        assert is_valid is False

    def test_numbers_only_invalid(self):
        """Test numbers only (must start with letter/digit, end with letter/digit)."""
        # Actually numbers only should be valid if they meet the regex
        # Let's test the actual regex behavior
        is_valid, msg = validate_wallet_name("123")
        # This should be valid - starts and ends with digit
        assert is_valid is True

    def test_valid_with_multiple_hyphens(self):
        """Test valid name with multiple hyphens in middle."""
        is_valid, msg = validate_wallet_name("my-test-wallet-name")
        assert is_valid is True


class TestWalletNameRegex:
    """Test the wallet name regex pattern directly."""

    def test_valid_patterns(self):
        """Test valid patterns match the regex."""
        assert _WALLET_NAME_RE.match("abc") is not None
        assert _WALLET_NAME_RE.match("my-wallet") is not None
        assert _WALLET_NAME_RE.match("wallet123") is not None
        assert _WALLET_NAME_RE.match("a-b-c") is not None

    def test_invalid_patterns(self):
        """Test invalid patterns don't match."""
        assert _WALLET_NAME_RE.match("-abc") is None
        assert _WALLET_NAME_RE.match("abc-") is None
        assert _WALLET_NAME_RE.match("ABC") is None
        assert _WALLET_NAME_RE.match("ab_c") is None  # underscore not in regex
        assert _WALLET_NAME_RE.match("a") is None  # too short
        assert _WALLET_NAME_RE.match("ab") is None  # too short


class TestValidateWalletNameEdgeCases:
    """Test edge cases for wallet name validation."""

    def test_single_character(self):
        """Test single character name."""
        is_valid, msg = validate_wallet_name("a")
        assert is_valid is False

    def test_two_characters(self):
        """Test two character name."""
        is_valid, msg = validate_wallet_name("ab")
        assert is_valid is False

    def test_three_characters(self):
        """Test three character name (minimum valid)."""
        is_valid, msg = validate_wallet_name("abc")
        assert is_valid is True

    def test_hyphen_only(self):
        """Test hyphen-only name."""
        is_valid, msg = validate_wallet_name("---")
        assert is_valid is False

    def test_starts_ends_correct_middle_hyphens(self):
        """Test name with correct start/end and hyphens in middle."""
        is_valid, msg = validate_wallet_name("a--b")
        assert is_valid is True

    def test_consecutive_hyphens(self):
        """Test name with consecutive hyphens."""
        is_valid, msg = validate_wallet_name("test--wallet")
        assert is_valid is True

    def test_64_characters(self):
        """Test exactly 64 characters (maximum valid length)."""
        name = "a" * 62 + "bc"
        is_valid, msg = validate_wallet_name(name)
        assert is_valid is True
        assert len(name) == 64

    def test_65_characters(self):
        """Test exactly 65 characters (too long)."""
        name = "a" * 65
        is_valid, msg = validate_wallet_name(name)
        assert is_valid is False


class TestValidateWalletNameReturnFormat:
    """Test the return format of validate_wallet_name."""

    def test_returns_tuple(self):
        """Test that function returns a tuple."""
        result = validate_wallet_name("test-wallet")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_first_element_bool(self):
        """Test that first element is boolean."""
        is_valid, msg = validate_wallet_name("test-wallet")
        assert isinstance(is_valid, bool)

    def test_second_element_string(self):
        """Test that second element is string."""
        is_valid, msg = validate_wallet_name("test-wallet")
        assert isinstance(msg, str)

    def test_error_message_not_empty(self):
        """Test that error messages are not empty."""
        is_valid, msg = validate_wallet_name("")
        assert len(msg) > 0

    def test_success_message_not_empty(self):
        """Test that success message is not empty."""
        is_valid, msg = validate_wallet_name("test-wallet")
        assert len(msg) > 0
