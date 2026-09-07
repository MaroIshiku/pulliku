from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
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

    def test_08_public_links_and_safe_rename_are_owner_controlled(self) -> None:
        self.login()
        media = b"pulliku-public-media-test"
        original_name = "Frischer_Fisch.mp4"
        original_path = main.DOWNLOAD_DIR / original_name
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_bytes(media)
        now = main.utc_now()
        with main.connect() as conn:
            owner_id = conn.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()[0]
            cursor = conn.execute(
                """
                INSERT INTO downloads (
                  url, mode, playlist, title, status, progress, filename, file_size,
                  settings_json, created_by, created_at, updated_at
                ) VALUES (?, 'video', 0, ?, 'completed', 100, ?, ?, '{}', ?, ?, ?)
                """,
                ("https://example.test/media", "Frischer Fisch", original_name, len(media), owner_id, now, now),
            )
            download_id = cursor.lastrowid

        missing_csrf = self.client.post(f"/api/downloads/{download_id}/share")
        self.assertEqual(missing_csrf.status_code, 403)

        other_client = TestClient(main.app)
        self.login("download-user", "Strong-User-Credential-2027!", other_client)
        forbidden_share = other_client.post(
            f"/api/downloads/{download_id}/share",
            headers={"X-CSRF-Token": self.csrf(other_client)},
        )
        self.assertEqual(forbidden_share.status_code, 404)
        forbidden_rename = other_client.patch(
            f"/api/downloads/{download_id}/filename",
            headers={"X-CSRF-Token": self.csrf(other_client)},
            json={"filename": "stolen.mp4"},
        )
        self.assertEqual(forbidden_rename.status_code, 404)
        other_client.close()

        shared = self.client.post(
            f"/api/downloads/{download_id}/share",
            headers={"X-CSRF-Token": self.csrf()},
        )
        self.assertEqual(shared.status_code, 200, shared.text)
        public_url = shared.json()["public_url"]
        public_path = urlparse(public_url).path
        path_parts = public_path.split("/")
        self.assertRegex(path_parts[1], r"^[A-Za-z0-9_-]{32}$")
        self.assertEqual(unquote(path_parts[2]), original_name)

        anonymous = TestClient(main.app)
        opened = anonymous.get(public_path)
        self.assertEqual(opened.status_code, 200, opened.text)
        self.assertEqual(opened.content, media)
        self.assertIn("inline", opened.headers["content-disposition"])
        self.assertEqual(opened.headers["cache-control"], "no-store")
        ranged = anonymous.get(public_path, headers={"Range": "bytes=0-6"})
        self.assertEqual(ranged.status_code, 206, ranged.text)
        self.assertEqual(ranged.content, media[:7])
        self.assertEqual(anonymous.get(f"/{'A' * 32}/{original_name}").status_code, 404)

        traversal = self.client.patch(
            f"/api/downloads/{download_id}/filename",
            headers={"X-CSRF-Token": self.csrf()},
            json={"filename": "../outside.mp4"},
        )
        self.assertEqual(traversal.status_code, 400)
        wrong_extension = self.client.patch(
            f"/api/downloads/{download_id}/filename",
            headers={"X-CSRF-Token": self.csrf()},
            json={"filename": "Frischer Fisch.mov"},
        )
        self.assertEqual(wrong_extension.status_code, 400)

        collision_path = main.DOWNLOAD_DIR / "Already here.mp4"
        collision_path.write_bytes(b"occupied")
        collision = self.client.patch(
            f"/api/downloads/{download_id}/filename",
            headers={"X-CSRF-Token": self.csrf()},
            json={"filename": collision_path.name},
        )
        self.assertEqual(collision.status_code, 409)
        collision_path.unlink()

        renamed = self.client.patch(
            f"/api/downloads/{download_id}/filename",
            headers={"X-CSRF-Token": self.csrf()},
            json={"filename": "Wie man Pad Thai kocht"},
        )
        self.assertEqual(renamed.status_code, 200, renamed.text)
        new_name = "Wie man Pad Thai kocht.mp4"
        self.assertEqual(renamed.json()["download"]["filename"], new_name)
        self.assertFalse(original_path.exists())
        self.assertTrue((main.DOWNLOAD_DIR / new_name).is_file())

        stale = anonymous.get(public_path, follow_redirects=False)
        self.assertEqual(stale.status_code, 307)
        self.assertEqual(unquote(stale.headers["location"].split("/")[-1]), new_name)
        canonical = anonymous.get(stale.headers["location"])
        self.assertEqual(canonical.status_code, 200)
        self.assertEqual(canonical.content, media)

        with main.connect() as conn:
            row = conn.execute(
                "SELECT public_share_nonce, public_token_hash FROM downloads WHERE id = ?",
                (download_id,),
            ).fetchone()
            audit_rows = conn.execute(
                "SELECT action, target FROM audit_events WHERE target = ?",
                (str(download_id),),
            ).fetchall()
        token = path_parts[1]
        self.assertNotEqual(row["public_share_nonce"], token)
        self.assertEqual(row["public_token_hash"], main.hash_token(token))
        self.assertTrue(all(token not in (entry["target"] or "") for entry in audit_rows))
        self.assertEqual(main.SHARE_KEY_PATH.stat().st_mode & 0o777, 0o600)

        revoked = self.client.delete(
            f"/api/downloads/{download_id}/share",
            headers={"X-CSRF-Token": self.csrf()},
        )
        self.assertEqual(revoked.status_code, 200, revoked.text)
        self.assertEqual(anonymous.get(stale.headers["location"]).status_code, 404)
        anonymous.close()

    def test_09_progress_parser_and_native_progress_styling(self) -> None:
        progress, speed, eta = main.parse_progress("[download]  42.7% of 10.00MiB at 3.25MiB/s ETA 00:03")
        self.assertEqual(progress, 42.7)
        self.assertEqual(speed, "3.25MiB/s")
        self.assertEqual(eta, "00:03")
        script = (Path(main.__file__).parent / "static" / "app.js").read_text(encoding="utf-8")
        styles = (Path(main.__file__).parent / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn('<progress class="progress-bar" value="${progress}"', script)
        progress_rule = styles.split(".progress-bar {", 1)[1].split("}", 1)[0]
        self.assertIn("background: transparent", progress_rule)


if __name__ == "__main__":
    unittest.main()
