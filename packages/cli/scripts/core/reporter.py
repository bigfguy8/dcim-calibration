"""
Timestamped report archival.

Every pipeline run produces a JSON report archived under
``analysis/reports/<YYYYMMDD>T<HHMMSS>_<runid>.json`` along with a human
readable markdown summary. Transient, per-run logs live in ``logs/``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .pipeline import PipelineResult

from .config import DaemonConfig


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Reporter:
    """Writes and archives calibration reports."""

    def __init__(self, config: DaemonConfig, log) -> None:
        self.cfg = config
        self.log = log
        self.cfg.reports_dir.mkdir(parents=True, exist_ok=True)
        self.cfg.metrics_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def write_run_report(
        self, run_id: str, result: PipelineResult, state: dict[str, Any]
    ) -> list[Path]:
        """Archive a full run report; return the paths written."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        base = self.cfg.reports_dir / f"{stamp}_{run_id}"
        base.mkdir(parents=True, exist_ok=True)

        report = {
            "run_id": run_id,
            "timestamp": result.timestamp,
            "success": result.success,
            "stages": result.stages,
            "processed": result.processed,
            "errors": result.errors,
            "auto_tune": result.auto_tune,
            "git": result.git,
            "state_summary": {
                "profiles_tracked": len(state.get("profiles", {})),
                "captures_tracked": len(state.get("captures", {})),
                "run_count": state.get("run_count", 0),
            },
            "directories": {
                "dcim": str(self.cfg.dcim_path),
                "configs_xml": str(self.cfg.configs_xml_path),
                "captures": str(self.cfg.captures_dir),
                "reports": str(self.cfg.reports_dir),
            },
        }

        paths: list[Path] = []
        json_path = base / "run_report.json"
        json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        paths.append(json_path)

        md_path = base / "run_report.md"
        md_path.write_text(self._markdown(report), encoding="utf-8")
        paths.append(md_path)

        # Also append a one-line index entry for quick discovery.
        index = self.cfg.reports_dir / "index.jsonl"
        with open(index, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "run_id": run_id,
                        "timestamp": result.timestamp,
                        "success": result.success,
                        "processed": len(result.processed),
                        "errors": len(result.errors),
                        "report": str(json_path),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

        self.log.info("reporter", f"Archived run report -> {json_path}")
        return paths

    def write_metrics_report(
        self, metrics: dict[str, Any], label: str = "metrics"
    ) -> Path:
        """Archive an ad-hoc metrics snapshot (e.g. auto-tune input)."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = self.cfg.reports_dir / f"{stamp}_{label}.json"
        path.write_text(
            json.dumps(
                {"timestamp": _utc_now(), "label": label, "metrics": metrics},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.log.info("reporter", f"Archived metrics report -> {path}")
        return path

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _markdown(report: dict[str, Any]) -> str:
        lines = [
            f"# Calibration Run Report",
            f"- **Run ID:** {report['run_id']}",
            f"- **Timestamp:** {report['timestamp']}",
            f"- **Success:** {report['success']}",
            "",
            "## Stages",
        ]
        for name, data in report["stages"].items():
            lines.append(f"### {name}")
            if isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f"- {k}: {v}")
            lines.append("")
        lines.append("## Processed")
        for item in report["processed"]:
            lines.append(f"- {item.get('kind')} {item.get('path') or item.get('file')}")
        if report["errors"]:
            lines.append("")
            lines.append("## Errors")
            for e in report["errors"]:
                lines.append(f"- {e}")
        lines.append("")
        lines.append(f"## State")
        ss = report["state_summary"]
        lines.append(f"- Profiles tracked: {ss['profiles_tracked']}")
        lines.append(f"- Captures tracked: {ss['captures_tracked']}")
        lines.append(f"- Run count: {ss['run_count']}")
        return "\n".join(lines)
