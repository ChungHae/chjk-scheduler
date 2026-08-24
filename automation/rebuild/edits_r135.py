# -*- coding: utf-8 -*-
# r135: [미배정 드롭다운 — "계산서에만 있는 거래처" 섹션 + 원클릭 업체 등록/배정]
#  - 드롭다운 하단에 회색 구분 섹션으로 일정>업체에 없는 계산서 거래처 표시
#    (사업자번호 기준 중복 제거 — 표기 변형은 최신 계산서의 상호 하나로)
#  - 선택 시 확인창 → 일정>업체에 등록(사업자번호 포함) + 입금 배정을 한 번에
#  - 같은 사업자번호가 이미 다른 이름으로 등록돼 있으면 등록 없이 그 업체로 배정
#    (앱 표준 규칙 _findClientByBiz 재사용 — 중복 등록 방지)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R135 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, a, b, new, label):
    if s.count(a) != 1 or s.count(b) != 1: raise SystemExit('R135 FAIL cut %s (a:%d b:%d)' % (label, s.count(a), s.count(b)))
    i = s.index(a); j = s.index(b)
    if j <= i: raise SystemExit('R135 FAIL cut order %s' % label)
    return s[:i] + new + s[j:]

NEW_DD = r"""  function _fxInvOnlyOpts(biz){
    // 계산서에는 있으나 일정>업체에 없는 거래처 (사업자번호 기준 중복 제거, 최신 상호로 표시)
    var cl=_fxClientOpts();
    var byBiz={}, byName={};
    cl.forEach(function(o){ if(o.vbiz) byBiz[o.vbiz.replace(/[^0-9]/g,'')]=1; byName[o.name]=1; });
    var m={};
    fxSalesInv.forEach(function(e){
      if(e.biz!==biz || !e.vendor) return;
      var digits=String(e.vbiz||'').replace(/[^0-9]/g,'');
      if(digits && byBiz[digits]) return;
      if(byName[e.vendor]) return;
      var k=digits || ('N|'+e.vendor);
      if(!m[k] || (e.date||'') > m[k].date) m[k]={name:e.vendor, vbiz:e.vbiz||'', date:e.date||''};
    });
    return Object.keys(m).map(function(k){ return m[k]; })
      .sort(function(a,b){ return a.name.localeCompare(b.name,undefined,{numeric:true,sensitivity:'base'}); });
  }
  window.fxPickNewVend = function(i, name, vbiz){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 지정할 수 없습니다.'); return; }
    fxUnDdHide();
    // 같은 사업자번호가 이미 다른 이름으로 등록돼 있으면 그 업체로 바로 배정 (중복 등록 방지)
    var dup = (typeof _findClientByBiz==='function' && vbiz) ? _findClientByBiz(vbiz, null) : null;
    if(dup){ fxPickVend(i, dup); return; }
    if((allClients()||[]).some(function(c){ return c && c[0]===name; })){ fxPickVend(i, name); return; }
    showConfirmModal('업체 등록 + 배정',
      '"'+esc(name)+'"'+(vbiz?' ('+vbiz+')':'')+' 업체가 일정 > 업체에 없습니다.\n일정 > 업체에 등록하고 이 입금을 배정할까요?',
      function(){
        try{ ensureClientList(); }catch(_e){}
        clientList.push([name, vbiz||'']);
        _saveClients();
        fxPickVend(i, name);
      }, '등록 + 배정', '#1B3A6B');
  };
  window.fxUnDdRender = function(i){
    var inp=document.getElementById('fxUnV'+i); if(!inp) return;
    var e=_fxUnList[i]; if(!e) return;
    var dd=document.getElementById('fxUnDdG');
    if(!dd){
      dd=document.createElement('div');
      dd.id='fxUnDdG';
      dd.style.cssText='display:none;position:fixed;width:300px;background:#fff;border:1px solid #d6e4f5;border-radius:8px;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:260px;overflow:auto;z-index:100060';
      document.body.appendChild(dd);
      dd.addEventListener('mousedown', function(ev){ ev.preventDefault(); });  // blur 방지 → 항목 클릭 보장
    }
    var r=inp.getBoundingClientRect();
    dd.style.left=r.left+'px';
    if(window.innerHeight - r.bottom < 270){ dd.style.top='auto'; dd.style.bottom=(window.innerHeight - r.top + 2)+'px'; }
    else { dd.style.bottom='auto'; dd.style.top=(r.bottom + 2)+'px'; }
    var q=String(inp.value||'').trim().toLowerCase();
    var opts=_fxClientOpts();
    if(q) opts=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    opts=opts.slice(0,60);
    var inv=_fxInvOnlyOpts(e.biz);
    if(q) inv=inv.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    inv=inv.slice(0,60);
    var html='';
    if(opts.length){
      html += opts.map(function(o){
        var rn=String(o.name).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        return '<div onclick="fxPickVend('+i+',\''+rn+'\')" style="padding:8px 12px;border-bottom:1px solid #edf1f5;cursor:pointer;display:flex;align-items:baseline;gap:6px" onmouseover="this.style.background=\'#f4f6f9\'" onmouseout="this.style.background=\'#fff\'">'
          + '<span style="font-size:12.5px;color:#1a1a1a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(o.name)+'</span>'
          + (o.vbiz?'<span style="font-size:11px;color:#9ca3af;white-space:nowrap;flex-shrink:0">'+o.vbiz+'</span>':'')
          + '</div>';
      }).join('');
    }
    if(inv.length){
      html += '<div style="padding:6px 12px;font-size:11px;font-weight:700;color:#9ca3af;background:#f8fafc;border-top:2px solid #d6e4f5;border-bottom:1px solid #edf1f5">계산서에만 있는 거래처 — 선택하면 업체 등록 후 배정</div>';
      html += inv.map(function(o){
        var rn=String(o.name).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        var rb=String(o.vbiz||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        return '<div onclick="fxPickNewVend('+i+',\''+rn+'\',\''+rb+'\')" style="padding:8px 12px;border-bottom:1px solid #edf1f5;cursor:pointer;display:flex;align-items:baseline;gap:6px" onmouseover="this.style.background=\'#f4f6f9\'" onmouseout="this.style.background=\'#fff\'">'
          + '<span style="font-size:12.5px;color:#374151;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(o.name)+'</span>'
          + (o.vbiz?'<span style="font-size:11px;color:#9ca3af;white-space:nowrap;flex-shrink:0">'+o.vbiz+'</span>':'')
          + '<span style="margin-left:auto;font-size:10.5px;color:#b6bec9;white-space:nowrap;flex-shrink:0">업체 미등록</span>'
          + '</div>';
      }).join('');
    }
    if(!html){
      html='<div style="padding:9px 12px;color:#bbb;font-size:12.5px">'+(q?'일치하는 업체 없음':'일정 > 업체에 등록된 업체가 없습니다')+'</div>';
    }
    dd.innerHTML=html;
    dd.style.display='block';
  };
"""

def apply_r135(s, path):
    s = cut(s, "  window.fxUnDdRender = function(i){", "  window.fxPickVend = function(i, name){", NEW_DD, 'DD')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r135(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r134 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r134 2026-08-24 -->', '<!-- test build r135 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
