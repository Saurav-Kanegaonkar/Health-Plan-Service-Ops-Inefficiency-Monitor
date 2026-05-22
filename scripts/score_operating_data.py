import csv
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "analysis" / "outputs"

random.seed(22)

BUSINESS_UNITS = [
    ("Member Services", 0.32, 0.20, 15500, 12.5),
    ("Claims Operations", 0.44, 0.34, 11800, 18.0),
    ("Utilization Management", 0.38, 0.42, 7600, 22.5),
    ("Provider Services", 0.36, 0.30, 9300, 16.5),
    ("Billing and Enrollment", 0.40, 0.24, 8200, 14.0),
    ("Pharmacy Operations", 0.34, 0.36, 6100, 19.0),
    ("Care Navigation", 0.29, 0.28, 5400, 17.0),
    ("Risk Adjustment Support", 0.33, 0.40, 4200, 21.0),
]

SEGMENTS = [
    ("Digital password reset and login help", "Access friction", "Member Services"),
    ("Provider directory mismatch calls", "Network data quality", "Member Services"),
    ("Benefits and cost-share explanation", "Plan literacy", "Member Services"),
    ("Claims status repeat contact", "Claims transparency", "Claims Operations"),
    ("Pended claim documentation chase", "Claims documentation", "Claims Operations"),
    ("Appeal intake rework", "Claims escalation", "Claims Operations"),
    ("Prior authorization status follow-up", "Authorization visibility", "Utilization Management"),
    ("Imaging authorization turnaround", "Utilization review", "Utilization Management"),
    ("Concurrent review extension queue", "Clinical utilization", "Utilization Management"),
    ("Provider demographic update requests", "Provider data maintenance", "Provider Services"),
    ("Contracted rate clarification", "Provider payment support", "Provider Services"),
    ("Credentialing status questions", "Provider onboarding", "Provider Services"),
    ("Premium payment reconciliation", "Billing operations", "Billing and Enrollment"),
    ("Enrollment file mismatch", "Enrollment operations", "Billing and Enrollment"),
    ("Binder payment grace period outreach", "Billing operations", "Billing and Enrollment"),
    ("Formulary exception status", "Pharmacy operations", "Pharmacy Operations"),
    ("Specialty medication shipment issue", "Pharmacy operations", "Pharmacy Operations"),
    ("Medication prior authorization handoff", "Pharmacy utilization", "Pharmacy Operations"),
    ("Care guide handoff after ED visit", "Care navigation", "Care Navigation"),
    ("Virtual care routing issue", "Care navigation", "Care Navigation"),
    ("Complex case follow-up lag", "Care navigation", "Care Navigation"),
    ("Risk adjustment chart retrieval", "Risk adjustment", "Risk Adjustment Support"),
    ("In-home assessment scheduling", "Risk adjustment", "Risk Adjustment Support"),
    ("Provider coding education outreach", "Risk adjustment", "Risk Adjustment Support"),
]

REQUEST_TYPES = [
    "Executive operating review",
    "Dashboard enhancement",
    "Root cause drilldown",
    "Manager follow-up",
    "Metric definition clarification",
]

SYSTEMS = [
    "Service CRM",
    "Claims platform",
    "Utilization management system",
    "Provider data mart",
    "Billing ledger",
    "Looker semantic layer",
]


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def money(value):
    return int(round(value, 0))


def build_segments():
    rows = []
    for idx, (name, theme, unit) in enumerate(SEGMENTS, start=1):
        base = next(item for item in BUSINESS_UNITS if item[0] == unit)
        rows.append(
            {
                "segment_id": f"SEG-{idx:03d}",
                "business_unit": unit,
                "segment_name": name,
                "inefficiency_theme": theme,
                "primary_stakeholder": random.choice(
                    ["Senior Manager", "Associate Director", "Operations Manager", "Analytics Manager"]
                ),
                "baseline_weekly_volume": int(random.gauss(base[3], base[3] * 0.12)),
                "financial_sensitivity": round(random.gauss(base[4], 2.6), 1),
                "utilization_sensitivity": round(clamp(random.gauss(base[2], 0.08), 0.10, 0.62), 2),
                "avoidable_contact_base": round(clamp(random.gauss(base[1], 0.08), 0.12, 0.64), 2),
            }
        )
    return rows


def build_weekly_metrics(segments):
    rows = []
    start = date(2026, 1, 5)
    for segment in segments:
        baseline = int(segment["baseline_weekly_volume"])
        avoidable_base = float(segment["avoidable_contact_base"])
        util_sensitivity = float(segment["utilization_sensitivity"])
        financial_sensitivity = float(segment["financial_sensitivity"])
        unit = segment["business_unit"]

        for week in range(20):
            week_start = start + timedelta(days=week * 7)
            seasonal = 1 + 0.06 * random.choice([-1, 0, 1]) + week * random.uniform(-0.003, 0.007)
            if unit in {"Billing and Enrollment", "Member Services"} and week in {0, 1, 2, 3}:
                seasonal += 0.14
            if unit == "Utilization Management" and week in {8, 9, 10, 11, 12}:
                seasonal += 0.09

            contact_volume = max(300, int(random.gauss(baseline * seasonal, baseline * 0.08)))
            avoidable_rate = clamp(random.gauss(avoidable_base, 0.045), 0.08, 0.72)
            repeat_contact_rate = clamp(avoidable_rate * random.uniform(0.28, 0.48), 0.03, 0.35)
            sla_attainment = clamp(random.gauss(0.88 - avoidable_rate * 0.22, 0.045), 0.52, 0.98)
            avg_handle_minutes = clamp(random.gauss(7.4 + avoidable_rate * 8.5, 1.6), 4.0, 21.0)
            claims_pended_rate = clamp(random.gauss(0.06 + util_sensitivity * 0.11, 0.025), 0.01, 0.24)
            auth_turnaround_days = clamp(random.gauss(1.4 + util_sensitivity * 4.2, 0.8), 0.4, 7.6)
            member_abrasion = clamp(
                repeat_contact_rate * 46 + (1 - sla_attainment) * 34 + max(0, avg_handle_minutes - 10) * 1.6,
                5,
                92,
            )
            avoidable_contacts = int(contact_volume * avoidable_rate)
            estimated_cost_leakage = avoidable_contacts * financial_sensitivity
            utilization_exposure = money(contact_volume * util_sensitivity * random.uniform(8.0, 18.0))

            rows.append(
                {
                    "week_start": week_start.isoformat(),
                    "segment_id": segment["segment_id"],
                    "business_unit": unit,
                    "contact_volume": contact_volume,
                    "avoidable_contact_rate": round(avoidable_rate, 3),
                    "repeat_contact_rate": round(repeat_contact_rate, 3),
                    "sla_attainment": round(sla_attainment, 3),
                    "avg_handle_minutes": round(avg_handle_minutes, 1),
                    "claims_pended_rate": round(claims_pended_rate, 3),
                    "auth_turnaround_days": round(auth_turnaround_days, 1),
                    "member_abrasion_index": round(member_abrasion, 1),
                    "estimated_cost_leakage": money(estimated_cost_leakage),
                    "utilization_exposure": utilization_exposure,
                }
            )
    return rows


def segment_rollups(segments, weekly):
    by_segment = defaultdict(list)
    for row in weekly:
        by_segment[row["segment_id"]].append(row)

    segment_map = {row["segment_id"]: row for row in segments}
    ranked = []
    for segment_id, rows in by_segment.items():
        latest = sorted(rows, key=lambda item: item["week_start"])[-6:]
        prior = sorted(rows, key=lambda item: item["week_start"])[-12:-6]
        volume = sum(int(row["contact_volume"]) for row in latest)
        avoidable_contacts = sum(
            int(int(row["contact_volume"]) * float(row["avoidable_contact_rate"])) for row in latest
        )
        cost = sum(int(row["estimated_cost_leakage"]) for row in latest)
        util = sum(int(row["utilization_exposure"]) for row in latest)
        abrasion = sum(float(row["member_abrasion_index"]) for row in latest) / len(latest)
        sla = sum(float(row["sla_attainment"]) for row in latest) / len(latest)
        repeat = sum(float(row["repeat_contact_rate"]) for row in latest) / len(latest)
        auth_days = sum(float(row["auth_turnaround_days"]) for row in latest) / len(latest)
        prior_avoidable = sum(
            int(int(row["contact_volume"]) * float(row["avoidable_contact_rate"])) for row in prior
        )
        avoidable_delta = avoidable_contacts - prior_avoidable
        score = clamp(
            (avoidable_contacts / max(volume, 1)) * 38
            + repeat * 44
            + (1 - sla) * 32
            + abrasion * 0.44
            + min(cost / 95000, 18)
            + min(util / 85000, 13)
            + max(0, avoidable_delta / 900),
            0,
            100,
        )
        if score >= 64:
            action = "Manager review and requirement enhancement"
        elif repeat >= 0.18:
            action = "Root-cause repeat contacts"
        elif auth_days >= 3.5:
            action = "Tighten utilization handoff"
        elif cost >= 220000:
            action = "Quantify financial leakage"
        else:
            action = "Monitor trend and owner notes"

        segment = segment_map[segment_id]
        ranked.append(
            {
                "segment_id": segment_id,
                "business_unit": segment["business_unit"],
                "segment_name": segment["segment_name"],
                "inefficiency_theme": segment["inefficiency_theme"],
                "priority_score": round(score, 1),
                "six_week_volume": volume,
                "avoidable_contacts": avoidable_contacts,
                "avoidable_delta": avoidable_delta,
                "estimated_cost_leakage": money(cost),
                "utilization_exposure": money(util),
                "member_abrasion_index": round(abrasion, 1),
                "sla_attainment": round(sla, 3),
                "repeat_contact_rate": round(repeat, 3),
                "recommended_action": action,
                "leadership_note": (
                    f"{segment['segment_name']} has {avoidable_contacts:,} avoidable contacts over six weeks "
                    f"with ${money(cost):,} estimated service cost exposure and ${money(util):,} utilization exposure."
                ),
            }
        )

    ranked.sort(key=lambda row: row["priority_score"], reverse=True)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx
    return ranked


def build_requests(ranked):
    rows = []
    for idx, row in enumerate(ranked[:18], start=1):
        if float(row["priority_score"]) >= 64:
            status = "Ready for requirements"
            enhancement = "Add drilldown and owner notes"
        elif int(row["avoidable_delta"]) > 0:
            status = "Needs scoping"
            enhancement = "Add trend alert and threshold"
        else:
            status = "Monitor"
            enhancement = "Add metric definition tooltip"
        rows.append(
            {
                "request_id": f"REQ-{idx:03d}",
                "segment_id": row["segment_id"],
                "business_unit": row["business_unit"],
                "request_type": random.choice(REQUEST_TYPES),
                "requested_by": random.choice(["Sr. Manager", "Associate Director", "Ops Manager", "Analytics Lead"]),
                "dashboard_gap": enhancement,
                "decision_supported": random.choice(
                    [
                        "Weekly operating review",
                        "Staffing and routing decision",
                        "Provider data remediation",
                        "Claims rework reduction",
                        "Utilization handoff cleanup",
                    ]
                ),
                "status": status,
                "priority": row["rank"],
            }
        )
    return rows


def build_quality_checks():
    rows = []
    checks = [
        ("Service CRM", "contact_reason_mapping", 0.94, "Certify reason hierarchy before dashboard expansion"),
        ("Claims platform", "claim_status_freshness", 0.89, "Add freshness check to daily load"),
        ("Utilization management system", "auth_case_join_rate", 0.87, "Review auth identifiers missing from service contacts"),
        ("Provider data mart", "provider_directory_alignment", 0.91, "Reconcile provider IDs with latest directory snapshot"),
        ("Billing ledger", "payment_event_completeness", 0.96, "Monitor grace-period file delivery"),
        ("Looker semantic layer", "metric_definition_coverage", 0.84, "Add certified dimensions for repeat-contact analysis"),
    ]
    for idx, (system, check_name, pass_rate, fix) in enumerate(checks, start=1):
        failing = int((1 - pass_rate) * random.randint(1200, 5200))
        rows.append(
            {
                "check_id": f"DQ-{idx:03d}",
                "source_system": system,
                "check_name": check_name,
                "pass_rate": round(pass_rate, 3),
                "failing_records": failing,
                "freshness_hours": random.choice([3, 4, 6, 12, 18, 26]),
                "certification": "Certified" if pass_rate >= 0.93 else "Watch" if pass_rate >= 0.88 else "Needs work",
                "operating_fix": fix,
            }
        )
    return rows


def build_initiatives(ranked):
    rows = []
    candidates = ranked[:8]
    for idx, row in enumerate(candidates, start=1):
        baseline = int(row["avoidable_contacts"])
        target_reduction = round(clamp(float(row["priority_score"]) / 240, 0.12, 0.34), 2)
        current_reduction = round(clamp(target_reduction - random.uniform(-0.08, 0.10), 0.03, 0.40), 2)
        saved_contacts = int(baseline * current_reduction)
        saved_cost = money(saved_contacts * random.uniform(11, 23))
        rows.append(
            {
                "initiative_id": f"INIT-{idx:03d}",
                "segment_id": row["segment_id"],
                "segment_name": row["segment_name"],
                "owner": random.choice(["Mina", "Jordan", "Avery", "Priya", "Noah", "Elena"]),
                "initiative": random.choice(
                    [
                        "Self-service content fix",
                        "Queue routing rule update",
                        "Provider data correction sprint",
                        "Claims status explanation refresh",
                        "Authorization handoff checklist",
                    ]
                ),
                "baseline_avoidable_contacts": baseline,
                "target_reduction": target_reduction,
                "current_reduction": current_reduction,
                "estimated_contacts_avoided": saved_contacts,
                "estimated_cost_avoided": saved_cost,
                "status": "Ahead" if current_reduction >= target_reduction else "At risk",
            }
        )
    return rows


def build_summary(ranked, weekly, initiatives):
    latest_week = max(row["week_start"] for row in weekly)
    latest_rows = [row for row in weekly if row["week_start"] == latest_week]
    avoidable_contacts = sum(
        int(int(row["contact_volume"]) * float(row["avoidable_contact_rate"])) for row in latest_rows
    )
    total_contacts = sum(int(row["contact_volume"]) for row in latest_rows)
    cost = sum(int(row["estimated_cost_leakage"]) for row in latest_rows)
    util = sum(int(row["utilization_exposure"]) for row in latest_rows)
    top = ranked[0]
    return {
        "latest_week": latest_week,
        "active_segments": len(ranked),
        "total_contacts": total_contacts,
        "avoidable_contacts": avoidable_contacts,
        "avoidable_contact_rate": round(avoidable_contacts / total_contacts, 3),
        "weekly_cost_leakage": money(cost),
        "weekly_utilization_exposure": money(util),
        "high_priority_segments": len([row for row in ranked if float(row["priority_score"]) >= 64]),
        "top_segment": top["segment_name"],
        "top_business_unit": top["business_unit"],
        "top_priority_score": top["priority_score"],
        "estimated_contacts_avoided": sum(int(row["estimated_contacts_avoided"]) for row in initiatives),
        "estimated_cost_avoided": money(sum(int(row["estimated_cost_avoided"]) for row in initiatives)),
    }


def build_sql():
    return """-- Health plan service operations inefficiency checks.
-- Table names mirror the synthetic CSVs in this public portfolio artifact.

with weekly_segment as (
    select
        segment_id,
        business_unit,
        week_start,
        contact_volume,
        contact_volume * avoidable_contact_rate as avoidable_contacts,
        repeat_contact_rate,
        sla_attainment,
        estimated_cost_leakage,
        utilization_exposure
    from weekly_operating_metrics
),

six_week_rollup as (
    select
        segment_id,
        business_unit,
        sum(contact_volume) as six_week_volume,
        sum(avoidable_contacts) as avoidable_contacts,
        avg(repeat_contact_rate) as repeat_contact_rate,
        avg(sla_attainment) as sla_attainment,
        sum(estimated_cost_leakage) as estimated_cost_leakage,
        sum(utilization_exposure) as utilization_exposure
    from weekly_segment
    where week_start >= dateadd(week, -6, current_date)
    group by 1, 2
)

select
    segment_id,
    business_unit,
    six_week_volume,
    avoidable_contacts,
    estimated_cost_leakage,
    utilization_exposure,
    case
        when avoidable_contacts / nullif(six_week_volume, 0) >= 0.35 then 'manager review'
        when repeat_contact_rate >= 0.18 then 'repeat-contact root cause'
        when sla_attainment < 0.80 then 'service level recovery'
        else 'monitor'
    end as recommended_follow_up
from six_week_rollup
order by estimated_cost_leakage + utilization_exposure desc;
"""


def write_docs(summary, ranked):
    (ROOT / "analysis").mkdir(exist_ok=True)
    (ROOT / "analysis" / "analysis_plan.md").write_text(
        """# Analysis Plan

## Business Question

Which health plan service operations segments should managers review first because they combine avoidable contact volume, financial leakage, utilization exposure, and poor member experience?

## Method

1. Build a weekly segment grain across service contacts, claims friction, authorization follow-up, billing events, provider support, and care navigation.
2. Calculate avoidable contacts, repeat-contact rate, SLA attainment, member abrasion, estimated service cost leakage, and utilization exposure.
3. Score each segment with transparent weights that a non-technical stakeholder can review.
4. Convert the highest-scoring segments into dashboard requirements, stakeholder follow-up, and initiative impact monitoring.

## Leadership Use

The output is meant for weekly operating review with managers and senior managers. It separates the analytical readout from the action path so each issue has a clear owner, requirement, and follow-up metric.
"""
    )
    (ROOT / "analysis" / "executive_findings.md").write_text(
        f"""# Executive Findings

## Readout

- The latest synthetic week includes {summary['total_contacts']:,} service contacts and {summary['avoidable_contacts']:,} avoidable contacts.
- The modeled avoidable-contact rate is {summary['avoidable_contact_rate']:.1%}, with ${summary['weekly_cost_leakage']:,} in weekly service cost leakage.
- {summary['high_priority_segments']} segments exceed the high-priority threshold for manager follow-up.
- The top segment is {summary['top_segment']} in {summary['top_business_unit']} with a priority score of {summary['top_priority_score']}.

## Recommended Operating Moves

- Use the priority queue for the next service operations review.
- Convert repeated stakeholder requests into dashboard requirements instead of one-off pulls.
- Track initiative impact by avoided contacts and avoided cost, not only completion status.
"""
    )
    (ROOT / "analysis" / "sql_checks.sql").write_text(build_sql())
    (ROOT / "data_dictionary.md").write_text(
        """# Data Dictionary

## data/service_segments.csv

Segment grain for business unit, stakeholder, baseline volume, financial sensitivity, utilization sensitivity, and avoidable-contact baseline.

## data/weekly_operating_metrics.csv

Weekly operating facts by segment. Includes contact volume, avoidable contact rate, repeat contact rate, SLA attainment, handle time, pended claims rate, authorization turnaround, member abrasion index, estimated cost leakage, and utilization exposure.

## data/dashboard_requirements.csv

Stakeholder requests translated into dashboard enhancement requirements, status, decision supported, and priority.

## data/data_quality_checks.csv

Source-system quality checks used to decide whether a metric is ready for recurring leadership reporting.

## data/initiative_monitor.csv

Action tracking by segment, owner, baseline avoidable contacts, target reduction, current reduction, estimated contacts avoided, and estimated cost avoided.

## analysis/outputs/priority_queue.csv

Ranked service operations segments with six-week exposure, inefficiency score, recommended action, and leadership note.

## analysis/outputs/summary.json

Topline metrics used by the interactive artifact.
"""
    )


def main():
    segments = build_segments()
    weekly = build_weekly_metrics(segments)
    ranked = segment_rollups(segments, weekly)
    requests = build_requests(ranked)
    quality = build_quality_checks()
    initiatives = build_initiatives(ranked)
    summary = build_summary(ranked, weekly, initiatives)

    write_csv(
        DATA / "service_segments.csv",
        segments,
        [
            "segment_id",
            "business_unit",
            "segment_name",
            "inefficiency_theme",
            "primary_stakeholder",
            "baseline_weekly_volume",
            "financial_sensitivity",
            "utilization_sensitivity",
            "avoidable_contact_base",
        ],
    )
    write_csv(
        DATA / "weekly_operating_metrics.csv",
        weekly,
        [
            "week_start",
            "segment_id",
            "business_unit",
            "contact_volume",
            "avoidable_contact_rate",
            "repeat_contact_rate",
            "sla_attainment",
            "avg_handle_minutes",
            "claims_pended_rate",
            "auth_turnaround_days",
            "member_abrasion_index",
            "estimated_cost_leakage",
            "utilization_exposure",
        ],
    )
    write_csv(
        DATA / "dashboard_requirements.csv",
        requests,
        [
            "request_id",
            "segment_id",
            "business_unit",
            "request_type",
            "requested_by",
            "dashboard_gap",
            "decision_supported",
            "status",
            "priority",
        ],
    )
    write_csv(
        DATA / "data_quality_checks.csv",
        quality,
        [
            "check_id",
            "source_system",
            "check_name",
            "pass_rate",
            "failing_records",
            "freshness_hours",
            "certification",
            "operating_fix",
        ],
    )
    write_csv(
        DATA / "initiative_monitor.csv",
        initiatives,
        [
            "initiative_id",
            "segment_id",
            "segment_name",
            "owner",
            "initiative",
            "baseline_avoidable_contacts",
            "target_reduction",
            "current_reduction",
            "estimated_contacts_avoided",
            "estimated_cost_avoided",
            "status",
        ],
    )
    write_csv(
        OUT / "priority_queue.csv",
        ranked,
        [
            "rank",
            "segment_id",
            "business_unit",
            "segment_name",
            "inefficiency_theme",
            "priority_score",
            "six_week_volume",
            "avoidable_contacts",
            "avoidable_delta",
            "estimated_cost_leakage",
            "utilization_exposure",
            "member_abrasion_index",
            "sla_attainment",
            "repeat_contact_rate",
            "recommended_action",
            "leadership_note",
        ],
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    write_docs(summary, ranked)

    print(
        f"Generated {len(segments)} service segments, {len(weekly)} weekly rows, "
        f"{len(ranked)} ranked queue items, and {len(initiatives)} initiatives."
    )


if __name__ == "__main__":
    main()
