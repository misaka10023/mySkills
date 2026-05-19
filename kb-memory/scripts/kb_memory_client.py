#!/usr/bin/env python3
"""Small MCP HTTP client for the kb-memory skill.

The script keeps kb-mcp out of global host configuration by reading an ignored
local config file or environment variables, then calling the MCP HTTP endpoint
directly.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONFIG_PATH = SKILL_DIR / "config.local.json"
DEFAULT_URL = "http://127.0.0.1:8000/mcp/"
DEFAULT_TIMEOUT = 30.0

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class KbMemoryError(RuntimeError):
    pass


@dataclass
class RuntimeConfig:
    url: str
    headers: dict[str, str]
    timeout: float
    path: Path


class HttpMcpClient:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.session_id: str | None = None
        self._next_id = 1

    def initialize(self) -> None:
        result, headers = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "kb-memory-skill-client", "version": "0.1.0"},
                },
            }
        )
        self._next_id += 1
        self.session_id = headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
        if isinstance(result, dict) and "error" in result:
            raise KbMemoryError(json.dumps(result["error"], ensure_ascii=False))
        self.notify("notifications/initialized")

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self._next_id
        self._next_id += 1
        result, _headers = self._post(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
        )
        if not isinstance(result, dict):
            raise KbMemoryError(f"Invalid MCP response for {method}: {result!r}")
        if "error" in result:
            raise KbMemoryError(json.dumps(result["error"], ensure_ascii=False))
        return result.get("result")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._post({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _post(self, payload: dict[str, Any]) -> tuple[Any, dict[str, str]]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            **self.config.headers,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        request = Request(
            self.config.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.config.timeout) as response:
                body = response.read()
                parsed = parse_http_body(body, response.headers.get("Content-Type", ""))
                return parsed, dict(response.headers.items())
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise KbMemoryError(f"HTTP {exc.code} from kb-mcp: {detail}") from exc
        except URLError as exc:
            raise KbMemoryError(f"Unable to reach kb-mcp at {self.config.url}: {exc.reason}") from exc


def parse_http_body(body: bytes, content_type: str) -> Any:
    if not body:
        return None
    text = body.decode("utf-8", errors="replace")
    if "text/event-stream" not in content_type.lower():
        return json.loads(text)

    events: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("data:"):
            current.append(line[5:].strip())
        elif not line and current:
            events.append("\n".join(current))
            current = []
    if current:
        events.append("\n".join(current))

    for event in events:
        if event and event != "[DONE]":
            return json.loads(event)
    return None


def extract_text(result: Any) -> str:
    if isinstance(result, dict) and isinstance(result.get("content"), list):
        chunks: list[str] = []
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(str(item.get("text", "")))
        return "\n".join(chunk for chunk in chunks if chunk)
    return json.dumps(result, ensure_ascii=False, indent=2)


def config_path(args: argparse.Namespace) -> Path:
    raw = args.config or os.environ.get("KB_MEMORY_CONFIG") or str(DEFAULT_CONFIG_PATH)
    return Path(os.path.expandvars(os.path.expanduser(raw)))


def default_config_data() -> dict[str, Any]:
    return {
        "url": DEFAULT_URL,
        "headers": {
            "Authorization": ""
        },
        "timeout": DEFAULT_TIMEOUT,
    }


def load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise KbMemoryError(f"Invalid JSON config: {path}") from exc
    if not isinstance(data, dict):
        raise KbMemoryError(f"Config must be a JSON object: {path}")
    return data


def parse_header_values(values: list[str] | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise KbMemoryError(f"Header must use Name=Value form: {value}")
        name, header_value = value.split("=", 1)
        name = name.strip()
        if not name:
            raise KbMemoryError(f"Header name is empty: {value}")
        headers[name] = header_value
    return headers


def load_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    path = config_path(args)
    data = load_config_file(path)

    file_headers = data.get("headers", {})
    if file_headers is None:
        file_headers = {}
    if not isinstance(file_headers, dict):
        raise KbMemoryError("Config field 'headers' must be an object.")

    headers = {str(key): str(value) for key, value in file_headers.items() if str(value)}

    env_headers = os.environ.get("KB_MEMORY_MCP_HEADERS_JSON")
    if env_headers:
        parsed = json.loads(env_headers)
        if not isinstance(parsed, dict):
            raise KbMemoryError("KB_MEMORY_MCP_HEADERS_JSON must be a JSON object.")
        headers.update({str(key): str(value) for key, value in parsed.items() if str(value)})

    authorization = os.environ.get("KB_MEMORY_MCP_AUTHORIZATION")
    bearer_token = os.environ.get("KB_MEMORY_MCP_BEARER_TOKEN")
    if authorization:
        headers["Authorization"] = authorization
    elif bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    headers.update(parse_header_values(args.header))

    url = args.url or os.environ.get("KB_MEMORY_MCP_URL") or data.get("url") or DEFAULT_URL
    timeout_raw = args.timeout or os.environ.get("KB_MEMORY_MCP_TIMEOUT") or data.get("timeout") or DEFAULT_TIMEOUT
    return RuntimeConfig(url=str(url), headers=headers, timeout=float(timeout_raw), path=path)


def write_config(path: Path, force: bool) -> None:
    if path.exists() and not force:
        print(f"Config already exists: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(default_config_data(), indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    print(f"Created config: {path}")
    print("Edit the file or set KB_MEMORY_MCP_URL / KB_MEMORY_MCP_BEARER_TOKEN before connecting.")


def git_ignore_state(path: Path) -> str:
    root = find_git_root(SKILL_DIR)
    cwd = root or SKILL_DIR.parent
    command = ["git"]
    if root is not None:
        command.extend(["-c", f"safe.directory={root.as_posix()}"])
        try:
            target = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            target = str(path)
    else:
        target = str(path)
    command.extend(["check-ignore", "--quiet", "--", target])
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (OSError, ValueError):
        return "unknown"
    if completed.returncode == 0:
        return "ignored"
    if completed.returncode == 1:
        return "not ignored"
    return "unknown"


def find_git_root(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        if not value:
            redacted[key] = "<empty>"
        elif key.lower() in {"authorization", "x-api-key", "api-key", "cookie"}:
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


def load_arguments(args: argparse.Namespace) -> dict[str, Any]:
    if args.arguments_json and args.arguments_file:
        raise KbMemoryError("Use either --arguments-json or --arguments-file, not both.")
    if args.arguments_file:
        if args.arguments_file == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(args.arguments_file).read_text(encoding="utf-8")
        data = json.loads(raw)
    elif args.arguments_json:
        data = json.loads(args.arguments_json)
    else:
        data = {}
    if not isinstance(data, dict):
        raise KbMemoryError("Tool arguments must be a JSON object.")
    return data


def add_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Path to config.local.json. Defaults to KB_MEMORY_CONFIG or the skill-local config.")
    parser.add_argument("--url", help="kb-mcp HTTP endpoint. Overrides config and KB_MEMORY_MCP_URL.")
    parser.add_argument("--header", action="append", help="HTTP header in Name=Value form. May be repeated.")
    parser.add_argument("--timeout", type=float, help="HTTP timeout in seconds.")


def format_tools(result: Any) -> str:
    if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
        return extract_text(result)
    lines: list[str] = []
    for tool in result["tools"]:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name", "<unnamed>")
        description = str(tool.get("description", "")).strip()
        lines.append(f"- {name}: {description}" if description else f"- {name}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Call kb-mcp through a skill-local MCP HTTP client.")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    init_parser = subparsers.add_parser("init-config", help="Create the ignored skill-local config file.")
    init_parser.add_argument("--config", help="Path to create. Defaults to KB_MEMORY_CONFIG or kb-memory/config.local.json.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite an existing config file.")

    doctor_parser = subparsers.add_parser("doctor", help="Show effective configuration and optionally connect.")
    add_config_args(doctor_parser)
    doctor_parser.add_argument("--connect", action="store_true", help="Initialize kb-mcp and list tools.")

    tools_parser = subparsers.add_parser("tools", help="List kb-mcp tools.")
    add_config_args(tools_parser)

    call_parser = subparsers.add_parser("call", help="Call a kb-mcp tool by name.")
    add_config_args(call_parser)
    call_parser.add_argument("tool_name")
    call_parser.add_argument("--arguments-json", help="Tool arguments as a JSON object.")
    call_parser.add_argument("--arguments-file", help="Path to JSON object arguments, or '-' for stdin.")

    args = parser.parse_args()
    try:
        if args.command_name == "init-config":
            write_config(config_path(args), force=args.force)
            return 0

        config = load_runtime_config(args)
        if args.command_name == "doctor":
            print(f"config: {config.path}")
            print(f"config_exists: {str(config.path.exists()).lower()}")
            print(f"config_git_state: {git_ignore_state(config.path)}")
            print(f"url: {config.url}")
            print("headers: " + json.dumps(redact_headers(config.headers), ensure_ascii=False))
            print(f"timeout: {config.timeout:g}")
            if not args.connect:
                return 0

        client = HttpMcpClient(config)
        client.initialize()
        if args.command_name in {"doctor", "tools"}:
            print(format_tools(client.request("tools/list")))
            return 0

        result = client.request(
            "tools/call",
            {"name": args.tool_name, "arguments": load_arguments(args)},
        )
        output = extract_text(result)
        if isinstance(result, dict) and result.get("isError"):
            print(output, file=sys.stderr)
            return 2
        print(output)
        return 0
    except (KbMemoryError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"kb-memory client error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
