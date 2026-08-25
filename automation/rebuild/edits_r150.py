# -*- coding: utf-8 -*-
# r151(원래 r150 번호): [미수현황 페이지네이션]
#  업체 목록(r148/r149)과 동일한 이유 — 매입매출 > 미수현황은 자료가 더 방대해서
#  거래처가 많을수록 한 번에 DOM에 다 그려 넣어 렉이 심해짐.
#  업체 목록과 동일한 방식(1페이지 20개, 이전/다음 버튼)으로 교체.
#  상단 요약 칩(총 미수·연령 합계 등)은 전체 데이터 기준 그대로 유지하고,
#  표에 그려지는 행만 페이지 단위로 자름. 검색·상태필터·사업장 전환·탭 전환 시
#  1페이지로 리셋.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R150 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r150(s, path):
    s = rep(s,
            "  var _fxRegion='all', _fxQ='', _fxStatusF='all', _fxExp=null, _fxLdFrom='', _fxLdTo='', _fxNotesOpen=false, _fxAdjForm=false, _fxExclOpen=false;",
            "  var _fxRegion='all', _fxQ='', _fxStatusF='all', _fxExp=null, _fxLdFrom='', _fxLdTo='', _fxNotesOpen=false, _fxAdjForm=false, _fxExclOpen=false, _fxArPage=1, _fxArPageSize=20;",
            1, 'VAR')
    s = rep(s, "  window.fxSwitchTab = function(t){ _fxTab = t; renderFxPage(); };",
            "  window.fxSwitchTab = function(t){ _fxTab = t; _fxArPage=1; renderFxPage(); };", 1, 'SWITCHTAB')
    s = rep(s, "  window.fxSetRegion = function(b){ _fxRegion=b; _fxExp=null; _fxSumYear=null; renderFxPage(); };",
            "  window.fxSetRegion = function(b){ _fxRegion=b; _fxExp=null; _fxSumYear=null; _fxArPage=1; renderFxPage(); };", 1, 'SETREGION')
    s = rep(s, "  window.fxSearchInput = function(v){ _fxQ=String(v||'').trim().toLowerCase(); _fxExp=null; _fxRenderArBody(); };",
            "  window.fxSearchInput = function(v){ _fxQ=String(v||'').trim().toLowerCase(); _fxExp=null; _fxArPage=1; _fxRenderArBody(); };", 1, 'SEARCH')
    s = rep(s, "  window.fxSetStatusF = function(v){ _fxStatusF=v; _fxExp=null; _fxRenderArBody(); };",
            "  window.fxSetStatusF = function(v){ _fxStatusF=v; _fxExp=null; _fxArPage=1; _fxRenderArBody(); };", 1, 'STATUSF')

    # 페이저 함수 삽입 (r146과 동일한 위치 패턴)
    s = rep(s, "  function _fxRenderArBody(){",
            r"""  window.fxArPageDelta = function(d){
    _fxArPage += d; if(_fxArPage<1) _fxArPage=1;
    _fxRenderArBody();
    var host=document.getElementById('fxArList'); if(host) host.scrollIntoView({block:'start'});
  };
  function _fxArPagerHtml(total, pageSize, page){
    var totalPages=Math.max(1, Math.ceil(total/pageSize));
    if(total<=pageSize) return '';
    return '<div style="display:flex;align-items:center;justify-content:center;gap:10px;padding:10px var(--mpx,24px);border-top:1px solid #eef2f7;background:#fafbfc">'
      + '<button type="button" class="btn" onclick="fxArPageDelta(-1)"'+(page<=1?' disabled':'')+' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(page<=1?'#c9d0da':'#374151')+';cursor:'+(page<=1?'default':'pointer')+'">&lsaquo; 이전</button>'
      + '<span style="font-size:12px;color:#6b7280">'+page+' / '+totalPages+' 페이지 &middot; 조건에 맞는 거래처 '+total+'곳</span>'
      + '<button type="button" class="btn" onclick="fxArPageDelta(1)"'+(page>=totalPages?' disabled':'')+' style="font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(page>=totalPages?'#c9d0da':'#374151')+';cursor:'+(page>=totalPages?'default':'pointer')+'">다음 &rsaquo;</button>'
      + '</div>';
  }
  function _fxRenderArBody(){""", 1, 'PAGERFN')

    # 빈 목록 안내 다음, 페이지 계산 + 슬라이스 삽입
    s = rep(s,
            """    if(!data.length){ host.innerHTML=noteHtml+'<div style="text-align:center;padding:48px;color:#b6bec9;font-size:13px">조건에 맞는 거래처가 없습니다.</div>'; return; }""",
            """    if(!data.length){ host.innerHTML=noteHtml+'<div style="text-align:center;padding:48px;color:#b6bec9;font-size:13px">조건에 맞는 거래처가 없습니다.</div>'; return; }
    var _arTotal=data.length;
    var _arTotalPages=Math.max(1, Math.ceil(_arTotal/_fxArPageSize));
    if(_fxArPage>_arTotalPages) _fxArPage=_arTotalPages;
    if(_fxArPage<1) _fxArPage=1;
    var _arStart=(_fxArPage-1)*_fxArPageSize;
    var pageData=data.slice(_arStart, _arStart+_fxArPageSize);""",
            1, 'PAGECALC')

    # rows 렌더 대상을 전체 data → 현재 페이지(pageData)로 변경
    s = rep(s, "    var rows=data.map(function(x){",
            "    var rows=pageData.map(function(x){", 1, 'ROWSSRC')

    # 표 닫힘 직후 페이저 삽입
    s = rep(s, "      + '<tbody>'+rows+'</tbody></table></div>';",
            "      + '<tbody>'+rows+'</tbody></table>' + _fxArPagerHtml(_arTotal, _fxArPageSize, _fxArPage) + '</div>';",
            1, 'PAGERHTML')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r150(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r149 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r149 2026-08-25 -->', '<!-- test build r150 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
