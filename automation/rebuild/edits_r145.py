# -*- coding: utf-8 -*-
# r145: [대표자명 자동 배정]
#  입금자명이 업체 상세정보의 '대표자' 이름과 일치하면 해당 업체로 자동 배정.
#  - 동명이인(같은 대표자명이 2개 이상 업체에 등록)은 매칭하지 않음(오배정 방지)
#  - 매칭 순서: 별칭 → 업체명 직접 일치 → 원장 거래명 → 대표자명(단독일 때만)
#  - 공백 무시 비교("김 재 성"=="김재성"), 대표자 칸의 쉼표/슬래시 복수 표기 지원
#  - 소급: 미배정 헤더 [자동 배정 재실행] 버튼(관리자) → 미배정·보류 전체에
#    현행 규칙(별칭·업체명·대표자명) 재적용, 성공 건은 보류 해제
#  - 업로드 자동 배정 시 사업자번호를 업체 목록 기준(_fxClientVbiz)으로 채움

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R145 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r145(s, path):
    # (1) 대표자명 맵 + 판정 확장
    s = rep(s, r"""  function _fxResolveVendor(biz, payer){
    var p=String(payer||'').trim(); if(!p) return null;
    if(fxAlias[biz+'|'+p]) return fxAlias[biz+'|'+p];
    if(typeof allClients==='function' && (allClients()||[]).some(function(c){ return c && String(c[0]).trim()===p; })) return p;
    if(_fxVendorNames(biz).indexOf(p)>=0) return p;
    return null;
  }""",
            r"""  // r145: 대표자명 → 업체 맵 (업체 상세의 '대표자' 기준, 공백 제거·쉼표/슬래시 분리)
  var _fxCeoMemo=null, _fxCeoStamp='';
  function _fxCeoMap(){
    var cl=(typeof allClients==='function' && allClients())||[];
    var ci=(typeof clientInfo==='object' && clientInfo)||{};
    var stamp=cl.length+':'+Object.keys(ci).length;
    if(_fxCeoMemo && _fxCeoStamp===stamp) return _fxCeoMemo;
    var m={};
    cl.forEach(function(c){
      if(!c || !c[0]) return;
      var nm=String(c[0]).trim(); if(!nm) return;
      var inf=ci[nm]||{};
      String(inf.ceo||'').split(/[,\/·]/).forEach(function(part){
        var k=part.replace(/\s+/g,''); if(k.length<2) return;
        if(!m[k]) m[k]=[];
        if(m[k].indexOf(nm)<0) m[k].push(nm);
      });
    });
    _fxCeoMemo=m; _fxCeoStamp=stamp;
    return m;
  }
  function _fxResolveVendor(biz, payer){
    var p=String(payer||'').trim(); if(!p) return null;
    if(fxAlias[biz+'|'+p]) return fxAlias[biz+'|'+p];
    if(typeof allClients==='function' && (allClients()||[]).some(function(c){ return c && String(c[0]).trim()===p; })) return p;
    if(_fxVendorNames(biz).indexOf(p)>=0) return p;
    var cm=_fxCeoMap(), ck=p.replace(/\s+/g,'');
    if(cm[ck] && cm[ck].length===1) return cm[ck][0];  // 대표자명 단독 일치 (동명이인 제외)
    return null;
  }""", 1, 'RESOLVE')

    # (2) 업로드 자동 배정 시 사업자번호를 업체 목록 기준으로
    s = rep(s, "vendor:v6||'', vbiz:v6?_fxVbizOf(biz,v6):'', kind:'bank', bank:bank,",
            "vendor:v6||'', vbiz:v6?_fxClientVbiz(v6,biz):'', kind:'bank', bank:bank,", 1, 'VBIZ')

    # (3) 소급 재매칭 핸들러
    s = rep(s, "  window.fxPickCrossVend = function(i, name, vbiz, other){",
            r"""  // r145: 현행 규칙(별칭·업체명·대표자명)으로 미배정·보류 재매칭
  window.fxReassignRun = function(){
    if(!_isAdmin()) return;
    var hits=[];
    fxDeposits.forEach(function(e){
      if(e.vendor || e.excluded) return;
      var v=_fxResolveVendor(e.biz, e.payer);
      if(v) hits.push([e,v]);
    });
    if(!hits.length){ showInfoModal('자동 배정 재실행','현재 규칙(별칭·업체명·대표자명)으로 새로 배정되는 미배정·보류 입금이 없습니다.'); return; }
    showConfirmModal('자동 배정 재실행',
      '별칭·업체명·대표자명 규칙으로 미배정·보류 입금 '+hits.length+'건이 배정됩니다.\n(대표자명은 동명이인이 없을 때만 매칭됩니다)\n\n계속할까요?',
      function(){
        hits.forEach(function(h){ var e=h[0]; e.vendor=h[1]; e.vbiz=_fxClientVbiz(h[1], e.biz); delete e.held; });
        _fxSaveBig().catch(function(_e){});
        _fxMetaRefresh();
        _fxRenderUnasg();
        showInfoModal('자동 배정', hits.length+'건을 배정했습니다. 잘못 배정된 건은 원장의 연필 버튼으로 되돌릴 수 있습니다.');
      }, '배정', '#14305c');
  };
  window.fxPickCrossVend = function(i, name, vbiz, other){""", 1, 'RERUN')

    # (4) 미배정 헤더 버튼 추가 (자동 배정 재실행 — 카드·결제 버튼 왼쪽)
    s = rep(s, """        + (_isAdmin()?'<button type="button" class="btn" onclick="fxAutoExclRun()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#dc2626;background:#fff;font-weight:400" title="입금자명이 카드·결제 정산 형식(카드 / 카드사명+숫자 / 결+숫자)인 건을 일괄 제외">카드·결제 자동 제외</button>':'')""",
            """        + (_isAdmin()?'<button type="button" class="btn" onclick="fxReassignRun()" style="font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#14305c;background:#fff;font-weight:400" title="별칭·업체명·대표자명 규칙으로 미배정·보류 건을 다시 매칭">자동 배정 재실행</button>':'')
        + (_isAdmin()?'<button type="button" class="btn" onclick="fxAutoExclRun()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#dc2626;background:#fff;font-weight:400" title="입금자명이 카드·결제 정산 형식(카드 / 카드사명+숫자 / 결+숫자)인 건을 일괄 제외">카드·결제 자동 제외</button>':'')""", 1, 'BTN')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r145(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r144 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r144 2026-08-25 -->', '<!-- test build r145 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
