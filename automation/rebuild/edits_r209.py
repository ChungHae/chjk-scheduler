# -*- coding: utf-8 -*-
# r209(회계): 미수현황 페이지 이동에 '처음'·'끝' 버튼 추가
#  사용자 요청: "이전, 다음 칸 말고도 처음과 끝으로 바로 갈 수 있는 버튼도 만들어줘"
#  처리: fxArPageGo(n) 추가(1=처음, -1=끝), 페이저에 « 처음 / 끝 » 버튼을 이전·다음 바깥에 둔다.
#        비활성 조건·색·스크롤 동작은 기존 이전·다음과 동일하게 맞춘다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD1 = """  window.fxArPageDelta = function(d){
    _fxArPage += d; if(_fxArPage<1) _fxArPage=1;
    _fxRenderArBody();
    var host=document.getElementById('fxArList'); if(host) host.scrollIntoView({block:'start'});
  };
"""
NEW1 = """  window.fxArPageDelta = function(d){
    _fxArPage += d; if(_fxArPage<1) _fxArPage=1;
    _fxRenderArBody();
    var host=document.getElementById('fxArList'); if(host) host.scrollIntoView({block:'start'});
  };
  // r209: 처음(n=1) / 끝(n=-1) 으로 바로 이동. 끝 페이지 번호는 _fxRenderArBody 가 범위를 맞춰준다.
  window.fxArPageGo = function(n){
    _fxArPage = (n<0) ? 999999 : 1;
    _fxRenderArBody();
    var host=document.getElementById('fxArList'); if(host) host.scrollIntoView({block:'start'});
  };
"""

OLD2 = """    return '<div style="display:flex;align-items:center;justify-content:center;gap:10px;padding:10px var(--mpx,24px);border-top:1px solid #eef2f7;background:#fafbfc">'
      + '<button type="button" class="btn" onclick="fxArPageDelta(-1)"'+(page<=1?' disabled':'')+' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(page<=1?'#c9d0da':'#374151')+';cursor:'+(page<=1?'default':'pointer')+'">&lsaquo; 이전</button>'
      + '<span style="font-size:12px;color:#6b7280">'+page+' / '+totalPages+' 페이지 &middot; 조건에 맞는 거래처 '+total+'곳</span>'
      + '<button type="button" class="btn" onclick="fxArPageDelta(1)"'+(page>=totalPages?' disabled':'')+' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(page>=totalPages?'#c9d0da':'#374151')+';cursor:'+(page>=totalPages?'default':'pointer')+'">다음 &rsaquo;</button>'
      + '</div>';
"""
NEW2 = """    // r209: 처음·끝 버튼을 이전·다음 바깥에 둔다
    var _pb=function(fn, lbl, off){
      return '<button type="button" class="btn" onclick="'+fn+'"'+(off?' disabled':'')
        + ' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'
        + (off?'#c9d0da':'#374151')+';cursor:'+(off?'default':'pointer')+'">'+lbl+'</button>';
    };
    var _first=(page<=1), _last=(page>=totalPages);
    return '<div style="display:flex;align-items:center;justify-content:center;gap:6px;padding:10px var(--mpx,24px);border-top:1px solid #eef2f7;background:#fafbfc">'
      + _pb('fxArPageGo(1)',    '&laquo; 처음', _first)
      + _pb('fxArPageDelta(-1)','&lsaquo; 이전', _first)
      + '<span style="font-size:12px;color:#6b7280;margin:0 6px">'+page+' / '+totalPages+' 페이지 &middot; 조건에 맞는 거래처 '+total+'곳</span>'
      + _pb('fxArPageDelta(1)', '다음 &rsaquo;', _last)
      + _pb('fxArPageGo(-1)',   '끝 &raquo;', _last)
      + '</div>';
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD1, NEW1, 1, 'r209 fxArPageGo (%s)' % path)
    s = rep(s, OLD2, NEW2, 1, 'r209 페이저 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r209 2026-09-29 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
