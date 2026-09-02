from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


TEST_ROOT = Path(tempfile.mkdtemp(prefix="pulliku-tests-"))
os.environ["ISHIKU_DATA_DIR"] = str(TEST_ROOT / "data")
os.environ["DOWNLOAD_DIR"] = str(TEST_ROOT / "downloads")
os.environ["ISHIKU_SETUP_SECRET_FILE"] = ""
os.environ["ISHIKU_SETUP_SECRET"] = "Pulliku-Test-Setup-Secret-2026"
os.environ["APP_COOKIE_SECURE"] = "false"
os.environ["ISHIKU_TRUST_PROXY"] = "false"

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402


ADMIN_USERNAME = "security-admin"
ADMIN_PASSWORD = "Strong-Admin-Credential-2026!"
USER_PASSWORD = "Strong-User-Credential-2026!"


class SecurityIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(main.app)
        cls.client = cls.client_context.__enter__()
        response = cls.client.post(
            "/api/setup/register",
            json={
                "setup_secret": os.environ["ISHIKU_SETUP_SECRET"],
                "display_name": "Security Admin",
                "username": ADMIN_USERNAME,
                "email": "admin@example.test",
                "password": ADMIN_PASSWORD,
                "password_confirm": ADMIN_PASSWORD,
            },
        )
        assert response.status_code == 200, response.text

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def login(self, username: str = ADMIN_USERNAME, password: str | None = None, client: TestClient | None = None):
        active_client = client or self.client
        password = password or ADMIN_PASSWORD
        response = active_client.post("/api/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def csrf(self, client: TestClient | None = None) -> str:
        active_client = client or self.client
        value = active_client.cookies.get(main.CSRF_COOKIE_NAME)
        self.assertTrue(value)
        return value

    def test_01_argon2id_and_legacy_upgrade_contract(self) -> None:
        encoded = main.hash_password(ADMIN_PASSWORD)
        self.assertTrue(encoded.startswith("$argon2id$"))
        self.assertIn("m=19456,t=2,p=1", encoded)
        self.assertTrue(main.verify_password(ADMIN_PASSWORD, encoded))
        legacy = main.legacy_hash_password(ADMIN_PASSWORD)
        self.assertTrue(main.verify_password(ADMIN_PASSWORD, legacy))
        self.assertTrue(main.password_needs_rehash(legacy))

    def test_02_private_network_urls_are_rejected(self) -> None:
        with patch("app.main.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 80))]):
            with self.assertRaises(HTTPException) as context:
                main.validate_url("http://internal.example/video")
        self.assertEqual(context.exception.status_code, 400)

    def test_02b_legacy_hash_is_upgraded_on_login(self) -> None:
        with main.connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (main.legacy_hash_password(ADMIN_PASSWORD), ADMIN_USERNAME),
            )
        self.login()
        with main.connect() as conn:
            stored = conn.execute("SELECT password_hash FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()[0]
        self.assertTrue(stored.startswith("$argon2id$"))

    def test_03_login_errors_are_generic_and_audited(self) -> None:
        known = self.client.post("/api/login", json={"username": ADMIN_USERNAME, "password": "wrong"})
        unknown = self.client.post("/api/login", json={"username": "missing-user", "password": "wrong"})
        self.assertEqual(known.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(known.json()["detail"], unknown.json()["detail"])

        self.login()
        audit = self.client.get("/api/admin/audit")
        self.assertEqual(audit.status_code, 200)
        self.assertTrue(any(event["action"] == "auth.login" and event["result"] == "failed" for event in audit.json()["events"]))

    def test_04_csrf_and_forwarded_host_bypass_are_rejected(self) -> None:
        self.login()
        missing_csrf = self.client.put(
            "/api/me",
            json={"display_name": "Security Admin", "username": ADMIN_USERNAME},
        )
        self.assertEqual(missing_csrf.status_code, 403)

        bypass = self.client.post(
            "/api/login",
            headers={"Origin": "https://attacker.example", "X-Forwarded-Host": "attacker.example"},
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        self.assertEqual(bypass.status_code, 403)

    def test_05_idle_sessions_expire_server_side(self) -> None:
        self.login()
        token_hash = main.hash_token(self.client.cookies.get(main.SESSION_COOKIE_NAME))
        stale = (datetime.now(timezone.utc) - timedelta(minutes=main.SESSION_IDLE_MINUTES + 1)).isoformat()
        with main.connect() as conn:
            conn.execute("UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?", (stale, token_hash))
        response = self.client.get("/api/me")
        self.assertEqual(response.status_code, 401)
        with main.connect() as conn:
            self.assertIsNone(conn.execute("SELECT 1 FROM sessions WHERE token_hash = ?", (token_hash,)).fetchone())

    def test_06_password_change_revokes_sessions(self) -> None:
        global ADMIN_PASSWORD
        self.login()
        response = self.client.put(
            "/api/me",
            headers={"X-CSRF-Token": self.csrf()},
            json={
                "display_name": "Security Admin",
                "username": ADMIN_USERNAME,
                "current_password": ADMIN_PASSWORD,
                "new_password": "Strong-Admin-Credential-2027!",
                "password_confirm": "Strong-Admin-Credential-2027!",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["reauthenticate"])
        self.assertEqual(self.client.get("/api/me").status_code, 401)
        ADMIN_PASSWORD = "Strong-Admin-Credential-2027!"

    def test_07_admin_password_reset_revokes_target_sessions(self) -> None:
        self.login()
        created = self.client.post(
            "/api/admin/users",
            headers={"X-CSRF-Token": self.csrf()},
            json={"username": "download-user", "password": USER_PASSWORD, "is_admin": False},
        )
        self.assertEqual(created.status_code, 200, created.text)
        user_id = created.json()["user"]["id"]

        user_client = TestClient(main.app)
        self.login("download-user", USER_PASSWORD, user_client)
        reset = self.client.put(
            f"/api/admin/users/{user_id}/password",
            headers={"X-CSRF-Token": self.csrf()},
            json={"password": "Strong-User-Credential-2027!"},
        )
        self.assertEqual(reset.status_code, 200, reset.text)
        self.assertEqual(user_client.get("/api/me").status_code, 401)


if __name__ == "__main__":
    unittest.main()
