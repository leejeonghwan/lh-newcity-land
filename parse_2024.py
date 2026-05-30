#!/usr/bin/env python3
"""
2024-11-05 발표 신규택지 4곳 토지 매매 분석 파서.

지구:
  서리풀  (서울 서초구):     원지동·신원동·염곡동·내곡동·우면동
  고양대곡 (고양 덕양구):     내곡동·대장동·화정동·토당동·주교동
  의왕    (의왕시):          오전동·왕곡동
  의정부  (의정부시):        용현동·신곡동
"""
from __future__ import annotations
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
RAW = HERE / "data" / "raw_2024"
OUT = HERE / "data" / "parsed"

TREATMENT = {
    "서초구":         {"원지동", "신원동", "염곡동", "내곡동", "우면동"},
    "고양시 덕양구": {"내곡동", "대장동", "화정동", "토당동", "주교동"},
    "의왕시":         {"오전동", "왕곡동"},
    "의정부시":       {"용현동", "신곡동"},
}

DISTRICT = {}
for d in TREATMENT["서초구"]: DISTRICT[("서초구", d)] = "서리풀"
for d in TREATMENT["고양시 덕양구"]: DISTRICT[("고양시 덕양구", d)] = "고양대곡"
for d in TREATMENT["의왕시"]: DISTRICT[("의왕시", d)] = "오전왕곡"
for d in TREATMENT["의정부시"]: DISTRICT[("의정부시", d)] = "의정부용현"

HEADER = [
    "연월","일","시군구","법정동","번지",
    "지목","용도지역","도로조건",
    "계약면적_m2","거래금액_만원",
    "지분구분","해제일","거래유형","중개사소재지",
    "지구포함","지구",
]


def parse_csv(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    try: text = raw.decode("euc-kr")
    except UnicodeDecodeError: text = raw.decode("cp949", errors="replace")
    rows = []
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith('"NO","시군구"'):
            start = i + 1; break
    if start is None: return rows
    reader = csv.reader(lines[start:])
    for row in reader:
        if not row or not row[0].strip(): continue
        if not row[0].lstrip().isdigit(): continue
        try:
            (_no, sigungu, bunji, jimok, useArea, roadCond,
             ym, day, area, amount, share, cancel, dealType, agentLoc) = row[:14]
        except ValueError: continue
        # 예: "서울특별시 서초구 우면동" / "경기도 고양시 덕양구 내곡동" / "경기도 의왕시 오전동"
        parts = sigungu.split()
        if len(parts) < 3:
            base = sigungu; dong = ""
        else:
            if parts[0].endswith("특별시") or parts[0].endswith("광역시"):
                # 서울특별시 서초구 OOO
                base = parts[1]; dong = parts[2]
            elif len(parts) >= 4 and parts[2].endswith("구"):
                # 경기도 고양시 덕양구 OOO
                base = f"{parts[1]} {parts[2]}"; dong = parts[3]
            else:
                # 경기도 의왕시 OOO
                base = parts[1]; dong = parts[2]

        is_treat = "1" if (base in TREATMENT and dong in TREATMENT[base]) else "0"
        district = DISTRICT.get((base, dong), "")
        amount_clean = re.sub(r"[, ]", "", amount).strip()
        area_clean = re.sub(r"[, ]", "", area).strip()
        rows.append([
            ym.strip(), day.strip(), base, dong, bunji.strip(),
            jimok.strip(), useArea.strip(), roadCond.strip(),
            area_clean, amount_clean,
            share.strip(), cancel.strip(), dealType.strip(), agentLoc.strip(),
            is_treat, district,
        ])
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW.glob("land_*.csv"))
    all_rows = []
    for f in files:
        rs = parse_csv(f)
        print(f"  {f.name}: {len(rs)} rows")
        all_rows.extend(rs)
    out = OUT / "land_all_2024.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(HEADER); w.writerows(all_rows)
    print(f"[i] {len(all_rows):,}건 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
