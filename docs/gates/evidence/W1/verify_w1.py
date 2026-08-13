"""Verify the proposed W1 Simulator MVP product package."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PRODUCT = ROOT / "docs" / "product"
PATHS = {
    "PRD": PRODUCT / "PRD-001 教育机器人云平台.md",
    "RTM": PRODUCT / "RTM-001 教育机器人云平台需求追踪矩阵.md",
    "PILOT": PRODUCT / "PILOT-001 模拟器工程验证范围.md",
    "MVP": PRODUCT / "MVP-001 阶段1A模拟器MVP范围.md",
    "STORY": PRODUCT / "STORY-MAP-001 阶段1A用户故事地图.md",
    "ACCEPTANCE": PRODUCT / "ACCEPTANCE-001 阶段1A验收矩阵.md",
    "DEMO": PRODUCT / "DEMO-001 阶段1A合成数据演示脚本.md",
}


@dataclass(frozen=True)
class Check:
    check_id: str
    passed: bool
    detail: str


checks: list[Check] = []


def add_check(check_id: str, passed: bool, detail: str) -> None:
    checks.append(Check(check_id, passed, detail))


def section(text: str, start: str, end: str) -> str:
    start_index = text.find(start)
    if start_index < 0:
        return ""
    end_index = text.find(end, start_index + len(start))
    if end_index < 0:
        return ""
    return text[start_index:end_index]


def unique_matches(pattern: str, text: str) -> list[str]:
    return sorted(set(re.findall(pattern, text, flags=re.MULTILINE)))


def print_result() -> int:
    width = max(len(item.check_id) for item in checks)
    for item in checks:
        status = "PASS" if item.passed else "FAIL"
        print(f"{item.check_id:<{width}}  {status:<4}  {item.detail}")

    failed = [item for item in checks if not item.passed]
    if failed:
        print(f"W1_RESULT=FAIL; CHECKS={len(checks)}; FAILED={len(failed)}")
        return 1

    print(f"W1_RESULT=PASS; CHECKS={len(checks)}; FAILED=0; APPROVAL=PENDING")
    return 0


def main() -> int:
    for name, path in PATHS.items():
        add_check(f"W1-FILE-{name}", path.is_file(), str(path.relative_to(ROOT)))

    if any(not item.passed for item in checks):
        return print_result()

    texts = {name: path.read_text(encoding="utf-8") for name, path in PATHS.items()}
    prd = texts["PRD"]
    rtm = texts["RTM"]
    pilot = texts["PILOT"]
    mvp = texts["MVP"]
    story = texts["STORY"]
    acceptance = texts["ACCEPTANCE"]
    demo = texts["DEMO"]

    proposed_status = "> 状态：Proposed — Awaiting Product/QA Owner Approval"
    add_check(
        "W1-STATUS",
        all(proposed_status in text for text in (mvp, story, acceptance))
        and "> 状态：Proposed Script — Not Yet Executable" in demo,
        "All W1 artifacts remain proposed until human approval",
    )
    pending_owners = re.findall(
        r"^\| (?:Product Owner|QA/验收 Owner) \| 高端阳 \| Pending",
        mvp,
        flags=re.MULTILINE,
    )
    add_check(
        "W1-APPROVAL-BOUNDARY",
        len(pending_owners) == 2 and "不得批准自己的产物" in mvp,
        "Product and QA approval belong to 高端阳, not Codex",
    )

    prd_stories = unique_matches(r"^\| (ST-[A-Z]+-\d{3}) \|", prd)
    p0_text = section(
        story,
        "### 1. P0：阶段 1A 最小闭环",
        "### 2. P1：阶段 1A 启动支撑",
    )
    p1_text = section(
        story,
        "### 2. P1：阶段 1A 启动支撑",
        "### 3. Out：阶段 1A 明确排除",
    )
    out_text = section(
        story,
        "### 3. Out：阶段 1A 明确排除",
        "## 五、Story Definition of Ready",
    )
    story_pattern = r"^\| `(ST-[A-Z]+-\d{3})` \|"
    p0_stories = unique_matches(story_pattern, p0_text)
    p1_stories = unique_matches(story_pattern, p1_text)
    out_stories = unique_matches(story_pattern, out_text)
    classified = p0_stories + p1_stories + out_stories
    classified_unique = sorted(set(classified))
    expected_p0 = sorted(
        [
            "ST-GOV-001",
            "ST-GOV-002",
            "ST-DEV-001",
            "ST-DEV-002",
            "ST-DEV-003",
            "ST-OPS-001",
            "ST-OPS-002",
        ]
    )
    add_check(
        "W1-STORY-COUNTS",
        (len(p0_stories), len(p1_stories), len(out_stories)) == (7, 1, 11),
        f"P0={len(p0_stories)}, P1={len(p1_stories)}, Out={len(out_stories)}",
    )
    add_check(
        "W1-STORY-UNIQUE",
        len(classified) == len(classified_unique) == 19,
        f"classified={len(classified)}, unique={len(classified_unique)}",
    )
    differences = sorted(set(prd_stories).symmetric_difference(classified_unique))
    add_check(
        "W1-STORY-COVERAGE",
        len(prd_stories) == 19 and not differences,
        f"PRD={len(prd_stories)}, differences={','.join(differences) or 'none'}",
    )
    add_check(
        "W1-P0-EXACT",
        p0_stories == expected_p0 and p1_stories == ["ST-REL-002"],
        f"P0 exact={p0_stories == expected_p0}, P1={','.join(p1_stories)}",
    )
    future_prefixes = ("ST-CNT-", "ST-TCH-", "ST-AI-", "ST-OTA-")
    invalid_p0 = [item for item in p0_stories if item.startswith(future_prefixes)]
    invalid_p1 = [
        item
        for item in p1_stories
        if item.startswith((*future_prefixes, "ST-OPS-"))
    ]
    add_check(
        "W1-FUTURE-OUT",
        not invalid_p0 and not invalid_p1,
        "Content, Teaching, AI, OTA and diagnostics are absent from P0/P1",
    )

    expected_requirements = [
        "PRD-GOV-001",
        "PRD-GOV-002",
        "PRD-GOV-003",
        "PRD-DEV-001",
        "PRD-DEV-002",
        "PRD-DEV-003",
        "PRD-DEV-004",
        "PRD-DEV-005",
        "PRD-DEV-006",
        "PRD-OPS-001",
        "PRD-OPS-002",
        "PRD-OPS-003",
    ]
    missing_requirements = [
        item for item in expected_requirements if item not in prd or item not in rtm
    ]
    add_check(
        "W1-REQUIREMENTS",
        len(expected_requirements) == 12
        and not missing_requirements
        and "12 项 P0 Requirement" in mvp,
        f"expected=12, missing={','.join(missing_requirements) or 'none'}",
    )

    scenario_ids = re.findall(
        r"^\| (S1A-AC-(?:GOV|DEV|OPS)-\d{3}-[NPED]) \|",
        acceptance,
        flags=re.MULTILINE,
    )
    unique_scenarios = sorted(set(scenario_ids))
    expected_scenarios = {
        f"{story_id.replace('ST-', 'S1A-AC-')}-{quadrant}"
        for story_id in expected_p0
        for quadrant in "NPED"
    }
    missing_scenarios = sorted(expected_scenarios.difference(unique_scenarios))
    add_check(
        "W1-ACCEPTANCE-COUNT",
        len(scenario_ids) == len(unique_scenarios) == 28,
        f"rows={len(scenario_ids)}, unique={len(unique_scenarios)}",
    )
    add_check(
        "W1-ACCEPTANCE-QUADRANTS",
        not missing_scenarios,
        f"missing={','.join(missing_scenarios) or 'none'}",
    )

    demo_steps = re.findall(r"^\| (DEMO-\d{2}) \|", demo, flags=re.MULTILINE)
    add_check(
        "W1-DEMO-STEPS",
        len(demo_steps) == len(set(demo_steps)) == 16
        and demo_steps[0] == "DEMO-00"
        and demo_steps[-1] == "DEMO-15",
        f"steps={len(demo_steps)}, first={demo_steps[0]}, last={demo_steps[-1]}",
    )

    required_assets = [
        "ORG-SIM-A",
        "ORG-SIM-B",
        "SITE-SIM-A1",
        "SITE-SIM-B1",
        "SIM_EDU_ROBOT_V1",
        "SIM-A-001",
        "SIM-A-002",
        "SIM-A-003",
        "SIM-A-004",
        "SIM-B-001",
        "SIM-B-002",
    ]
    missing_assets = [
        item
        for item in required_assets
        if item not in mvp or item not in pilot or item not in demo
    ]
    add_check(
        "W1-SYNTHETIC-ASSETS",
        not missing_assets,
        f"missing={','.join(missing_assets) or 'none'}",
    )
    add_check(
        "W1-SIMULATOR-TRUTH",
        "is_physical_hardware: false" in mvp
        and "production_supported: false" in mvp
        and "blocked_no_physical_device" in pilot
        and "contains_personal_data: false" in demo,
        "Simulator, non-production, no-personal-data and G1-Device are explicit",
    )

    disabled = ["Content", "Teaching", "AI", "Diagnostic", "Bulk", "OTA"]
    missing_disabled = [item for item in disabled if item not in mvp or item not in demo]
    add_check(
        "W1-FAIL-CLOSED",
        not missing_disabled and "disabled/not_started" in mvp,
        f"missing disabled declarations={','.join(missing_disabled) or 'none'}",
    )
    add_check(
        "W1-PRODUCT-TRUTH",
        "No-Go" in mvp
        and "客户痛点频率/成本未量化" in mvp
        and "不证明客户确有该痛点" in mvp,
        "Engineering feasibility is separate from customer-value evidence",
    )
    return print_result()


if __name__ == "__main__":
    sys.exit(main())
