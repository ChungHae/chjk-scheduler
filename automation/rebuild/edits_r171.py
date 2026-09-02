# -*- coding: utf-8 -*-
# r171: 미배정 검색창 — 한글이 계속 깨지는 문제의 뿌리를 없애고, 지웠을 때 커서 유지
#
#  r170 은 증상만 눌렀다. 뿌리는 그대로였다:
#    _fxRenderUnasg() 가 host.innerHTML 을 통째로 갈아끼우는데 검색창이 그 안에 있다.
#    즉 걸러서 다시 그릴 때마다 입력칸이 "새 요소"로 바뀐다.
#    - r170 은 조합 중에는 안 그리게 막았지만, 한 글자가 끝나 다시 그리는 그 순간
#      사용자가 이미 다음 글자를 치고 있으면 그 조합이 또 끊긴다 -> 두 글자 이상 연속으로
#      치면 여전히 깨진다(사용자 보고).
#    - 글자를 전부 지우면 _fxUnQ 가 '' 이라 포커스 복원 조건(if(_fxUnQ))에 안 걸려
#      커서가 사라진다(사용자 보고).
#
#  근본 수정: 검색창을 다시 그리는 영역 밖으로 뺀다.
#    #fxUnasg
#      ├─ #fxUnQBar   ← 딱 한 번 만들고 다시는 건드리지 않는다(입력칸이 살아 있음)
#      └─ #fxUnBody   ← 기존 내용 전부. 여기만 innerHTML 로 다시 그린다.
#    입력칸이 교체되지 않으므로
#      · 조합이 끊길 일이 없다(몇 글자를 연속으로 치든 그대로 들어간다)
#      · 포커스·커서 위치가 그대로다(지워도 커서 유지)
#      · 포커스 복원 꼼수도 필요 없다.
#    입력칸이 안정적이니 조합 중이라고 걸러내기를 미룰 이유도 없다 -> isComposing 가드를 없애고
#    입력이 있을 때마다(200ms 디바운스) 그대로 거른다. 조합 완료 시에는 즉시 한 번 더.
#    건수 안내는 텍스트만 갈아끼운다(요소 교체 없음).
#
#  업체 검색창(#clxSearch)은 정적 마크업이라 애초에 교체되지 않는다.
#    다만 r170 의 isComposing 가드 때문에 한글은 조합이 끝나야만 반영됐다.
#    조합 중에도 반영되도록 가드를 없앤다(입력칸이 안정적이라 안전).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R171 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r171(s, path):
    # (1) 입력 핸들러: 조합 가드 제거 + 디바운스 200ms. 값은 입력칸에서 직접 읽는다.
    s = rep(s,
        "  // r170: 한글 조합 중에 패널을 다시 그리면 입력칸이 새 것으로 갈려 조합이 끊긴다\n"
        "  //  ('씬' -> 'ㅆㅣㄴ'). 조합이 끝난 뒤에만 거른다.\n"
        "  window.fxUnQInput = function(v, ev){\n"
        "    if(ev && ev.isComposing) return;   // 조합 중 — 아무것도 하지 않는다\n"
        "    if(_fxUnQTimer) clearTimeout(_fxUnQTimer);\n"
        "    _fxUnQTimer=setTimeout(function(){ _fxUnQTimer=null; _fxUnQ=String(v==null?'':v).trim(); _fxRenderUnasg(); }, 180);\n"
        "  };\n"
        "  // 조합이 끝나는 순간(한 글자 완성)에 그 값으로 거른다\n"
        "  window.fxUnQEnd = function(v){\n"
        "    if(_fxUnQTimer) clearTimeout(_fxUnQTimer);\n"
        "    _fxUnQTimer=setTimeout(function(){ _fxUnQTimer=null; _fxUnQ=String(v==null?'':v).trim(); _fxRenderUnasg(); }, 180);\n"
        "  };",
        "  // r171: 검색창은 다시 그리는 영역(#fxUnBody) 밖에 있으므로 입력 중에 교체되지 않는다.\n"
        "  //  그래서 조합(한글) 중에도 그냥 걸러도 안전하다 — 조합이 끊길 일이 없다.\n"
        "  function _fxUnQRun(){\n"
        "    _fxUnQTimer=null;\n"
        "    var el=document.getElementById('fxUnQ');\n"
        "    var v=el ? el.value : '';\n"
        "    var nq=String(v==null?'':v).trim();\n"
        "    if(nq===_fxUnQ) return;      // 값이 그대로면 굳이 다시 그리지 않는다\n"
        "    _fxUnQ=nq; _fxRenderUnasg();\n"
        "  }\n"
        "  window.fxUnQInput = function(){\n"
        "    if(_fxUnQTimer) clearTimeout(_fxUnQTimer);\n"
        "    _fxUnQTimer=setTimeout(_fxUnQRun, 200);\n"
        "  };\n"
        "  window.fxUnQEnd = function(){   // 조합 완료 — 곧바로 반영\n"
        "    if(_fxUnQTimer) clearTimeout(_fxUnQTimer);\n"
        "    _fxUnQTimer=setTimeout(_fxUnQRun, 0);\n"
        "  };",
        1, 'UNQHANDLER')

    # (2) 검색창을 고정 영역으로 분리 + 본문만 다시 그림
    s = rep(s,
        "  function _fxRenderUnasg(){\n"
        "    var host=document.getElementById('fxUnasg'); if(!host) return;\n"
        "    _fxUnList = fxDeposits.filter(function(e){ return !e.vendor && !e.excluded && !e.held; });",
        "  // r171: 검색창(#fxUnQBar)은 한 번만 만들고 본문(#fxUnBody)만 다시 그린다.\n"
        "  //  입력칸이 교체되지 않아야 한글 조합이 안 끊기고 커서도 안 사라진다.\n"
        "  function _fxUnShell(host){\n"
        "    var bar=host.querySelector('#fxUnQBar');\n"
        "    if(!bar){\n"
        "      host.innerHTML='<div id=\"fxUnQBar\" style=\"display:none;align-items:center;gap:8px;flex-wrap:wrap;"
        "background:#fff;border:1px solid #d6deea;border-bottom:0;padding:9px 14px;font-size:12.5px\"></div>'\n"
        "        + '<div id=\"fxUnBody\"></div>';\n"
        "      bar=host.querySelector('#fxUnQBar');\n"
        "      bar.innerHTML='<span style=\"font-weight:700;color:#d97706\">미배정 입금</span>'\n"
        "        + '<input type=\"text\" id=\"fxUnQ\" class=\"q-flat\" placeholder=\"입금자·날짜·금액 검색…\" autocomplete=\"off\" "
        "style=\"width:210px;border:1px solid #d6deea !important;background:#fff;font-weight:400\">'\n"
        "        + '<button type=\"button\" id=\"fxUnQClr\" class=\"btn\" style=\"font-size:11px;padding:2px 10px;border:1px solid #d6deea;"
        "color:#6b7280;background:#fff;font-weight:400\">지우기</button>'\n"
        "        + '<span id=\"fxUnQInfo\" style=\"color:#8a94a6;font-weight:400\"></span>';\n"
        "      var el=bar.querySelector('#fxUnQ');\n"
        "      el.addEventListener('input', function(){ fxUnQInput(); });\n"
        "      el.addEventListener('compositionend', function(){ fxUnQEnd(); });\n"
        "      el.addEventListener('keydown', function(ev){ if(ev.key==='Escape'){ this.value=''; fxUnQEnd(); } });\n"
        "      bar.querySelector('#fxUnQClr').addEventListener('click', function(){\n"
        "        var q=document.getElementById('fxUnQ');\n"
        "        if(q){ q.value=''; try{ q.focus(); }catch(_e){} }   // 지워도 커서는 검색창에 남는다\n"
        "        fxUnQEnd();\n"
        "      });\n"
        "    }\n"
        "    return { bar:bar, body:host.querySelector('#fxUnBody') };\n"
        "  }\n"
        "  function _fxRenderUnasg(){\n"
        "    var host=document.getElementById('fxUnasg'); if(!host) return;\n"
        "    _fxUnList = fxDeposits.filter(function(e){ return !e.vendor && !e.excluded && !e.held; });",
        1, 'UNSHELL')

    # 빈 상태: 검색창까지 지우지 않도록 (검색 중이면 껍데기 유지)
    s = rep(s,
        "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length && !_fxAsgBatches().length && !_fxNoBizAssigned().length){ host.innerHTML=''; return; }",
        "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length && !_fxAsgBatches().length && !_fxNoBizAssigned().length){\n"
        "      if(!_fxUnQ){ host.innerHTML=''; }   // 검색 중이면 껍데기(검색창)를 남겨 둔다\n"
        "      return;\n"
        "    }",
        1, 'UNEMPTY')

    # (3) 패널 머리에서 검색창·지우기 제거 (이제 고정 바에 있다)
    s = rep(s,
        "        + '<div style=\"padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706;display:flex;align-items:center;gap:8px;flex-wrap:wrap\">미배정 입금 '+_fxFmt(_unAll)+'건'\n"
        "        + (_fxUnQ?'<span style=\"font-weight:400;color:#b45309\">(검색 '+_fxFmt(_fxUnList.length)+'건)</span>':'')\n"
        "        + '<input type=\"text\" id=\"fxUnQ\" class=\"q-flat\" placeholder=\"입금자·날짜·금액 검색…\" autocomplete=\"off\" value=\"'+esc(_fxUnQ)+'\" oninput=\"fxUnQInput(this.value, event)\" style=\"width:190px;border:1px solid #d6deea !important;background:#fff;font-weight:400\">'\n"
        "        + (_fxUnQ?'<button type=\"button\" class=\"btn\" onclick=\"fxUnQClear()\" style=\"font-size:11px;padding:2px 10px;border:1px solid #d6deea;color:#6b7280;background:#fff;font-weight:400\">검색 지우기</button>':'')",
        "        + '<div style=\"padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706;display:flex;align-items:center;gap:8px;flex-wrap:wrap\">미배정 입금 '+_fxFmt(_unAll)+'건'\n"
        "        + (_fxUnQ?'<span style=\"font-weight:400;color:#b45309\">(검색 '+_fxFmt(_fxUnList.length)+'건)</span>':'')",
        1, 'UNHEADCLEAN')

    # (4) 마무리: 본문만 교체 + 고정 바 갱신(요소 교체 없음)
    s = rep(s,
        "    host.innerHTML=html;\n"
        "    // r169: innerHTML 로 다시 그리면 포커스가 날아가므로 검색 중이면 되돌려 준다.\n"
        "    var _qi=document.getElementById('fxUnQ');\n"
        "    if(_qi && !_qi.__imeBound){\n"
        "      _qi.__imeBound=1;\n"
        "      _qi.addEventListener('compositionend', function(){ fxUnQEnd(this.value); });\n"
        "    }\n"
        "    if(_fxUnQ && _qi && document.activeElement!==_qi){\n"
        "      try{ _qi.focus(); _qi.setSelectionRange(_qi.value.length, _qi.value.length); }catch(_e){}\n"
        "    }\n"
        "  }",
        "    // r171: 본문만 갈아끼운다. 검색창은 건드리지 않으므로 조합·커서가 그대로 유지된다.\n"
        "    var _sh=_fxUnShell(host);\n"
        "    _sh.body.innerHTML=html;\n"
        "    _sh.bar.style.display = _unAll ? 'flex' : 'none';\n"
        "    var _inf=document.getElementById('fxUnQInfo');\n"
        "    if(_inf) _inf.textContent = _fxUnQ\n"
        "      ? ('전체 '+_fxFmt(_unAll)+'건 중 '+_fxFmt(_fxUnList.length)+'건 일치')\n"
        "      : ('전체 '+_fxFmt(_unAll)+'건 — 이름·날짜·금액으로 좁혀보세요');\n"
        "    var _clr=document.getElementById('fxUnQClr');\n"
        "    if(_clr) _clr.style.visibility = _fxUnQ ? 'visible' : 'hidden';\n"
        "  }",
        1, 'UNTAIL')

    # (5) 옛 fxUnQClear 는 고정 바 버튼으로 대체 — 남아 있어도 되게 값만 비우도록 정리
    s = rep(s,
        "  window.fxUnQClear = function(){\n"
        "    if(_fxUnQTimer){ clearTimeout(_fxUnQTimer); _fxUnQTimer=null; }\n"
        "    _fxUnQ=''; _fxRenderUnasg();\n"
        "  };",
        "  window.fxUnQClear = function(){\n"
        "    var q=document.getElementById('fxUnQ');\n"
        "    if(q){ q.value=''; try{ q.focus(); }catch(_e){} }\n"
        "    if(_fxUnQTimer){ clearTimeout(_fxUnQTimer); _fxUnQTimer=null; }\n"
        "    _fxUnQ=''; _fxRenderUnasg();\n"
        "  };",
        1, 'UNQCLEAR')

    # (6) 업체 검색: 조합 가드 제거 (입력칸이 정적이라 교체되지 않는다)
    s = rep(s,
        "  window.clxSearchInput = function(v, ev){\n"
        "    if(ev && ev.isComposing) return;   // 한글 조합 중에는 거르지 않는다\n"
        "    if(_clxQTimer) clearTimeout(_clxQTimer);\n"
        "    _clxQTimer=setTimeout(function(){ _clxQTimer=null; _clxQApply(v); }, 180);\n"
        "  };",
        "  // r171: 이 입력칸은 정적 마크업이라 목록을 다시 그려도 교체되지 않는다.\n"
        "  //  따라서 조합 중에도 그냥 걸러도 안전하다(조합이 끊기지 않음).\n"
        "  window.clxSearchInput = function(v, ev){\n"
        "    if(_clxQTimer) clearTimeout(_clxQTimer);\n"
        "    _clxQTimer=setTimeout(function(){ _clxQTimer=null; _clxQApply(v); }, 200);\n"
        "  };",
        1, 'CLXNOGUARD')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r171(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r170 2026-08-31 -->') == 1
            s = s.replace('<!-- test build r170 2026-08-31 -->', '<!-- test build r171 2026-08-31 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
