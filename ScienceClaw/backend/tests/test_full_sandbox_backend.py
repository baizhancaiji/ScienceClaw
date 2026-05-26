import asyncio
import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _install_deepagents_protocol_stub() -> None:
    if "deepagents.backends.protocol" in sys.modules:
        return

    deepagents_pkg = types.ModuleType("deepagents")
    backends_pkg = types.ModuleType("deepagents.backends")
    protocol_pkg = types.ModuleType("deepagents.backends.protocol")

    @dataclass
    class ExecuteResponse:
        output: str
        exit_code: int
        truncated: bool = False

    @dataclass
    class WriteResult:
        path: str | None = None
        error: str | None = None

    @dataclass
    class EditResult:
        path: str | None = None
        occurrences: int = 0
        error: str | None = None

    @dataclass
    class FileDownloadResponse:
        url: str | None = None
        error: str | None = None

    @dataclass
    class FileUploadResponse:
        path: str | None = None
        error: str | None = None

    @dataclass
    class FileInfo:
        path: str = ""
        name: str = ""
        is_dir: bool = False
        size: int = 0
        modified_at: str = ""

    @dataclass
    class GrepMatch:
        path: str = ""
        line_number: int = 0
        line: str = ""

    class SandboxBackendProtocol:
        pass

    protocol_pkg.EditResult = EditResult
    protocol_pkg.ExecuteResponse = ExecuteResponse
    protocol_pkg.FileDownloadResponse = FileDownloadResponse
    protocol_pkg.FileInfo = FileInfo
    protocol_pkg.FileUploadResponse = FileUploadResponse
    protocol_pkg.GrepMatch = GrepMatch
    protocol_pkg.SandboxBackendProtocol = SandboxBackendProtocol
    protocol_pkg.WriteResult = WriteResult

    sys.modules["deepagents"] = deepagents_pkg
    sys.modules["deepagents.backends"] = backends_pkg
    sys.modules["deepagents.backends.protocol"] = protocol_pkg


_install_deepagents_protocol_stub()

from backend.deepagent.full_sandbox_backend import FullSandboxBackend  # noqa: E402


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self):
        self.exec_calls = []
        self.is_closed = False

    async def get(self, path, timeout=None):
        return _FakeResponse({"success": True, "data": {"status": "ok"}})

    async def post(self, path, json=None, timeout=None):
        if path == "/v1/shell/sessions/create":
            return _FakeResponse({"success": True, "data": {"session_id": "sid-1"}})
        if path == "/v1/shell/exec":
            command = json["command"]
            self.exec_calls.append(command)
            if command == "slow":
                await asyncio.sleep(0.2)
            return _FakeResponse({"success": True, "data": {"output": command, "exit_code": 0}})
        raise AssertionError(f"Unexpected path: {path}")

    async def aclose(self):
        self.is_closed = True


class FullSandboxBackendTests(unittest.IsolatedAsyncioTestCase):
    async def test_execute_serializes_commands_within_same_session(self):
        backend = FullSandboxBackend("sess-1", "user-1", execute_timeout=5)
        client = _FakeClient()
        backend._client = client

        async def run(command: str):
            return await backend.aexecute(command, timeout=1)

        slow_task = asyncio.create_task(run("slow"))
        await asyncio.sleep(0.05)
        fast_task = asyncio.create_task(run("fast"))

        slow_result, fast_result = await asyncio.gather(slow_task, fast_task)

        self.assertEqual("slow", slow_result.output)
        self.assertEqual("fast", fast_result.output)
        self.assertEqual(["slow", "fast"], client.exec_calls)

    async def test_execute_reports_infrastructure_error_when_queue_wait_exhausts_timeout(self):
        backend = FullSandboxBackend("sess-2", "user-2", execute_timeout=5)
        client = _FakeClient()
        backend._client = client

        backend._session_exec_lock.acquire()
        try:
            result = await backend.aexecute("fast", timeout=1)
        finally:
            backend._session_exec_lock.release()

        self.assertEqual(-1, result.exit_code)
        self.assertIn("[infrastructure_error]", result.output)
        self.assertIn("queue was full", result.output)
        self.assertEqual([], client.exec_calls)


if __name__ == "__main__":
    unittest.main()
