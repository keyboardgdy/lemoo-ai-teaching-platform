"""Verify the proposed W4 security and privacy boundary package."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DOCS = ROOT / "docs"
PATHS = {
    "PRD": DOCS / "product" / "PRD-001 教育机器人云平台.md",
    "RTM": DOCS / "product" / "RTM-001 教育机器人云平台需求追踪矩阵.md",
    "W1": DOCS / "gates" / "evidence" / "W1" / "baseline.yaml",
    "THREAT": DOCS / "security" / "THREAT-MODEL-001 平台威胁模型.md",
    "PRIVACY": DOCS / "privacy" / "PRIVACY-APPLICABILITY-001 隐私与AI法规适用性.md",
    "AUTHORITY": DOCS
    / "privacy"
    / "PROCESSING-AUTHORITY-001 数据处理权限与目的矩阵.md",
    "DATA": DOCS / "privacy" / "DATA-POLICY-001 数据分类保留与删除政策.md",
    "CONTENT": DOCS / "content" / "CONTENT-GOVERNANCE-001 内容权利审核与撤回.md",
    "ADR": DOCS / "decisions" / "ADR-001 AI Provider适配器与Fake-first策略.md",
    "APPROVAL": DOCS / "security" / "APPROVAL-MATRIX-001 高风险操作审批矩阵.md",
    "SECRETS": DOCS / "security" / "SECRET-INVENTORY-001 Secret与密钥清单.md",
    "ADR_INDEX": DOCS / "decisions" / "README.md",
    "ADR_TEMPLATE": DOCS / "decisions" / "template.md",
}


@dataclass(frozen=True)
class Check:
    check_id: str
    passed: bool
    detail: str


checks: list[Check] = []


def add_check(check_id: str, passed: bool, detail: str) -> None:
    checks.append(Check(check_id, passed, detail))


def unique_matches(pattern: str, text: str) -> list[str]:
    return sorted(set(re.findall(pattern, text, flags=re.MULTILINE)))


def print_result() -> int:
    width = max(len(item.check_id) for item in checks)
    for item in checks:
        status = "PASS" if item.passed else "FAIL"
        print(f"{item.check_id:<{width}}  {status:<4}  {item.detail}")

    failed = [item for item in checks if not item.passed]
    if failed:
        print(f"W4_RESULT=FAIL; CHECKS={len(checks)}; FAILED={len(failed)}")
        return 1

    print(f"W4_RESULT=PASS; CHECKS={len(checks)}; FAILED=0; APPROVAL=PENDING")
    return 0


def main() -> int:
    for name, path in PATHS.items():
        add_check(f"W4-FILE-{name}", path.is_file(), str(path.relative_to(ROOT)))

    if any(not item.passed for item in checks):
        return print_result()

    texts = {name: path.read_text(encoding="utf-8") for name, path in PATHS.items()}
    threat = texts["THREAT"]
    privacy = texts["PRIVACY"]
    authority = texts["AUTHORITY"]
    data = texts["DATA"]
    content = texts["CONTENT"]
    adr = texts["ADR"]
    approval = texts["APPROVAL"]
    secrets = texts["SECRETS"]
    package = (DOCS / "gates" / "evidence" / "W4" / "README.md").read_text(
        encoding="utf-8"
    )

    candidate_docs = [threat, privacy, authority, data, content, approval, secrets]
    proposed_status = "> 状态：Proposed — Awaiting Security/Privacy Owner Approval"
    add_check(
        "W4-STATUS",
        all(proposed_status in text for text in candidate_docs)
        and "**Status**: proposed" in adr,
        "All eight W4 artifacts remain proposed pending human approval",
    )
    add_check(
        "W4-APPROVAL-BOUNDARY",
        all("高端阳（待批准）" in text for text in (threat, privacy, authority, data))
        and "OpenAI Codex（非批准人）" in threat
        and "不能用 OpenAI Codex 充当第二批准人" in approval,
        "Named human approval and Codex non-approval boundaries are explicit",
    )

    threat_ids = unique_matches(r"^\| (THR-\d{3}) \|", threat)
    control_ids = unique_matches(r"\b(SEC-\d{3})\b", threat)
    add_check(
        "W4-THREATS",
        threat_ids == [f"THR-{number:03d}" for number in range(1, 27)],
        f"threats={len(threat_ids)}, expected=26",
    )
    add_check(
        "W4-CONTROLS",
        control_ids == [f"SEC-{number:03d}" for number in range(1, 13)],
        f"security invariants={len(control_ids)}, expected=12",
    )

    regime_ids = unique_matches(r"^\| (REG-[A-Z-]+) \|", privacy)
    jurisdiction_ids = unique_matches(r"^\| (JUR-\d{3}) \|", privacy)
    assessment_ids = unique_matches(r"^\| (PIA-\d{3}) \|", privacy)
    official_domains = [
        "npc.gov.cn",
        "cac.gov.cn",
        "moe.gov.cn",
        "eur-lex.europa.eu",
        "ftc.gov",
    ]
    add_check(
        "W4-APPLICABILITY",
        len(regime_ids) == 7
        and len(jurisdiction_ids) == 8
        and len(assessment_ids) == 6
        and all(domain in privacy for domain in official_domains)
        and "不能得出“合规”结论" in privacy,
        (
            f"regimes={len(regime_ids)}, facts={len(jurisdiction_ids)}, "
            f"assessment triggers={len(assessment_ids)}"
        ),
    )

    purpose_ids = unique_matches(r"^\| (PUR-\d{3}) \|", authority)
    add_check(
        "W4-PURPOSES",
        purpose_ids == [f"PUR-{number:03d}" for number in range(1, 14)]
        and authority.count("UNSET_BLOCKED") >= 10,
        f"purposes={len(purpose_ids)}, blocked references={authority.count('UNSET_BLOCKED')}",
    )
    data_classes = unique_matches(r"^\| (D[0-4]) ", data)
    policy_ids = unique_matches(r"^\| (DP-\d{3}) \|", data)
    add_check(
        "W4-DATA-POLICY",
        data_classes == [f"D{number}" for number in range(5)]
        and policy_ids == [f"DP-{number:03d}" for number in range(1, 8)]
        and "ZERO_PERSISTENCE_DEFAULT" in data,
        f"classes={len(data_classes)}, synthetic policies={len(policy_ids)}",
    )

    approval_ids = unique_matches(r"^\| (APR-\d{3}) \|", approval)
    add_check(
        "W4-APPROVAL-MATRIX",
        approval_ids == [f"APR-{number:03d}" for number in range(1, 15)]
        and "两名不同自然人" in approval,
        f"actions={len(approval_ids)}, expected=14",
    )
    secret_ids = unique_matches(r"^\| (SEC-[A-Z0-9-]+-\d{3}) \|", secrets)
    add_check(
        "W4-SECRET-INVENTORY",
        len(secret_ids) == 14
        and "不保存任何真实值" in secrets
        and "OTA Root" in secrets
        and "Prohibited" in secrets,
        f"secret classes={len(secret_ids)}, expected=14",
    )

    expected_content_fields = [
        "rights_record_id",
        "content_version_id",
        "asset_digest",
        "source_type",
        "source_reference",
        "rightsholder",
        "license_type",
        "license_version",
        "permissions",
        "territories",
        "audience",
        "effective_at",
        "expires_at",
        "attribution",
        "ai_disclosure",
        "reviewer_ids",
        "reviewed_at",
        "withdrawal_status",
    ]
    missing_content_fields = [
        field for field in expected_content_fields if f"`{field}`" not in content
    ]
    add_check(
        "W4-CONTENT-GOVERNANCE",
        not missing_content_fields
        and "ai_draft" in content
        and "Rights Record" in content
        and "withdrawn" in content
        and "不同信任域" in content,
        f"rights fields={len(expected_content_fields)}, missing={','.join(missing_content_fields) or 'none'}",
    )
    expected_capabilities = {
        "answer.semantic_match",
        "asr.transcribe",
        "author.question_draft",
        "ops.log_summary",
        "tts.synthesize",
        "tutor.explain",
        "tutor.follow_up",
        "tutor.hint",
    }
    adr_capabilities = set(re.findall(r"^- `([^`]+)`$", adr, flags=re.MULTILINE))
    add_check(
        "W4-AI-ADR",
        adr_capabilities == expected_capabilities
        and "deterministic Fake" in adr
        and "真实网络 Provider、凭据和数据发送入口默认不存在" in adr
        and "业务层不得直接导入 Provider SDK" in adr,
        f"AI capabilities={len(adr_capabilities)}, status=proposed",
    )

    requirement_ids = [
        "PRD-GOV-001",
        "PRD-GOV-002",
        "PRD-GOV-003",
        "PRD-DEV-001",
        "PRD-OPS-002",
        "PRD-OPS-004",
        "PRD-CNT-002",
        "PRD-CNT-003",
        "PRD-CNT-005",
        "PRD-TCH-001",
        "PRD-TCH-004",
        "PRD-TCH-005",
        "PRD-AI-001",
        "PRD-AI-002",
        "PRD-AI-003",
        "PRD-AI-004",
        "PRD-AI-005",
        "PRD-OTA-002",
        "PRD-OTA-005",
    ]
    missing_requirements = [
        item
        for item in requirement_ids
        if item not in texts["PRD"] or item not in texts["RTM"] or item not in package
    ]
    decision_ids = [f"D-{number:03d}" for number in range(8, 15)]
    missing_decisions = [item for item in decision_ids if item not in package]
    add_check(
        "W4-TRACEABILITY",
        not missing_requirements and not missing_decisions,
        (
            f"requirements={len(requirement_ids)}, missing req={','.join(missing_requirements) or 'none'}, "
            f"missing decisions={','.join(missing_decisions) or 'none'}"
        ),
    )

    all_w4 = "\n".join([*candidate_docs, adr, package])
    boundaries = [
        "blocked_no_physical_device",
        "UNSET_BLOCKED",
        "原始学生音频默认不持久化",
        "AI 无任意工具、MQTT、设备命令、OTA、数据库、文件系统或网络访问",
        "普通服务、开发机和 CI 不持有 OTA Root/发布私钥",
        "Content、Teaching、AI、Diagnostic、Bulk Command、OTA",
    ]
    missing_boundaries = [item for item in boundaries if item not in all_w4]
    add_check(
        "W4-FAIL-CLOSED",
        not missing_boundaries,
        f"missing boundaries={','.join(missing_boundaries) or 'none'}",
    )
    add_check(
        "W4-W1-BOUNDARY",
        "status: approved" in texts["W1"]
        and 'mode: "simulator-only"' in texts["W1"]
        and "not_started" in texts["W1"],
        "W1 remains approved Simulator-only and future implementation is not started",
    )
    return print_result()


if __name__ == "__main__":
    sys.exit(main())
