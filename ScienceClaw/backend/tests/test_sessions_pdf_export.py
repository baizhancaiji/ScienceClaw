import sys
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.config import settings  # noqa: E402
from backend.deepagent.sessions import ScienceSessionNotFoundError  # noqa: E402
from backend.route import sessions as sessions_route  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402


@dataclass
class FakeScienceSession:
    session_id: str = "session-1"
    user_id: str = "user-1"
    title: str = "ScienceClaw PDF Export Title"


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(sessions_route.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


def _post_export(client: TestClient, payload: dict | None = None):
    return client.post(
        "/api/v1/sessions/session-1/export-pdf",
        json=payload or {"html": "<h1>Report</h1>", "css": ".markdown-content{color:#111827}", "locale": "zh"},
    )


class SessionsPdfExportTests(unittest.TestCase):
    def test_export_pdf_requires_authenticated_user(self):
        with patch.object(settings, "auth_provider", "local"):
            response = _post_export(TestClient(_make_app(authenticated=False)))

        self.assertEqual(401, response.status_code)

    def test_export_pdf_rejects_non_owner_with_i18n_error_code(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession(user_id="other-user")),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(403, response.status_code)
        self.assertEqual(
            {"code": "PDF_EXPORT_ACCESS_DENIED", "msg": "pdf_export.access_denied", "data": None},
            response.json(),
        )

    def test_export_pdf_returns_i18n_404_for_missing_session(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(side_effect=ScienceSessionNotFoundError("missing traceback secret html css stderr")),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(404, response.status_code)
        payload = response.json()
        self.assertEqual("PDF_EXPORT_SESSION_NOT_FOUND", payload["code"])
        self.assertEqual("pdf_export.session_not_found", payload["msg"])
        self.assertNotIn("missing", response.text)
        self.assertNotIn("traceback", response.text.lower())
        self.assertNotIn("stderr", response.text.lower())

    def test_export_pdf_rejects_payload_over_50mb_without_raw_body(self):
        too_large_html = "a" * (sessions_route._PDF_EXPORT_MAX_PAYLOAD_BYTES + 1)
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ):
            response = _post_export(TestClient(_make_app()), {"html": too_large_html, "css": "", "locale": "en"})

        self.assertEqual(413, response.status_code)
        self.assertEqual("PDF_EXPORT_PAYLOAD_TOO_LARGE", response.json()["code"])
        self.assertEqual("pdf_export.payload_too_large", response.json()["msg"])
        self.assertNotIn("aaaa", response.text)

    def test_pdf_request_model_does_not_accept_dark_field(self):
        fields = getattr(sessions_route.ExportPdfRequest, "model_fields", None) or sessions_route.ExportPdfRequest.__fields__
        self.assertNotIn("dark", fields)

    def test_truncates_pdf_header_title_by_unicode_character_count(self):
        self.assertEqual("一二三四五六七八九十甲乙丙丁戊...", sessions_route._truncate_pdf_header_title("一二三四五六七八九十甲乙丙丁戊己"))
        self.assertEqual("123456789012345", sessions_route._truncate_pdf_header_title("123456789012345"))

    def test_formats_pdf_exported_at_to_seconds_by_locale(self):
        exported_at = datetime(2026, 6, 3, 9, 8, 7, 123456)
        self.assertEqual("导出时间：2026-06-03 09:08:07", sessions_route._format_pdf_exported_at(exported_at, "zh"))
        self.assertEqual("Exported at: 2026-06-03 09:08:07", sessions_route._format_pdf_exported_at(exported_at, "en"))
        self.assertEqual("Exported at: 2026-06-03 09:08:07", sessions_route._format_pdf_exported_at(exported_at, "fr"))

    def test_build_pdf_html_is_light_and_has_no_dark_root(self):
        html = sessions_route._build_pdf_html(
            "<p>Hello</p>",
            ".markdown-content{font-size:14px}",
            header_title="<Title>",
            exported_at_text="Exported at: 2026-06-03 09:08:07",
            locale="en",
        )

        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn('<html lang="en">', html)
        self.assertIn("script-src 'none'", html)
        self.assertIn("color-scheme: light", html)
        self.assertIn("background: #ffffff", html)
        self.assertIn("color: #111827", html)
        self.assertIn('<main class="markdown-content pdf-export-root"><p>Hello</p></main>', html)
        self.assertNotIn('class="dark"', html)
        self.assertIn("&lt;Title&gt;", html)

    def test_error_responses_do_not_expose_raw_exception_html_css_or_stderr(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(side_effect=RuntimeError("<h1>raw html</h1> css stderr traceback")),
        ):
            response = _post_export(TestClient(_make_app()), {"html": "<h1>secret</h1>", "css": "body{color:red}", "locale": "zh"})

        self.assertEqual(500, response.status_code)
        self.assertEqual("PDF_EXPORT_UNKNOWN_ERROR", response.json()["code"])
        lower_text = response.text.lower()
        for forbidden in ("secret", "body{", "raw html", "stderr", "traceback"):
            self.assertNotIn(forbidden, lower_text)

    def test_cache_miss_generates_pdf_and_returns_headers(self):
        rendered_pdf = b"%PDF-1.7 generated"
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession(title="A Very Long ScienceClaw Export Title")),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ) as cleanup, patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=None),
        ) as cache_lookup, patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(return_value=rendered_pdf),
        ) as render, patch.object(
            sessions_route,
            "_write_pdf_cache_metadata",
            new=AsyncMock(),
        ) as write_meta, patch.object(
            sessions_route,
            "_delete_pdf_cache_key_later",
            new=AsyncMock(),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(200, response.status_code)
        self.assertEqual(rendered_pdf, response.content)
        self.assertEqual("application/pdf", response.headers["content-type"])
        self.assertEqual("miss", response.headers["x-pdf-export-cache"])
        self.assertIn('attachment; filename="scienceclaw-session-1.pdf"', response.headers["content-disposition"])
        cleanup.assert_awaited_once_with("session-1")
        cache_lookup.assert_awaited_once()
        render.assert_awaited_once()
        write_meta.assert_awaited_once()
        args = render.await_args.args
        self.assertEqual("session-1", args[0])
        self.assertIn("<!doctype html>", args[1])
        self.assertEqual("A Very Long Sci...", args[2])
        self.assertTrue(args[3].startswith("导出时间："))
        self.assertTrue(args[4].endswith(".pdf"))

    def test_cache_hit_returns_cached_pdf_without_render(self):
        cached_pdf = b"%PDF-1.7 cached"
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=cached_pdf),
        ), patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(),
        ) as render:
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(200, response.status_code)
        self.assertEqual(cached_pdf, response.content)
        self.assertEqual("hit", response.headers["x-pdf-export-cache"])
        render.assert_not_awaited()

    def test_corrupt_cache_hit_returns_invalid_pdf_without_render(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=b"not a pdf"),
        ), patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(),
        ) as render:
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(502, response.status_code)
        self.assertEqual("PDF_EXPORT_INVALID_PDF", response.json()["code"])
        render.assert_not_awaited()

    def test_expired_cache_miss_regenerates_pdf(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=None),
        ), patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(return_value=b"%PDF regenerated"),
        ) as render, patch.object(
            sessions_route,
            "_write_pdf_cache_metadata",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_delete_pdf_cache_key_later",
            new=AsyncMock(),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(200, response.status_code)
        self.assertEqual("miss", response.headers["x-pdf-export-cache"])
        render.assert_awaited_once()

    def test_sandbox_timeout_returns_i18n_timeout(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=None),
        ), patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(side_effect=sessions_route.httpx.TimeoutException("stderr secret timeout")),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(504, response.status_code)
        self.assertEqual("PDF_EXPORT_TIMEOUT", response.json()["code"])
        self.assertEqual("pdf_export.timeout", response.json()["msg"])
        self.assertNotIn("stderr", response.text.lower())

    def test_non_pdf_render_result_returns_invalid_pdf(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=None),
        ), patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(return_value=b"not a pdf"),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(502, response.status_code)
        self.assertEqual("PDF_EXPORT_INVALID_PDF", response.json()["code"])
        self.assertEqual("pdf_export.invalid_pdf", response.json()["msg"])

    def test_sandbox_invalid_pdf_exception_returns_invalid_pdf(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(
            sessions_route,
            "_cleanup_expired_pdf_cache",
            new=AsyncMock(),
        ), patch.object(
            sessions_route,
            "_download_pdf_cache_if_fresh",
            new=AsyncMock(return_value=None),
        ), patch.object(
            sessions_route,
            "_render_pdf_in_sandbox",
            new=AsyncMock(side_effect=ValueError("invalid pdf")),
        ):
            response = _post_export(TestClient(_make_app()))

        self.assertEqual(502, response.status_code)
        self.assertEqual("PDF_EXPORT_INVALID_PDF", response.json()["code"])


if __name__ == "__main__":
    unittest.main()
