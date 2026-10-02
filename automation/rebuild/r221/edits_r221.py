# -*- coding: utf-8 -*-
# r221 (사용자 요청 2026-10-02): 회계 > 입출금 탭 삭제.
#   그 화면은 구 Streamlit 앱(chjk-manage)이 Firebase 에 써 둔 요약(_misu_summary)을 읽어 그리던 대시보드인데,
#   요약이 2026-08-10 에서 멈춰 옛 숫자를 보여주고 있었다. 하던 일(미수·대사·내용증명)은 모두 미수현황/집계로 옮겨왔고,
#   마지막으로 남아 있던 매출총이익·마진율·연도별 추이는 r220 에서 집계 탭에 들어갔다.
#   - 하위 탭 버튼 / _ACCT / pageMap / 진입 훅 / #pageArmatch 마크업 / 전용 CSS / 요약·차트 함수 제거
#   - Streamlit 앱 링크(https://chjk-manage.streamlit.app/) 제거
#   - 상단 '회계' 탭을 누르면 이제 집계(fxsum)가 먼저 열린다
import io, sys

OPS = [
 # ① 하위 탭 버튼
 ['  <button class="sub-tab" data-page="armatch">입출금</button>\n', '', 1, "SUBTAB"],
 # ② 회계 하위 페이지 목록
 ["    var _ACCT=['armatch','fx','fxsum','fxup','cardsales'];   // r214: 집계·자료 업로드를 상위 탭으로",
  "    var _ACCT=['fx','fxsum','fxup','cardsales'];   // r221: 입출금 탭 삭제",
  1, "ACCT"],
 # ③ 페이지 매핑
 ["estimate:'pageEstimate', armatch:'pageArmatch', fx:'pageFx'",
  "estimate:'pageEstimate', fx:'pageFx'",
  1, "PAGEMAP"],
 # ④ 진입 훅
 ["    if (page === 'armatch'){ if(typeof loadMisuSummary==='function') loadMisuSummary(); }\n", '', 1, "HOOK"],
 # ⑤ 상단 회계 탭의 기본 화면 → 집계
 ["(function(){ var ta=document.getElementById('tabAccounting'); if(ta) ta.addEventListener('click', function(){ switchPage('armatch'); }); })();",
  "(function(){ var ta=document.getElementById('tabAccounting'); if(ta) ta.addEventListener('click', function(){ switchPage('fxsum'); }); })();   // r221: 입출금 삭제 → 집계가 기본",
  1, "DEFAULT"],
 # ⑥ 입출금 전용 반응형 CSS
 ["      /* 입금매칭 요약: 카드/그래프는 이미 auto-fit → 여백만 */\n      #misuSummaryWrap { margin-bottom: 12px !important; }\n"
  "      /* 좁은 화면: 앱 설명 문구 숨김 (버튼 title로 대체) — 요약 칩은 flex-wrap으로 자동 줄바꿈 */\n      .arm-appdesc { display:none !important; }\n"
  "      /* 좁은 화면: 회계 차트는 한 줄에 1개 */\n      #armChartGrid { grid-template-columns: 1fr !important; }\n",
  '', 1, "CSS"],
]

# ⑥-2 test 빌드에만 있는 모바일 전용 입출금 CSS (live 에는 없다 → 있을 때만 지운다)
OPT = [
 ["      /* \u2550\u2550 \ud68c\uacc4(\uc785\ucd9c\uae08) \u2550\u2550 */\n"
  "      /* \ud234\ubc14: \uc81c\ubaa9\u00b7\uae30\uc900\uc77c \ud55c \uc904, \uc571 \uc5f4\uae30 \ubc84\ud2bc\uc740 \uc544\ub798 \uc804\ud3ed */\n"
  "      #pageArmatch .q-toolbar { row-gap: 8px; }\n"
  "      #pageArmatch .q-toolbar a[href*=\"chjk-manage\"] { flex: 1 1 100%; justify-content: center; }\n"
  "      /* \ucc28\ud2b8: \uc138\ub85c \ub9c9\ub300 SVG\ub294 \ube44\uc728 \uc720\uc9c0\ub85c \ucd95\uc18c(\ube48 \uc5ec\ubc31 \ubc29\uc9c0) + \ub118\uce58\uba74 \uac00\ub85c \uc2a4\ud06c\ub864 */\n"
  "      #armChartGrid > div > div:last-child { overflow-x: auto; -webkit-overflow-scrolling: touch; }\n"
  "      #armChartGrid svg { height: auto !important; min-width: 520px; }\n"
  "      /* \uc0c1\uc704\uc5c5\uccb4 \uac00\ub85c \ub9c9\ub300: \uc5c5\uccb4\uba85\u00b7\uae08\uc561 \uce78 \ucd95\uc18c \u2192 \ub9c9\ub300\uac00 \uc0b4\ub3c4\ub85d */\n"
  "      .arm-hbn { width: 96px !important; flex: 0 0 96px !important; font-size: 11px !important; }\n"
  "      .arm-hbv { width: 56px !important; flex: 0 0 56px !important; font-size: 11px !important; }\n",
  '', "CSS_MOBILE"],
]

# ⑦ #pageArmatch 마크업 통째로 (주석 줄은 되살린다)
FX_COMMENT = "  <!-- ─── 매입매출(신) 페이지 (r122, r128 디자인 통일: 재고/매입처 툴바 패턴) ─── -->\n"

# ⑧ 요약·차트 함수 묶음 — 카드매출이 쓰는 _misuNote 만 남긴다
KEEP_NOTE = ("  // r221: 입출금 탭(구 Streamlit 요약 대시보드) 삭제. _misuNote 는 카드매출이 쓰므로 남긴다.\n"
             "  function _misuNote(gridId, msg){ var g=document.getElementById(gridId); if(g) g.innerHTML='<div style=\"color:#9ca3af;font-size:13px;padding:14px\">'+msg+'</div>'; }\n")

SPLICES = [
 ['  <div id="pageArmatch" class="page-section">',
  "  <!-- ─── 매입매출(신) 페이지 (r122, r128 디자인 통일: 재고/매입처 툴바 패턴) ─── -->\n",
  FX_COMMENT, "MARKUP"],
 ["  function _misuFmtWon(x){\n",
  "    }catch(e){ _misuNote('misuSummaryGrid','요약을 불러오지 못했습니다.'); _misuNote('salesSummaryGrid','요약을 불러오지 못했습니다.'); }\n  }\n",
  KEEP_NOTE, "FUNCS"],
]

MARKER = ["<!-- test build r220 2026-10-02 -->", "<!-- test build r221 2026-10-02 -->"]

FORBIDDEN = ['chjk-manage.streamlit.app', 'pageArmatch', 'arm-hbn', 'arm-hbv', 'arm-appdesc', 'loadMisuSummary', '_misuChip',
             '_misuVBarChart', '_misuHBarChart', '_misuFmtWon', 'misuSummaryGrid', 'armChartGrid']


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R221 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def splice(s, a, b, new, label):
    if s.count(a) != 1: raise SystemExit('R221 FAIL %s startAnchor %d' % (label, s.count(a)))
    if s.count(b) != 1: raise SystemExit('R221 FAIL %s endAnchor %d' % (label, s.count(b)))
    i = s.index(a); j = s.index(b, i)
    if j < i: raise SystemExit('R221 FAIL %s order' % label)
    return s[:i] + new + s[j + len(b):]


def apply_r221(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    for old, new, label in OPT:
        n = s.count(old)
        if n > 1: raise SystemExit('R221 FAIL %s count %d' % (label, n))
        if n == 1: s = s.replace(old, new)
    for a, b, new, label in SPLICES:
        s = splice(s, a, b, new, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for w in FORBIDDEN:
        if w in s: raise SystemExit('R221 FAIL 잔재 남음: %s (%d)' % (w, s.count(w)))
    if s.count('_misuNote') < 3: raise SystemExit('R221 FAIL _misuNote 가 사라짐 (카드매출이 씀)')
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r221(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r221 applied:', path)
