# -*- coding: utf-8 -*-
# r151: [매입매출 전체 속도 개선 — 원장 캐시 + O(n^2) 제거 + 검색 디바운스]
#
#  증상: 회계 > 매입매출의 모든 탭(미수현황·집계·자료업로드)이 버벅임.
#        특히 검색어 입력·페이지 이동·필터 변경 때마다 화면이 멈춤.
#
#  실측(거래처 1,700곳 / 매출 15,300건 / 매입 12,240건 / 입금 10,600건 기준):
#    _fxLedgers('all')          101ms
#    _fxDupCandidates('all')    217ms   (내부에서 _fxLedgers 를 또 부름)
#    _fxRenderArBody() 1회      263ms
#    검색 1글자                  391ms  -> "한국과학" 4글자 = 약 1.5초 멈춤
#    _fxLedgersOne 단계별: 기초이월 매칭 31.9ms(O(기초 x 거래처)) 가 최대 단일 병목
#
#  원인 4가지:
#   (1) _fxRenderArBody 한 번에 _fxLedgers 가 2~3회 중복 계산됨
#       (본문 1회 + 중복거래처 칩 1회 + 중복 패널 열려 있으면 1회 더).
#       원장은 자료가 안 바뀌면 결과가 같은데 매번 처음부터 다시 만들고 있었음.
#   (2) _fxDupCandidates 가 거래처 전체를 두 겹 for 문으로 비교 -> 1,700곳이면
#       약 144만 쌍, 각 쌍마다 이름 정규화(정규식)를 2번씩 = 290만 번 문자열 연산.
#   (3) _fxLedgersOne 안의 기초이월 매칭 / 'N|이름' 병합이 각각 O(n^2) 중첩 루프.
#   (4) 검색창이 한 글자마다 전체 재계산+재렌더를 즉시 실행.
#
#  수정:
#   A. 원장 캐시: 자료 상태 지문(_fxDataStamp)이 같으면 _fxLedgers/_fxDupCandidates
#      결과를 재사용. 지문은 저장 카운터(_fxCacheBump) + 각 배열 길이로 구성하고,
#      _fxSave() / _fxSaveBig() / 자료 로드 / 외부 동기화 재적재 시 카운터를 올려
#      자료가 바뀌면 반드시 새로 계산되게 함(오래된 수치 표시 방지).
#   B. _fxDupCandidates: 정규화 이름으로 묶어 O(n^2) -> O(n). 짝 순서(i<j)는 기존 동일.
#   C. _fxLedgersOne: 이름 인덱스를 미리 만들어 기초이월 매칭·N| 병합을 O(n)으로.
#   D. _fxDue: (일자,결제조건) 결과 메모이제이션 — 계산서 건수만큼 Date 생성하던 것 제거.
#   E. 검색창(미수현황·거래처별 집계) 180ms 디바운스 — 타이핑 중 재계산 안 함.
#   F. fxArXls 가 캐시 배열을 그대로 sort 하지 않도록 slice() 추가(캐시 오염 방지).
#
#  주의: 표시되는 숫자·판정 로직은 하나도 바뀌지 않음. 계산 결과는 완전히 동일하고
#        "언제 다시 계산하느냐"와 "어떻게 찾느냐"만 바꾼 순수 성능 수정.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R151 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r151(s, path):
    # A-1. 캐시 무효화 카운터 선언 (fx 상태 변수 옆)
    s = rep(s,
        "  let fxExcluded  = load('sched_fx_excluded') ?? [];  // 제외 거래처 [{biz,vendor,vbiz,reason}]",
        "  let fxExcluded  = load('sched_fx_excluded') ?? [];  // 제외 거래처 [{biz,vendor,vbiz,reason}]\n"
        "  var _fxCacheBump = 0;  // r151: 원장 캐시 무효화 카운터 (자료가 바뀔 때마다 +1)",
        1, 'BUMPDECL')

    # A-2. 외부 동기화 재적재 시 무효화
    s = rep(s,
        "    fxExcluded       = load('sched_fx_excluded') ?? [];\n    personalSchedules= load('sched_personal')    ?? [];",
        "    fxExcluded       = load('sched_fx_excluded') ?? [];\n    _fxCacheBump++;\n    personalSchedules= load('sched_personal')    ?? [];",
        1, 'BUMPSYNC')

    # A-3. 대용량 자료 로드 완료 시 무효화
    s = rep(s,
        "      fxDeposits = got['dep_서울'].concat(got['dep_화성']);\n      _fxLoaded = true;",
        "      fxDeposits = got['dep_서울'].concat(got['dep_화성']);\n      _fxCacheBump++;\n      _fxLoaded = true;",
        1, 'BUMPLOAD')

    # A-4. 저장 시 무효화 (모든 변경 경로가 이 둘 중 하나를 반드시 거침)
    s = rep(s, "  async function _fxSaveBig(){\n    var jobs=[];",
               "  async function _fxSaveBig(){\n    _fxCacheBump++;\n    var jobs=[];", 1, 'BUMPBIG')
    s = rep(s, "  function _fxSave(){   // 소용량 설정만 메인 동기화로\n    save('sched_fx_alias', fxAlias);",
               "  function _fxSave(){   // 소용량 설정만 메인 동기화로\n    _fxCacheBump++;\n    save('sched_fx_alias', fxAlias);",
               1, 'BUMPSAVE')

    # E-1. 미수현황 검색 디바운스
    s = rep(s,
        "  window.fxSearchInput = function(v){ _fxQ=String(v||'').trim().toLowerCase(); _fxExp=null; _fxArPage=1; _fxRenderArBody(); };",
        r"""  var _fxSearchT=null;
  window.fxSearchInput = function(v){
    _fxQ=String(v||'').trim().toLowerCase(); _fxExp=null; _fxArPage=1;
    if(_fxSearchT) clearTimeout(_fxSearchT);
    _fxSearchT=setTimeout(function(){ _fxSearchT=null; _fxRenderArBody(); }, 180);
  };""", 1, 'DEBAR')

    # E-2. 거래처별 집계 검색 디바운스
    s = rep(s,
        "  window.fxSumSearch = function(v){ _fxSumQ=String(v||'').trim().toLowerCase(); _fxRenderSumBody(); };",
        r"""  var _fxSumSearchT=null;
  window.fxSumSearch = function(v){
    _fxSumQ=String(v||'').trim().toLowerCase();
    if(_fxSumSearchT) clearTimeout(_fxSumSearchT);
    _fxSumSearchT=setTimeout(function(){ _fxSumSearchT=null; _fxRenderSumBody(); }, 180);
  };""", 1, 'DEBSUM')

    # C-1. 기초이월 매칭: O(기초 x 거래처) -> O(기초 + 거래처)
    s = rep(s,
        """    Object.keys(fxOpenings).forEach(function(k){
      var p=k.split('|'); if(p[0]!==region) return;
      var o=fxOpenings[k]||{};
      var target=null;
      Object.keys(map).forEach(function(mk){ if(!target && _fxNormWs(map[mk].name)===_fxNormWs(p[1])) target=map[mk]; });
      var sl = target || slot('', p[1]);
      sl.opening=Number(o.amount)||0; sl.openDate=o.asOf||null;
    });""",
        r"""    // r151: 정규화 이름 인덱스를 한 번만 만들어 매칭 (결과는 기존과 동일 - 첫 일치 슬롯 선택)
    var _nmIdx=Object.create(null);
    Object.keys(map).forEach(function(mk){ var n=_fxNormWs(map[mk].name); if(n && _nmIdx[n]===undefined) _nmIdx[n]=mk; });
    Object.keys(fxOpenings).forEach(function(k){
      var p=k.split('|'); if(p[0]!==region) return;
      var o=fxOpenings[k]||{};
      var _pn=_fxNormWs(p[1]);
      var target=(_pn && _nmIdx[_pn]!==undefined) ? map[_nmIdx[_pn]] : null;
      var sl = target || slot('', p[1]);
      if(!target && _pn && _nmIdx[_pn]===undefined) _nmIdx[_pn]=sl.key;
      sl.opening=Number(o.amount)||0; sl.openDate=o.asOf||null;
    });""", 1, 'OPENIDX')

    # C-2. 'N|이름' 슬롯 병합: O(거래처^2) -> O(거래처)
    s = rep(s,
        """    Object.keys(map).forEach(function(mk){
      if(mk.indexOf('N|')!==0) return;
      var nm=map[mk].name; if(!nm) return;
      var tgt=null;
      Object.keys(map).forEach(function(ok){ if(!tgt && ok.indexOf('N|')!==0 && _fxNormWs(map[ok].name)===_fxNormWs(nm)) tgt=map[ok]; });
      if(tgt){""",
        r"""    // r151: 사업자번호 있는 슬롯을 정규화 이름으로 미리 인덱싱 (첫 일치 선택 - 기존과 동일)
    var _regIdx=Object.create(null);
    Object.keys(map).forEach(function(ok){
      if(ok.indexOf('N|')===0) return;
      var n=_fxNormWs(map[ok].name); if(n && _regIdx[n]===undefined) _regIdx[n]=ok;
    });
    Object.keys(map).forEach(function(mk){
      if(mk.indexOf('N|')!==0) return;
      var nm=map[mk].name; if(!nm) return;
      var _nn=_fxNormWs(nm);
      var tgt=(_nn && _regIdx[_nn]!==undefined) ? map[_regIdx[_nn]] : null;
      if(tgt){""", 1, 'MERGEIDX')

    # A-5. 원장 캐시
    s = rep(s,
        """  function _fxLedgers(region){
    if(region==='all') return _fxLedgersOne('서울').concat(_fxLedgersOne('화성'));
    return _fxLedgersOne(region);
  }""",
        r"""  // r151: 원장 캐시 - 자료가 그대로면 다시 계산하지 않음
  //  (한 번 그릴 때 본문·중복거래처 칩·중복 패널이 각각 _fxLedgers 를 부르던 중복 제거)
  var _fxLedCache=Object.create(null), _fxDupCache=Object.create(null), _fxLedStamp=null;
  function _fxDataStamp(){
    return _fxCacheBump+'|'+fxSalesInv.length+'|'+fxPurchInv.length+'|'+fxDeposits.length
         +'|'+fxAdjusts.length+'|'+fxExcluded.length;
  }
  function _fxCacheSync(){
    var st=_fxDataStamp();
    if(st!==_fxLedStamp){ _fxLedCache=Object.create(null); _fxDupCache=Object.create(null); _fxLedStamp=st; }
  }
  function _fxLedgers(region){
    _fxCacheSync();
    var ck='R|'+region;
    if(_fxLedCache[ck]) return _fxLedCache[ck];
    var r = (region==='all') ? _fxLedgersOne('서울').concat(_fxLedgersOne('화성')) : _fxLedgersOne(region);
    _fxLedCache[ck]=r;
    return r;
  }""", 1, 'LEDCACHE')

    # B. 중복 거래처 후보: O(n^2) -> O(n) + 캐시
    s = rep(s,
        """  function _fxDupCandidates(region){
    var rows = _fxLedgers(region==='all'?'all':region);
    var out=[];
    for(var i=0;i<rows.length;i++){
      for(var j=i+1;j<rows.length;j++){
        var a=rows[i], b=rows[j];
        if(a.rgn!==b.rgn || a.name===b.name) continue;
        var na=_fxNormName(a.name);
        if(na && na===_fxNormName(b.name)) out.push([a,b]);
      }
    }
    return out;
  }""",
        r"""  function _fxDupCandidates(region){
    _fxCacheSync();
    var ck='D|'+region;
    if(_fxDupCache[ck]) return _fxDupCache[ck];
    var rows = _fxLedgers(region==='all'?'all':region);
    // r151: 사업장+정규화이름으로 묶어서 같은 묶음 안에서만 비교 (기존 전수 비교와 결과·순서 동일)
    var g=Object.create(null), nk=new Array(rows.length);
    for(var i=0;i<rows.length;i++){
      var na=_fxNormName(rows[i].name);
      nk[i] = na ? (rows[i].rgn+' '+na) : null;
      if(nk[i]!==null){ if(g[nk[i]]===undefined) g[nk[i]]=[]; g[nk[i]].push(i); }
    }
    var out=[];
    for(var i2=0;i2<rows.length;i2++){
      var k2=nk[i2]; if(k2===null) continue;
      var arr=g[k2]; if(arr.length<2) continue;
      for(var t=0;t<arr.length;t++){
        var j2=arr[t];
        if(j2<=i2) continue;
        if(rows[i2].name===rows[j2].name) continue;
        out.push([rows[i2], rows[j2]]);
      }
    }
    _fxDupCache[ck]=out;
    return out;
  }""", 1, 'DUPFAST')

    # D. 만기일 계산 메모이제이션
    s = rep(s,
        """  function _fxDue(dateStr, term){
    var m=String(term||'').match(/^(익+)월(초|중순|말)$/);""",
        r"""  var _fxDueCache=Object.create(null);
  function _fxDue(dateStr, term){
    var _ck=dateStr+' '+(term||'');
    var _cv=_fxDueCache[_ck];
    if(_cv!==undefined) return _cv;
    var _r=_fxDueCalc(dateStr, term);
    _fxDueCache[_ck]=_r;
    return _r;
  }
  function _fxDueCalc(dateStr, term){
    var m=String(term||'').match(/^(익+)월(초|중순|말)$/);""", 1, 'DUEMEMO')

    # F. 엑셀 내보내기가 캐시 배열을 직접 정렬하지 않도록
    s = rep(s, "      var data=_fxLedgers(_fxRegion);",
               "      var data=_fxLedgers(_fxRegion).slice();", 1, 'XLSSLICE')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r151(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r150 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r150 2026-08-25 -->', '<!-- test build r151 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
