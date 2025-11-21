import sys
import types
from pathlib import Path
from types import SimpleNamespace


def _install_stub_modules():
	if "firebase_admin" not in sys.modules:
		firebase_admin_stub = types.ModuleType("firebase_admin")
		firebase_auth_stub = types.ModuleType("firebase_admin.auth")
		firebase_auth_stub.verify_id_token = lambda token: {"uid": "test-user"}
		firebase_auth_stub.get_user = lambda uid: SimpleNamespace(
			email_verified=True,
			display_name="Test User",
		)
		firebase_admin_stub.auth = firebase_auth_stub
		sys.modules["firebase_admin"] = firebase_admin_stub
	sys.modules.setdefault("firebase_admin.auth", sys.modules["firebase_admin"].auth)

	if "google" not in sys.modules:
		google_module = types.ModuleType("google")
		sys.modules["google"] = google_module
	else:
		google_module = sys.modules["google"]

	auth_module = sys.modules.setdefault("google.auth", types.ModuleType("google.auth"))
	transport_module = sys.modules.setdefault(
		"google.auth.transport", types.ModuleType("google.auth.transport")
	)
	requests_module = sys.modules.setdefault(
		"google.auth.transport.requests",
		types.ModuleType("google.auth.transport.requests"),
	)

	google_module.auth = auth_module
	auth_module.transport = transport_module
	transport_module.requests = requests_module
	requests_module.Request = SimpleNamespace

	if "requests" not in sys.modules:
		requests_stub = types.ModuleType("requests")

		def _stubbed_post(*args, **kwargs):
			raise RuntimeError("requests.post stub called without monkeypatch")

		requests_stub.post = _stubbed_post
		sys.modules["requests"] = requests_stub


_install_stub_modules()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
	sys.path.insert(0, str(SRC_PATH))

