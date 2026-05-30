#!/usr/bin/env python3
"""
인터넷등기소 등기사항증명서(부동산) PDF 파서.

발급한 PDF를 `registry/raw_pdfs/` 폴더에 넣고 실행하면
표제부·갑구·을구를 파싱해 `registry/extracted.csv`로 통합한다.

스키마: cluster_id, 지구, 시군구, 법정동, 필지본번, 부번, 면적_m2, 지목,
       등기순위, 등기원인, 등기일자, 매수자성명, 매수자주소(시군구),
       지분_분자, 지분_분모, 매매가_만원, 비고

사용법:
    pip install pdfplumber
    python3 parse_pdf.py
    또는
    python3 parse_pdf.py raw_pdfs/하남시_초일동_산10.pdf

CSV 헤더는 extracted_template.csv와 동일.
"""
from __future__ import annotations
import argparse, csv, re, sys
from pathlib import Path

try:
    import pdfplumber  # type: ignore
except ImportError:
    print("pip install pdfplumber 필요", file=sys.stderr)
    sys.exit(1)

HERE = Path(__file__).parent.resolve()
RAW = HERE / "raw_pdfs"
OUT = HERE / "extracted.csv"

HEADER = [
    "cluster_id","지구","시군구","법정동","필지본번","부번",
    "면적_m2","지목","등기순위","등기원인","등기일자",
    "매수자성명","매수자주소(시군구)","지분_분자","지분_분모","매매가_만원","비고",
]


def parse_표제부(text: str) -> dict:
    """표제부(부동산 표시) — 소재지·면적·지목 추출."""
    out = {}
    # 예: "[토지] 경기도 광명시 옥길동 산12 임야 1,290㎡"
    m = re.search(r"\[(?:토지|임야)\]\s*([^\n]+)", text)
    if m:
        line = m.group(1).strip()
        out["소재지"] = line
        # 면적
        am = re.search(r"([\d,]+)\s*(?:㎡|m2)", line)
        if am:
            out["면적_m2"] = am.group(1).replace(",", "")
        # 지목 (전·답·임야·대·도로·잡종지 등)
        jm = re.search(r"\s(전|답|임야|대|도로|잡종지|과수원|목장용지|구거|유지|공장용지)\s", " " + line + " ")
        if jm:
            out["지목"] = jm.group(1)
        # 본번·부번
        # "옥길동 산12-3" → 본번 산12, 부번 3
        bm = re.search(r"(?:동|읍|면|리)\s+(산?\d+)(?:-(\d+))?", line)
        if bm:
            out["필지본번"] = bm.group(1)
            out["부번"] = bm.group(2) or ""
    return out


def parse_갑구(text: str) -> list[dict]:
    """갑구(소유권에 관한 사항) — 매매·증여·상속 이력 추출.

    등기부의 갑구 항목은 보통 다음 형태:
      [순위번호][등기목적][접수일자/접수번호][등기원인][권리자 및 기타사항]

    매수자 정보는 "권리자 및 기타사항"에 있다:
      홍길동
      서울 강남구 ...
      지분 1/7
    """
    entries = []
    # 갑구 섹션을 찾는다
    gab_match = re.search(r"\【\s*갑\s*구\s*\】.*?(?=\【\s*을\s*구\s*\】|$)", text, re.S)
    if not gab_match:
        return entries

    gab = gab_match.group(0)
    # 등기 한 건 = 순위번호로 시작하는 블록
    blocks = re.split(r"\n\s*(?=\d+\s+\S)", gab)

    for block in blocks:
        if not block.strip():
            continue
        # 등기 목적 + 접수
        # 예: "5  소유권일부이전  2020년 6월 23일  매매  ..."
        date_m = re.search(r"(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일", block)
        cause_m = re.search(r"(매매|증여|상속|합병|분할|판결|경매|공유물분할)", block)

        if not date_m or "이전" not in block:
            continue

        # 권리자(매수자) 정보
        # 한 등기에 다수 공유자가 있을 수 있음
        # 예: "공유자\n  지분 1/7\n  홍길동  710101-1******\n  서울특별시 강남구 ..."
        share_matches = list(re.finditer(
            r"지분\s*(\d+)(?:분의|\s*/\s*)(\d+)\s*\n?\s*([가-힣]{2,4})\s+\d{6}",
            block,
        ))

        if share_matches:
            # 공유 매수자 다수
            for sm in share_matches:
                denom, num, name = sm.group(1), sm.group(2), sm.group(3)
                addr_m = re.search(
                    rf"{re.escape(name)}\s+\d{{6}}-\d\*{{6}}\s*\n?\s*([가-힣\s\d]+(?:특별시|광역시|시|도)\s+\S+(?:구|시|군))",
                    block,
                )
                addr = addr_m.group(1).strip() if addr_m else ""
                entries.append({
                    "등기원인": cause_m.group(1) if cause_m else "",
                    "등기일자": f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}",
                    "매수자성명": name,
                    "매수자주소(시군구)": addr,
                    "지분_분자": num,
                    "지분_분모": denom,
                })
        else:
            # 단독 매수
            name_m = re.search(r"([가-힣]{2,4})\s+\d{6}-\d\*{6}", block)
            if name_m:
                name = name_m.group(1)
                addr_m = re.search(
                    rf"{re.escape(name)}\s+\d{{6}}-\d\*{{6}}\s*\n?\s*([가-힣\s\d]+(?:특별시|광역시|시|도)\s+\S+(?:구|시|군))",
                    block,
                )
                addr = addr_m.group(1).strip() if addr_m else ""
                entries.append({
                    "등기원인": cause_m.group(1) if cause_m else "",
                    "등기일자": f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}",
                    "매수자성명": name,
                    "매수자주소(시군구)": addr,
                    "지분_분자": "",
                    "지분_분모": "",
                })

    # 등기순위 부여
    for i, e in enumerate(entries, 1):
        e["등기순위"] = str(i)
    return entries


def parse_pdf(path: Path, cluster_id: str = "", default_region: dict | None = None) -> list[dict]:
    """단일 PDF에서 행 추출."""
    default_region = default_region or {}
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)

    표제 = parse_표제부(text)
    갑구 = parse_갑구(text)

    소재지 = 표제.get("소재지", "")
    # 시군구·법정동 추출 시도
    sgg_m = re.search(r"([가-힣]+(?:특별시|광역시|시|도))\s+([가-힣]+(?:구|시|군))\s+([가-힣]+(?:동|읍|면|리))", 소재지)
    if sgg_m:
        sido_sgg = f"{sgg_m.group(1)} {sgg_m.group(2)}"
        dong = sgg_m.group(3)
    else:
        sido_sgg = default_region.get("시군구", "")
        dong = default_region.get("법정동", "")

    rows = []
    for e in 갑구:
        rows.append({
            "cluster_id": cluster_id,
            "지구": default_region.get("지구", ""),
            "시군구": sido_sgg,
            "법정동": dong,
            "필지본번": 표제.get("필지본번", ""),
            "부번": 표제.get("부번", ""),
            "면적_m2": 표제.get("면적_m2", ""),
            "지목": 표제.get("지목", ""),
            "등기순위": e.get("등기순위", ""),
            "등기원인": e.get("등기원인", ""),
            "등기일자": e.get("등기일자", ""),
            "매수자성명": e.get("매수자성명", ""),
            "매수자주소(시군구)": e.get("매수자주소(시군구)", ""),
            "지분_분자": e.get("지분_분자", ""),
            "지분_분모": e.get("지분_분모", ""),
            "매매가_만원": "",
            "비고": f"PDF: {path.name}",
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="개별 PDF 경로(생략 시 raw_pdfs/*.pdf 전체)")
    ap.add_argument("--cluster", default="", help="cluster_id (택1: 1차3기/광명시흥/2차3기/의왕군포안산/2024)")
    args = ap.parse_args()

    if args.files:
        paths = [Path(p) for p in args.files]
    else:
        if not RAW.exists():
            print(f"[!] {RAW} 없음. PDF를 넣어 주세요.", file=sys.stderr)
            return 1
        paths = sorted(RAW.glob("*.pdf"))

    if not paths:
        print("[!] PDF 없음", file=sys.stderr)
        return 1

    all_rows = []
    for p in paths:
        # 파일명 패턴: "{지구}_{시군구}_{법정동}_{지번}.pdf"
        stem = p.stem
        parts = stem.split("_")
        region = {}
        if len(parts) >= 3:
            region["지구"] = parts[0]
            region["시군구"] = parts[1]
            region["법정동"] = parts[2]

        cluster_id = args.cluster or region.get("지구", "")
        rows = parse_pdf(p, cluster_id=cluster_id, default_region=region)
        print(f"  {p.name}: {len(rows)}행 추출")
        all_rows.extend(rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\n[i] {len(all_rows):,}행 → {OUT}")

    # 간단 통계
    if all_rows:
        from collections import Counter
        # 매수자 빈도
        names = Counter(r["매수자성명"] for r in all_rows if r["매수자성명"])
        print("\n=== 매수자 빈도 (상위 10) ===")
        for n, c in names.most_common(10):
            print(f"  {n}: {c}")

        # 같은 일자 다중 매수자
        date_groups = {}
        for r in all_rows:
            key = (r["필지본번"], r["등기일자"])
            date_groups.setdefault(key, []).append(r)
        print("\n=== 동일 일자 다중 매수자 (5명+) ===")
        for (bunji, date), rows in sorted(date_groups.items()):
            if len(rows) >= 5:
                print(f"  {bunji} {date}: {len(rows)}명")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
