# -*- coding: utf-8 -*-
# r148: [미수현황 표 전체폭 확장 + 업체 목록 페이지네이션]
#  1) 매입매출 > 미수현황 표가 다른 표들(업체 목록·집계 등)과 달리 .main 좌우 여백
#     안쪽에 갇혀 있어 넓은 화면에서 좌우가 비어 보임 → 다른 표와 동일하게
#     화면 좌우로 여백을 뚫고 전체폭을 쓰도록 통일.
#  2) 업체 목록이 "처음 200개 + 스크롤 시 200개씩 추가" 방식이라 업체가 많을 때
#     한 번에 DOM에 많은 행이 쌓여 느려짐 → 1페이지당 20개, 이전/다음 페이지
#     버튼으로 넘기는 방식으로 교체.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R148 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r148(s, path):
    # (1) 미수현황 표 전체폭
    s = rep(s,
            "      + '<div style=\"background:#fff;border:1px solid #d6deea;overflow-x:auto\"><table style=\"width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px;min-width:1280px\">'",
            "      + '<div style=\"background:#fff;border:1px solid #d6deea;border-left:none;border-right:none;margin:0 calc(var(--mpx, 24px)*-1);overflow-x:auto\"><table style=\"width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px;min-width:1280px\">'",
            1, 'ARWIDTH')

    # (2) 업체 목록: 무한 스크롤 → 페이지네이션(1페이지 20개)
    s = rep(s, "  var _clxShown = 200;   // 무한 스크롤: 처음 200개, 바닥 근처에서 200개씩 추가",
            "  var _clxPage = 1;   // r148: 페이지네이션(1페이지 20개)\n  var _clxPageSize = 20;", 1, 'VAR')
    s = rep(s, """  window.addEventListener('scroll', function(){
    var pg=document.getElementById('pageClients');
    if(!pg || !pg.classList.contains('active')) return;
    if(_clxExp!==null) return;                             // 펼침/편집 중에는 추가 로드 정지
    if(!document.getElementById('clxMoreNote')) return;    // 더 불러올 항목이 없으면 정지
    var de=document.documentElement;
    if(de.scrollHeight - de.scrollTop - de.clientHeight > 400) return;
    _clxShown += 200;
    _clxRender();
  }, {passive:true});""",
            """  window.clxPageDelta = function(d){
    _clxPage += d; if(_clxPage<1) _clxPage=1;
    _clxRender();
    var box=document.getElementById('clxList'); if(box) box.scrollIntoView({block:'start'});
  };
  function _clxPagerHtml(total, pageSize, page){
    var totalPages=Math.max(1, Math.ceil(total/pageSize));
    if(total<=pageSize) return '';
    return '<div style="display:flex;align-items:center;justify-content:center;gap:10px;padding:10px var(--mpx,24px);border-top:1px solid #eef2f7;background:#fafbfc">'
      + '<button type="button" class="btn" onclick="clxPageDelta(-1)"'+(page<=1?' disabled':'')+' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(page<=1?'#c9d0da':'#374151')+';cursor:'+(page<=1?'default':'pointer')+'">&lsaquo; 이전</button>'
      + '<span style="font-size:12px;color:#6b7280">'+page+' / '+totalPages+' 페이지 &middot; 전체 '+total+'개</span>'
      + '<button type="button" class="btn" onclick="clxPageDelta(1)"'+(page>=totalPages?' disabled':'')+' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(page>=totalPages?'#c9d0da':'#374151')+';cursor:'+(page>=totalPages?'default':'pointer')+'">다음 &rsaquo;</button>'
      + '</div>';
  }""", 1, 'SCROLLRM')
    s = rep(s, "window.clxSearchInput = function(v){ _clxQ = String(v||'').trim().toLowerCase(); _clxShown = 200; _clxRender(); };",
            "window.clxSearchInput = function(v){ _clxQ = String(v||'').trim().toLowerCase(); _clxPage = 1; _clxRender(); };", 1, 'SEARCHRESET')
    s = rep(s, "_clxExp=null; _clxQ=''; _clxShown=200; var _cx8=document.getElementById('clxSearch');",
            "_clxExp=null; _clxQ=''; _clxPage=1; var _cx8=document.getElementById('clxSearch');", 1, 'PAGEINIT')
    s = rep(s, "_clxExp=null; _clxShown=200;",
            "_clxExp=null; _clxPage=1;", 1, 'SAVERESET')
    s = rep(s, """    var _total=list.length;
    var _capNote='';
    if(_total>_clxShown){
      _capNote='<div id="clxMoreNote" style="text-align:center;padding:10px;color:#9ca3af;font-size:11.5px">전체 '+_total+'개 중 '+_clxShown+'개 표시 &middot; 아래로 스크롤하면 더 불러옵니다</div>';
      list=list.slice(0,_clxShown);
      if(_clxExp && _clxExp!=='' && !list.some(function(c){ return c[0]===_clxExp; })){
        var _exRow=all.filter(function(c){ return c[0]===_clxExp; });
        list=_exRow.concat(list);   // 펼친 업체는 표시 제한과 무관하게 맨 위에 노출
      }
    }""",
            """    var _total=list.length;
    var _totalPages=Math.max(1, Math.ceil(_total/_clxPageSize));
    if(_clxPage>_totalPages) _clxPage=_totalPages;
    if(_clxPage<1) _clxPage=1;
    var _startIdx=(_clxPage-1)*_clxPageSize;
    list=list.slice(_startIdx, _startIdx+_clxPageSize);
    if(_clxExp && _clxExp!=='' && !list.some(function(c){ return c[0]===_clxExp; })){
      var _exRow=all.filter(function(c){ return c[0]===_clxExp; });
      list=_exRow.concat(list);   // 펼친 업체는 현재 페이지에 없어도 맨 위에 노출
    }""", 1, 'PAGECALC')
    s = rep(s, "      + '</tbody></table></div>' + _capNote;\n    box.innerHTML=html;",
            "      + '</tbody></table>' + _clxPagerHtml(_total, _clxPageSize, _clxPage) + '</div>';\n    box.innerHTML=html;", 1, 'PAGERHTML')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r148(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r147 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r147 2026-08-25 -->', '<!-- test build r148 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
