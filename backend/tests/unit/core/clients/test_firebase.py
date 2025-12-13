"""Unit tests for Firebase client initialization."""

import pytest
from unittest.mock import patch, MagicMock


class TestInitializeFirebase:
	"""Test initialize_firebase function."""

	@patch("ai_ticket_platform.core.clients.firebase.firebase_admin")
	def test_initialize_firebase_emulator_new_app(self, mock_firebase):
		"""Test Firebase initialization with emulator (new app)."""
		from ai_ticket_platform.core.clients.firebase import initialize_firebase

		# Simulate no existing app
		mock_firebase.get_app.side_effect = ValueError("No app")

		with patch.dict(
			"os.environ",
			{"USING_FIREBASE_EMULATOR": "true", "FB_PROJECT_ID": "test-project"},
		):
			initialize_firebase()

			mock_firebase.get_app.assert_called_once()
			mock_firebase.initialize_app.assert_called_once_with(
				options={"projectId": "test-project"}
			)

	@patch("ai_ticket_platform.core.clients.firebase.firebase_admin")
	def test_initialize_firebase_emulator_existing_app(self, mock_firebase):
		"""Test Firebase initialization with emulator (app already exists)."""
		from ai_ticket_platform.core.clients.firebase import initialize_firebase

		# Simulate existing app
		mock_firebase.get_app.return_value = MagicMock()

		with patch.dict(
			"os.environ",
			{"USING_FIREBASE_EMULATOR": "true", "FB_PROJECT_ID": "test-project"},
		):
			initialize_firebase()

			mock_firebase.get_app.assert_called_once()
			mock_firebase.initialize_app.assert_not_called()

	@patch("ai_ticket_platform.core.clients.firebase.firebase_admin")
	@patch("ai_ticket_platform.core.clients.firebase.credentials.Certificate")
	def test_initialize_firebase_real_auth_new_app(
		self, mock_certificate, mock_firebase
	):
		"""Test Firebase initialization with real auth (new app)."""
		from ai_ticket_platform.core.clients.firebase import initialize_firebase

		# Simulate no existing app
		mock_firebase.get_app.side_effect = ValueError("No app")
		mock_cred = MagicMock()
		mock_certificate.return_value = mock_cred

		with patch.dict(
			"os.environ", {"FIREBASE_CREDENTIALS_PATH": "/path/to/creds.json"}, clear=True
		):
			with patch("os.path.exists", return_value=True):
				initialize_firebase()

				mock_firebase.get_app.assert_called_once()
				mock_certificate.assert_called_once_with("/path/to/creds.json")
				mock_firebase.initialize_app.assert_called_once_with(mock_cred)

	@patch("ai_ticket_platform.core.clients.firebase.firebase_admin")
	@patch("ai_ticket_platform.core.clients.firebase.credentials.Certificate")
	def test_initialize_firebase_real_auth_existing_app(
		self, mock_certificate, mock_firebase
	):
		"""Test Firebase initialization with real auth (app already exists)."""
		from ai_ticket_platform.core.clients.firebase import initialize_firebase

		# Simulate existing app
		mock_firebase.get_app.return_value = MagicMock()
		mock_cred = MagicMock()
		mock_certificate.return_value = mock_cred

		with patch.dict(
			"os.environ", {"FIREBASE_CREDENTIALS_PATH": "/path/to/creds.json"}, clear=True
		):
			with patch("os.path.exists", return_value=True):
				initialize_firebase()

				mock_firebase.get_app.assert_called_once()
				mock_certificate.assert_called_once_with("/path/to/creds.json")
				mock_firebase.initialize_app.assert_not_called()

	def test_initialize_firebase_real_auth_missing_credentials_path(self):
		"""Test that ValueError is raised when credentials path is missing."""
		from ai_ticket_platform.core.clients.firebase import initialize_firebase

		with patch.dict("os.environ", {}, clear=True):
			with pytest.raises(ValueError) as exc_info:
				initialize_firebase()

			assert "FIREBASE_CREDENTIALS_PATH" in str(exc_info.value)

	def test_initialize_firebase_real_auth_credentials_file_not_found(self):
		"""Test that FileNotFoundError is raised when credentials file doesn't exist."""
		from ai_ticket_platform.core.clients.firebase import initialize_firebase

		with patch.dict(
			"os.environ", {"FIREBASE_CREDENTIALS_PATH": "/path/to/nonexistent.json"}, clear=True
		):
			with patch("os.path.exists", return_value=False):
				with pytest.raises(FileNotFoundError) as exc_info:
					initialize_firebase()

				assert "not found" in str(exc_info.value)
