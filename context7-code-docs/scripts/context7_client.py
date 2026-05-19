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
import shlex
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class McpError(RuntimeError):
    pass


class McpStdioClient:
    def __init__(self, command: list[str], cwd: Path | None, timeout: float = 60.0) -> None:
        self.command = command
        self.cwd = cwd
        self.timeout = timeout
        self._next_id = 1
        self._stderr_lines: list[str] = []
        self._stdout_queue: queue.Queue[str | None] = queue.Queue()

        if not command:
            raise McpError("Context7 command is empty.")
        if cwd is not None and not cwd.exists():
            raise McpError(f"Context7 cwd not found: {cwd}")

        popen_args: list[str]
        command_path = Path(command[0])
        if os.name == "nt" and command_path.suffix.lower() in {".cmd", ".bat"}:
            popen_args = ["cmd.exe", "/d", "/s", "/c", subprocess.list2cmdline(command)]
        else:
            popen_args = command

        self.proc = subprocess.Popen(
            popen_args,
            cwd=str(cwd) if cwd is not None else None,
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


def executable_names() -> list[str]:
    if os.name == "nt":
        return ["context7-mcp.cmd", "context7-mcp.exe", "context7-mcp"]
    return ["context7-mcp", "context7-mcp.cmd"]


def split_command(value: str) -> list[str]:
    try:
        parts = shlex.split(value, posix=os.name != "nt")
    except ValueError as exc:
        raise McpError(f"Invalid command string: {value}") from exc
    if not parts:
        raise McpError("Command string is empty.")
    return parts


def is_path_like(value: str) -> bool:
    separators = [sep for sep in (os.sep, os.altsep) if sep]
    return value.startswith(("~", ".")) or any(sep in value for sep in separators)


def resolve_executable(value: str) -> str:
    expanded = os.path.expandvars(os.path.expanduser(value))
    if is_path_like(expanded):
        path = Path(expanded)
        if path.exists():
            return str(path)
        raise McpError(f"Context7 command not found: {path}")

    found = shutil.which(expanded)
    if found:
        return found
    raise McpError(f"Context7 command not found on PATH: {expanded}")


def parse_args_list(values: list[str] | None) -> list[str]:
    parsed: list[str] = []
    for value in values or []:
        parsed.extend(split_command(value))
    return parsed


def local_command_candidates(cwd_hint: Path | None) -> list[tuple[Path, Path]]:
    roots: list[Path] = []
    if cwd_hint is not None:
        roots.append(cwd_hint)
    roots.extend([Path.cwd(), SKILL_DIR])

    candidates: list[tuple[Path, Path]] = []
    seen: set[Path] = set()
    for root in roots:
        root = root.expanduser().resolve()
        if root in seen:
            continue
        seen.add(root)
        for name in executable_names():
            candidates.append((root / "node_modules" / ".bin" / name, root))
    return candidates


def resolve_cwd(value: str | None) -> Path | None:
    if not value:
        return None
    cwd = Path(os.path.expandvars(os.path.expanduser(value)))
    if not cwd.exists():
        raise McpError(f"Context7 cwd not found: {cwd}")
    return cwd


def resolve_command(args: argparse.Namespace) -> tuple[list[str], Path | None]:
    cwd = resolve_cwd(args.cwd or os.environ.get("CONTEXT7_MCP_CWD"))
    raw_command = args.command or os.environ.get("CONTEXT7_MCP_COMMAND")
    extra_args = parse_args_list(args.command_arg) + parse_args_list(
        [os.environ["CONTEXT7_MCP_ARGS"]] if os.environ.get("CONTEXT7_MCP_ARGS") else None
    )

    if raw_command:
        parts = split_command(raw_command)
        return [resolve_executable(parts[0]), *parts[1:], *extra_args], cwd

    for candidate, root in local_command_candidates(cwd):
        if candidate.exists():
            return [str(candidate), *extra_args], cwd or root

    for name in executable_names():
        found = shutil.which(name)
        if found:
            return [found, *extra_args], cwd

    raise McpError(
        "Context7 command not found. Install context7-mcp on PATH, place it in "
        "node_modules/.bin, or set CONTEXT7_MCP_COMMAND/--command."
    )


def build_client(args: argparse.Namespace) -> McpStdioClient:
    command, cwd = resolve_command(args)
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
    parser.add_argument("--command", help="context7-mcp executable name/path or quoted command line.")
    parser.add_argument("--command-arg", action="append", help="Extra argument for the Context7 command. May be repeated.")
    parser.add_argument("--cwd", help="Working directory for context7-mcp. Defaults to CONTEXT7_MCP_CWD, local install root, or current directory.")
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

    doctor_parser = subparsers.add_parser("doctor", help="Show resolved Context7 command and optionally test connection.")
    add_common_args(doctor_parser)
    doctor_parser.add_argument("--connect", action="store_true", help="Initialize the server and list available tools.")

    args = parser.parse_args()
    client: McpStdioClient | None = None
    try:
        if args.command_name == "doctor":
            command, cwd = resolve_command(args)
            print("command: " + " ".join(command))
            print("cwd: " + (str(cwd) if cwd is not None else "<current process cwd>"))
            if not args.connect:
                return 0
            client = build_client(args)
            result = client.request("tools/list")
            print(extract_text(result))
            return 0

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
