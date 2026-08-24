# -*- coding: utf-8 -*-
# r132: [미배정 입금 — 거래처 선택창 디자인 통일]
#  - 브라우저 기본 datalist → 견적 화면 거래처 검색과 동일한 앱 공통 드롭다운
#    (흰 배경·#d6e4f5 테두리·그림자·호버 하이라이트·거래처명+사업자번호 표기)
#  - 목록 = 해당 사업장의 매입매출에 등록된 거래처(계산서 상호 + 이미 배정된 입금 거래처)
#  - 항목 클릭 = 즉시 지정 / Enter = 검색 첫 항목 지정 (프로젝트 업체 검색과 동일 규칙)
#  - 표 스크롤에 잘리지 않도록 드롭다운은 화면 기준(fixed)으로 띄우고 아래 공간이
#    부족하면 위로 펼침

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R132 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, a, b, new, label):
    if s.count(a) != 1 or s.count(b) != 1: raise SystemExit('R132 FAIL cut %s (a:%d b:%d)' % (label, s.count(a), s.count(b)))
    i = s.index(a); j = s.index(b)
    if j <= i: raise SystemExit('R132 FAIL cut order %s' % label)
    return s[:i] + new + s[j:]

def apply_r132(s, path):
    # ── (1) 드롭다운 헬퍼 (미배정 패널 앞) ──
    HELPERS = r"""  // ── r132: 미배정 거래처 선택 — 앱 공통 드롭다운 ──
  function _fxVendorOpts(biz){
    var m={};
    fxSalesInv.forEach(function(e){ if(e.biz===biz && e.vendor){ if(!(e.vendor in m) || (!m[e.vendor] && e.vbiz)) m[e.vendor]=e.vbiz||''; } });
    fxDeposits.forEach(function(e){ if(e.biz===biz && e.vendor && !(e.vendor in m)) m[e.vendor]=e.vbiz||''; });
    return Object.keys(m).sort(function(a,b){ return a.localeCompare(b,undefined,{numeric:true,sensitivity:'base'}); })
      .map(function(n){ return {name:n, vbiz:m[n]}; });
  }
  window.fxUnDdHide = function(){ var dd=document.getElementById('fxUnDdG'); if(dd) dd.style.display='none'; };
  window.fxUnDdRender = function(i){
    var inp=document.getElementById('fxUnV'+i); if(!inp) return;
    var e=_fxUnList[i]; if(!e) return;
    var dd=document.getElementById('fxUnDdG');
    if(!dd){
      dd=document.createElement('div');
      dd.id='fxUnDdG';
      dd.style.cssText='display:none;position:fixed;width:300px;background:#fff;border:1px solid #d6e4f5;border-radius:8px;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:240px;overflow:auto;z-index:100060';
      document.body.appendChild(dd);
      dd.addEventListener('mousedown', function(ev){ ev.preventDefault(); });  // blur 방지 → 항목 클릭 보장
    }
    var r=inp.getBoundingClientRect();
    dd.style.left=r.left+'px';
    if(window.innerHeight - r.bottom < 250){ dd.style.top='auto'; dd.style.bottom=(window.innerHeight - r.top + 2)+'px'; }
    else { dd.style.bottom='auto'; dd.style.top=(r.bottom + 2)+'px'; }
    var q=String(inp.value||'').trim().toLowerCase();
    var opts=_fxVendorOpts(e.biz);
    if(q) opts=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    opts=opts.slice(0,60);
    if(!opts.length){
      dd.innerHTML='<div style="padding:9px 12px;color:#bbb;font-size:12.5px">'+(q?'일치하는 거래처 없음':'등록된 거래처 없음')+'</div>';
    } else {
      dd.innerHTML=opts.map(function(o){
        var rn=String(o.name).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        return '<div onclick="fxPickVend('+i+',\''+rn+'\')" style="padding:8px 12px;border-bottom:1px solid #edf1f5;cursor:pointer;display:flex;align-items:baseline;gap:6px" onmouseover="this.style.background=\'#f4f6f9\'" onmouseout="this.style.background=\'#fff\'">'
          + '<span style="font-size:12.5px;color:#1a1a1a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(o.name)+'</span>'
          + (o.vbiz?'<span style="font-size:11px;color:#9ca3af;white-space:nowrap;flex-shrink:0">'+o.vbiz+'</span>':'')
          + '</div>';
      }).join('');
    }
    dd.style.display='block';
  };
  window.fxPickVend = function(i, name){
    var inp=document.getElementById('fxUnV'+i);
    if(inp) inp.value=name;
    fxUnDdHide();
    fxAssignDep(i);
  };
"""
    s = rep(s, "  function _fxRenderUnasg(){", HELPERS + "  function _fxRenderUnasg(){", 1, 'HELPERS')

    # ── (2) 행 입력칸: datalist → 커스텀 드롭다운 ──
    OLD_DL = """      var dl='<datalist id="fxVendDl">'
        + _fxVendorNames('서울').concat(_fxVendorNames('화성'))
            .filter(function(x,i,a){ return a.indexOf(x)===i; })
            .map(function(n){ return '<option value="'+esc(n)+'">'; }).join('')
        + '</datalist>';
      var rows=_fxUnList.slice(0,300).map(function(e,i){"""
    NEW_DL = """      fxUnDdHide();
      var rows=_fxUnList.slice(0,300).map(function(e,i){"""
    s = rep(s, OLD_DL, NEW_DL, 1, 'DL')
    s = rep(s, """          +   '<input id="fxUnV'+i+'" list="fxVendDl" class="q-flat" placeholder="거래처명 입력…" style="width:170px" onkeydown="if(event.key===\\'Enter\\'){event.preventDefault();fxAssignDep('+i+');}">'""",
            """          +   '<input id="fxUnV'+i+'" class="q-flat" placeholder="거래처 검색…" autocomplete="off" style="width:190px;border:1px solid #d6deea !important;background:#fff" oninput="fxUnDdRender('+i+')" onfocus="fxUnDdRender('+i+')" onblur="fxUnDdHide()" onkeydown="if(event.key===\\'Enter\\'){event.preventDefault();fxAssignDep('+i+');}else if(event.key===\\'Escape\\'){fxUnDdHide();}">'""", 1, 'INPUT')
    s = rep(s, "        + '<tbody>'+rows+'</tbody></table></div></div>' + dl;",
            "        + '<tbody>'+rows+'</tbody></table></div></div>';", 1, 'NODL')

    # ── (3) 지정: Enter/버튼 시 검색 첫 항목 자동 선택 ──
    s = rep(s, """    var el=document.getElementById('fxUnV'+i);
    var v=(el && el.value || '').trim();
    if(!v){ if(el) el.focus(); return; }""",
            """    fxUnDdHide();
    var el=document.getElementById('fxUnV'+i);
    var v=(el && el.value || '').trim();
    if(!v){ if(el) el.focus(); return; }
    var opts=_fxVendorOpts(d.biz);
    if(!opts.some(function(o){ return o.name===v; })){
      var q=v.toLowerCase();
      var mm=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
      if(mm.length) v=mm[0].name;   // 검색 첫 항목 자동 선택 (프로젝트 업체 검색과 동일 규칙)
    }""", 1, 'ASSIGN')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r132(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r131 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r131 2026-08-24 -->', '<!-- test build r132 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
