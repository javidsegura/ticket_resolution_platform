"""Unit tests for Firebase authentication dependency."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request


class TestVerifyUser:
	"""Test verify_user dependency factory."""

	def test_verify_user_success_basic(self):
		"""Test successful token verification without extra checks."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {}

		mock_decoded_token = {
			"uid": "user123",
			"email": "test@example.com",
		}

		mock_user_record = MagicMock()
		mock_user_record.email_verified = True
		mock_user_record.display_name = "Test User"

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.return_value = mock_decoded_token
			mock_auth.get_user.return_value = mock_user_record

			dependency_func = verify_user(
				email_needs_verification=False, user_private_route=False
			)
			result = dependency_func(request=mock_request, token="valid_token")

			assert result["uid"] == "user123"
			assert result["email"] == "test@example.com"
			assert result["email_verified"] is True
			assert result["display_name"] == "Test User"
			mock_auth.verify_id_token.assert_called_once_with("valid_token")
			mock_auth.get_user.assert_called_once_with("user123")

	def test_verify_user_email_verification_required_and_verified(self):
		"""Test email verification when required and email is verified."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {}

		mock_decoded_token = {"uid": "user123", "email": "test@example.com"}
		mock_user_record = MagicMock()
		mock_user_record.email_verified = True
		mock_user_record.display_name = "Test User"

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.return_value = mock_decoded_token
			mock_auth.get_user.return_value = mock_user_record

			dependency_func = verify_user(
				email_needs_verification=True, user_private_route=False
			)
			result = dependency_func(request=mock_request, token="valid_token")

			assert result["uid"] == "user123"
			assert result["email_verified"] is True

	def test_verify_user_email_not_verified_raises_exception(self):
		"""Test that unverified email raises exception when verification required."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {}

		mock_decoded_token = {"uid": "user123", "email": "test@example.com"}
		mock_user_record = MagicMock()
		mock_user_record.email_verified = False
		mock_user_record.display_name = "Test User"

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.return_value = mock_decoded_token
			mock_auth.get_user.return_value = mock_user_record

			dependency_func = verify_user(
				email_needs_verification=True, user_private_route=False
			)

			with pytest.raises(HTTPException) as exc_info:
				dependency_func(request=mock_request, token="valid_token")

			assert exc_info.value.status_code == 401
			assert "Email not verified" in str(exc_info.value.detail)

	def test_verify_user_private_route_matching_user_id(self):
		"""Test private route with matching user_id in path."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {"user_id": "user123"}

		mock_decoded_token = {"uid": "user123", "email": "test@example.com"}
		mock_user_record = MagicMock()
		mock_user_record.email_verified = True
		mock_user_record.display_name = "Test User"

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.return_value = mock_decoded_token
			mock_auth.get_user.return_value = mock_user_record

			dependency_func = verify_user(
				email_needs_verification=False, user_private_route=True
			)
			result = dependency_func(request=mock_request, token="valid_token")

			assert result["uid"] == "user123"

	def test_verify_user_private_route_mismatched_user_id(self):
		"""Test private route with mismatched user_id raises exception."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {"user_id": "different_user"}

		mock_decoded_token = {"uid": "user123", "email": "test@example.com"}
		mock_user_record = MagicMock()
		mock_user_record.email_verified = True
		mock_user_record.display_name = "Test User"

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.return_value = mock_decoded_token
			mock_auth.get_user.return_value = mock_user_record

			dependency_func = verify_user(
				email_needs_verification=False, user_private_route=True
			)

			with pytest.raises(HTTPException) as exc_info:
				dependency_func(request=mock_request, token="valid_token")

			assert exc_info.value.status_code == 401
			assert "Access denied" in str(exc_info.value.detail)

	def test_verify_user_private_route_missing_user_id_in_path(self):
		"""Test private route without user_id in path raises exception."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {}

		mock_decoded_token = {"uid": "user123", "email": "test@example.com"}
		mock_user_record = MagicMock()
		mock_user_record.email_verified = True
		mock_user_record.display_name = "Test User"

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.return_value = mock_decoded_token
			mock_auth.get_user.return_value = mock_user_record

			dependency_func = verify_user(
				email_needs_verification=False, user_private_route=True
			)

			with pytest.raises(HTTPException) as exc_info:
				dependency_func(request=mock_request, token="valid_token")

			# The inner HTTPException(500) is caught and re-raised as 401 with detail message
			assert exc_info.value.status_code == 401
			assert "Need to pass user id route" in str(exc_info.value.detail)

	def test_verify_user_invalid_token(self):
		"""Test that invalid token raises 401."""
		from ai_ticket_platform.dependencies.firebase import verify_user

		mock_request = MagicMock(spec=Request)
		mock_request.path_params = {}

		with patch("ai_ticket_platform.dependencies.firebase.auth") as mock_auth:
			mock_auth.verify_id_token.side_effect = Exception("Invalid token")

			dependency_func = verify_user(
				email_needs_verification=False, user_private_route=False
			)

			with pytest.raises(HTTPException) as exc_info:
				dependency_func(request=mock_request, token="invalid_token")

			assert exc_info.value.status_code == 401
			assert "Invalid token" in str(exc_info.value.detail)
