# -*- coding: utf-8 -*-
# r138: [미배정 드롭다운 — '계산서에만 있는 거래처' 섹션이 묻히는 문제 수정]
#  원인: 검색어 없이 열면 등록 업체 60개가 먼저 채워져 미등록 섹션이 스크롤
#  한참 아래(offsetTop ~2000px)에 위치 → 보이는 높이 258px 안에 안 들어옴.
#  수정: 검색어가 없을 때는 두 섹션 각각 8개씩 + "외 N곳 — 이름을 입력해 검색"
#  안내행 → 두 섹션이 항상 첫 화면에 함께 보임. 검색 시에는 기존처럼 60개.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R138 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, a, b, new, label):
    if s.count(a) != 1 or s.count(b) != 1: raise SystemExit('R138 FAIL cut %s (a:%d b:%d)' % (label, s.count(a), s.count(b)))
    i = s.index(a); j = s.index(b)
    if j <= i: raise SystemExit('R138 FAIL cut order %s' % label)
    return s[:i] + new + s[j:]

NEW_DD = r"""  window.fxUnDdRender = function(i){
    var inp=document.getElementById('fxUnV'+i); if(!inp) return;
    var e=_fxUnList[i]; if(!e) return;
    var dd=document.getElementById('fxUnDdG');
    if(!dd){
      dd=document.createElement('div');
      dd.id='fxUnDdG';
      dd.style.cssText='display:none;position:fixed;width:300px;background:#fff;border:1px solid #d6e4f5;border-radius:0;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:320px;overflow:auto;z-index:100060';
      document.body.appendChild(dd);
      dd.addEventListener('mousedown', function(ev){ ev.preventDefault(); });  // blur 방지 → 항목 클릭 보장
    }
    var r=inp.getBoundingClientRect();
    dd.style.left=r.left+'px';
    if(window.innerHeight - r.bottom < 330){ dd.style.top='auto'; dd.style.bottom=(window.innerHeight - r.top + 2)+'px'; }
    else { dd.style.bottom='auto'; dd.style.top=(r.bottom + 2)+'px'; }
    var q=String(inp.value||'').trim().toLowerCase();
    var LIM = q ? 60 : 5;   // 검색어 없으면 두 섹션이 함께 보이도록 짧게
    var opts=_fxClientOpts();
    if(q) opts=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    var optsTotal=opts.length;
    opts=opts.slice(0,LIM);
    var inv=_fxInvOnlyOpts(e.biz);
    if(q) inv=inv.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    var invTotal=inv.length;
    inv=inv.slice(0,LIM);
    var MORE='padding:6px 12px;font-size:11px;color:#b6bec9;border-bottom:1px solid #edf1f5;background:#fcfdfe';
    var html='';
    if(opts.length){
      html += '<div style="padding:6px 12px;font-size:11px;font-weight:700;color:#9ca3af;background:#f8fafc;border-bottom:1px solid #edf1f5">등록된 업체'+(optsTotal>opts.length?' ('+optsTotal+'곳)':'')+'</div>';
      html += opts.map(function(o){
        var rn=String(o.name).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        return '<div onclick="fxPickVend('+i+',\''+rn+'\')" style="padding:8px 12px;border-bottom:1px solid #edf1f5;cursor:pointer;display:flex;align-items:baseline;gap:6px" onmouseover="this.style.background=\'#f4f6f9\'" onmouseout="this.style.background=\'#fff\'">'
          + '<span style="font-size:12.5px;color:#1a1a1a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(o.name)+'</span>'
          + (o.vbiz?'<span style="font-size:11px;color:#9ca3af;white-space:nowrap;flex-shrink:0">'+o.vbiz+'</span>':'')
          + '</div>';
      }).join('');
      if(optsTotal>opts.length) html += '<div style="'+MORE+'">… 외 '+(optsTotal-opts.length)+'곳 — 이름을 입력해 검색하세요</div>';
    }
    if(inv.length){
      html += '<div style="padding:6px 12px;font-size:11px;font-weight:700;color:#b45309;background:#fff8ef;border-top:2px solid #f0d9b8;border-bottom:1px solid #f0d9b8">계산서에만 있는 거래처'+(invTotal>inv.length?' ('+invTotal+'곳)':'')+' — 선택하면 업체 등록 후 배정</div>';
      html += inv.map(function(o){
        var rn=String(o.name).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        var rb=String(o.vbiz||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        return '<div onclick="fxPickNewVend('+i+',\''+rn+'\',\''+rb+'\')" style="padding:8px 12px;border-bottom:1px solid #edf1f5;cursor:pointer;display:flex;align-items:baseline;gap:6px" onmouseover="this.style.background=\'#f4f6f9\'" onmouseout="this.style.background=\'#fff\'">'
          + '<span style="font-size:12.5px;color:#374151;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(o.name)+'</span>'
          + (o.vbiz?'<span style="font-size:11px;color:#9ca3af;white-space:nowrap;flex-shrink:0">'+o.vbiz+'</span>':'')
          + '<span style="margin-left:auto;font-size:10.5px;color:#b6bec9;white-space:nowrap;flex-shrink:0">업체 미등록</span>'
          + '</div>';
      }).join('');
      if(invTotal>inv.length) html += '<div style="'+MORE+'">… 외 '+(invTotal-inv.length)+'곳 — 이름을 입력해 검색하세요</div>';
    }
    if(!html){
      html='<div style="padding:9px 12px;color:#bbb;font-size:12.5px">'+(q?'일치하는 업체 없음':'일정 > 업체에 등록된 업체가 없습니다')+'</div>';
    }
    dd.innerHTML=html;
    dd.style.display='block';
  };
"""

def apply_r138(s, path):
    s = cut(s, "  window.fxUnDdRender = function(i){", "  window.fxPickVend = function(i, name){", NEW_DD, 'DD')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r138(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r137 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r137 2026-08-24 -->', '<!-- test build r138 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
