#!/usr/bin/env python3
"""2024-11-05 발표 4개 지구 개별 페이지 생성 (템플릿 기반)."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent.resolve()

DISTRICTS = [
    {
        "slug": "seoripool",
        "title": "서울 서리풀 — 토지 거래 시계열",
        "h1": "서울 서리풀지구 (서초)",
        "color": "#8e44ad",
        "anno_label": "발표 2024-11-05",
        "anno_x": "2024-11",
        "band_start": "2023-11",
        "band_end": "2024-10",
        "lead": "강남 인접 그린벨트 해제. 5개 동(원지·신원·염곡·내곡·우면). 서초구 다른 동들이 강남 재건축 호재로 ×4.45 폭증한 사이, 지구는 ×0.71 감소.",
        "highlight": "내곡동 2024-03-04 — 한 날 15건, <strong>지분 80%</strong>, 모두 대지, 평균 26억. 광명·시흥(임야·지분 100%)과 형태는 다르지만 매집 정황. 강남권 입주권 사재기 가능성.",
    },
    {
        "slug": "goyang-daegok",
        "title": "고양 대곡 역세권 — 토지 거래 시계열",
        "h1": "고양 대곡 역세권",
        "color": "#1565c0",
        "anno_label": "발표 2024-11-05",
        "anno_x": "2024-11",
        "band_start": "2023-11",
        "band_end": "2024-10",
        "lead": "GTX-A 등 5개 노선 환승역세권. 5개 동(내곡·대장·화정·토당·주교). 시장 둔화기에 지구도 ×0.64 감소.",
        "highlight": "주교동 2024-05-20 클러스터 29건이 한 번지(1***)에 집중. 그러나 지목이 도로·양어장·창고용지 위주, 지분 3%. 단일 보유 필지 분할 매도로 추정.",
    },
    {
        "slug": "uiwang",
        "title": "의왕 오전왕곡 — 토지 거래 시계열",
        "h1": "의왕 오전왕곡",
        "color": "#d33",
        "anno_label": "발표 2024-11-05",
        "anno_x": "2024-11",
        "band_start": "2023-11",
        "band_end": "2024-10",
        "lead": "2개 동(오전·왕곡). 4개 지구 중 격차 ×1.54로 가장 강신호. 지구 ×1.16(증가) vs 통제군 ×0.76(감소).",
        "highlight": "오전동 2023-12-01 66건이 한 번지(3**)에 53건 묶임. 지목 도로 32·대 13·임야 9, <strong>지분 0%</strong>. 단일 보유 필지 분할 매도 가능성이 크나 면적·매수자 분포 확인 필요. 등기부 추적이 다음 단계.",
    },
    {
        "slug": "uijeongbu",
        "title": "의정부 용현 — 토지 거래 시계열",
        "h1": "의정부 용현",
        "color": "#0a5",
        "anno_label": "발표 2024-11-05",
        "anno_x": "2024-11",
        "band_start": "2023-11",
        "band_end": "2024-10",
        "lead": "2개 동(용현·신곡). 지구 ×0.47, 통제 ×0.34. 둘 다 감소했지만 통제군이 더 큰 폭으로 줄어 격차 ×1.39.",
        "highlight": "신곡동 2023-11-15 9건 클러스터(산6* 번지 5건), 지목 도로·임야, 지분 0%. 광명·시흥 시그니처와 형태 다름. 발표 후 지구 거래 -82% 급감(시군구 통제군은 -66%).",
    },
]


HTML_TMPL = r'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
         max-width: 1200px; margin: 24px auto; padding: 0 16px; color: #1a1a1a; background:#fafafa; }
  a { color:__COLOR__; text-decoration:none; }
  a:hover { text-decoration:underline; }
  h1 { font-size: 22px; margin-bottom: 4px; }
  h2 { font-size: 17px; margin-top: 36px; border-left: 3px solid __COLOR__; padding-left: 8px; }
  .sub { color:#666; font-size:13px; margin-bottom: 24px; }
  .crumbs { font-size:12px; color:#888; margin-bottom:12px; }
  .crumbs a { color:#0451a5; }
  .kpi-row { display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin: 16px 0 24px; }
  .kpi { background:#fff; border:1px solid #e3e3e3; border-radius:6px; padding:12px 14px; }
  .kpi .v { font-size: 22px; font-weight: 700; color:__COLOR__; }
  .kpi .l { font-size: 12px; color:#666; margin-top:2px; }
  .chart-wrap { background:#fff; border:1px solid #e3e3e3; border-radius:6px; padding:16px; margin:12px 0; }
  .chart-wrap h3 { font-size:14px; margin:0 0 8px; color:#333; }
  .small-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
  table { width:100%; border-collapse: collapse; font-size:13px; background:#fff; }
  th, td { border-bottom: 1px solid #eee; padding:6px 8px; text-align:left; }
  th { background:#f3f3f3; }
  td.num { text-align:right; font-variant-numeric: tabular-nums; }
  .note { font-size:12px; color:#666; margin-top:6px; line-height:1.5; }
  .pill { display:inline-block; background:#eee; color:#333; border-radius:3px; padding:1px 6px; font-size:11px; margin-left:4px; }
  .pill.hot { background:#fee; color:#a00; }
  .pill.med { background:#fef0e0; color:#a55; }
  .pill.muted { background:#eee; color:#666; }
  .ctx { background:#fff8e6; border:1px solid #f5e4a8; border-radius:6px; padding:12px 14px; font-size:13px; line-height:1.6; }
  .ctx.cool { background:#f0f7ff; border-color:#a8c4e4; }
  .lead { font-size:14px; color:#333; }
  .highlight { background:#fff; border-left:4px solid __COLOR__; padding:10px 14px; margin:14px 0; font-size:13px; line-height:1.7; }
</style>
</head>
<body>

<div class="crumbs"><a href="../index.html">← 메인</a> · <a href="2024-candidates.html">2024 후보지 4곳 비교</a></div>
<h1>__H1__</h1>
<div class="sub">2024-11-05 발표 신규택지 후보지 · 국토부 실거래가 데이터</div>

<div class="ctx">
  <strong>지구 요약:</strong> <span class="lead">__LEAD__</span>
</div>

<div class="highlight"><strong>주목할 신호:</strong> __HIGHLIGHT__</div>

<h2>핵심 숫자</h2>
<div class="kpi-row">
  <div class="kpi"><div class="v" id="kpi1">—</div><div class="l">지구 발표 12개월전/평년 배율</div></div>
  <div class="kpi"><div class="v" id="kpi2">—</div><div class="l">시군구 통제군 배율</div></div>
  <div class="kpi"><div class="v" id="kpi3">—</div><div class="l">지구-통제 격차</div></div>
  <div class="kpi"><div class="v" id="kpi4">—</div><div class="l">발표 후 2개월 잔존율</div></div>
</div>

<h2>지구 vs 시군구 통제군 — 월별 거래</h2>
<div class="chart-wrap">
  <canvas id="mainChart" height="120"></canvas>
  <div class="note">세로 점선: 발표일. 회색 음영: 가설 검증 구간(발표 12개월 전).</div>
</div>

<h2>동별 시계열</h2>
<div class="small-grid" id="dongGrid"></div>

<h2>같은 동·같은 날 클러스터 (5건 이상)</h2>
<div class="chart-wrap">
  <table id="clusterTable">
    <thead><tr><th>동</th><th>일자</th><th class="num">총건수</th><th>최다 번지</th><th class="num">그 번지에서</th><th class="num">지분비율</th><th>지목 분포</th></tr></thead>
    <tbody></tbody>
  </table>
  <div class="note">광명·시흥은 같은 클러스터가 임야 + 지분 100%. 지분 비율이 높을수록 매집 가능성, 0%면 단일 보유 필지 분할 매도일 확률.</div>
</div>

<h2>번지별 매집 집중도 (발표 12개월 전)</h2>
<div class="chart-wrap">
  <table id="bunjiTable">
    <thead><tr><th>동</th><th>번지</th><th class="num">12개월 거래</th></tr></thead>
    <tbody></tbody>
  </table>
</div>

<h2>지목 분포 (발표 12개월 전 지구 거래)</h2>
<div class="chart-wrap">
  <table id="jimokTable">
    <thead><tr><th>지목</th><th class="num">건수</th></tr></thead>
    <tbody></tbody>
  </table>
  <div class="note">광명·시흥 12개월 전 지목 분포는 임야·전·답 등 농지·임야가 압도적. 대지·도로 비율이 높으면 보상가 노린 입주권 사재기 또는 단순 도시 토지 거래 가능성.</div>
</div>

<script id="vizdata" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('vizdata').textContent);
const ANNO_X = "__ANNO_X__";
const PEAK_START = "__BAND_START__", PEAK_END = "__BAND_END__";
const COLOR = "__COLOR__";

document.getElementById('kpi1').textContent = "×" + D.kpi["지구_배율"];
document.getElementById('kpi2').textContent = "×" + D.kpi["통제_배율"];
document.getElementById('kpi3').textContent = "×" + D.kpi["격차"];
document.getElementById('kpi4').textContent = (D.kpi["잔존율"] * 100).toFixed(0) + "%";

const annoAll = {
  ann:{ type:'line', xMin:ANNO_X, xMax:ANNO_X, borderColor:COLOR, borderWidth:1.5, borderDash:[4,3],
        label:{ display:true, content:'__ANNO_LABEL__', position:'start', color:COLOR, font:{size:11}, backgroundColor:'transparent' } },
  band:{ type:'box', xMin:PEAK_START, xMax:PEAK_END, backgroundColor:'rgba(0,0,0,0.05)', borderWidth:0 }
};

new Chart(document.getElementById('mainChart'), {
  type:'line',
  data:{
    labels:D.main.labels,
    datasets:[
      { label:'지구 (좌)', data:D.main.treatment, borderColor:COLOR, tension:0.2, yAxisID:'y', pointRadius:1, borderWidth:2 },
      { label:'시군구 통제군 (우)', data:D.main.control, borderColor:'#888', tension:0.2, yAxisID:'y1', pointRadius:1, borderWidth:1.2 }
    ]
  },
  options:{ responsive:true, interaction:{mode:'index', intersect:false},
    scales:{ x:{ ticks:{autoSkip:true, maxTicksLimit:14}}, y:{title:{display:true, text:'지구'}, beginAtZero:true},
      y1:{position:'right', title:{display:true, text:'통제군'}, grid:{display:false}, beginAtZero:true} },
    plugins:{ annotation:{annotations:annoAll} } }
});

const dongGrid = document.getElementById('dongGrid');
const orderEntries = Object.entries(D.kpi["동별배율"]).sort((a,b)=>b[1]-a[1]);
for (const [k, mult] of orderEntries) {
  if (!D.by_dong[k]) continue;
  const wrap = document.createElement('div');
  wrap.className = 'chart-wrap';
  const cls = mult >= 1.5 ? 'pill hot' : (mult >= 1.0 ? 'pill med' : 'pill muted');
  wrap.innerHTML = '<h3>' + k + ' <span class="' + cls + '">×' + mult + '</span></h3><canvas height="100"></canvas>';
  dongGrid.appendChild(wrap);
  new Chart(wrap.querySelector('canvas'), {
    type:'line',
    data:{ labels:D.main.labels, datasets:[{ data:D.by_dong[k], borderColor:COLOR, tension:0.25, pointRadius:0, borderWidth:1.6, fill:'origin', backgroundColor:COLOR+'1a' }] },
    options:{ responsive:true, plugins:{ legend:{display:false}, annotation:{annotations:annoAll} }, scales:{ x:{ticks:{display:false}}, y:{beginAtZero:true} } }
  });
}

const ctb = document.querySelector('#clusterTable tbody');
for (const c of D.clusters_topN) {
  const tr = document.createElement('tr');
  const shareColor = c['지분비율'] >= 50 ? '#a00' : (c['지분비율'] >= 20 ? '#a55' : '#666');
  tr.innerHTML = '<td>'+c['동']+'</td><td>'+c['일자']+'</td>'
               + '<td class="num">'+c['건수']+'</td><td>'+c['최다번지']+'</td>'
               + '<td class="num">'+c['번지건수']+'</td>'
               + '<td class="num" style="color:'+shareColor+'">'+c['지분비율']+'%</td>'
               + '<td style="font-size:11px; color:#666">'+(c['지목']||'')+'</td>';
  ctb.appendChild(tr);
}
const btb = document.querySelector('#bunjiTable tbody');
for (const b of D.bunji_top) {
  const tr = document.createElement('tr');
  tr.innerHTML = '<td>'+b['동']+'</td><td>'+b['번지']+'</td><td class="num">'+b['건수']+'</td>';
  btb.appendChild(tr);
}
const jtb = document.querySelector('#jimokTable tbody');
for (const [k, v] of Object.entries(D.kpi["지목분포"])) {
  const tr = document.createElement('tr');
  tr.innerHTML = '<td>'+k+'</td><td class="num">'+v+'</td>';
  jtb.appendChild(tr);
}
</script>

</body>
</html>
'''


def render(d: dict) -> str:
    data = (HERE / "data" / "parsed" / f"viz_2024_{d['slug']}.json").read_text(encoding="utf-8")
    data_safe = data.replace('</', '<\\/')
    html = HTML_TMPL
    for k, v in [
        ("__TITLE__", d["title"]),
        ("__H1__", d["h1"]),
        ("__COLOR__", d["color"]),
        ("__ANNO_LABEL__", d["anno_label"]),
        ("__ANNO_X__", d["anno_x"]),
        ("__BAND_START__", d["band_start"]),
        ("__BAND_END__", d["band_end"]),
        ("__LEAD__", d["lead"]),
        ("__HIGHLIGHT__", d["highlight"]),
        ("__DATA__", data_safe),
    ]:
        html = html.replace(k, v)
    return html


def main():
    out_dir = HERE / "pages"
    out_dir.mkdir(exist_ok=True)
    for d in DISTRICTS:
        path = out_dir / f"2024-{d['slug']}.html"
        path.write_text(render(d), encoding="utf-8")
        print(f"  → {path.name}")


if __name__ == "__main__":
    main()
