#!/usr/bin/env python3
"""U15 Volleyball Team Management - local runnable app (CLI).

This is a lightweight runtime so coaches can start the system immediately,
add records, and generate a daily KPI snapshot from CSV databases.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).parent
DB = ROOT / "database"
TEMPLATES = ROOT / "data_templates"

TABLES = {
    "players": "players.csv",
    "trainings": "trainings.csv",
    "matches": "matches.csv",
    "injuries": "injuries.csv",
    "attendance": "attendance.csv",
}


@dataclass
class KPIReport:
    total_players: int
    avg_commitment: float
    attendance_today: int
    absences_today: int
    active_injuries: int

    def to_dict(self) -> Dict[str, float | int]:
        return {
            "total_players": self.total_players,
            "avg_commitment_%": round(self.avg_commitment, 2),
            "attendance_today": self.attendance_today,
            "absences_today": self.absences_today,
            "active_injuries": self.active_injuries,
        }


def ensure_database() -> None:
    DB.mkdir(exist_ok=True)
    for _, filename in TABLES.items():
        target = DB / filename
        if not target.exists():
            target.write_text((TEMPLATES / filename).read_text(encoding="utf-8"), encoding="utf-8")


def read_rows(table: str) -> List[Dict[str, str]]:
    path = DB / TABLES[table]
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def append_row(table: str, row: Dict[str, str]) -> None:
    path = DB / TABLES[table]
    rows = read_rows(table)
    header = rows[0].keys() if rows else csv_header(path)
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(header))
        writer.writerow(row)


def csv_header(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def compute_kpis() -> KPIReport:
    players = read_rows("players")
    attendance = read_rows("attendance")
    injuries = read_rows("injuries")

    commitment_values = []
    for p in players:
        raw = p.get("نسبة_الالتزام_%", "").strip()
        if raw:
            try:
                commitment_values.append(float(raw))
            except ValueError:
                pass

    today = date.today().isoformat()
    attendance_today = sum(1 for r in attendance if r.get("التاريخ") == today and r.get("حالة_الحضور") == "حاضر")
    absences_today = sum(1 for r in attendance if r.get("التاريخ") == today and r.get("حالة_الحضور") == "غائب")
    active_injuries = sum(1 for r in injuries if r.get("الحالة_الحالية") in {"نشطة", "تعافي"})

    return KPIReport(
        total_players=len(players),
        avg_commitment=sum(commitment_values) / len(commitment_values) if commitment_values else 0.0,
        attendance_today=attendance_today,
        absences_today=absences_today,
        active_injuries=active_injuries,
    )


def run_demo_seed() -> None:
    if read_rows("players"):
        return

    append_row(
        "players",
        {
            "player_id": "P001",
            "الاسم": "لينا",
            "السن": "14",
            "الطول_cm": "165",
            "الوزن_kg": "54",
            "مركز_اللعب": "Setter",
            "اليد_المفضلة": "يمين",
            "رقم_القميص": "7",
            "المدرسة": "مدرسة النور",
            "ولي_الأمر": "أحمد",
            "رقم_التواصل": "0500000000",
            "تاريخ_بداية_التدريب": date.today().isoformat(),
            "مستوى_اللياقة": "7",
            "مستوى_المهارات": "7",
            "التقييم_الفني": "7",
            "التقييم_البدني": "6",
            "التقييم_الخططي": "7",
            "التقييم_النفسي": "8",
            "نسبة_الالتزام_%": "92",
            "الحضور_والغياب": "20/1",
            "الإصابات_السابقة": "",
            "الحمل_التدريبي_الأسبوعي": "950",
            "عدد_القفزات_الأسبوعي": "120",
            "تقييم_المباراة": "7",
            "التطور_الشهري_%": "6",
        },
    )


def main() -> None:
    ensure_database()
    run_demo_seed()
    kpi = compute_kpis().to_dict()
    print("U15 Volleyball Team Management System is running.")
    print(json.dumps(kpi, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
