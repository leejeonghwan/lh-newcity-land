#!/usr/bin/env python3
"""
1차 3기 신도시 (2018-12-19 발표) 토지 매매 분석 파서.

지구:
  남양주왕숙 (남양주시):  진접읍·진건읍·퇴계원읍·일패동·이패동·다산동
  하남교산   (하남시):    교산동·천현동·춘궁동·덕풍동·하사창동·상사창동·광암동·상산곡동·창우동·초이동·초일동
  인천계양   (인천 계양구): 동양동·박촌동·귤현동·병방동·상야동
"""
from __future__ import annotations
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
RAW = HERE / "data" / "raw_1cha"
OUT = HERE / "data" / "parsed"

# 시군구별 지구 포함 동 ((시군구명 키, 동 집합))
TREATMENT = {
    "남양주시": {
        "진접읍", "진건읍", "퇴계원읍",
        "일패동", "이패동", "다산동",
    },
    "하남시": {
        "교산동", "천현동", "춘궁동", "덕풍동",
        "하사창동", "상사창동", "광암동", "상산곡동",
        "창우동", "초이동", "초일동",
    },
    "인천 계양구": {
        "동양동", "박촌동", "귤현동", "병방동", "상야동",
    },
}

# 지구 매핑 (분리 분석용)
DISTRICT = {}
for d in TREATMENT["남양주시"]: DISTRICT[("남양주시", d)] = "왕숙"
for d in TREATMENT["하남시"]:   DISTRICT[("하남시", d)] = "교산"
for d in TREATMENT["인천 계양구"]: DISTRICT[("인천 계양구", d)] = "계양"

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
        # 예: ["경기도","남양주시","진접읍"] / ["인천광역시","계양구","박촌동"] / ["경기도","하남시","교산동"]
        parts = sigungu.split()
        if len(parts) < 3:
            base = sigungu; dong = ""
        else:
            # 광역시(서울특별시·인천광역시 등)일 때 자치구를 base로
            if parts[0].endswith("광역시") or parts[0].endswith("특별시"):
                base = f"인천 {parts[1]}" if parts[0] == "인천광역시" else f"{parts[0]} {parts[1]}"
                dong = parts[2]
            else:
                # "경기도 OO시 XX동" → base = "OO시", dong = "XX동"
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
    out = OUT / "land_all_1cha.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(HEADER); w.writerows(all_rows)
    print(f"[i] {len(all_rows):,}건 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
