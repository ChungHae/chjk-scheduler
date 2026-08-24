# -*- coding: utf-8 -*-
# r137: [미배정 입금 — 보류(건너뛰기)]
#  아무리 봐도 모르는 입금은 "보류"로 넘겨두고, 나중에 보류 목록에서 그대로 다시
#  확인 요청을 받는 흐름.
#  - 미배정 행에 [보류] 버튼 (지정·제외 옆, 회색)
#  - 보류한 입금은 미배정 목록에서 빠지고 "보류한 입금 N건 — 다음에 다시 확인"
#    섹션에 쌓임 (펼치면 동일한 정보 + [다시 확인]/[제외] 버튼)
#  - [전체 다시 확인] = 보류 전부 미배정으로 복귀
#  - "별칭 다시 적용"은 보류 건도 검사해서 별칭·업체명이 생기면 자동 배정(보류 해제)
#  - held 플래그는 입금 레코드에 저장(Firebase 블롭) → 재업로드에도 유지

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R137 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r137(s, path):
    # (1) 목록 분리: 미배정 = 보류 아님 / 보류 목록 추가
    s = rep(s, "    _fxUnList = fxDeposits.filter(function(e){ return !e.vendor && !e.excluded; });",
            """    _fxUnList = fxDeposits.filter(function(e){ return !e.vendor && !e.excluded && !e.held; });
    _fxHeldList = fxDeposits.filter(function(e){ return !e.vendor && !e.excluded && e.held; });
    _fxHeldList.sort(function(a,b){ return a.date<b.date?1:a.date>b.date?-1:0; });""", 1, 'LISTS')
    s = rep(s, "    if(!_fxUnList.length && !_fxExList.length && !Object.keys(fxAlias).length){ host.innerHTML=''; return; }",
            "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length){ host.innerHTML=''; return; }", 1, 'EMPTY')

    # (2) 미배정 행에 [보류] 버튼
    s = rep(s, """          +   '<button type="button" class="btn" onclick="fxExcludeDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #dc2626;color:#dc2626;background:#fff">제외</button>'""",
            """          +   '<button type="button" class="btn" onclick="fxHoldDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;color:#6b7280;background:#fff" title="지금은 모르겠음 — 나중에 다시 확인">보류</button>'
          +   '<button type="button" class="btn" onclick="fxExcludeDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #dc2626;color:#dc2626;background:#fff">제외</button>'""", 1, 'HOLDBTN')

    # (3) 보류 섹션 (제외 섹션 앞)
    s = rep(s, "    if(_fxExList.length){",
            r"""    if(_fxHeldList.length){
      html += '<div style="margin-top:8px;font-size:11.5px;color:#b45309;font-weight:700">보류한 입금 '+_fxHeldList.length+'건 — 다음에 다시 확인 '
        + '<button type="button" class="btn" onclick="fxHeldToggle()" style="font-size:11px;padding:2px 10px;border:1px solid #d6deea;color:#6b7280;background:#fff;font-weight:400">'+(_fxHeldOpen?'접기':'보기')+'</button>'
        + ' <button type="button" class="btn" onclick="fxUnholdAll()" style="font-size:11px;padding:2px 10px;border:1px solid #b45309;color:#b45309;background:#fff;font-weight:400">전체 다시 확인</button></div>';
      if(_fxHeldOpen){
        var hrows=_fxHeldList.slice(0,300).map(function(e,i){
          return '<tr>'
            + '<td style="'+TD+';text-align:center;color:#6b7280">'+e.biz+'</td>'
            + '<td style="'+TD+';color:#6b7280">'+e.date+'</td>'
            + '<td style="'+TD+';text-align:center;color:#6b7280">'+esc(e.bank||'')+(e.kind==='note'?' <span style="font-size:10.5px;font-weight:700;color:#7c3aed;border:1px solid #7c3aed;padding:0 5px">어음</span>':'')+'</td>'
            + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(e.payer||'')+'</td>'
            + '<td style="'+TD+';text-align:right;font-weight:700">'+_fxFmt(e.amount)+'</td>'
            + '<td style="'+TD+'"><div style="display:flex;gap:6px;align-items:center">'
            +   '<button type="button" class="btn" onclick="fxUnholdDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">다시 확인</button>'
            +   '<button type="button" class="btn" onclick="fxExcludeHeld('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #dc2626;color:#dc2626;background:#fff">제외</button>'
            + '</div></td></tr>';
        }).join('');
        html += '<div style="margin-top:6px;background:#fff;border:1px solid #f0d9b8;max-height:300px;overflow:auto"><table style="width:100%;border-collapse:collapse"><tbody>'+hrows+'</tbody></table></div>';
      }
    }
    if(_fxExList.length){""", 1, 'HELDSEC')

    # (4) 핸들러 + 상태
    s = rep(s, "  var _fxUnList=[], _fxExList=[], _fxShowExcl=false;",
            "  var _fxUnList=[], _fxExList=[], _fxHeldList=[], _fxShowExcl=false, _fxHeldOpen=false;", 1, 'STATE')
    s = rep(s, "  window.fxExcludeDep = function(i){",
            """  window.fxHoldDep = function(i){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 사용할 수 없습니다.'); return; }
    var d=_fxUnList[i]; if(!d) return;
    d.held=true;
    _fxSaveBig().catch(function(_e){});
    _fxRenderUnasg();
  };
  window.fxHeldToggle = function(){ _fxHeldOpen=!_fxHeldOpen; _fxRenderUnasg(); };
  window.fxUnholdDep = function(i){
    var d=_fxHeldList[i]; if(!d) return;
    delete d.held;
    _fxSaveBig().catch(function(_e){});
    _fxRenderUnasg();
  };
  window.fxUnholdAll = function(){
    _fxHeldList.forEach(function(e){ delete e.held; });
    _fxSaveBig().catch(function(_e){});
    _fxRenderUnasg();
  };
  window.fxExcludeHeld = function(i){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 제외할 수 없습니다.'); return; }
    var d=_fxHeldList[i]; if(!d) return;
    d.excluded=true; delete d.held;
    _fxSaveBig().catch(function(_e){});
    _fxRenderUnasg();
  };
  window.fxExcludeDep = function(i){""", 1, 'HANDLERS')

    # (5) 별칭 다시 적용: 배정 성공 시 보류 해제
    s = rep(s, "      if(v){ e.vendor=v; e.vbiz=_fxClientVbiz(v, e.biz); n++; }",
            "      if(v){ e.vendor=v; e.vbiz=_fxClientVbiz(v, e.biz); delete e.held; n++; }", 1, 'REAPPLY')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r137(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r136 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r136 2026-08-24 -->', '<!-- test build r137 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
