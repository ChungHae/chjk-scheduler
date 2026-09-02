# -*- coding: utf-8 -*-
# r170: 세 가지 수정 (사용자 보고 2026-08-31)
#
#  (1) 미배정 입금 검색창에 한글이 '씬' -> 'ㅆㅣㄴ' 으로 깨져 들어감
#      원인(실측): r169 검색이 입력할 때마다 _fxRenderUnasg() 로 패널을 innerHTML 통째 교체한다.
#        하니스로 확인 — 다시 그리기 전후의 #fxUnQ 가 서로 다른 DOM 요소(inputReplaced=true).
#        한글은 여러 자모가 모여 한 글자가 되는 '조합 중' 상태로 입력되는데, 그 도중에 입력칸이
#        새 것으로 갈리면 조합이 강제로 끊겨 자모가 낱개로 확정된다. (IME 조합 보호 코드 없었음)
#      수정: 조합 중(event.isComposing)에는 다시 그리지 않고, 조합이 끝나면(compositionend)
#        그때 한 번 거른다. 영문·숫자는 종전대로 즉시(180ms 디바운스) 동작.
#
#  (2) 일정 > 업체 업체명 검색이 느림
#      원인(실측): clxSearchInput 이 디바운스 없이 글자마다 _clxRender() 를 통째로 돌린다.
#        1,500곳 기준 글자당 11ms, 4,000곳 기준 21ms — 실제 PC·실데이터에서는 타이핑이 밀린다.
#        (매입매출 검색은 r151 에서 이미 180ms 디바운스를 넣었는데 업체 검색은 빠져 있었음)
#      수정: 같은 방식으로 180ms 디바운스 + 한글 조합 보호. 엔터/검색어 지우기는 즉시 반영.
#
#  (3) 업체 등록 창만 라운딩(둥근 모서리)이라 화면마다 버튼 모양이 달라 보임
#      원인(실측): 배정 흐름의 확인창·행 버튼은 전부 각짐(계산된 border-radius 0px)인데,
#        openAddClient 의 addClientOverlay 만 옛 디자인 그대로 — 카드 14px, 입력칸 8px,
#        버튼은 .btn 기본값 6px(#pageFx 밖이라 각지게 만드는 규칙이 안 걸림).
#      수정: 이 창을 현재 디자인(각진 형태)으로 통일. 카드/입력칸/버튼 전부 border-radius:0,
#        머리글도 showConfirmModal 과 같은 결로. 덤으로 모달·드롭다운 버튼을 각지게 하는
#        보호 규칙을 CSS 에 추가해 다른 경로가 남아 있어도 둥글게 나오지 않게 한다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R170 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r170(s, path):
    # ── (1) 미배정 검색창 IME 보호 ──
    s = rep(s,
        "  window.fxUnQInput = function(v){\n"
        "    if(_fxUnQTimer) clearTimeout(_fxUnQTimer);\n"
        "    _fxUnQTimer=setTimeout(function(){ _fxUnQTimer=null; _fxUnQ=String(v==null?'':v).trim(); _fxRenderUnasg(); }, 180);\n"
        "  };",
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
        1, 'FXUNQIME')

    s = rep(s,
        '''oninput="fxUnQInput(this.value)" style="width:190px;border:1px solid #d6deea !important;background:#fff;font-weight:400">''',
        '''oninput="fxUnQInput(this.value, event)" style="width:190px;border:1px solid #d6deea !important;background:#fff;font-weight:400">''',
        1, 'FXUNQATTR')

    # ── (2) 업체 검색 디바운스 + IME 보호 ──
    s = rep(s,
        "  window.clxSearchInput = function(v){ _clxQ = String(v||'').trim().toLowerCase(); _clxPage = 1; _clxRender(); };",
        "  // r170: 글자마다 목록을 통째로 다시 그리느라 타이핑이 밀렸다(4,000곳 기준 글자당 21ms).\n"
        "  //  매입매출 검색(r151)과 같은 180ms 디바운스 + 한글 조합 보호를 넣는다.\n"
        "  var _clxQTimer=null;\n"
        "  function _clxQApply(v){\n"
        "    if(_clxQTimer){ clearTimeout(_clxQTimer); _clxQTimer=null; }\n"
        "    _clxQ = String(v||'').trim().toLowerCase(); _clxPage = 1; _clxRender();\n"
        "  }\n"
        "  window.clxSearchInput = function(v, ev){\n"
        "    if(ev && ev.isComposing) return;   // 한글 조합 중에는 거르지 않는다\n"
        "    if(_clxQTimer) clearTimeout(_clxQTimer);\n"
        "    _clxQTimer=setTimeout(function(){ _clxQTimer=null; _clxQApply(v); }, 180);\n"
        "  };\n"
        "  window.clxSearchEnd = function(v){   // 조합 완료 / 엔터 — 즉시 반영\n"
        "    _clxQApply(v);\n"
        "  };",
        1, 'CLXDEBOUNCE')

    s = rep(s,
        """oninput="clxSearchInput(this.value)">""",
        """oninput="clxSearchInput(this.value, event)" onkeydown="if(event.key==='Enter'){event.preventDefault();clxSearchEnd(this.value);}">""",
        1, 'CLXATTR')

    # ── (3) 업체 등록 창을 각진 디자인으로 ──
    s = rep(s,
        """    ov.innerHTML='<div style="width:100%;max-width:380px;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 14px 44px rgba(27,58,107,.22)">'
      +'<div style="padding:16px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">'+(isEdit?'거래처 수정':'신규 업체 추가')+'</span><button class="btn" onclick="document.getElementById(\\'addClientOverlay\\').style.display=\\'none\\'" style="padding:4px 10px">닫기</button></div>'""",
        """    // r170: 다른 창(확인창 등)은 전부 각진 디자인인데 이 창만 둥글어서 버튼 모양이 달라 보였다.
    ov.innerHTML='<div style="width:100%;max-width:380px;background:#fff;border:1px solid #c8d2de;border-radius:0;overflow:hidden">'
      +'<div style="padding:9px 14px;border-bottom:1px solid #c8d2de;background:#f4f6f9;display:flex;justify-content:space-between;align-items:center;gap:8px"><span style="display:flex;align-items:center;gap:8px"><span style="width:3px;height:15px;background:#1a1a1a"></span><span style="font-size:13.5px;font-weight:700;color:#1a1a1a">'+(isEdit?'거래처 수정':'신규 업체 추가')+'</span></span><button type="button" onclick="document.getElementById(\\'addClientOverlay\\').style.display=\\'none\\'" style="padding:0 10px;height:24px;background:#fff;border:1px solid #c8d2de;border-radius:0;font-size:11.5px;color:#4b5563;cursor:pointer;font-family:inherit">닫기</button></div>'""",
        1, 'ACHEAD')

    s = rep(s,
        """style="width:100%;box-sizing:border-box;padding:8px 11px;border:1.5px solid #e5e5e5;border-radius:8px;font-size:13px;font-family:inherit"></div>'
      +'<div><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">""",
        """style="width:100%;box-sizing:border-box;padding:7px 10px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></div>'
      +'<div><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">""",
        1, 'ACIN1')

    s = rep(s,
        """placeholder="000-00-00000" style="width:100%;box-sizing:border-box;padding:8px 11px;border:1.5px solid #e5e5e5;border-radius:8px;font-size:13px;font-family:inherit"></div>'""",
        """placeholder="000-00-00000" style="width:100%;box-sizing:border-box;padding:7px 10px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></div>'""",
        1, 'ACIN2')

    s = rep(s,
        """      +'<div style="display:flex;gap:8px;justify-content:flex-end;padding:0 20px 18px">'
      +'<button class="btn" onclick="document.getElementById(\\'addClientOverlay\\').style.display=\\'none\\'">닫기</button>'
      +'<button class="btn btn-primary" id="acNewSave">'+(isEdit?'저장':'추가')+'</button>'
      +'</div></div>';""",
        """      +'<div style="display:flex;gap:6px;justify-content:flex-end;padding:0 14px 14px">'
      +'<button type="button" onclick="document.getElementById(\\'addClientOverlay\\').style.display=\\'none\\'" style="padding:0 12px;height:28px;background:#fff;border:1px solid #c8d2de;border-radius:0;font-size:12px;color:#4b5563;cursor:pointer;font-family:inherit">닫기</button>'
      +'<button type="button" id="acNewSave" style="padding:0 14px;height:28px;border:1px solid #1B3A6B;background:#1B3A6B;color:#fff;border-radius:0;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit">'+(isEdit?'저장':'추가')+'</button>'
      +'</div></div>';""",
        1, 'ACBTN')

    # ── 조합 완료(compositionend) 는 addEventListener 로만 붙는다 ──
    #  주의: oncompositionend 는 HTML 인라인 속성으로 지원되지 않는다(실측 — 속성은 남지만 호출 안 됨).
    #  한글은 조합이 끝나야 값이 확정되므로, 이걸 안 붙이면 한글 검색이 아예 안 걸린다.
    s = rep(s,
        "    if(_fxUnQ){\n"
        "      var _qi=document.getElementById('fxUnQ');\n"
        "      if(_qi && document.activeElement!==_qi){\n"
        "        try{ _qi.focus(); _qi.setSelectionRange(_qi.value.length, _qi.value.length); }catch(_e){}\n"
        "      }\n"
        "    }",
        "    var _qi=document.getElementById('fxUnQ');\n"
        "    if(_qi && !_qi.__imeBound){\n"
        "      _qi.__imeBound=1;\n"
        "      _qi.addEventListener('compositionend', function(){ fxUnQEnd(this.value); });\n"
        "    }\n"
        "    if(_fxUnQ && _qi && document.activeElement!==_qi){\n"
        "      try{ _qi.focus(); _qi.setSelectionRange(_qi.value.length, _qi.value.length); }catch(_e){}\n"
        "    }",
        1, 'FXUNQBIND')

    s = rep(s,
        "  window.renderClientsPage = function(){",
        "  // r170: 업체 검색창의 한글 조합 완료 처리 (인라인 속성으로는 안 붙는다)\n"
        "  function _clxBindIme(){\n"
        "    var el=document.getElementById('clxSearch');\n"
        "    if(!el || el.__imeBound) return;\n"
        "    el.__imeBound=1;\n"
        "    el.addEventListener('compositionend', function(){ clxSearchInput(this.value); });\n"
        "  }\n"
        "  window.renderClientsPage = function(){\n"
        "    _clxBindIme();",
        1, 'CLXBIND')

    # 모달·드롭다운 버튼 각지게 (다른 경로가 남아 있어도 둥글게 안 나오도록)
    s = rep(s,
        "    #invExcelGuideOverlay .btn { border-radius:0 !important; }",
        "    #invExcelGuideOverlay .btn { border-radius:0 !important; }\n"
        "    /* r170: 창(모달)과 떠 있는 목록의 버튼·입력칸은 항상 각지게 — 화면마다 모양이 달라 보이지 않도록 */\n"
        "    #confirmOverlay button, #infoOverlay button, #promptOverlay button,\n"
        "    #addClientOverlay button, #addClientOverlay input[type=text],\n"
        "    #fxUnDdG button, #fxUnasg button { border-radius:0 !important; }",
        1, 'CSSGUARD')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r170(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r169 2026-08-31 -->') == 1
            s = s.replace('<!-- test build r169 2026-08-31 -->', '<!-- test build r170 2026-08-31 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
