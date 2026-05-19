#!/usr/bin/env python3
"""Small MCP stdio client for the local Context7 server.

This script lets the context7-code-docs skill use Context7 without registering
Context7 as a global Codex MCP server.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


DEFAULT_CONTEXT7_ROOT = Path(r"D:\Pe\Project\codex-mcp\context7")
DEFAULT_CONTEXT7_CMD = DEFAULT_CONTEXT7_ROOT / "node_modules" / ".bin" / "context7-mcp.cmd"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class McpError(RuntimeError):
    pass


class McpStdioClient:
    def __init__(self, command: Path, cwd: Path, timeout: float = 60.0) -> None:
        self.command = command
        self.cwd = cwd
        self.timeout = timeout
        self._next_id = 1
        self._stderr_lines: list[str] = []
        self._stdout_queue: queue.Queue[str | None] = queue.Queue()

        if not command.exists():
            raise McpError(f"Context7 command not found: {command}")
        if not cwd.exists():
            raise McpError(f"Context7 cwd not found: {cwd}")

        popen_args: list[str]
        if os.name == "nt" and command.suffix.lower() in {".cmd", ".bat"}:
            popen_args = ["cmd.exe", "/d", "/s", "/c", str(command)]
        else:
            popen_args = [str(command)]

        self.proc = subprocess.Popen(
            popen_args,
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        threading.Thread(target=self._drain_stdout, daemon=True).start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()

    def _drain_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._stdout_queue.put(line)
        self._stdout_queue.put(None)

    def _drain_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self._stderr_lines.append(line.rstrip())

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self._next_id
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})

        while True:
            try:
                line = self._stdout_queue.get(timeout=self.timeout)
            except queue.Empty as exc:
                stderr = "\n".join(self._stderr_lines[-10:])
                raise McpError(f"Timed out waiting for Context7 response to {method}.\n{stderr}") from exc
            if line is None:
                stderr = "\n".join(self._stderr_lines[-10:])
                raise McpError(f"Context7 server exited while waiting for {method}.\n{stderr}")
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise McpError(json.dumps(message["error"], ensure_ascii=False))
            return message.get("result")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _send(self, message: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()


def extract_text(result: Any) -> str:
    if isinstance(result, dict) and isinstance(result.get("content"), list):
        chunks: list[str] = []
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(str(item.get("text", "")))
        return "\n".join(chunk for chunk in chunks if chunk)
    return json.dumps(result, ensure_ascii=False, indent=2)


def build_client(args: argparse.Namespace) -> McpStdioClient:
    command = Path(args.command or os.environ.get("CONTEXT7_MCP_COMMAND", DEFAULT_CONTEXT7_CMD))
    cwd = Path(args.cwd or os.environ.get("CONTEXT7_MCP_CWD", DEFAULT_CONTEXT7_ROOT))
    client = McpStdioClient(command=command, cwd=cwd, timeout=args.timeout)
    client.request(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "context7-skill-client", "version": "0.1.0"},
        },
    )
    client.notify("notifications/initialized")
    return client


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--command", help="Path to context7-mcp command. Defaults to CONTEXT7_MCP_COMMAND or local install.")
    parser.add_argument("--cwd", help="Working directory for context7-mcp. Defaults to CONTEXT7_MCP_CWD or local install.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Call Context7 through its local MCP stdio server.")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a library name to Context7-compatible IDs.")
    add_common_args(resolve_parser)
    resolve_parser.add_argument("library_name")

    docs_parser = subparsers.add_parser("docs", help="Fetch docs for a Context7-compatible library ID.")
    add_common_args(docs_parser)
    docs_parser.add_argument("library_id")
    docs_parser.add_argument("--topic", default=None)
    docs_parser.add_argument("--mode", choices=["code", "info"], default="code")
    docs_parser.add_argument("--page", type=int, default=1)

    args = parser.parse_args()
    client: McpStdioClient | None = None
    try:
        client = build_client(args)
        if args.command_name == "resolve":
            result = client.request("tools/call", {"name": "resolve-library-id", "arguments": {"libraryName": args.library_name}})
        else:
            arguments: dict[str, Any] = {
                "context7CompatibleLibraryID": args.library_id,
                "mode": args.mode,
                "page": args.page,
            }
            if args.topic:
                arguments["topic"] = args.topic
            result = client.request("tools/call", {"name": "get-library-docs", "arguments": arguments})
        output = extract_text(result)
        if isinstance(result, dict) and result.get("isError"):
            print(output, file=sys.stderr)
            return 2
        print(output)
        return 0
    except (McpError, OSError, json.JSONDecodeError) as exc:
        print(f"Context7 client error: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
