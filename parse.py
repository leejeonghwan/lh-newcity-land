#!/usr/bin/env python3
"""
국토부 실거래가(rt.molit.go.kr)에서 받은 토지 매매 CSV를 통합·정규화.

입력: data/raw/land_{sgg}_{year}.csv  (EUC-KR, 헤더 앞에 안내문 다수)
산출: data/parsed/land_all.csv (UTF-8, 1건=1행)

컬럼 정규화:
  연월(YYYYMM), 일, 시군구, 법정동, 번지(마스킹), 지목, 용도지역, 도로조건,
  계약면적_m2, 거래금액_만원, 지분구분, 해제일, 거래유형, 중개사소재지,
  지구포함(0/1)
"""
from __future__ import annotations
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
RAW = HERE / "data" / "raw"
OUT = HERE / "data" / "parsed"

# 광명·시흥 지구 포함 7개 법정동
TREATMENT = {
    "광명동", "노온사동", "옥길동", "가학동",  # 광명시
    "과림동", "무지내동", "금이동",           # 시흥시
}

HEADER = [
    "연월", "일", "시군구", "법정동", "번지",
    "지목", "용도지역", "도로조건",
    "계약면적_m2", "거래금액_만원",
    "지분구분", "해제일", "거래유형", "중개사소재지",
    "지구포함",
]


def parse_csv(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    # try EUC-KR first
    try:
        text = raw.decode("euc-kr")
    except UnicodeDecodeError:
        text = raw.decode("cp949", errors="replace")
    rows: list[list[str]] = []
    lines = text.splitlines()
    # find header line — starts with "NO","시군구",...
    start = None
    for i, line in enumerate(lines):
        if line.startswith('"NO","시군구"'):
            start = i + 1
            break
    if start is None:
        return rows
    reader = csv.reader(lines[start:])
    for row in reader:
        if not row or not row[0].strip():
            continue
        if not row[0].lstrip().isdigit():
            continue
        # row layout from sample:
        # NO, 시군구, 번지, 지목, 용도지역, 도로조건,
        # 계약년월, 계약일, 계약면적, 거래금액(만원), 지분구분,
        # 해제사유발생일, 거래유형, 중개사소재지
        try:
            (_no, sigungu, bunji, jimok, useArea, roadCond,
             ym, day, area, amount, share, cancel, dealType, agentLoc) = row[:14]
        except ValueError:
            continue

        # split 시군구 into 시군구·법정동
        parts = sigungu.split()
        # ['경기도', '광명시', '노온사동'] → 시군구='경기도 광명시', 법정동='노온사동'
        if len(parts) >= 3:
            base = " ".join(parts[:2])
            dong = parts[2]
        else:
            base = sigungu
            dong = ""

        amount_clean = re.sub(r"[, ]", "", amount).strip()
        area_clean = re.sub(r"[, ]", "", area).strip()

        rows.append([
            ym.strip(), day.strip(), base, dong, bunji.strip(),
            jimok.strip(), useArea.strip(), roadCond.strip(),
            area_clean, amount_clean,
            share.strip(), cancel.strip(), dealType.strip(), agentLoc.strip(),
            "1" if dong in TREATMENT else "0",
        ])
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW.glob("land_*.csv"))
    if not files:
        print(f"[!] {RAW}에 CSV 없음", file=sys.stderr)
        return 1
    all_rows: list[list[str]] = []
    for f in files:
        rs = parse_csv(f)
        print(f"  {f.name}: {len(rs)} rows")
        all_rows.extend(rs)
    out = OUT / "land_all.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(HEADER)
        w.writerows(all_rows)
    print(f"[i] 통합: {len(all_rows):,}건 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
