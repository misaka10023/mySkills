# Visio Automation Troubleshooting Reference

> Scope: production-grade diagnostics and fixes for the most common failure
> modes encountered when driving Microsoft Visio from `pywin32`,
> `Visio.InvisibleApp` over PowerShell, the cross-platform `vsdx` Python
> package, and VSTO / IDTExtensibility2 add-ins. Each section names exact
> HRESULTs, `EXCEPINFO` payload strings, ShapeSheet cell names, OPC part
> paths, registry hives, and Visio enumeration constants. Aim: from raw
> stack trace to fix in under three minutes.

---

## 0. HRESULT Quick-Lookup Table

The integer literal `-2147467259` is the signed view of the unsigned HRESULT
`0x80004005` (`E_FAIL`). `pywin32` surfaces the signed form through
`pywintypes.com_error.args[0]`; PowerShell's
`System.Runtime.InteropServices.COMException.HResult` shows the same value;
.NET's `Marshal.GetExceptionForHR` round-trips both. Always normalize with
`h & 0xFFFFFFFF` before equality checks.

| Decimal (signed)  | Hex (unsigned) | Symbol                          | Class      | Surface                                                           |
| ----------------: | -------------- | ------------------------------- | ---------- | ----------------------------------------------------------------- |
| `-2147467259`     | `0x80004005`   | `E_FAIL`                        | Generic    | "Unspecified error" - inspect `excepinfo[2]` / `Exception.Message` |
| `-2147352567`     | `0x80020009`   | `DISP_E_EXCEPTION`              | IDispatch  | Visio raised an `EXCEPINFO`; real text is in `excepinfo[2]`        |
| `-2147352573`     | `0x80020003`   | `DISP_E_MEMBERNOTFOUND`         | IDispatch  | Method/property name typo or missing on this Visio version        |
| `-2147352571`     | `0x80020005`   | `DISP_E_TYPEMISMATCH`           | IDispatch  | Wrong arg type (e.g. `str` where `Visio.Master` expected)         |
| `-2147418111`     | `0x800100FF`   | `RPC_E_*` family                | RPC        | Apartment / call-rejected                                          |
| `-2147418107`     | `0x80010001`   | `RPC_E_CALL_REJECTED`           | RPC        | "Visio is busy" (modal dialog or in-flight call)                   |
| `-2147417842`     | `0x8001010A`   | `RPC_E_SERVERCALL_RETRYLATER`   | RPC        | Server thread blocked; retry with backoff                          |
| `-2147417848`     | `0x80010108`   | `RPC_E_DISCONNECTED`            | RPC        | Stale proxy after `Quit`, crash, or GC of event sink               |
| `-2147417850`     | `0x80010106`   | `RPC_E_CHANGED_MODE`            | RPC        | `CoInitializeEx` called with different apartment than already set  |
| `-2147417842`     | `0x8001010E`   | `RPC_E_WRONG_THREAD`            | RPC        | Cross-apartment marshalling without GIT cookie                     |
| `-2147221164`     | `0x80040154`   | `REGDB_E_CLASSNOTREG`           | COM        | Visio not installed, or 32-/64-bit Python mismatch                 |
| `-2146959355`     | `0x80080005`   | `CO_E_SERVER_EXEC_FAILURE`      | COM        | Visio failed to launch (Session 0, missing profile, no license)    |
| `-2147221008`     | `0x800401F0`   | `CO_E_NOTINITIALIZED`           | COM        | Thread missing `pythoncom.CoInitialize()`                          |
| `-2147221005`     | `0x800401F3`   | `CO_E_CLASSSTRING`              | COM        | ProgID misspelled or unregistered                                  |
| `-2146823281`     | `0x800AC10F`   | (Visio: file in use)            | Visio      | `.vsdx` locked by another process                                  |
| `-2146823024`     | `0x800AC210`   | (Visio: bad master)             | Visio      | Master not present in the document, or `Master` ref dangling       |
| `-2146823037`     | `0x800AC203`   | (Visio: bad file name)          | Visio      | `OpenEx` rejected the path                                         |
| `-2146823286`     | `0x800AC10A`   | (Visio: macros blocked)         | Visio      | `OpenEx` declined macros without consent                           |
| `-2146822925`     | `0x800AC1B3`   | (Visio: unable to load master)  | Visio      | Stencil missing the named master (`Masters.ItemU` failed)          |
| `-2146822609`     | `0x800AC2EF`   | (Visio: invalid formula)        | Visio      | `Cells(...).FormulaU = "..."` rejected                             |

Convert in Python:

```python
def to_hex(h: int) -> str:
    return f"0x{h & 0xFFFFFFFF:08X}"
```

Convert in PowerShell:

```powershell
'0x{0:X8}' -f $err.Exception.HResult
```

`pywintypes.com_error.args` is a 4-tuple `(hresult, source, excepinfo, argerror)`.
`excepinfo` is a 6-tuple `(wCode, bstrSource, bstrDescription, bstrHelpFile, dwHelpContext, scode)`.
For Visio failures the human-readable text is in `excepinfo[2]` (`bstrDescription`).
Always print it; the HRESULT alone is rarely enough to identify the cause.

---

## 1. `pywintypes.com_error -2147467259` (`0x80004005 E_FAIL`)

`E_FAIL` is the catch-all HRESULT Visio returns when its IDispatch invoke
path completes but the underlying operation refused. The HRESULT alone
tells you nothing; the cause lives in `excepinfo[2]`. Print it before
anything else.

### 1.1 Decode pattern

```python
import pywintypes

try:
    page.Drop(master, 4.0, 6.0)
except pywintypes.com_error as e:
    hresult, source, excepinfo, argerror = e.args
    if excepinfo is not None:
        wcode, wsource, wdescr, whelp, whelpid, scode = excepinfo
        print(f"HRESULT={hresult & 0xFFFFFFFF:#010x}")
        print(f"Source : {wsource}")
        print(f"Detail : {wdescr}")          # human text lives here
        print(f"SCODE  : {scode & 0xFFFFFFFF:#010x}")
    raise
```

PowerShell equivalent:

```powershell
try { $doc.SaveAs($path) }
catch [System.Runtime.InteropServices.COMException] {
    Write-Host ("HRESULT=0x{0:X8}" -f $_.Exception.HResult)
    Write-Host  $_.Exception.Message
    Write-Host  $_.ScriptStackTrace
}
```

### 1.2 Common causes mapped to `bstrDescription`

| `excepinfo[2]` substring (case-insensitive)               | Root cause                                                | Fix                                                                                                |
| -------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| "Visio cannot find a printer on this computer"           | No default printer, Print Spooler not running             | Start `Spooler` service, install `Microsoft Print to PDF`, set default printer for the running user |
| "Unable to open file ... in use by another process"      | `.vsdx` open in interactive Visio or held by indexer      | Close visible Visio; pause Windows Search on the folder; see §4                                    |
| "Could not load object ... master"                       | Master deleted from stencil but instance reference stale  | Re-resolve via `stencil.Masters.ItemU("Process")`; never cache a `Master` across `Document.Close`  |
| "Bad cell name" / "Could not find that cell"             | Localized cell access on non-en-US Visio                  | Use `CellsU` / `FormulaU` / `NameU` (universal-syntax variants) - never `Cells`/`Formula`/`Name`   |
| "Visio could not parse formula"                          | Locale-decimal `,` instead of `.` or stale unit token     | Send `=4 in` not `=4,0 in`; always set formula via `FormulaU` so syntax is en-US                   |
| "Unable to print"                                        | `ExportAsFixedFormat` Print intent without spooler        | Install `Microsoft Print to PDF`; restart Spooler; switch `Intent` to `visDocExIntentScreen` (2)   |
| "Invalid argument"                                       | `argerror` 1-based index points to the offender           | Inspect `e.args[3]`; e.g. `Drop(master, x, y)` with `master=None` after a failed `ItemU`           |
| "Class not registered"                                   | bitness mismatch                                          | See §5.1 - rerun makepy in matching bitness or switch interpreters                                  |

### 1.3 Decision flow

If the description matches a row in §1.2, apply the fix. Otherwise
search the description verbatim in this document. If still
unmatched, repro under `app.Visible = True` and watch the modal
dialog - the dialog text is identical to `bstrDescription` for 90%
of failures.

### 1.4 The "always print, never swallow" rule

Bare `except pywintypes.com_error: pass` is the single most common
anti-pattern in Visio automation. `E_FAIL` carries no actionable signal
without `bstrDescription`. The minimal acceptable handler:

```python
except pywintypes.com_error as e:
    descr = e.args[2][2] if e.args[2] else ""
    raise RuntimeError(f"Visio: {descr or e}") from e
```

For library code, translate to a domain exception that carries the
description as a string field rather than burying it inside the
`com_error.args` tuple.

---

## 2. COM "Visio is busy" / `RPC_E_CALL_REJECTED` (`0x80010001`)

The application object is single-threaded apartment (`ThreadingModel =
Apartment`). When Visio is mid-call - showing a modal dialog, processing
an inbound event, repainting the offscreen buffer - it rejects new
inbound calls with `RPC_E_CALL_REJECTED`. Sibling code is
`RPC_E_SERVERCALL_RETRYLATER` (`0x8001010A`) for the same situation
when the dispatcher chose to ask the caller to retry instead of
outright reject.

### 2.1 Diagnosis matrix

| Trigger                                                                | Symptom                                                                | Why                                                              |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `Visible = True` and a `MsgBox`/`AlertResponse` dialog is open          | All subsequent COM calls fail until user dismisses                     | STA dispatcher waits for UI message-pump return                  |
| `app.Quit()` while another thread still holds proxies                  | Quit succeeds, next call throws                                        | Server tearing down; new requests rejected                       |
| Long `Page.Layout()` or `ExportAsFixedFormat()` running                | Concurrent caller fails immediately                                    | Server thread blocked computing                                  |
| Two independent processes pointing at the same `Documents.OpenEx` path | Second `OpenEx` fails                                                  | File-share lock held by first opener                             |
| Foreground user clicks a Ribbon button mid-script                      | Random rejection                                                       | User input enters STA queue ahead of automation calls            |

### 2.2 Suppress dialogs at startup

```python
app = wc.DispatchEx("Visio.InvisibleApp")
app.AlertResponse        = 7        # answer "No" to every Yes/No prompt
app.Visible              = False
app.AutomationSecurity   = 3        # msoAutomationSecurityForceDisable - no macro prompts
app.AutoRecover          = False
app.ScreenUpdating       = 0
app.EventsEnabled        = 0
```

`AlertResponse` accepts `1=OK`, `2=Cancel`, `6=Yes`, `7=No`. Setting `7`
is the canonical "automate past every Yes/No" idiom and prevents the
Save-changes dialog from blocking `Quit`. Always set it before the
first `Documents.Open` so the document-recovery prompt cannot appear.

### 2.3 Retry decorator with exponential backoff

```python
import time, pywintypes
from functools import wraps

_RETRYABLE = {0x80010001, 0x8001010A, 0x80010108, 0x800706BE}

def retry_com(times: int = 8, base: float = 0.2):
    def deco(fn):
        @wraps(fn)
        def wrap(*a, **kw):
            last = None
            for n in range(times):
                try:
                    return fn(*a, **kw)
                except pywintypes.com_error as e:
                    h = e.args[0] & 0xFFFFFFFF
                    if h not in _RETRYABLE:
                        raise
                    last = e
                    time.sleep(base * (2 ** n))
            raise last
        return wrap
    return deco
```

### 2.4 IMessageFilter for fine-grained control (.NET/C# only)

A C#/VSTO add-in can register an `IOleMessageFilter` (IID
`00000016-0000-0000-C000-000000000046`) on the STA thread via
`CoRegisterMessageFilter` to intercept `HandleIncomingCall` /
`RetryRejectedCall` and decide per-call whether to retry, fail, or
busy-wait. Return `99` from `RetryRejectedCall` for "retry after 100
ms"; return `-1` to give up. Python and PowerShell users do not need
this; the retry decorator above handles 95% of cases.

### 2.5 PowerShell apartment trap

PowerShell 5.1 (`powershell.exe`) defaults to STA. PowerShell 7+
(`pwsh.exe`) defaults to **MTA**. An MTA caller against Visio surfaces
as `0x80010105 RPC_E_SERVERFAULT` or as silent hangs at `OpenEx`.
Always launch with `-STA`:

```powershell
pwsh.exe -STA -NoProfile -ExecutionPolicy Bypass -File .\Export-Visio.ps1
```

Inside Task Scheduler, the action's "Arguments" must include `-STA`.
Verify at runtime:

```powershell
[System.Threading.Thread]::CurrentThread.GetApartmentState()  # must be STA
```

### 2.6 Process hygiene after rejection

If a `RPC_E_CALL_REJECTED` storm leaves Visio in an unrecoverable state
(orphan dialogs, hung print job), kill and restart in the same script:

```powershell
$before = (Get-Process VISIO -ErrorAction SilentlyContinue).Id
try { ... } finally {
    Get-Process VISIO -ErrorAction SilentlyContinue |
        Where-Object { $before -notcontains $_.Id } |
        Stop-Process -Force
}
```

---

## 3. Stale `makepy` Cache and Early-Binding Failures

`win32com.client.gencache.EnsureDispatch` caches the Visio type-library
under `%LOCALAPPDATA%\Temp\gen_py\<py-version>\<typelib-guid>x0x4x12.py`.
The cache is keyed by the typelib GUID and the
`(major, minor, lcid)` triple. After Visio updates its typelib version
(M365 click-to-run pushes minor bumps every few months), the cache
points at member layouts that no longer match.

### 3.1 Symptoms

| Symptom                                                          | Likely cause                                          |
| ---------------------------------------------------------------- | ----------------------------------------------------- |
| `AttributeError: <unknown>.Documents`                             | `gencache` aborted mid-generation; partial stub        |
| `AttributeError: 'CDispatch' object has no attribute 'Cells'`     | Late-binding fallback after gen_py mismatch            |
| `win32com.client.constants.visOpenRO` -> `AttributeError`         | Constants module empty because no `EnsureDispatch` ran |
| Method that worked yesterday now raises `DISP_E_MEMBERNOTFOUND`   | Visio updated; cached stub is from the previous build  |
| `pywin32` import succeeds but every Visio call goes via IDispatch slowly | `EnsureDispatch` skipped; only `Dispatch` was used     |

### 3.2 Manual flush

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Temp\gen_py"
```

Or more surgically, delete just the Visio entries:

```powershell
Get-ChildItem "$env:LOCALAPPDATA\Temp\gen_py" -Recurse -Filter "*00021A98*" |
    Remove-Item -Force
```

Then regenerate explicitly:

```powershell
py -3.12 -m win32com.client.makepy -i "Microsoft Visio 16.0 Type Library"
```

The `-i` flag prints the GUID/version triple on stdout - paste it into
`gencache.EnsureModule`. Output ends in
`<GUID>x0x4x12.py` for Visio 2019/2021/365 and `x0x4x0.py` for older.

### 3.3 Programmatic flush at start of script

```python
import shutil, sys, os, win32com.client as wc

def reset_gen_py() -> None:
    gp = os.path.join(
        os.environ["LOCALAPPDATA"], "Temp", "gen_py",
        f"{sys.version_info.major}.{sys.version_info.minor}",
    )
    shutil.rmtree(gp, ignore_errors=True)

reset_gen_py()
wc.gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)
app = wc.DispatchEx("Visio.InvisibleApp")
```

### 3.4 Typelib version matrix

| Visio release          | Typelib GUID                              | Major | Minor | gen_py filename suffix |
| ---------------------- | ----------------------------------------- | ----- | ----- | ---------------------- |
| Visio 2010              | `{00021A98-0000-0000-C000-000000000046}` | 4     | 0     | `x0x4x0.py`            |
| Visio 2013              | same                                      | 4     | 0     | `x0x4x0.py`            |
| Visio 2016              | same                                      | 4     | 0     | `x0x4x0.py`            |
| Visio 2019 / M365       | same                                      | 4     | 12    | `x0x4x12.py`           |
| Visio 2021 / M365 cur   | same                                      | 4     | 12-15 | `x0x4x12.py`+          |

Mismatched `(major, minor)` values are silently tolerated - pywin32
picks the latest registered version. Pin the value you depend on so a
Click-to-Run update does not reshape your cache without notice.

### 3.5 The "always EnsureDispatch first" rule

```python
# WRONG: late-binding only; constants module is empty
app = win32com.client.Dispatch("Visio.InvisibleApp")
print(win32com.client.constants.visOpenRO)   # AttributeError

# RIGHT: hydrate constants by ensuring the typelib stub once
import win32com.client as wc
wc.gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)
app = wc.DispatchEx("Visio.InvisibleApp")
from win32com.client import constants as c
print(c.visOpenRO)   # 2
```

`EnsureDispatch` itself returns a Dispatch proxy bound to the *running*
Visio (via the ROT) which is rarely what you want for batch jobs. The
two-step `EnsureModule` + `DispatchEx` pattern guarantees fresh
out-of-process Visio plus typed constants.

### 3.6 Hard-coded constants as a fallback

When you cannot regenerate stubs (locked-down build server, gen_py
cache is read-only), the numeric values are stable across Visio
2010-2024 and can be hardcoded. The full list lives in
`com-quick-ref.md`; the most-used values are `visOpenRO=2`,
`visOpenHidden=64`, `visOpenMacrosDisabled=128`,
`visOpenNoWorkspace=256`, `visFixedFormatPDF=1`,
`visDocExIntentPrint=1`, `visAutoConnectDirNone=0`,
`visAutoConnectDirRight=1`, `visAlertResponseNo=7`.

---

## 4. Locked `.vsdx` Files

OPC `.vsdx` is a ZIP container. Visio holds an exclusive write lock on
the package between `Documents.Open` (or `OpenEx` without `visOpenRO`)
and `Document.Close`. The `vsdx` Python library similarly holds the
underlying ZIP file handle until `close_vsdx()` (or context-manager
exit). Indexers, antivirus scanners, OneDrive sync, and Windows Search
can also pin a transient lock.

### 4.1 Symptoms

| Layer                     | Surface                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| `pywin32` / Visio COM     | `pywintypes.com_error` with `excepinfo[2]` = "in use by another process" or HRESULT `0x800AC10F` |
| `vsdx` Python library     | `PermissionError: [WinError 32] The process cannot access the file because it is being used` |
| `vsdx` save               | `BadZipFile: ... is not a valid zip file` (Visio still writing partial archive)               |
| Raw `zipfile.ZipFile(..., 'a')` | `OSError: [Errno 13] Permission denied`                                                  |
| PowerShell `Move-Item`    | `Cannot remove ... because it is being used by another process`                               |

### 4.2 Identify the holder

Use Sysinternals `handle.exe` (CLI) or Resource Monitor (Performance >
CPU > Associated Handles, search by filename):

```powershell
# Sysinternals handle.exe accepts -a -u for full search
handle.exe -a -u 'D:\Drawings\process.vsdx'
```

Common holders:

| Holder process     | Why                                                                            | Mitigation                                                   |
| ------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| `VISIO.EXE`        | Interactive session has the file open                                           | Close the file in Visio UI                                   |
| `python.exe`       | Previous run did not call `vis.close_vsdx()` or crashed inside `with` block    | Add `try/finally`, restart interpreter                       |
| `OneDrive.exe`     | Sync engine reading file mid-upload                                            | Pause OneDrive sync on the folder during batch jobs          |
| `SearchProtocolHost` | Windows Search indexer scanning the file                                     | Exclude folder from indexing, or expect transient retries    |
| `MsMpEng.exe`      | Defender real-time scan                                                        | Add path exclusion for batch directories                     |
| `explorer.exe`     | Preview pane has the file selected                                             | Disable Preview pane or click another file                   |

### 4.3 Open with `visOpenRO` whenever you do not mutate

For pure read paths (PDF export, CSV extract, validation), always use
`visOpenRO + visOpenHidden + visOpenMacrosDisabled`:

```python
flags = 2 | 64 | 128 | 256   # RO + Hidden + MacrosDisabled + NoWorkspace
doc = app.Documents.OpenEx(path, flags)
```

`visOpenRO` puts Visio in `dwShareMode = FILE_SHARE_READ`, allowing
multiple processes to inspect the same file concurrently.

### 4.4 Always use a context manager for `vsdx`

```python
from vsdx import VisioFile

# WRONG: leaks the underlying ZipFile if anything raises
v = VisioFile("input.vsdx")
v.save_vsdx("output.vsdx")    # exception here -> handle never closed

# RIGHT: deterministic close on every exit path
with VisioFile("input.vsdx") as v:
    v.save_vsdx("output.vsdx")
```

`VisioFile` copies the input to a temp directory at open and unzips it
there; the original file handle is released quickly, but the temp
directory is held until `close_vsdx()`. The context-manager form
guarantees cleanup.

> Do not `save_vsdx(same_path_you_opened_from)` while still inside the
> `with` block on Windows. The library may still hold the original
> path's lock until exit. Save to a sibling path, then `os.replace` it
> over the original after the block.

### 4.5 Lock-aware retry pattern

```python
import time, errno
from pathlib import Path
from vsdx import VisioFile

def open_with_retry(p: Path, attempts: int = 6, delay: float = 0.5):
    last = None
    for n in range(attempts):
        try:
            return VisioFile(str(p))
        except PermissionError as e:           # WinError 32 sharing violation
            if e.errno not in (errno.EACCES, errno.EPERM):
                raise
            last = e
            time.sleep(delay * (2 ** n))
    raise last
```

The same pattern wraps `Documents.OpenEx` for the COM path - fold it
into the `retry_com` decorator from §2.3 by adding `0x800AC10F` to
`_RETRYABLE`.

### 4.6 Stale Visio process leaks

If a script crashed before `app.Quit()`, an orphan `VISIO.EXE` keeps
the file locked indefinitely. Snapshot PIDs before the run, then
kill any new ones in `finally`:

```powershell
$beforePids = (Get-Process VISIO -ErrorAction SilentlyContinue).Id
try { ... } finally {
    if ($visio) { try { $visio.Quit() } catch {} }
    Start-Sleep -Milliseconds 500
    Get-Process VISIO -ErrorAction SilentlyContinue |
        Where-Object { $beforePids -notcontains $_.Id } |
        Stop-Process -Force
}
```

### 4.7 OneDrive / SharePoint files

Files synced from OneDrive or SharePoint Online have a "Files
On-Demand" placeholder layer; the first `Documents.Open` triggers
hydration that may take seconds and surfaces as `RPC_E_CALL_REJECTED`
rather than a true lock. Either pin the file with `attrib +U -P
big.vsdx` (always keep on device) or `shutil.copy2` it to a non-synced
local path for the duration of the batch.

---

## 5. Locale, Bitness, and Cell-Name Pitfalls

### 5.1 32-bit vs 64-bit mismatch

`pywintypes.com_error: (-2147221164, 'Class not registered', None, None)`
(`0x80040154 REGDB_E_CLASSNOTREG`) almost always means the calling
process bitness does not match the installed Office bitness. Visio
2019/2021/365 ship 64-bit by default; older installs may be 32-bit.

```powershell
# Confirm installed Visio bitness
(Get-ItemProperty 'HKLM:\Software\Microsoft\Office\ClickToRun\Configuration' Platform).Platform

# Confirm Python bitness
py -3.12 -c "import platform; print(platform.architecture())"
```

If they disagree, switch interpreters:

```powershell
# 64-bit Python launcher
py -3.12-64 script.py

# 32-bit Python launcher
py -3.12-32 script.py
```

For PowerShell, `powershell.exe` is 64-bit on x64 Windows; the 32-bit
shim is at `%WINDIR%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe`.

### 5.2 Localized cell names

Visio's COM API has *two* parallel sets of properties - localized and
universal:

| Localized (avoid) | Universal (always use) |
| ----------------- | ---------------------- |
| `Cells(...)`      | `CellsU(...)`          |
| `Formula`         | `FormulaU`             |
| `Result(unit)`    | `ResultIU` (inches) / `Result(unit)` reads either |
| `Name`            | `NameU`                |
| `Item(name)`      | `ItemU(name)`          |

On a French Visio install, `shape.Cells("PinX")` raises
`DISP_E_MEMBERNOTFOUND` because `PinX` is `BrocheX` in French.
`shape.CellsU("PinX")` always works regardless of UI language.

### 5.3 Decimal separator in formulas

`FormulaU` always expects en-US syntax: period as decimal separator,
no thousands grouping, semicolon-free arguments. A French-locale
runtime that does

```python
shape.CellsU("Width").Formula = f"={width:.2f} in"   # writes "3,50 in"
```

raises "Visio could not parse formula". Use `FormulaU` and pass an
invariant culture format:

```python
import locale
val = f"={width:.2f}".replace(",", ".") + " in"
shape.CellsU("Width").FormulaU = val
```

Or in C#:

```csharp
shape.CellsU["Width"].FormulaU =
    $"={width.ToString("F3", CultureInfo.InvariantCulture)} in";
```

---

## 6. Connector Glue Lost After Master Re-Import

Re-importing a master from a stencil to fix a visual bug or update a
connection-point list has a side effect: every existing connector that
was glued to the old instance loses its glue and falls back to a
"floating" geometry, leaving the connector pointing at the spatial
location it last computed but no longer dynamically tracking the
shape.

### 6.1 What "glue" actually is

A connector is a 1-D shape with `BeginX`, `BeginY`, `EndX`, `EndY`
cells. Glue is recorded in two places:

1. The connector's `BeginX` / `EndX` cell `Formula` is set to a
   `PNTX(GLUETO(...))` expression that references the target shape.
2. A `<Connect>` row in the page's `<Connects>` section logs the
   triplet `(connector_id, "BeginX"|"EndX", target_id, target_part)`.

When you delete a master and re-import, the new instances get fresh
shape IDs. The `<Connect>` rows still reference the *old* target IDs,
which no longer resolve, so Visio drops the glue silently on next
open.

### 6.2 Detection

```python
def is_dangling(page) -> list:
    """Return Connect rows whose to_id no longer resolves."""
    bad = []
    for c in page.connects:
        if page.find_shape_by_id(c.to_id) is None:
            bad.append(c)
        elif page.find_shape_by_id(c.from_id) is None:
            bad.append(c)
    return bad
```

In the COM API, walk `page.Connects`:

```python
for i in range(1, page.Connects.Count + 1):
    conn = page.Connects.Item(i)
    from_shape = conn.FromSheet      # connector
    to_shape   = conn.ToSheet        # target
    from_part  = conn.FromPart        # 9 = BeginX, 12 = EndX
    to_part    = conn.ToPart          # 100+ = connection point
    print(from_shape.Name, "->", to_shape.Name, from_part, to_part)
```

`FromPart` constants from `VisCellIndices`:

| Value | Constant            | Meaning              |
| ----- | ------------------- | -------------------- |
| 9     | `visBegin`          | `BeginX`             |
| 12    | `visEnd`            | `EndX`               |
| 100+  | `visConnectionPt`   | Specific connection point on target |

### 6.3 Re-import without breaking glue

The safe sequence is *replace-in-place* using `Master.Replace`, which
preserves shape IDs and rewires connectors automatically:

```python
old = doc.Masters.ItemU("Process")
stencil = app.Documents.OpenEx(stencil_path, 2 + 64 + 512)  # RO+Hidden+Docked
new = stencil.Masters.ItemU("Process")
old.Replace(new)        # preserves IDs, rewires <Connects> rows
stencil.Close()
```

`Master.Replace(otherMaster)` replaces the master in the active
document with `otherMaster`, preserving every instance's `ID`,
`PinX/PinY`, `Width/Height`, text, Shape Data, and crucially the
`<Connects>` rows that reference instance IDs.

### 6.4 Re-glue after a destructive re-import

If re-import already happened without `Master.Replace`, walk the
former glue table (cached pre-import) and re-glue:

```python
def reglue(page, from_shape_name: str, end: str, target_name: str,
           target_pin: str = "PinX") -> None:
    """end is 'BeginX' or 'EndX'; target_pin is 'PinX' or a connection point cell."""
    conn   = page.Shapes.ItemU(from_shape_name)
    target = page.Shapes.ItemU(target_name)
    conn.CellsU(end).GlueTo(target.CellsU(target_pin))
```

`Cell.GlueTo(targetCell)` resolves to the nearest connection point on
the target. For positional glue (e.g. always at the right edge), use
`Cell.GlueToPos(target_shape, x_frac, y_frac)` where `(0,0)` is the
target's bottom-left local origin and `(1,1)` is its top-right.

### 6.5 Bulk regenerator

When dozens of connectors lost glue, regenerate from a saved manifest
of `(connector, end, target, target_pin)` rows. Pseudocode:

```python
for row in csv.DictReader(open(manifest_csv, encoding="utf-8")):
    conn   = page.Shapes.ItemU(row["connector"])
    target = page.Shapes.ItemU(row["target"])
    conn.CellsU(row["end"]).GlueTo(target.CellsU(row["target_pin"]))
```

Always export the manifest *before* re-importing masters - the
`<Connect>` rows are the source of truth and are easy to lose.

### 6.6 Layout vs glue, vsdx limits

`Page.Layout()` recomputes connector geometry but does *not*
re-establish broken glue. A connector with no `<Connect>` rows is a
free-floating 1-D shape; `Layout()` routes it from `BeginX/Y` to
`EndX/Y` literal coordinates. Re-glue first, then call `Layout()`.

The pure-Python `vsdx` library can read and rewrite `<Connect>` rows
through `Page.connects`, but it cannot resolve "best connection
point" the way `Cell.GlueTo()` does in COM. After mass-mutating glue
with `vsdx`, the next Visio open re-validates. Visually-stable
templates keep glue baked into the master and only mutate text /
Shape Data through `vsdx`.

---

## 7. Theme Reset on Stencil Drag

Dropping a master from a freshly opened stencil onto a themed page can
silently reset the page's theme to the *stencil's* theme, replacing
your QuickStyle assignments. The trigger is Visio's auto-merge of
theme parts when a stencil with its own theme is loaded into a
document that already has one.

### 7.1 Theme storage

Themes are stored under the OPC parts:

| Part path                          | Content                                    |
| ---------------------------------- | ------------------------------------------ |
| `/visio/theme/theme1.xml`          | Theme color/font/effect scheme              |
| `/visio/document.xml`              | Active theme reference (`theme="theme1"`)   |
| `/visio/pages/page*.xml`           | Per-shape `QuickStyle*` cell values         |

Per shape, the relevant cells are:

| Cell                    | Meaning                                          |
| ----------------------- | ------------------------------------------------ |
| `QuickStyleFillColor`   | Index into theme's accent palette (1-6)          |
| `QuickStyleLineColor`   | Same                                             |
| `QuickStyleShadowColor` | Same                                             |
| `QuickStyleFontColor`   | Same                                             |
| `QuickStyleFillMatrix`  | Variant: 0=solid, 1-99=preset combinations       |
| `QuickStyleLineMatrix`  | Same for line styles                             |
| `QuickStyleEffectMatrix` | Same for effects                                |
| `QuickStyleFontMatrix`  | Same for typography                              |
| `QuickStyleType`        | 0=geometric, 1=connector                         |
| `QuickStyleVariation`   | 0-3 - theme variant within accent                |

These integers reference the *active* theme; replacing the theme part
changes how every shape renders without touching the cells.

### 7.2 Repro

```python
# Author a page with a custom theme already applied
doc = app.Documents.Open("templated-with-Whisp.vsdx")
page = doc.Pages.Item(1)

# Open a stencil that ships with its own default theme (Office, Linear, etc.)
stencil = app.Documents.OpenEx("BasicShapes.vssx", 2 + 64)

# Drop a master - Visio merges the stencil theme silently
m = stencil.Masters.ItemU("Process")
page.Drop(m, 4, 6)
# At this point the page may have switched from "Whisp" to "Office"
```

### 7.3 Defenses

| # | Approach                          | Code                                                                                                |
| - | --------------------------------- | --------------------------------------------------------------------------------------------------- |
| 1 | Drop with no-theme flag            | `page.DropEx(master, x, y, 8)` - pass `visDropEx_NoTheme = 8` to suppress theme merge                |
| 2 | Drop then re-apply theme           | `prev = doc.Themes.Item(0); shape = page.Drop(master, x, y); doc.Themes.Apply(prev)`                |
| 3 | Lock theme on the DocumentSheet    | `doc.DocumentSheet.CellsU("ThemeIndex").FormulaU = '=THEMENAME("Whisp")'`                            |
| 4 | Reset QuickStyle on dropped shapes | Set every `QuickStyleFillColor` / `LineColor` / `ShadowColor` / `FontColor` / `FillMatrix` / `LineMatrix` / `EffectMatrix` cell to `=THEMEGUARD(THEMEVAL())` |

`THEMEGUARD(THEMEVAL())` is the Visio formula equivalent to "use the
default theme value and resist override attempts" - the same formula
Visio applies on "Reset to theme defaults" in the Design ribbon. If
your Visio build does not expose `DropEx`, defense 2 is the fallback.

### 7.4 Detecting a silent reset in tests

```python
def assert_theme(doc, expected: str) -> None:
    cell = doc.DocumentSheet.CellsU("ThemeIndex").FormulaU
    if expected not in cell:
        raise AssertionError(
            f"theme drift: expected {expected!r}, got {cell!r}")
```

Run after every `Drop` / `DropMany` / `Documents.OpenEx` of a stencil.
The pattern catches drift before it propagates to the saved file.

### 7.5 Authoring and library limits

The `vsdx` Python library can read and write QuickStyle indices and
the raw `theme1.xml` part, but it cannot synthesize a coherent theme
from a name like `"Whisp"` the way `Document.Themes` does in COM. If
your pipeline mutates with `vsdx` and needs theme correctness, do the
theme work in a Windows COM post-step (see `vsdx` chapter §13.1).

Best authoring practice: stencils that ship in templates should *not*
embed their own theme parts. In Visio Edit Master mode, set Design >
Themes > **No Theme**, save the `.vssx`, and verify the `theme/`
parts inside the OPC ZIP contain only a default `theme1.xml`. A
stencil with no theme cannot trigger merge on drop.

---

## 8. Font Substitution: No Aptos / Calibri Available

Visio 365 (post-2024) defaults shape text to **Aptos** (the Office UI
font that replaced Calibri). Older files default to **Calibri**.
Neither font ships with the OS or with `.vsdx` packages by default;
they are part of the Office font installation. Headless Linux runners,
Server Core, hardened images without Office fonts, or `vsdx` running
without rendering all face the same fallback.

### 8.1 Where font names live

| Location                       | Cell / element                                 |
| ------------------------------ | ---------------------------------------------- |
| ShapeSheet (per-shape)         | `Char.Font` (numeric font index into Document.Fonts) |
| ShapeSheet (per-shape)         | `Char.AsianFont`, `Char.ComplexScriptFont`     |
| Document.Fonts collection      | `Document.Fonts.Item(idx).Name`                |
| OPC `document.xml`             | `<FaceName>Aptos</FaceName>`                   |
| OPC theme `theme1.xml`         | `<a:majorFont>` / `<a:minorFont>` per locale   |

### 8.2 Symptoms

| Surface                       | Manifestation                                                           |
| ----------------------------- | ----------------------------------------------------------------------- |
| Visio open on Office machine  | Renders correctly; no warning                                            |
| Visio open on plain Windows   | Falls back to **Microsoft Sans Serif** or **Arial**; metrics shift      |
| Page.Export PNG/SVG           | Glyphs reflowed; bounding boxes off                                      |
| ExportAsFixedFormat PDF       | PDF embeds *substituted* font, not Aptos                                 |
| Linux container (vsdx + LibreOffice render) | "Aptos not found" warnings; substitute is Liberation Sans     |

### 8.3 Detection in the OPC

```python
import zipfile, re
from xml.etree import ElementTree as ET

NS = "http://schemas.microsoft.com/office/visio/2012/main"

def fonts_used(vsdx_path: str) -> set:
    out = set()
    with zipfile.ZipFile(vsdx_path) as z:
        for name in z.namelist():
            if not name.endswith(".xml"):
                continue
            data = z.read(name).decode("utf-8", errors="ignore")
            for m in re.finditer(r'Char\.Font\b.*?V="([^"]+)"', data):
                out.add(m.group(1))
            for m in re.finditer(r'<FaceName>([^<]+)</FaceName>', data):
                out.add(m.group(1))
    return out

print(fonts_used("input.vsdx"))    # {'Aptos', 'Calibri', ...}
```

### 8.4 Substitution policy on Windows

Windows resolves missing fonts through the registry:

```
HKLM\Software\Microsoft\Windows NT\CurrentVersion\FontSubstitutes
    Aptos    REG_SZ   Microsoft Sans Serif
    Calibri  REG_SZ   Carlito
```

The default substitution chain is:

| Missing font | Win10/11 default substitute   | Linux (Liberation pack)   |
| ------------ | ----------------------------- | ------------------------- |
| Aptos        | Microsoft Sans Serif (10/11)  | DejaVu Sans               |
| Calibri      | Carlito (if installed) / Arial | Carlito (Liberation Sans) |
| Cambria      | Caladea                       | Caladea                   |
| Consolas     | Consolas (always installed?) - else Courier New | DejaVu Sans Mono |
| Segoe UI     | Tahoma                         | DejaVu Sans               |

Carlito and Caladea are metric-compatible substitutes for Calibri and
Cambria. They are not pixel-identical but preserve line breaks and
column widths.

### 8.5 Fix on Office-less workers

**Option A: install the Office font pack.** Microsoft distributes
Aptos and Calibri inside the Office Click-to-Run installation. For
non-Office machines, redistributable sources:

| Font     | Source                                                            |
| -------- | ----------------------------------------------------------------- |
| Aptos    | `aka.ms/AptosFontFamily` (free download from Microsoft Cloud)     |
| Calibri  | Bundled with PowerPoint Viewer 2007 (legacy) or Office click-to-run |
| Carlito  | Google Fonts (open source, Calibri metric-compatible)             |
| Caladea  | Google Fonts (Cambria metric-compatible)                          |

Install per-user on Windows (no admin needed since Win10 1803):

```powershell
$dst = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
New-Item -ItemType Directory $dst -Force | Out-Null
Copy-Item ".\Aptos.ttf" $dst
$reg = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
New-Item -Path $reg -Force | Out-Null
Set-ItemProperty $reg 'Aptos (TrueType)' -Value (Join-Path $dst 'Aptos.ttf')
```

Debian/Ubuntu: `apt-get install -y fonts-crosextra-carlito
fonts-crosextra-caladea && fc-cache -fv`.

**Option B: rewrite font names in the source `.vsdx`.** If you
cannot install fonts, rewrite face names to a universally-available
font (e.g. **Arial**):

```python
from vsdx import VisioFile

REPLACEMENTS = {"Aptos": "Arial", "Calibri": "Arial",
                "Cambria": "Times New Roman"}

with VisioFile("input.vsdx") as v:
    for p in v.pages:
        for s in p.all_shapes:
            for name in ("Char.Font", "Char.AsianFont",
                         "Char.ComplexScriptFont"):
                cell = s.cells.get(name)
                if cell and cell.value in REPLACEMENTS:
                    cell.value = REPLACEMENTS[cell.value]
    v.save_vsdx("output-arial.vsdx")
```

Note: `Char.Font` may store a numeric index into `Document.Fonts`
rather than a face name; in that case rewrite the `Document.Fonts`
entry via raw XML access instead.

### 8.6 Embedding fonts in the file

`Document.EmbedTrueTypeFonts` (Boolean) controls whether Visio embeds
font subsets in the saved `.vsdx`. Enable for portable distribution:

```python
doc.EmbedTrueTypeFonts = True
doc.SaveAs(out_path)
```

Embedded fonts inflate the `.vsdx` by ~200 KB-1 MB per font but
guarantee identical rendering on any machine. Licensed fonts (most
Microsoft fonts allow embedding for "preview and print", not edit).
Verify the licensing flag with the OS-1 table of the TTF before
relying on embedding.

### 8.7 Font cache corruption

If a font is installed but Visio still substitutes, the per-user font
cache may be corrupt. Symptoms: dialog "Some fonts are missing or
unable to be loaded". Fix:

```powershell
Stop-Service FontCache -Force
Remove-Item "$env:WINDIR\ServiceProfiles\LocalService\AppData\Local\FontCache\*" -Force -Recurse
Remove-Item "$env:LOCALAPPDATA\Microsoft\FontCache\*" -Force -Recurse
Start-Service FontCache
```

In a Server Core / non-interactive context, also ensure the per-user
profile has a valid `%LOCALAPPDATA%\Microsoft\FontCache` directory -
some service-account profiles miss this on first activation.

---

## 9. `vsdx` Python Read Errors After Macro Removal

When a `.vsdm` (macro-enabled) is converted to `.vsdx` (macro-free),
Visio strips the `visio/vbaProject.bin` part. If the conversion is
done by a tool that does *not* update `[Content_Types].xml` and the
`_rels` graph, the resulting file is structurally inconsistent.
`vsdx` then fails to parse it.

### 9.1 Symptoms

| Surface                                              | Exception                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| `VisioFile("converted.vsdx")`                        | `lxml.etree.XMLSyntaxError` on a content-types parse         |
| `VisioFile("converted.vsdx")`                        | `KeyError: 'visio/vbaProject.bin'` from internal lookup      |
| Visio interactive open                               | "Visio found unrecoverable problems" red bar; prompt to repair |
| Re-zip with python `zipfile`                         | `BadZipFile: Bad magic number for central directory`         |
| `python -m zipfile -t converted.vsdx`                | OK (zip itself valid) - mismatch is OPC-level                |

### 9.2 What to inspect

Three OPC parts must agree:

1. `[Content_Types].xml` - declares MIME type for every part.
2. `_rels/.rels` - root relationships graph.
3. `visio/_rels/document.xml.rels` - per-part relationships.

After macro removal, the following entries should be absent:

| Part to be absent                                | In which file              |
| ------------------------------------------------ | -------------------------- |
| `visio/vbaProject.bin`                           | ZIP entry list              |
| `<Default Extension="bin" ContentType="application/vnd.ms-office.vbaProject"/>` | `[Content_Types].xml` if no other `.bin` parts remain |
| `<Override PartName="/visio/vbaProject.bin" ...>` | `[Content_Types].xml`     |
| `<Relationship ... Type=".../vbaProject" Target="vbaProject.bin"/>` | `visio/_rels/document.xml.rels` |

If any of these reference the missing part, OPC validators (and `vsdx`)
treat the file as corrupt.

### 9.3 Diagnosis script

```python
import zipfile
from lxml import etree

CT  = "{http://schemas.openxmlformats.org/package/2006/content-types}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

def diagnose(path: str) -> None:
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        ct = etree.fromstring(z.read("[Content_Types].xml"))
        overrides = {o.get("PartName") for o in ct.findall(f"{CT}Override")}
        rp = "visio/_rels/document.xml.rels"
        rels = etree.fromstring(z.read(rp)) if rp in names else None
        targets = {r.get("Target") for r in (rels or [])} if rels is not None else set()

    has_vba = "visio/vbaProject.bin" in names
    if not has_vba and any("vbaProject" in t for t in targets):
        print("CORRUPT: rels still points at missing vbaProject.bin")
    if not has_vba and "/visio/vbaProject.bin" in overrides:
        print("CORRUPT: Content_Types Override still declares vbaProject.bin")
```

### 9.4 Repair recipe

The fix is mechanical: extract the OPC, drop the macro part if
present, strip stale `<Override>` and `<Relationship>` entries that
reference it, then re-zip. The cleanup steps in order:

1. **`visio/vbaProject.bin`** - delete if present in the extracted
   ZIP.
2. **`[Content_Types].xml`** - remove the `<Override
   PartName="/visio/vbaProject.bin" ...>` entry. Also drop the
   `<Default Extension="bin" ContentType="...vbaProject"/>` mapping
   if no other `.bin` parts remain.
3. **`visio/_rels/document.xml.rels`** - remove every
   `<Relationship>` whose `Target` contains `vbaProject`.
4. Re-zip the directory tree using `zipfile.ZIP_DEFLATED`.

```python
import zipfile, shutil, os, tempfile
from lxml import etree

CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
RL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

def repair(src: str, dst: str) -> None:
    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(src) as zin:
            zin.extractall(tmp)

        # 1. drop macro part
        vba = os.path.join(tmp, "visio", "vbaProject.bin")
        if os.path.exists(vba):
            os.remove(vba)

        # 2. clean Content_Types
        ct_path = os.path.join(tmp, "[Content_Types].xml")
        ct = etree.parse(ct_path)
        for o in ct.findall(f"{CT}Override"):
            if o.get("PartName") == "/visio/vbaProject.bin":
                o.getparent().remove(o)
        ct.write(ct_path, xml_declaration=True,
                 encoding="UTF-8", standalone=True)

        # 3. clean rels
        rels_path = os.path.join(tmp, "visio", "_rels",
                                 "document.xml.rels")
        if os.path.exists(rels_path):
            rels = etree.parse(rels_path)
            for r in rels.findall(f"{RL}Relationship"):
                if "vbaProject" in (r.get("Target") or ""):
                    r.getparent().remove(r)
            rels.write(rels_path, xml_declaration=True,
                       encoding="UTF-8", standalone=True)

        # 4. re-zip
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for dp, _, fs in os.walk(tmp):
                for f in fs:
                    full = os.path.join(dp, f)
                    rel = os.path.relpath(full, tmp).replace(os.sep, "/")
                    zout.write(full, arcname=rel)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

### 9.5 Prefer Visio's own conversion

The safest macro removal path is Visio itself - `Document.SaveAs` to a
`.vsdx` extension automatically strips macros and rewrites all OPC
metadata correctly:

```python
doc = app.Documents.OpenEx(macro_path, 64 + 128)   # Hidden + MacrosDisabled
doc.SaveAs(macro_free_path)                         # extension forces strip
doc.Close()
```

`.vsdm -> .vsdx` is the only path that preserves OPC well-formedness
in all corner cases.

### 9.6 Validate before saving

Add an OPC check to CI before publishing converted files:

```python
import vsdx
from lxml.etree import XMLSyntaxError
from zipfile import BadZipFile

def opc_valid(path: str) -> bool:
    try:
        with vsdx.VisioFile(path) as v:
            _ = len(v.pages)            # forces parse of every part
        return True
    except (BadZipFile, XMLSyntaxError, KeyError):
        return False
```

`vsdx` parses every XML part on open, so `len(v.pages)` immediately
after open forces any dangling-part violation to surface
deterministically rather than lazily during a later page walk.

---

## 10. Threading and Apartment Failures

### 10.1 `CO_E_NOTINITIALIZED` (`0x800401F0`)

The first COM call on a worker thread fails when no apartment has
been initialized. Always call `pythoncom.CoInitialize()` (STA) before
the first `Dispatch` / `DispatchEx` and `pythoncom.CoUninitialize()`
on exit.

```python
import threading, pythoncom, win32com.client as wc

def _worker(path: str) -> None:
    pythoncom.CoInitialize()
    try:
        app = wc.DispatchEx("Visio.InvisibleApp")
        try:
            doc = app.Documents.Open(path)
            doc.Close()
        finally:
            app.Quit()
    finally:
        pythoncom.CoUninitialize()

t = threading.Thread(target=_worker, args=(r"C:\d.vsdx",))
t.start(); t.join()
```

### 10.2 `RPC_E_CHANGED_MODE` (`0x80010106`)

A subsequent `CoInitializeEx` with a different apartment flag than
the one already set on the thread fails with `0x80010106`. The
canonical case: pytest-qt or another framework already initialized
MTA, then your code calls `CoInitialize()` (STA). Resolution: pick
one apartment per thread and stick with it. For Visio, that
apartment must be STA.

### 10.3 `RPC_E_DISCONNECTED` (`0x80010108`)

The proxy points at a server that no longer exists. Causes:

| Cause                                                  | Fix                                                                |
| ------------------------------------------------------ | ------------------------------------------------------------------ |
| Visio crashed mid-operation                            | Reacquire `Application` proxy; do not reuse old `Document` refs    |
| You called `app.Quit()` and then used a cached `doc`   | Reopen Visio; never cache document proxies across `Quit`           |
| Event delegate target was garbage-collected            | Hold the delegate in a class field (see `[[09-csharp-vsto-addins]]` §6) |
| `AddAdvise` sink object went out of scope              | Keep the sink in module scope or as a class field                  |

```python
# WRONG: lambda is GC'd; events stop firing
app.SelectionChanged += lambda w: do_something(w)

# RIGHT: hold a strong reference
self._handler = lambda w: do_something(w)
app.SelectionChanged += self._handler
```

### 10.4 `RPC_E_WRONG_THREAD` (`0x8001010E`)

A proxy bound to thread A used from thread B without GIT marshalling.
Visio is STA-bound; cross-thread access requires
`IGlobalInterfaceTable.RegisterInterfaceInGlobal` /
`GetInterfaceFromGlobal`. Practical advice: do not share proxies
across threads. Spawn one Visio per worker, use process-level
parallelism. For PowerShell 7 default MTA, see §2.5.

### 10.5 asyncio gotcha

`asyncio` tasks share one thread (the event loop). Visio calls block
that thread for the duration of every `Drop` / `Layout` /
`ExportAsFixedFormat`. Run COM work in `loop.run_in_executor(None,
fn)` with `pythoncom.CoInitialize()` inside `fn`. Without that, the
event loop stalls; with the wrong apartment in the executor, the
worker thread fails with `0x800401F0`.

```python
async def render(path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_render, path)

def _sync_render(path: str) -> str:
    pythoncom.CoInitialize()
    try:
        # ... Visio work ...
        return out
    finally:
        pythoncom.CoUninitialize()
```

---

## 11. Cross-Layer Decision Flow

Use this table when triaging a "Visio failed" report:

| Observed                                  | First action                                                  |
| ----------------------------------------- | ------------------------------------------------------------- |
| Hex `0x80004005` and no description       | Print `excepinfo[2]`; rerun `Visible=True` to read dialog     |
| Hex `0x80010001`                          | Add `retry_com`; check for orphan dialogs                     |
| `AttributeError` on Visio object          | Flush `gen_py`; rerun `EnsureModule` with current `(maj,min)` |
| `PermissionError` opening file            | `handle.exe` to find the holder; pause OneDrive/indexer       |
| Connectors look detached after re-import  | Use `Master.Replace`; restore glue from manifest CSV           |
| Theme drifted from "Whisp" to "Office"    | Drop with `DropEx(... 8)`; reapply theme; lock with formula   |
| Wrong glyph shapes in PDF                 | Confirm font installed; install Carlito/Caladea or rewrite     |
| `BadZipFile` on a converted `.vsdx`       | Run repair script (§9.4); validate before publishing           |
| `0x800401F0` on first call                | Add `pythoncom.CoInitialize()` to the calling thread           |
| `0x80010108` after long run               | Hold event handlers in fields; do not cache proxies past `Quit` |
| `0x80040154` on `Dispatch`                | Match Python bitness to Office bitness                         |
| Add-in disappeared from Ribbon            | Inspect `LoadBehavior`; reset to 3; check Disabled Items list   |

---

## 12. Diagnostic Tools

### 12.1 `excepinfo` printer

```python
import pywintypes

def explain(e: pywintypes.com_error) -> str:
    h, src, info, arg = e.args
    out = [f"HRESULT={h & 0xFFFFFFFF:#010x} ({h})"]
    if src:    out.append(f"Source : {src}")
    if info:
        wcode, wsrc, wdescr, whelp, whelpid, scode = info
        out.append(f"WCode  : {wcode}")
        out.append(f"Source2: {wsrc}")
        out.append(f"Detail : {wdescr}")
        out.append(f"SCode  : {scode & 0xFFFFFFFF:#010x}")
    if arg is not None:
        out.append(f"ArgErr : index {arg}")
    return "\n".join(out)
```

### 12.2 Tracing every COM call

```python
class TracingDispatch:
    def __init__(self, inner, name="Visio"):
        object.__setattr__(self, "_inner", inner)
        object.__setattr__(self, "_name",  name)
    def __getattr__(self, item):
        attr = getattr(self._inner, item)
        if callable(attr):
            def call(*a, **kw):
                print(f"{self._name}.{item}({a}, {kw})")
                rv = attr(*a, **kw)
                if hasattr(rv, "_oleobj_"):
                    return TracingDispatch(rv, f"{self._name}.{item}")
                return rv
            return call
        if hasattr(attr, "_oleobj_"):
            return TracingDispatch(attr, f"{self._name}.{item}")
        return attr
    def __setattr__(self, k, v):
        setattr(self._inner, k, v)

app = TracingDispatch(wc.DispatchEx("Visio.InvisibleApp"))
```

Wrapping every proxy logs every method call and property access.
Useful for catching the exact line that triggers `E_FAIL` in third-
party code that swallows exceptions.

### 12.3 ShapeSheet snapshot

```python
def dump_shapesheet(shape, path: str) -> None:
    import pywintypes
    with open(path, "w", encoding="utf-8") as f:
        for section in range(255):
            try:
                rows = shape.RowCount(section)
            except pywintypes.com_error:
                continue
            for r in range(rows):
                try:
                    cols = shape.RowsCellCount(section, r)
                except pywintypes.com_error:
                    continue
                for col in range(cols):
                    try:
                        cell = shape.CellsSRC(section, r, col)
                        f.write(f"{section},{r},{col}\t"
                                f"{cell.Name}\t{cell.FormulaU}\n")
                    except pywintypes.com_error:
                        pass
```

A complete pre/post snapshot makes "what cell did the operation
mutate?" debuggable; diff the two files.

### 12.4 OPC inspection without `vsdx`

For corrupt files that `vsdx` refuses to open, drop to raw `zipfile +
lxml` to inspect `[Content_Types].xml`, `_rels/.rels`, and
`visio/_rels/document.xml.rels`. Walk every `*.rels` part to find
dangling references to missing parts; that is the most common
source of "Visio found unrecoverable problems" errors after macro
removal (see §9.3 for a full diagnostic).

### 12.5 Other channels

| Channel                                 | Use                                                                          |
| --------------------------------------- | ---------------------------------------------------------------------------- |
| `Application.DiagnosticOutput` (Visio 2019+) | Live ShapeSheet recalc tracing in interactive Visio                          |
| ETW provider `Microsoft-Windows-Office-Document-Lifecycle-Provider` | OPC reader/writer internals via `logman` / `tracerpt`             |
| Process Monitor filter `Process Name is VISIO.EXE` | Activation failures: `ACCESS DENIED` on `%LOCALAPPDATA%\Microsoft\FontCache\` (font cache, §8.7); `NAME NOT FOUND` on `*\Desktop\` (server activation needs both `System32\config\systemprofile\Desktop` and `SysWOW64\config\systemprofile\Desktop`); `ACCESS DENIED` on `Office\root\Office16\VISIO.EXE` (per-user C2R install missing) |
| Event Viewer -> Application, source `VSTO` or your add-in's ProgID | Add-in load failures and `LoadBehavior` flips                                 |
| `%TEMP%\<addin>.vsto.log` with `VSTO_LOGALERTS=1` | VSTO startup diagnostics                                                     |

---

## 13. Sources

- `research/06-python-com-automation.md` - pywin32 / `win32com.client`
  COM automation, `pywintypes.com_error` decoding, makepy / gencache,
  threading, `IGlobalInterfaceTable`, retry decorator, performance.
- `research/07-python-vsdx-library.md` - the `vsdx` package, OPC
  semantics, `VisioFile` lifecycle, locking, raw XML access, theme /
  layout limits versus COM.
- `research/08-powershell-automation.md` - `Visio.InvisibleApp` from
  PowerShell, `RPC_E_*` decoding, default printer fix, Task Scheduler
  / Session 0 / Desktop folder fix, DCOM permissions, batch
  performance.
- `research/09-csharp-vsto-addins.md` - VSTO + IDTExtensibility2
  add-ins, `LoadBehavior` semantics, Ribbon callback signatures,
  event-delegate rooting rule, `RPC_E_DISCONNECTED` causes.
- `research/27-events-add-in-architecture.md` - `EventList` /
  `AddAdvise` sinks, `WithEvents`, scope and undo model,
  `UndoMechanism = visUndoMechOff`, font / theme / trust-center
  policy hives.

