# R3 MIGRATION PLAN: Profile Directory Restructuring

## 1. Existing paths (before restructuring)

### Current `profiles/` directory layout (19 XML files + 2 non-XML files)

| Path | Schema Family | Keys | Is Baseline |
|---|---|---|---|
| `profiles/LXX521_IMX682_LMC84_AllRounder.xml` | LMC | 2641 | Yes |
| `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` | LMC | 2641 | Yes |
| `profiles/LXX521_IMX682_AllInOne_V2.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_AllInOne_V3.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_AllRounder_NaturalBalanced.xml` | LMC | 2641 | No |
| `profiles/LXX521_IMX682_HDR_Video_Test.xml` | UNKNOWN/MIXED | 10 | No |
| `profiles/LXX521_IMX682_NightPro.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_Super_AllInOne_V6_NightIndoor.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml` | LMC | 25 | No |
| `profiles/LXX521_IMX682_UltimateMaster.xml` | LMC | 25 | No |
| `profiles/LXX521_IMX682_V8_FullAllRounder_Q100.xml` | LMC | 2641 | No |
| `profiles/LXX521_IMX682_V8_ProBalanced.xml` | LMC | 26 | No |
| `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml` | LMC | 2662 | No |
| `profiles/LXX521_MasterPortrait_Pro.xml` | LMC | 14 | No |
| `profiles/LXX521_BSG_Master.xml` | MIXED | 12 | No |
| `profiles/LXX521_BSG_Pro.xml` | MIXED | 12 | No |

### Top-level `LXX521_*.xml` files (14 files, also in `profiles/` for some)

Including `LXX521_FrontCam_Only_Sanitized.xml`, `LXX521_FrontCam_Sanitized_V2.xml`,
`LXX521_FrontCam_Sanitized_V3.xml`, `LXX521_IMX682_ActionCam.xml`, etc.

### Reference dependencies

| Consumer | Dependency | Impact if changed |
|---|---|---|
| `workflow_master_v4.py` line 11 | `PROFILE_DIRS = [BASE_DIR / "profiles", BASE_DIR / "analysis_results" / "imx682_config"]` | Must be updated to point to new sub-directories |
| `src/profile_manager.py` line 154 | `directories: Tuple[str, ...] = ("profiles",)` | Must be updated to include new sub-directories |
| `src/deployment.py` | Uses `PREFERRED_TERMUX_DIR` for destination, not profile discovery | Not directly affected, but `PROFILE_DIRS` change affects profile selection |
| `src/config_generator.py` | Generates candidates from baselines in `profiles/` | Profile discovery change may affect generation |
| `src/profile_compare.py` | `batch_compare()` operates on profile path lists | Must update path sources |
| `src/image_quality_analyzer.py` | Searches `new_captures/`, `analysis_results/` directories | Not directly affected |
| `lmc_guidelines.md` | References profile usage patterns | May need update |
| `V10_Termux_Master.py` | May reference profile paths | Check required |

### Proposed paths (after restructuring)

Create three sub-directories under `profiles/`:

```
profiles/
├── lmc84/        # All LMC-key profiles (48 profiles)
├── mgc_bsg/      # BSG/MGC-key and MIXED profiles (8 profiles)
└── frontcam/     # Front camera–only profiles (3 files)
```

#### Proposed `profiles/lmc84/` contents (LMC-key profiles)

All profiles whose schema family is LMC (per `camera_capabilities.py` `identify_schema_family()`), excluding BSG and front-camera files. This includes:

- `LXX521_IMX682_LMC84_AllRounder.xml`
- `LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml`
- `LXX521_IMX682_AllInOne_V2.xml`
- `LXX521_IMX682_AllInOne_V3.xml`
- `LXX521_IMX682_AllRounder_NaturalBalanced.xml`
- `LXX521_IMX682_NightPro.xml`
- `LXX521_IMX682_Super_AllInOne_V4.xml`
- `LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml`
- `LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml`
- `LXX521_IMX682_Super_AllInOne_V6_NightIndoor.xml`
- `LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml`
- `LXX521_IMX682_UltimateMaster.xml`
- `LXX521_IMX682_V8_FullAllRounder_Q100.xml`
- `LXX521_IMX682_V8_ProBalanced.xml`
- `LXX521_IMX682_V9_ConservativeBalanced.xml`
- `LXX521_MasterPortrait_Pro.xml`
- + top-level `LXX521_*.xml` files that are LMC schema (after migration)

#### Proposed `profiles/mgc_bsg/` contents (BSG/MGC-key and MIXED profiles)

- `LXX521_BSG_Master.xml`
- `LXX521_BSG_Pro.xml`
- `LXX521_IMX682_HDR_Video_Test.xml`
- + any MIXED profiles from the current `profiles/` directory

#### Proposed `profiles/frontcam/` contents (front camera–only profiles)

- `LXX521_FrontCam_Only_Sanitized.xml`
- `LXX521_FrontCam_Sanitized_V2.xml`
- `LXX521_FrontCam_Sanitized_V3.xml`

### Import/reference dependencies to update

1. **`workflow_master_v4.py`**: Update `PROFILE_DIRS` to include the new sub-directories:
   ```python
   PROFILE_DIRS = [
       BASE_DIR / "profiles" / "lmc84",
       BASE_DIR / "profiles" / "mgc_bsg",
       BASE_DIR / "profiles" / "frontcam",
       BASE_DIR / "analysis_results" / "imx682_config",
   ]
   ```

2. **`src/profile_manager.py`**: Update `list_profiles()` and `organize_profiles()`:
   - `list_profiles(directories=("profiles/lmc84", "profiles/mgc_bsg", "profiles/frontcam"))`
   - `organize_profiles()` already creates the sub-directories; needs to be run after file moves

3. **`src/deployment.py`**: The `deploy_interactive()` function lists profiles for user selection. Update the profile listing to reflect the new sub-directory structure.

4. **`src/profile_compare.py`**: `batch_compare()` and `compare_profiles()` operate on explicit file paths. If scripts glob `profiles/*.xml`, the glob pattern must change to include sub-directories (e.g., `profiles/lmc84/*.xml`, `profiles/mgc_bsg/*.xml`, `profiles/frontcam/*.xml`).

5. **`src/config_generator.py`**: Generates candidates from baselines in `profiles/`. The baseline path may need updating if the generator scans for profiles by glob pattern.

6. **`lmc_guidelines.md`**: May reference specific profile paths; update if any referenced profiles move.

### Compatibility risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Scripts that glob `profiles/*.xml` flat miss profiles in sub-directories | Medium | Update all glob patterns to include `profiles/lmc84/`, `profiles/mgc_bsg/`, `profiles/frontcam/` |
| `workflow_master_v4.py` profile selection break | Medium | Update `PROFILE_DIRS` in same change; run test suite |
| MGC profiles accidentally mixed into LMC set | Low | Schema sub-directories make mixing structurally impossible (enforced by organisation) |
| Top-level `LXX521_*.xml` files not migrated | Medium | These are duplicates of `profiles/` versions; assess whether unique content exists |
| `workflow_master_v4.py` `collect_profiles()` deduplication | May need update | `collect_profiles()` uses `folder.glob("*.xml")`; with multiple folders, deduplication by `name` may keep first-seen version |

### Rollback plan

1. **Backup before migration**: Run `python src/profile_manager.py organize_profiles()` or manually copy `profiles/` to `profiles.bak.$(date +%Y%m%d%H%M%S)/` before any moves.

2. **File restoration**: If migration needs to be reversed, copy files back from `profiles.bak/` to the original `profiles/` root directory.

3. **`workflow_master_v4.py` revert**: Restore the original `PROFILE_DIRS` and `SDCARD_LMC_DIR` values.

4. **Verification**: After rollback, run `python run.py audit` to confirm all profiles are still detectable and valid.

5. **New migration plan**: If the initial migration plan proves flawed, a second restructuring cycle can correct folder assignments. The `organize_profiles()` function in `src/profile_manager.py` is idempotent (creates dirs, skips existing files).

### Migration execution steps (wait for explicit approval)

1. Create target sub-directories: `profiles/lmc84/`, `profiles/mgc_bsg/`, `profiles/frontcam/`
2. Move LMC-key profiles to `profiles/lmc84/`
3. Move BSG-key and MIXED profiles to `profiles/mgc_bsg/`
4. Move front-camera profiles to `profiles/frontcam/`
5. Update `workflow_master_v4.py` `PROFILE_DIRS`
6. Update any script glob patterns that reference `profiles/*.xml`
7. Run `python run.py audit` to verify all profiles still validate
8. Run `python run.py compare` with sample profiles to confirm comparison still works
9. Document the new directory layout in `README_V4.md`

---
**R3 migration plan complete. No files have been moved. awaiting explicit approval before execution.**