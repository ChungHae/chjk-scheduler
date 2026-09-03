# -*- coding: utf-8 -*-
# r173: 조정 날짜 — 타이핑(r172)은 그대로 두고 달력 선택도 되게
#
#  r172 에서 input[type=date] 를 연/월/일 세 칸으로 바꾸면서 달력 아이콘이 사라졌다.
#  사용자 요청: 지금 타이핑 기능은 유지하면서 달력으로도 고를 수 있게.
#
#  방식: 세 칸 옆에 진짜 input[type=date] 를 '달력 아이콘 크기'로만 놓는다.
#    · 브라우저가 그려주는 달력 아이콘을 그대로 쓰므로 별도 달력 UI를 만들 필요가 없다.
#    · 클릭하면 네이티브 달력이 열린다. showPicker() 가 있으면 그걸로 열고(더 확실),
#      없으면 아이콘 클릭 자체로 열린다.
#    · tabindex="-1" — Tab 은 연/월/일 세 칸만 돈다(r172 동작 유지).
#    · 달력에서 고르면 세 칸에 채워지고, 반대로 타이핑하면 달력의 기준 날짜도 따라간다(양방향).
#  저장은 종전대로 _fxAdjDateVal() 이 세 칸을 읽는다 — 즉 달력은 '세 칸을 채워주는 보조 수단'이고
#  값의 출처는 하나뿐이라 두 곳이 어긋날 일이 없다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R173 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r173(s, path):
    # (1) 마크업: 세 칸 뒤에 달력 입력칸 추가
    s = rep(s,
        "      + '<input type=\"text\" class=\"fxdt\" data-p=\"d\" maxlength=\"2\" inputmode=\"numeric\" autocomplete=\"off\" value=\"'+p2(dt.getDate())+'\" title=\"일\" style=\"'+S+';width:32px\">'\n"
        "      + '</span>';",
        "      + '<input type=\"text\" class=\"fxdt\" data-p=\"d\" maxlength=\"2\" inputmode=\"numeric\" autocomplete=\"off\" value=\"'+p2(dt.getDate())+'\" title=\"일\" style=\"'+S+';width:32px\">'\n"
        "      // r173: 달력으로도 고를 수 있게. 브라우저가 그려주는 달력 아이콘만 보이도록 폭을 줄여 놓는다.\n"
        "      //  Tab 순서에서는 빠진다(tabindex=-1) — Tab 은 연/월/일만 돈다.\n"
        "      + '<input type=\"date\" class=\"fxdtpick\" tabindex=\"-1\" title=\"달력에서 고르기\" value=\"'+dt.getFullYear()+'-'+p2(dt.getMonth()+1)+'-'+p2(dt.getDate())+'\"'\n"
        "      +   ' style=\"height:24px;width:26px;box-sizing:border-box;padding:0 1px;margin-left:4px;border:1px solid #cdd8e6;border-radius:0;background:#fff;color:transparent;font-family:inherit;cursor:pointer\">'\n"
        "      + '</span>';",
        1, 'PICKHTML')

    # (2) 바인딩: 달력 -> 세 칸, 세 칸 -> 달력 (양방향)
    s = rep(s,
        "  function _fxAdjDateBind(){\n"
        "    var box=document.getElementById('fxAdjDate'); if(!box || box.__dtb) return; box.__dtb=1;\n"
        "    var els=[].slice.call(box.querySelectorAll('.fxdt'));",
        "  // r173: 타이핑한 값을 달력의 기준 날짜에도 반영해 둔다(달력을 열면 그 달이 보이게).\n"
        "  function _fxAdjDateSyncPick(){\n"
        "    var box=document.getElementById('fxAdjDate'); if(!box) return;\n"
        "    var p=box.querySelector('.fxdtpick'); if(!p) return;\n"
        "    try{ p.value = _fxAdjDateVal() || ''; }catch(_e){}\n"
        "  }\n"
        "  function _fxAdjDateBind(){\n"
        "    var box=document.getElementById('fxAdjDate'); if(!box || box.__dtb) return; box.__dtb=1;\n"
        "    var els=[].slice.call(box.querySelectorAll('.fxdt'));\n"
        "    // 달력에서 고르면 세 칸을 채운다. 저장은 늘 세 칸에서 읽으므로 값의 출처는 하나뿐이다.\n"
        "    var pick=box.querySelector('.fxdtpick');\n"
        "    if(pick){\n"
        "      pick.addEventListener('change', function(){\n"
        "        var m=String(this.value||'').match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);\n"
        "        if(!m) return;\n"
        "        var g=function(p){ return box.querySelector('.fxdt[data-p=\"'+p+'\"]'); };\n"
        "        if(g('y')) g('y').value=m[1];\n"
        "        if(g('m')) g('m').value=m[2];\n"
        "        if(g('d')) g('d').value=m[3];\n"
        "      });\n"
        "      // 아이콘 클릭으로도 열리지만, showPicker 가 있으면 더 확실하게 열어 준다\n"
        "      pick.addEventListener('click', function(){ try{ if(this.showPicker) this.showPicker(); }catch(_e){} });\n"
        "    }",
        1, 'PICKBIND')

    # (3) 타이핑·화살표로 값이 바뀔 때마다 달력 기준 날짜 동기화
    s = rep(s,
        "        if(this.value.length>=mx && idx<els.length-1) els[idx+1].focus();   // 다 채우면 다음 칸\n"
        "      });",
        "        if(this.value.length>=mx && idx<els.length-1) els[idx+1].focus();   // 다 채우면 다음 칸\n"
        "        _fxAdjDateSyncPick();\n"
        "      });",
        1, 'SYNC1')

    s = rep(s,
        "          try{ this.select(); }catch(_e){}\n"
        "          return;\n"
        "        }\n"
        "        if(k==='Enter'){ ev.preventDefault(); fxAdjSave(); }",
        "          try{ this.select(); }catch(_e){}\n"
        "          _fxAdjDateSyncPick();\n"
        "          return;\n"
        "        }\n"
        "        if(k==='Enter'){ ev.preventDefault(); fxAdjSave(); }",
        1, 'SYNC2')

    s = rep(s,
        "        if(p==='m'){ n=Math.min(12,Math.max(1,n)); this.value=(n<10?'0':'')+n; }\n"
        "        else if(p==='d'){ n=Math.min(31,Math.max(1,n)); this.value=(n<10?'0':'')+n; }\n"
        "      });",
        "        if(p==='m'){ n=Math.min(12,Math.max(1,n)); this.value=(n<10?'0':'')+n; }\n"
        "        else if(p==='d'){ n=Math.min(31,Math.max(1,n)); this.value=(n<10?'0':'')+n; }\n"
        "        _fxAdjDateSyncPick();\n"
        "      });",
        1, 'SYNC3')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r173(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r172 2026-08-31 -->') == 1
            s = s.replace('<!-- test build r172 2026-08-31 -->', '<!-- test build r173 2026-08-31 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
