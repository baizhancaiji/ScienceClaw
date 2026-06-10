"""Reproduce: send a command to a session that's in NO_CHANGE_TIMEOUT state
but whose tmux pane actually has a valid PS1 prompt."""

import asyncio, time, httpx

async def main():
    client = httpx.AsyncClient(base_url="http://sandbox:8080", timeout=httpx.Timeout(30))

    session_id = "EbuW9ASjCUxgLWNuzJPSdC"

    # Test: send echo alive with various timeouts
    for timeout_val in [5, 10, 15, 30]:
        t0 = time.monotonic()
        try:
            r = await client.post(
                "/v1/shell/exec",
                json={"id": session_id, "command": "echo alive", "async_mode": False, "exec_dir": f"/home/scienceclaw/{session_id}"},
                timeout=httpx.Timeout(timeout_val, connect=10),
            )
            elapsed = time.monotonic() - t0
            data = r.json()
            exit_code = data.get("data", {}).get("exit_code", "?")
            output = data.get("data", {}).get("output", "")[:200]
            status = data.get("data", {}).get("status", "?")
            print(f"  timeout={timeout_val}s: elapsed={elapsed:.2f}s, exit_code={exit_code}, status={status}")
            if output:
                print(f"    output: {output[:150]}")
        except httpx.TimeoutException as e:
            print(f"  timeout={timeout_val}s: HTTP TIMEOUT after {time.monotonic()-t0:.2f}s - {type(e).__name__}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
