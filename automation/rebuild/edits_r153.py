# -*- coding: utf-8 -*-
# r153: [거래처 검색 결과 정렬 — 검색어로 "시작"하는 곳을 먼저]
#
#  요청: 미수현황에서 "케이" 로 검색하면
#        케이테크 / 주식회사 케이에스 / 케이디엠 / 케이엠씨 (앞에서 일치) 가 먼저 나오고
#        주식회사 디티케이 / 에이치엔케이 주식회사 (중간에 포함) 가 그 뒤에 나오게.
#
#  기존: 검색 결과를 미수 잔액 큰 순으로만 정렬 → 이름이 어디서 일치했는지는 무관.
#
#  수정: 검색어가 있을 때만 3단계 우선순위로 묶어서 정렬하고, 같은 묶음 안에서는
#        기존 규칙(미수 잔액 큰 순)을 그대로 유지한다.
#          0순위 = 거래처명이 검색어로 시작
#          1순위 = 사업자번호가 검색어로 시작
#          2순위 = 그 외(중간에 포함)
#        앞자리 판단에는 이미 있는 _fxNormName() 을 재사용한다. 공백과 법인격 표기
#        ((주)·㈜·(유)·(사)·(재)·주식회사·유한회사) 를 없애고 비교하므로
#        "주식회사 케이에스" 도 0순위로 잡힌다.
#        정렬만 바뀌고, 검색에 걸리는 거래처 집합(필터 조건)은 전혀 건드리지 않음.
#
#  함께: 자료 업로드 > 미배정 입금의 거래처 검색 드롭다운도 같은 순서로 정렬.
#        이 목록은 60곳에서 잘리기 때문에, 정렬이 없으면 정작 찾는 거래처가
#        잘려나갈 수 있었다. (오배정을 줄이는 효과도 있음)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R153 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r153(s, path):
    # 1) 순위 helper 추가 (_fxNormName 바로 뒤)
    s = rep(s,
        """  function _fxNormName(s){
    return String(s||'').replace(/\\s+/g,'').replace(/\\(주\\)|㈜|\\(유\\)|\\(사\\)|\\(재\\)|주식회사|유한회사/g,'').toLowerCase();
  }""",
        r"""  function _fxNormName(s){
    return String(s||'').replace(/\s+/g,'').replace(/\(주\)|㈜|\(유\)|\(사\)|\(재\)|주식회사|유한회사/g,'').toLowerCase();
  }
  // r153: 검색 결과 순위 — 0=이름이 검색어로 시작, 1=사업자번호가 검색어로 시작, 2=중간에 포함.
  //  앞자리 판단은 공백·법인격 표기를 뺀 이름으로 하므로 "주식회사 케이에스" 도 "케이" 의 0순위.
  function _fxSearchRank(name, vbiz, q, nq){
    if(nq && _fxNormName(name).indexOf(nq)===0) return 0;
    if(q && vbiz && String(vbiz).indexOf(q)===0) return 1;
    return 2;
  }
  // 순위 오름차순 정렬(동점은 원래 순서 유지). tie 인자로 같은 순위 안의 추가 기준을 준다.
  function _fxRankSort(list, q, nameOf, vbizOf, tie){
    var nq=_fxNormName(q);
    var dec=list.map(function(x, ix){
      return { x:x, i:ix, r:_fxSearchRank(nameOf(x), vbizOf(x), q, nq) };
    });
    dec.sort(function(a,b){
      if(a.r!==b.r) return a.r-b.r;
      if(tie){ var t=tie(a.x, b.x); if(t) return t; }
      return a.i-b.i;
    });
    return dec.map(function(d){ return d.x; });
  }""", 1, 'RANKFN')

    # 2) 미수현황 목록 정렬
    s = rep(s,
        """    data.sort(function(a,b){ return b.bal-a.bal; });
    var totBal=0, nMisu=0, nLong=0, agT=[0,0,0,0,0];""",
        r"""    // r153: 검색 중에는 "검색어로 시작하는 거래처" 를 앞으로. 같은 순위 안에서는 기존대로 잔액 큰 순.
    if(_fxQ){
      data=_fxRankSort(data, _fxQ,
        function(x){ return x.name; }, function(x){ return x.vbiz; },
        function(a,b){ return b.bal-a.bal; });
    } else {
      data.sort(function(a,b){ return b.bal-a.bal; });
    }
    var totBal=0, nMisu=0, nLong=0, agT=[0,0,0,0,0];""", 1, 'ARSORT')

    # 3) 미배정 입금 드롭다운 — 등록된 업체
    s = rep(s,
        """    if(q) opts=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    var optsTotal=opts.length;""",
        r"""    if(q){
      opts=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
      // r153: 검색어로 시작하는 업체를 위로 (아래에서 60곳으로 잘리므로 순서가 중요)
      opts=_fxRankSort(opts, q, function(o){ return o.name; }, function(o){ return o.vbiz; }, null);
    }
    var optsTotal=opts.length;""", 1, 'DDOPTS')

    # 4) 미배정 입금 드롭다운 — 계산서에만 있는 거래처
    s = rep(s,
        """    if(q) inv=inv.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
    var invTotal=inv.length;""",
        r"""    if(q){
      inv=inv.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
      inv=_fxRankSort(inv, q, function(o){ return o.name; }, function(o){ return o.vbiz; }, null);
    }
    var invTotal=inv.length;""", 1, 'DDINV')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r153(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r152 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r152 2026-08-26 -->', '<!-- test build r153 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
