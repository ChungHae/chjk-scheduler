# -*- coding: utf-8 -*-
# r139: [미배정 드롭다운 — "왜 안 뜨는지" 자가 진단 안내]
#  검색했는데 '계산서에만 있는 거래처' 후보가 없을 때, 이유를 그 자리에서 안내:
#  (a) 같은 사업자번호가 이미 다른 이름으로 등록된 경우
#      → "이미 'OO'(으)로 등록됨" 안내 행 (클릭하면 그 업체로 바로 배정)
#  (b) 다른 사업장의 계산서 거래처인 경우
#      → "화성 계산서 거래처 — 이 입금은 서울" 경고 행 (사업장 확인 유도)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R139 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r139(s, path):
    # 진단 헬퍼 (fxUnDdRender 앞에 삽입)
    s = rep(s, "  window.fxUnDdRender = function(i){",
            r"""  // r139: 검색 결과가 없을 때의 원인 진단
  function _fxDdHints(biz, q){
    var hints=[];
    var qq=String(q||'').toLowerCase();
    var match=function(e){ return (e.vendor||'').toLowerCase().indexOf(qq)>=0 || (e.vbiz||'').indexOf(qq)>=0; };
    // (a) 같은 사업자번호가 이미 다른 이름으로 등록된 계산서 거래처
    var seenA={};
    fxSalesInv.forEach(function(e){
      if(e.biz!==biz || !e.vendor || !match(e)) return;
      var reg=(typeof _findClientByBiz==='function' && e.vbiz) ? _findClientByBiz(e.vbiz, null) : null;
      if(reg && reg!==e.vendor && !seenA[e.vendor+'|'+reg]){
        seenA[e.vendor+'|'+reg]=1;
        hints.push({type:'reg', inv:e.vendor, cli:reg});
      }
    });
    // (b) 다른 사업장의 계산서 거래처
    var other = biz==='서울' ? '화성' : '서울';
    var seenB={};
    fxSalesInv.forEach(function(e){
      if(e.biz!==other || !e.vendor || !match(e)) return;
      // 이 사업장(biz)에도 같은 사업자번호 계산서가 있으면 (a)/일반 경로로 처리되므로 제외
      var d=(e.vbiz||'').replace(/[^0-9]/g,'');
      var inThis = fxSalesInv.some(function(x){ return x.biz===biz && String(x.vbiz||'').replace(/[^0-9]/g,'')===d && d; });
      if(inThis) return;
      if(!seenB[e.vendor]){ seenB[e.vendor]=1; hints.push({type:'other', inv:e.vendor, other:other}); }
    });
    return hints.slice(0,4);
  }
  window.fxUnDdRender = function(i){""", 1, 'HINTFN')

    # 안내 행 렌더 (미등록 섹션 뒤, !html 앞)
    s = rep(s, """      if(invTotal>inv.length) html += '<div style="'+MORE+'">… 외 '+(invTotal-inv.length)+'곳 — 이름을 입력해 검색하세요</div>';
    }
    if(!html){""",
            r"""      if(invTotal>inv.length) html += '<div style="'+MORE+'">… 외 '+(invTotal-inv.length)+'곳 — 이름을 입력해 검색하세요</div>';
    }
    if(q && !inv.length){
      _fxDdHints(e.biz, q).forEach(function(h){
        if(h.type==='reg'){
          var rc=String(h.cli).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
          html += '<div onclick="fxPickVend('+i+',\''+rc+'\')" style="padding:8px 12px;border-top:1px solid #edf1f5;cursor:pointer;font-size:11.5px;color:#14305c;background:#f4f8fe" onmouseover="this.style.background=\'#eaf1fb\'" onmouseout="this.style.background=\'#f4f8fe\'">'
            + 'ℹ️ 계산서의 "'+esc(h.inv)+'" 은(는) 이미 <b>'+esc(h.cli)+'</b>(으)로 등록되어 있습니다 — 클릭하면 그 업체로 배정</div>';
        } else if(h.type==='other'){
          html += '<div style="padding:8px 12px;border-top:1px solid #f0d9b8;font-size:11.5px;color:#b45309;background:#fff8ef">'
            + '⚠️ "'+esc(h.inv)+'" 은(는) <b>'+h.other+'</b> 계산서 거래처입니다 — 이 입금은 '+esc(e.biz)+' 소속이라 여기 안 뜹니다. 은행 파일의 사업장 선택을 확인하세요.</div>';
        }
      });
    }
    if(!html){""", 1, 'HINTUI')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r139(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r138 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r138 2026-08-24 -->', '<!-- test build r139 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
