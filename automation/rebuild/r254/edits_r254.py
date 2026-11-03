# -*- coding: utf-8 -*-
# r254 (사용자 요청 2026-11-03): 회계 > [자료 검색] — 이름으로 입금 내역과 그 처리 결과를 찾는다
#
# 요청: "'홍길동' 으로 검색하면 그 이름으로 들어온 내역을 보여주고, 어디로 언제 배정됐는지 ·
#        배제됐으면 배제됐다고 · 없으면 없다고 알려주는 자료검색. 느려지지 않게."
#
# 확인한 사실(실제 자료 2026-11-03)
#   · 입금·어음 11,072건(2021-01-03~2026-10-13, 약 2.1MB) · 입금자 이름 1,488종
#     배정 8,073 / 제외 2,961 / 보류 39 / 미배정 38
#   · **출금은 저장되지 않는다** — 업로더가 `if(!amt6 || amt6<=0) continue;` 로 버린다.
#     사용자 결정: "일단 입금만으로".
#   · **배정 시각·사람(asgAt/asgBy)이 124건만 남아 있다** — `_fxAsgPrune()` 이 되돌리기용
#     최근 50묶음을 넘기면 `_fxAsgClear()` 로 통째로 지우기 때문.
#     사용자 결정: "앞으로는 지우지 않기" → 묶음 정보(asgBat·asgU)만 지우고 시각·사람은 남긴다.
#   · 검색 범위(사용자 결정): **입금자명 + 배정 거래처명**.
#
# 구성
#   · 회계 하위탭 `fxfind` 추가 — 화면은 기존 `pageFx` 를 `_fxTab='find'` 로 나눠 쓴다(fx/fxsum/fxup 과 같은 틀).
#   · 검색은 메모리 필터. 정규화 색인 `_ffIdx` 를 자료 버전(`_fxCacheBump`)당 한 번만 만들고
#     입력은 200ms 디바운스 → 11,000건이라도 한 번에 끝난다(색인 재사용).
#   · 결과: 요약 한 줄 + 건별 표(날짜·구분·계좌 사업장·금액·입금자·상태·배정 기록).
#   · 없으면 "없습니다" + 비슷한 이름 후보(눌러서 바로 재검색).
import io, sys

FIND = r"""    if(_fxTab==='find'){
      // ── r254: 이름으로 입금 내역·처리 결과 찾기 ──
      tb.innerHTML =
        '<span class="inv-flat-label">자료 검색</span>'
        + '<input type="text" class="q-flat" id="fxFindInput" placeholder="입금자명 · 거래처명 검색…" value="' + esc(_fxFindQ) + '" oninput="fxFindInput(this.value)" autocomplete="off">'
        + metaSpan
        + '<span style="flex:1"></span>'
        + '<span style="font-size:11px;color:#9ca3af;white-space:nowrap">통장에 찍힌 이름과 배정된 거래처를 함께 찾습니다</span>';
      body.innerHTML = _loading;
      _fxEnsureData().then(function(){
        if(_fxTab!=='find') return;
        _fxMetaRefresh();
        body.innerHTML = '<div id="fxFindBody"></div>';
        _ffRender();
        var i = document.getElementById('fxFindInput'); if(i) setTimeout(function(){ try{ i.focus(); }catch(_e){} }, 30);
      });
      return;
    }
"""

HELPERS = r"""  // ── r254: 자료 검색 (입금자명·거래처명 → 내역과 처리 결과) ─────────────
  //  자료는 회계 탭에 들어올 때 이미 메모리에 올라와 있다. 정규화 색인을 자료 버전당 한 번만
  //  만들어 두고 쓰므로, 11,000건이어도 글자를 칠 때마다 다시 훑지 않는다.
  var _fxFindQ = '', _fxFindShow = 200, _fxFindTimer = null;
  var _ffIdx = null, _ffIdxBump = -1;
  function _ffNorm(s){
    return String(s == null ? '' : s)
      .replace(/주식회사|유한회사|\(주\)|\(유\)|㈜|㈲/g, '')
      .replace(/[\s.\-_,'"()·\[\]]/g, '')
      .toLowerCase();
  }
  function _ffBuild(){
    if(_ffIdx && _ffIdxBump === _fxCacheBump) return _ffIdx;
    _ffIdx = (fxDeposits || []).map(function(e){
      return { e: e, p: _ffNorm(e && e.payer), v: _ffNorm(e && e.vendor) };
    });
    _ffIdxBump = _fxCacheBump;
    return _ffIdx;
  }
  function _ffDate(d){ return String(d || '').replace(/-/g, '.'); }
  function _ffWhen(ms){
    if(!ms) return '';
    var d = new Date(ms);
    return _ffDate(_fxD(d)) + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }
  function _ffState(e){        // [라벨, 색, 덧붙임]
    if(e.excluded) return ['제외', '#8a94a6', e.exAt ? ('제외 ' + _ffWhen(e.exAt)) : ''];
    if(e.held)     return ['보류', '#b45309', e.heldAt ? ('보류 ' + _ffWhen(e.heldAt)) : ''];
    if(e.vendor)   return [e.vendor, '#1B3A6B', (e.asgAt ? ('배정 ' + _ffWhen(e.asgAt) + (e.asgBy ? (' · ' + e.asgBy) : '')) : '')];
    return ['미배정', '#b45309', ''];
  }
  function _ffSuggest(q){      // 비슷한 이름 후보
    var nq = _ffNorm(q); if(nq.length < 2) return [];
    var head = nq.slice(0, 2), seen = {}, out = [];
    _ffBuild().forEach(function(r){
      [[r.e.payer, r.p], [r.e.vendor, r.v]].forEach(function(pair){
        var raw = pair[0], n = pair[1];
        if(!raw || !n || seen[raw]) return;
        if(n.indexOf(head) >= 0 || head.indexOf(n.slice(0, 2)) >= 0){ seen[raw] = 1; out.push(raw); }
      });
    });
    return out.slice(0, 10);
  }
  window.fxFindInput = function(v){
    _fxFindQ = String(v == null ? '' : v);
    _fxFindShow = 200;
    if(_fxFindTimer) clearTimeout(_fxFindTimer);
    _fxFindTimer = setTimeout(function(){ _fxFindTimer = null; _ffRender(); }, 200);
  };
  window.fxFindMore = function(){ _fxFindShow += 200; _ffRender(); };
  window.fxFindPick = function(name){
    _fxFindQ = String(name || ''); _fxFindShow = 200;
    var i = document.getElementById('fxFindInput'); if(i) i.value = _fxFindQ;
    _ffRender();
  };
  function _ffRender(){
    var host = document.getElementById('fxFindBody'); if(!host) return;
    var q = (_fxFindQ || '').trim();
    if(!q){
      host.innerHTML = '<div style="text-align:center;padding:52px 20px;color:#b6bec9;font-size:13px;line-height:2">'
        + '찾을 이름을 입력하세요.<br><span style="font-size:12px">통장에 찍힌 <b style="color:#5b7ba6">입금자 이름</b> 과 <b style="color:#5b7ba6">배정된 거래처</b> 를 함께 찾습니다.</span><br>'
        + '<span style="font-size:11.5px;color:#9ca3af">※ 출금 내역은 아직 보관하지 않아 검색되지 않습니다.</span></div>';
      return;
    }
    var nq = _ffNorm(q);
    if(!nq){ host.innerHTML = '<div style="text-align:center;padding:40px;color:#b6bec9;font-size:13px">찾을 이름을 입력하세요.</div>'; return; }
    var hits = _ffBuild().filter(function(r){ return (r.p && r.p.indexOf(nq) >= 0) || (r.v && r.v.indexOf(nq) >= 0); }).map(function(r){ return r.e; });
    hits.sort(function(a, b){ return (b.date || '') < (a.date || '') ? -1 : ((b.date || '') > (a.date || '') ? 1 : 0); });

    if(!hits.length){
      var sug = _ffSuggest(q);
      host.innerHTML = '<div style="border:1px solid #e3e9f0;background:#fbfcfe;padding:26px 20px;text-align:center">'
        + '<div style="font-size:14px;color:#14305c;font-weight:700">입출금 내역에 <b>' + esc(q) + '</b> 이(가) 없습니다.</div>'
        + '<div style="font-size:12px;color:#8a94a6;margin-top:7px;line-height:1.9">입금자 이름과 배정된 거래처를 모두 찾아봤습니다.<br>'
        + '출금 내역은 아직 보관하지 않아 검색되지 않습니다.</div>'
        + (sug.length ? ('<div style="margin-top:14px"><div style="font-size:11.5px;color:#8a94a6;margin-bottom:6px">혹시 이 이름인가요?</div>'
            + sug.map(function(n){ var r = String(n).replace(/'/g, "\\'");
                return '<button type="button" class="btn" style="margin:0 4px 5px 0;padding:3px 11px;font-size:12px" onclick="fxFindPick(\'' + esc(r) + '\')">' + esc(n) + '</button>'; }).join('')
            + '</div>') : '')
        + '</div>';
      return;
    }

    var sum = 0, nEx = 0, nHold = 0, nUn = 0, byV = {};
    hits.forEach(function(e){
      sum += Number(e.amount) || 0;
      if(e.excluded) nEx++;
      else if(e.held) nHold++;
      else if(e.vendor){ byV[e.vendor] = (byV[e.vendor] || 0) + 1; }
      else nUn++;
    });
    var vs = Object.keys(byV).sort(function(a, b){ return byV[b] - byV[a]; });
    var nAs = vs.reduce(function(t, v){ return t + byV[v]; }, 0);
    var parts = [];
    if(nAs) parts.push('<b style="color:#1B3A6B">배정 ' + _fxFmt(nAs) + '건</b>(' + esc(vs.slice(0, 3).map(function(v){ return v + ' ' + byV[v]; }).join(' · ')) + (vs.length > 3 ? (' 외 ' + (vs.length - 3) + '곳') : '') + ')');
    if(nEx) parts.push('<b style="color:#8a94a6">제외 ' + _fxFmt(nEx) + '건</b>');
    if(nHold) parts.push('<b style="color:#b45309">보류 ' + _fxFmt(nHold) + '건</b>');
    if(nUn) parts.push('<b style="color:#b45309">미배정 ' + _fxFmt(nUn) + '건</b>');

    var TH = 'padding:7px 8px;border-bottom:1px solid #d6deea;font-size:11.5px;color:#5b7ba6;font-weight:700;white-space:nowrap;text-align:left';
    var TD = 'padding:6px 8px;border-bottom:1px solid #eef1f4;font-size:12px;color:#1f2937;white-space:nowrap';
    var show = hits.slice(0, _fxFindShow);
    var rows = show.map(function(e){
      var st = _ffState(e);
      var acct = (e.obiz || e.biz || '');
      var moved = (e.obiz && e.biz && e.obiz !== e.biz) ? ('<span style="color:#9ca3af"> → ' + esc(e.biz) + ' 배정</span>') : '';
      var kind = (e.kind === 'note') ? ('어음' + (e.bank ? (' · ' + e.bank) : '')) : ('입금' + (e.bank ? (' · ' + e.bank) : ''));
      return '<tr>'
        + '<td style="' + TD + '">' + esc(_ffDate(e.date)) + '</td>'
        + '<td style="' + TD + ';color:#6b7280">' + esc(kind) + '</td>'
        + '<td style="' + TD + ';color:#6b7280">' + esc(acct) + moved + '</td>'
        + '<td style="' + TD + ';text-align:right;font-weight:600">' + _fxFmt(Number(e.amount) || 0) + '</td>'
        + '<td style="' + TD + '">' + esc(e.payer || '') + '</td>'
        + '<td style="' + TD + '"><span style="color:' + st[1] + ';font-weight:700">' + esc(st[0]) + '</span></td>'
        + '<td style="' + TD + ';color:#9ca3af;font-size:11.5px">' + esc(st[2]) + '</td>'
        + '</tr>';
    }).join('');

    host.innerHTML =
      '<div style="border:1px solid #d6deea;background:#fbfcfe;padding:10px 13px;margin-bottom:10px;line-height:1.9">'
        + '<div style="font-size:13.5px;color:#14305c"><b>' + esc(q) + '</b> — ' + _fxFmt(hits.length) + '건 · 합계 <b>' + _fxFmt(sum) + '</b>원</div>'
        + (parts.length ? ('<div style="font-size:12px;color:#374151">' + parts.join(' · ') + '</div>') : '')
      + '</div>'
      + '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;min-width:720px">'
        + '<thead><tr>'
          + '<th style="' + TH + '">거래일</th><th style="' + TH + '">구분</th><th style="' + TH + '">계좌 사업장</th>'
          + '<th style="' + TH + ';text-align:right">금액</th><th style="' + TH + '">입금자</th>'
          + '<th style="' + TH + '">처리</th><th style="' + TH + '">기록</th>'
        + '</tr></thead><tbody>' + rows + '</tbody></table></div>'
      + (hits.length > show.length
          ? ('<div style="text-align:center;margin-top:10px"><button type="button" class="btn" onclick="fxFindMore()">더보기 (' + _fxFmt(hits.length - show.length) + '건 남음)</button></div>')
          : '')
      + '<div style="font-size:11px;color:#9ca3af;margin-top:9px;line-height:1.8">※ 배정 시각·사람은 2026-11-03 이후 배정분부터 모두 남습니다. 그 전 자료는 되돌리기용으로 최근 분만 남아 있어 비어 있을 수 있습니다.<br>※ 출금 내역은 아직 보관하지 않아 검색되지 않습니다.</div>';
  }
"""

OPS = [
 # ① 하위탭 목록
 ["    var _ACCT=['fx','fxsum','fxup','cardsales','carduse'];   // r221: 입출금 탭 삭제 · r224 카드사용\n",
  "    var _ACCT=['fx','fxsum','fxfind','fxup','cardsales','carduse'];   // r221: 입출금 탭 삭제 · r224 카드사용 · r254 자료 검색\n",
  1, 'ACCT'],

 # ② 하위탭 버튼 (미수현황 옆)
 ['  <button class="sub-tab" data-page="fx">미수현황</button>\n',
  '  <button class="sub-tab" data-page="fx">미수현황</button>\n'
  '  <button class="sub-tab" data-page="fxfind">자료 검색</button><!-- r254 -->\n',
  1, 'SUBTAB'],

 # ③ pageMap
 ["fxup:'pageFx'", "fxup:'pageFx', fxfind:'pageFx'", 1, 'PAGEMAP'],

 # ④ switchPage 진입
 ["    if (page === 'fx' || page === 'fxsum' || page === 'fxup'){   // r214: 한 화면을 세 탭이 나눠 쓴다\n"
  "      _fxTab = (page==='fxsum') ? 'sum' : (page==='fxup' ? 'up' : 'ar');\n",
  "    if (page === 'fx' || page === 'fxsum' || page === 'fxup' || page === 'fxfind'){   // r214: 한 화면을 여러 탭이 나눠 쓴다 · r254 자료 검색\n"
  "      _fxTab = (page==='fxsum') ? 'sum' : (page==='fxup' ? 'up' : (page==='fxfind' ? 'find' : 'ar'));\n",
  1, 'SWITCH'],

 # ⑤ 검색 화면 분기 (ar 분기 바로 앞)
 ["    if(_fxTab==='ar'){\n      tb.innerHTML =\n        '<span class=\"inv-flat-label\">미수 현황</span>'",
  FIND + "    if(_fxTab==='ar'){\n      tb.innerHTML =\n        '<span class=\"inv-flat-label\">미수 현황</span>'",
  1, 'FIND_BRANCH'],

 # ⑥ 헬퍼
 ["  function renderFxPage(){\n", HELPERS + "  function renderFxPage(){\n", 1, 'HELPERS'],

 # ⑦ 배정 시각·사람은 지우지 않는다 (사용자 결정 11-03)
 ["  function _fxAsgClear(e){ delete e.asgBat; delete e.asgAt; delete e.asgBy; delete e.asgU; }\n",
  "  // r254: 되돌리기용 묶음 정보(asgBat·asgU)만 지우고, **언제·누가 배정했는지는 남긴다**.\n"
  "  //  (자료 검색에서 배정 이력을 보여 주기 위해 — 지우던 탓에 11,072건 중 124건만 남아 있었다)\n"
  "  function _fxAsgClear(e){ delete e.asgBat; delete e.asgU; }\n",
  1, 'ASG_KEEP'],
]

MARKER = ["<!-- test build r253 2026-11-03 -->", "<!-- test build r254 2026-11-03 -->"]

NEED = ["_fxTab==='find'", 'window.fxFindInput', '_ffBuild', "fxfind:'pageFx'", 'data-page="fxfind"', '_ffSuggest']
KEEP = ['_fxAsgBatches', 'window.fxAsgUndo', '_bkEnsureDaily', '_qsMergeFromServer']


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp:
        raise SystemExit('R254 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r254(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for need in NEED:
        if need not in s:
            raise SystemExit('R254 FAIL 누락: ' + need)
    for need in KEEP:
        if need not in s:
            raise SystemExit('R254 FAIL 사라짐: ' + need)
    if 'delete e.asgAt' in s:
        raise SystemExit('R254 FAIL 배정 시각을 아직 지우고 있다')
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f:
            s = f.read()
        s = apply_r254(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(s)
        print('r254 applied:', path)
