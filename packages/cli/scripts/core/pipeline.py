"""
Calibration pipeline runner.

Stages (per run)
    1. INGEST    - scan DCIM + configs/xml for new or changed assets
    2. PARSE     - parse XML profiles; extract EXIF from images
    3. ANALYZE   - compute quantitative image metrics (MTF50, dE, vignette, ...)
    4. STAGE     - copy captures into ./captures/<bucket>/
    5. PERSIST   - save state; optional git commit/push
    6. REPORT    - build a timestamped run report (written last so it includes git status)

The runner is idempotent: it tracks content fingerprints in a state file so a
file is only processed once unless it actually changes.
"""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# Make the sibling scripts/ package importable (calib_analysis, auto_tune, ...).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calib_analysis import analyze_image_full  # noqa: E402

try:  # auto-tune is optional in a single pipeline pass
    from auto_tune import run_auto_tune as _run_auto_tune  # noqa: E402
    HAS_AUTO_TUNE = True
except Exception:  # pragma: no cover - environment dependent
    HAS_AUTO_TUNE = False

from .config import DaemonConfig
from .events import Event, EventDispatcher
from .reporter import Reporter
from .gitops import GitOps


@dataclass
class PipelineResult:
    run_id: str
    timestamp: str
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    processed: list[dict[str, Any]] = field(default_factory=list)
    reports: list[Path] = field(default_factory=list)
    git: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    auto_tune: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return not self.errors


class PipelineRunner:
    """Runs one or more calibration pipeline passes."""

    def __init__(
        self,
        config: DaemonConfig,
        log,
        dispatcher: Optional[EventDispatcher] = None,
    ) -> None:
        self.cfg = config
        self.log = log
        self.dispatcher = dispatcher
        self.reporter = Reporter(config, log)
        self.git = GitOps(config, log)

        # Ensure all runtime directories exist.
        for d in (
            config.captures_dir,
            config.logs_dir,
            config.reports_dir,
            config.state_dir,
            config.metrics_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # State helpers
    # ------------------------------------------------------------------ #
    def load_state(self) -> dict[str, Any]:
        if self.cfg.state_file.exists():
            try:
                return _json_load(self.cfg.state_file)
            except Exception:
                return {}
        return {}

    def save_state(self, state: dict[str, Any]) -> None:
        self.cfg.state_file.write_text(
            _native_json(state), encoding="utf-8"
        )

    @staticmethod
    def fingerprint(path: Path) -> str:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
        except OSError:
            return ""
        return h.hexdigest()

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
    def run_once(self, state: Optional[dict[str, Any]] = None) -> PipelineResult:
        """Execute a single pipeline pass over currently pending assets."""
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        result = PipelineResult(run_id=run_id, timestamp=_utc_now())
        state = state if state is not None else self.load_state()

        try:
            changed: list[Path] = []

            # --- 1. INGEST + 2. PARSE + 3. ANALYZE + 4. STAGE ------------
            profiles_state = state.setdefault("profiles", {})
            captures_state = state.setdefault("captures", {})

            changed.extend(self._ingest_profiles(profiles_state, result))
            changed.extend(self._ingest_captures(captures_state, result))

            result.stages["ingest"] = {"files_processed": len(result.processed)}

            # --- 5. PERSIST (state + optional git) ------------------------
            state["last_run"] = result.timestamp
            state["run_count"] = int(state.get("run_count", 0)) + 1
            self.save_state(state)

            git_info = self.git.auto_commit_and_push(
                changed, result, prefix=self.cfg.git_commit_message_prefix
            )
            result.git = git_info
            result.stages["persist"] = {
                "state": str(self.cfg.state_file),
                "git_commit": git_info.get("committed", False),
                "git_push": git_info.get("pushed", False),
            }

            # --- 6. REPORT ------------------------------------------------
            report_paths = self.reporter.write_run_report(
                run_id, result, state
            )
            result.reports = report_paths
            result.stages["report"] = {
                "archived": [str(p) for p in report_paths],
            }

            if self.dispatcher:
                if result.success:
                    self.dispatcher.dispatch(
                        Event(
                            type="pipeline.done",
                            source="pipeline",
                            detail={
                                "run_id": run_id,
                                "processed": len(result.processed),
                                "reports": [str(p) for p in report_paths],
                            },
                        )
                    )
                else:
                    self.dispatcher.dispatch(
                        Event(
                            type="pipeline.failed",
                            source="pipeline",
                            detail={"run_id": run_id, "errors": result.errors},
                        )
                    )

        except Exception as exc:  # pragma: no cover - top-level safety net
            self.log.error("pipeline", f"Pipeline run {run_id} failed: {exc}")
            result.errors.append(str(exc))

        return result

    # ------------------------------------------------------------------ #
    # Stage: profiles
    # ------------------------------------------------------------------ #
    def _ingest_profiles(
        self, profiles_state: dict[str, Any], result: PipelineResult
    ) -> list[Path]:
        changed: list[Path] = []
        src = self.cfg.configs_xml_path
        if not src.exists():
            result.stages["profiles"] = {"source": str(src), "exists": False}
            return changed

        baseline = self._load_baseline()
        for path in sorted(src.glob("*.xml")):
            fp = self.fingerprint(path)
            prev = profiles_state.get(path.name, {}).get("fingerprint")
            if prev == fp:
                continue

            self.log.info("profile", f"Detected change: {path.name}")
            data = self._parse_xml_profile(path)
            diffs = self._profile_diff(baseline, data) if baseline else []

            profiles_state[path.name] = {
                "fingerprint": fp,
                "parsed_at": _utc_now(),
                "keys": len([k for k in data if not k.startswith("_")]),
                "diffs_vs_baseline": len(diffs),
            }
            result.processed.append(
                {"kind": "profile", "path": str(path), "diff_count": len(diffs)}
            )
            changed.append(path)
            result.stages.setdefault("profiles", {"changed": []})["changed"].append(
                {"file": path.name, "diffs": len(diffs)}
            )

        result.stages.setdefault("profiles", {"changed": []})
        return changed

    # ------------------------------------------------------------------ #
    # Stage: captures
    # ------------------------------------------------------------------ #
    def _ingest_captures(
        self, captures_state: dict[str, Any], result: PipelineResult
    ) -> list[Path]:
        changed: list[Path] = []
        src = self.cfg.dcim_path
        if not src.exists():
            result.stages["captures"] = {"source": str(src), "exists": False}
            return changed

        for path in sorted(src.iterdir()):
            if not path.is_file() or path.suffix.lower() not in self.cfg.image_exts:
                continue
            fp = self.fingerprint(path)
            prev = captures_state.get(path.name, {}).get("fingerprint")
            if prev == fp:
                continue

            self.log.info("capture", f"New capture: {path.name}")
            bucket = self._bucket_for(path.name)
            target_dir = self.cfg.captures_dir / bucket
            target_dir.mkdir(parents=True, exist_ok=True)
            destination = target_dir / path.name

            if not destination.exists() or self.fingerprint(destination) != fp:
                try:
                    shutil.copy2(path, destination)
                    changed.append(destination)
                except OSError as exc:
                    self.log.error("capture", f"Stage failed {path.name}: {exc}")
                    result.errors.append(f"stage:{path.name}:{exc}")
                    continue

            # Analyze metrics with the OpenCV/Pillow engine.
            analysis = analyze_image_full(destination)
            metrics = analysis.metrics or {}
            exif = _to_native(analysis.exif or {})

            captures_state[path.name] = {
                "fingerprint": fp,
                "bucket": bucket,
                "staged_at": _utc_now(),
                "source": str(path),
                "staged_path": str(destination),
                "metrics": metrics,
                "exif": exif,
            }
            result.processed.append(
                {
                    "kind": "capture",
                    "path": str(path),
                    "bucket": bucket,
                    "metrics": metrics,
                }
            )
            result.stages.setdefault("captures", {"staged": []})["staged"].append(
                {
                    "file": path.name,
                    "bucket": bucket,
                    "metrics": metrics,
                }
            )
        result.stages.setdefault("captures", {"staged": []})
        return changed

    # ------------------------------------------------------------------ #
    # Auto-tune (periodic, daemon mode)
    # ------------------------------------------------------------------ #
    def run_auto_tune_if_due(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run auto-tune if the interval has elapsed. Returns the tune result."""
        result: dict[str, Any] = {"skipped": True, "reason": "disabled"}
        if not self.cfg.auto_tune_enabled or not HAS_AUTO_TUNE:
            return result

        last_run = state.get("last_auto_tune")
        now = datetime.now(timezone.utc).timestamp()
        if last_run is not None and (now - float(last_run)) < self.cfg.auto_tune_interval:
            return result

        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                _run_auto_tune()
            output = buf.getvalue().strip()
            result = {
                "skipped": False,
                "ran_at": _utc_now(),
                "output": output,
            }
            state["last_auto_tune"] = now
            state["last_auto_tune_result"] = result
            self.save_state(state)
            if self.dispatcher:
                self.dispatcher.dispatch(
                    Event(
                        type="auto_tune.run",
                        source="pipeline",
                        detail={"output": output},
                    )
                )
            self.log.info("auto-tune", output or "auto-tune complete")
        except Exception as exc:
            self.log.error("auto-tune", f"Auto-tune failed: {exc}")
            result = {"skipped": False, "error": str(exc)}
        return result

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _bucket_for(self, name: str) -> str:
        m = re.match(r"^([A-Za-z0-9_]+?)_", name)
        return m.group(1) if m else "Auto_Captured_IMX682"

    def _load_baseline(self) -> dict[str, Any]:
        p = self.cfg.configs_xml_path / self.cfg.baseline_profile
        if p.exists():
            return self._parse_xml_profile(p)
        return {}

    @staticmethod
    def _parse_xml_profile(path: Path) -> dict[str, Any]:
        import xml.etree.ElementTree as ET

        result: dict[str, Any] = {"_file": str(path), "_name": path.name}
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as exc:
            result["_error"] = f"XML parse error: {exc}"
            return result
        for el in root:
            name = el.attrib.get("name")
            if not name:
                continue
            val = (el.text or "").strip()
            if val.lower() in ("true", "false"):
                val = val.lower() == "true"
            else:
                try:
                    val = float(val) if "." in val else int(val)
                except ValueError:
                    pass
            result[name] = val
        return result

    @staticmethod
    def _profile_diff(a: dict[str, Any], b: dict[str, Any]) -> list[dict[str, Any]]:
        keys = sorted(set(a.keys()) | set(b.keys()))
        diffs = []
        for k in keys:
            if k.startswith("_"):
                continue
            va = a.get(k, "<missing>")
            vb = b.get(k, "<missing>")
            if va != vb:
                diffs.append({"key": k, "a": va, "b": vb})
        return diffs


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_load(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _native_json(obj: Any) -> str:
    import json

    def _native(v):
        if isinstance(v, dict):
            return {k: _native(x) for k, x in v.items()}
        if isinstance(v, (list, tuple, set, frozenset)):
            return [_native(x) for x in v]
        if hasattr(v, "isoformat"):
            return v.isoformat()
        if isinstance(v, (bytes, bytearray)):
            return v.decode("utf-8", errors="replace")
        return v

    return json.dumps(_native(obj), indent=2, ensure_ascii=False)


def _to_native(value: Any) -> Any:
    """Recursively convert PIL/EXIF types (IFDRational, tuples) to JSON-native."""
    if isinstance(value, dict):
        return {k: _to_native(x) for k, x in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_native(x) for x in value]
    # PIL IFDRational (EXIF rational values) is float-convertible.
    if type(value).__name__ == "IFDRational":
        try:
            return float(value)
        except Exception:
            return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value
