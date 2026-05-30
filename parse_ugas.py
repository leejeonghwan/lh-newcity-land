#!/usr/bin/env python3
"""
의왕·군포·안산 + 화성진안 지구 토지 매매 통합·정규화.

발표: 2021-08-30 (3기 신도시 추가 발표)
지구지정: 의왕·군포·안산 2023-06-30 / 화성진안 2024-02-07

지구 포함 12개 법정동:
  의왕시: 삼동, 월암동, 초평동
  군포시: 도마교동, 부곡동, 대야미동
  안산시 상록구: 건건동, 사사동
  화성시 진안 지구: 진안동, 반정동, 반월동, 기산동
"""
from __future__ import annotations
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
RAW = HERE / "data" / "raw_ugas"
OUT = HERE / "data" / "parsed"

# 시군구별 지구 포함 동 — 같은 이름 다른 시 케이스 방지 (예: 군포 부곡동 vs 안산 부곡동)
TREATMENT = {
    ("의왕시",):    {"삼동", "월암동", "초평동"},
    ("군포시",):    {"도마교동", "부곡동", "대야미동"},
    ("안산시 상록구",): {"건건동", "사사동"},
    ("화성시 병점구",): {"진안동", "반정동", "반월동", "기산동"},
}

# 지구 그룹 — 의왕·군포·안산 vs 화성진안 분리 분석용
DISTRICT = {}
for d in ["삼동","월암동","초평동","도마교동","부곡동","대야미동","건건동","사사동"]:
    DISTRICT[d] = "의왕군포안산"
for d in ["진안동","반정동","반월동","기산동"]:
    DISTRICT[d] = "화성진안"

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
        # split into 시·자치구·법정동
        parts = sigungu.split()
        # 예: "경기도 안산시 상록구 건건동" → base = "안산시 상록구", dong = "건건동"
        #     "경기도 군포시 부곡동"         → base = "군포시",        dong = "부곡동"
        if len(parts) == 4:
            base = " ".join(parts[1:3]); dong = parts[3]
        elif len(parts) == 3:
            base = parts[1]; dong = parts[2]
        else:
            base = sigungu; dong = ""
        # treatment check
        is_treat = "0"
        for key, dongs in TREATMENT.items():
            if base == key[0] and dong in dongs:
                is_treat = "1"; break
        amount_clean = re.sub(r"[, ]", "", amount).strip()
        area_clean = re.sub(r"[, ]", "", area).strip()
        rows.append([
            ym.strip(), day.strip(), base, dong, bunji.strip(),
            jimok.strip(), useArea.strip(), roadCond.strip(),
            area_clean, amount_clean,
            share.strip(), cancel.strip(), dealType.strip(), agentLoc.strip(),
            is_treat, DISTRICT.get(dong, ""),
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
    out = OUT / "land_all_ugas.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(HEADER); w.writerows(all_rows)
    print(f"[i] {len(all_rows):,}건 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
