#!/usr/bin/env python3
"""
IMX682 & LMC 8.4 Calibration Pipeline Orchestrator

Runs the calibration pipeline in discrete, togglable steps:

  1. env      - dependency check + ensure standardized directories
  2. audit    - XML config validation & profile comparison
  3. calibrate- OpenCV MTF50 + sharpness over an image batch
  4. skin_tone- tune skin-tone profile parameters
  5. build_v10- build the V10 baseline config
  6. deploy   - deploy a profile to /sdcard/LMC8.4

Usage examples:
    ./run_pipeline.py                       # run all steps
    ./run_pipeline.py --dry-run             # print plan, execute nothing
    ./run_pipeline.py --skip-audit --verbose
    ./run_pipeline.py --steps env,calibrate --batch-dir /sdcard/DCIM/Camera
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable, List, Tuple

# Allow running both as `./run_pipeline.py` and `python run_pipeline.py`
# from the repo root without installing the package.
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from core import (  # noqa: E402
    DEFAULT_MASTER,
    DEFAULT_TARGET,
    LMC_STORAGE_DIR,
    REPORTS_DIR,
    ensure_dirs,
)
from core import build_v10, calibration, noise, skin_tone, xml_utils  # noqa: E402
from core.logging import get_logger, setup_logger  # noqa: E402

logger = get_logger()


def _step_env(args: argparse.Namespace) -> Tuple[bool, str]:
    ensure_dirs()
    missing = []
    for mod in ("cv2", "numpy", "PIL"):
        try:
            importlib.import_module("cv2" if mod == "cv2" else mod)
        except ImportError:
            missing.append(mod)
    if missing:
        return False, f"missing dependencies: {', '.join(missing)}"
    return True, "environment ready; directories ensured"


def _step_audit(args: argparse.Namespace) -> Tuple[bool, str]:
    master = Path(args.master)
    target = Path(args.target)
    if not master.is_file():
        return False, f"master profile missing: {master}"
    if not target.is_file():
        return False, f"target profile missing: {target}"
    diff_count = xml_utils.compare_profiles(master, target)
    if diff_count < 0:
        return False, "profile comparison failed"
    report = REPORTS_DIR / "profile_comparison_report.md"
    report.write_text(
        f"# Profile Comparison\n\n"
        f"- Master: {master}\n"
        f"- Target: {target}\n"
        f"- Differing keys: {diff_count}\n",
        encoding="utf-8",
    )
    return True, f"{diff_count} differing keys; report written to {report.name}"


def _step_calibrate(args: argparse.Namespace) -> Tuple[bool, str]:
    batch_dir = Path(args.batch_dir)
    if not batch_dir.is_dir():
        return False, f"batch directory not found: {batch_dir}"
    results = calibration.analyze_image_dir(
        batch_dir,
        output_dir=args.output_dir or REPORTS_DIR / ".." / "data",
        save_json=True,
        save_csv=True,
        make_plots=True,
    )
    measured = sum(1 for r in results if r["mtf50_cyc_px"] is not None)
    return True, f"analyzed {len(results)} images; MTF50 measured for {measured}"


def _step_skin_tone(args: argparse.Namespace) -> Tuple[bool, str]:
    source = Path(args.skin_tone_source)
    if not source.is_file():
        return False, f"skin-tone source missing: {source}"
    count = skin_tone.tune_skin_tone(source, output_path=args.skin_tone_output)
    return True, f"tuned {count} parameters -> {args.skin_tone_output}"


def _step_build_v10(args: argparse.Namespace) -> Tuple[bool, str]:
    try:
        build_v10.build_v10_baseline(
            source=Path(args.v10_source),
            dest_dir=Path(args.v10_dest),
        )
    except SystemExit as exc:
        return False, f"V10 build failed: {exc.code}"
    return True, "V10 baseline config built"


def _step_deploy(args: argparse.Namespace) -> Tuple[bool, str]:
    profile = Path(args.deploy_profile)
    if not profile.is_file():
        return False, f"profile to deploy not found: {profile}"
    dest = LMC_STORAGE_DIR / profile.name
    try:
        LMC_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(profile.read_bytes())
    except OSError as exc:
        return False, f"deploy failed: {exc}"
    return True, f"deployed {profile.name} to {dest}"


# Step name -> (description, callable). Order matters. Defined after the
# step functions so they are in scope at module import time.
STEPS: List[Tuple[str, str, Callable[[argparse.Namespace], Tuple[bool, str]]]] = [
    ("env", "dependency check + directory setup", _step_env),
    ("audit", "XML config validation & comparison", _step_audit),
    ("calibrate", "OpenCV MTF50 + sharpness over image batch", _step_calibrate),
    ("skin_tone", "tune skin-tone profile parameters", _step_skin_tone),
    ("build_v10", "build V10 baseline config", _step_build_v10),
    ("deploy", "deploy profile to /sdcard/LMC8.4", _step_deploy),
]

STEP_NAMES = [name for name, _desc, _fn in STEPS]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="IMX682 / LMC 8.4 calibration pipeline orchestrator",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the execution plan without running any step",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="enable debug-level logging",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="skip the XML audit/comparison step",
    )
    parser.add_argument(
        "--skip-calibration",
        action="store_true",
        help="skip the OpenCV calibration step",
    )
    parser.add_argument(
        "--skip-skin-tone",
        action="store_true",
        help="skip the skin-tone tuning step",
    )
    parser.add_argument(
        "--skip-build-v10",
        action="store_true",
        help="skip the V10 baseline build step",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="skip the deploy step",
    )
    parser.add_argument(
        "--steps",
        default=",".join(STEP_NAMES),
        help="comma-separated subset of steps to run (default: all)",
    )
    parser.add_argument(
        "--batch-dir",
        default="/sdcard/DCIM/Camera",
        help="image directory for the calibration step",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="override calibration output directory",
    )
    parser.add_argument(
        "--master",
        default=str(DEFAULT_MASTER),
        help="master XML profile path",
    )
    parser.add_argument(
        "--target",
        default=str(DEFAULT_TARGET),
        help="target XML profile path",
    )
    parser.add_argument(
        "--skin-tone-source",
        default=str(DEFAULT_MASTER),
        help="source profile for skin-tone tuning",
    )
    parser.add_argument(
        "--skin-tone-output",
        default=str(DEFAULT_TARGET),
        help="output path for tuned skin-tone profile",
    )
    parser.add_argument(
        "--v10-source",
        default=str(DEFAULT_MASTER),
        help="source profile for V10 baseline build",
    )
    parser.add_argument(
        "--v10-dest",
        default=str(LMC_STORAGE_DIR),
        help="destination directory for V10 baseline config",
    )
    parser.add_argument(
        "--deploy-profile",
        default=str(DEFAULT_TARGET),
        help="profile file to deploy to phone storage",
    )
    return parser


def resolve_steps(args: argparse.Namespace) -> List[Tuple[str, str, Callable]]:
    """Return the ordered list of steps to execute, honoring toggles."""
    requested = {s.strip() for s in args.steps.split(",") if s.strip()}
    invalid = requested - set(STEP_NAMES)
    if invalid:
        logger.error("Unknown step(s): %s (valid: %s)", ", ".join(sorted(invalid)), ", ".join(STEP_NAMES))
        sys.exit(2)

    skip = {
        "audit": args.skip_audit,
        "calibrate": args.skip_calibration,
        "skin_tone": args.skip_skin_tone,
        "build_v10": args.skip_build_v10,
        "deploy": args.skip_deploy,
    }

    plan = [step for step in STEPS if step[0] in requested and not skip.get(step[0], False)]
    return plan


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logger(verbose=args.verbose)
    logger = get_logger()

    if args.dry_run:
        plan = resolve_steps(args)
        logger.info("=== DRY RUN: %d step(s) planned ===", len(plan))
        for name, desc, _fn in plan:
            logger.info("  [ ] %s — %s", name, desc)
        logger.info("Dry run complete; nothing was executed.")
        return 0

    ensure_dirs()
    plan = resolve_steps(args)
    logger.info("Pipeline starting: %d step(s)", len(plan))

    failures = 0
    for name, desc, fn in plan:
        logger.info("=== step: %s — %s ===", name, desc)
        try:
            ok, message = fn(args)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Step %s raised: %s", name, exc)
            ok, message = False, str(exc)
        if ok:
            logger.info("  [✓] %s", message)
        else:
            failures += 1
            logger.error("  [✗] %s", message)
            if args.verbose:
                logger.error("Stopping on failed step %s", name)
                break

    if failures:
        logger.error("Pipeline finished with %d failed step(s)", failures)
        return 1
    logger.info("Pipeline complete — all steps succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
