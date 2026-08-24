# -*- coding: utf-8 -*-
# r142: [사명 변경 + 교차 입금 케이스 — 같은 사업자번호의 타사업장 배정 허용]
#  사례: (주)서진엔지니어링(서울 거래) → 주식회사 서진로보틱스(사명 변경, 화성 거래),
#  사업자번호 동일. 화성 거래대금이 서울 계좌로 입금됨.
#  기존 문제: 같은 번호의 계산서가 이 사업장(서울)에도 있으면 타사업장 안내를
#  숨겨서(r139의 inThis 억제) 화성으로 보낼 입구가 없었고, 기등록 안내를 누르면
#  서울의 옛 이름으로 배정돼 버림.
#  수정:
#  1) 타사업장 안내를 항상 표시 (같은 번호가 이 사업장에 있어도)
#  2) 사업장 이동 배정은 fxPickNewVend 경유를 버리고 직접 배정:
#     - vendor = 타사업장 계산서의 이름(새 사명), vbiz 그대로 → 그 사업장 원장에 연결
#     - 업체 목록은 같은 번호가 이미 등록돼 있으면 그대로 둠(중복 등록 안 함),
#       없으면 등록
#     - 별칭 학습 안 함 (예외 케이스라 자동화하면 오배정 위험)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R142 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r142(s, path):
    # (1) inThis 억제 제거 — 타사업장 계산서 거래처는 항상 안내
    s = rep(s, r"""    var seenB={};
    fxSalesInv.forEach(function(e){
      if(e.biz!==other || !e.vendor || !match(e)) return;
      // 이 사업장(biz)에도 같은 사업자번호 계산서가 있으면 (a)/일반 경로로 처리되므로 제외
      var d=(e.vbiz||'').replace(/[^0-9]/g,'');
      var inThis = fxSalesInv.some(function(x){ return x.biz===biz && String(x.vbiz||'').replace(/[^0-9]/g,'')===d && d; });
      if(inThis) return;
      if(!seenB[e.vendor]){ seenB[e.vendor]=1; hints.push({type:'other', inv:e.vendor, vbiz:e.vbiz||'', other:other}); }
    });""",
            r"""    var seenB={};
    fxSalesInv.forEach(function(e){
      if(e.biz!==other || !e.vendor || !match(e)) return;
      // 같은 사업자번호가 이 사업장에 있어도 안내 (사명 변경 후 타사업장 거래 케이스)
      if(!seenB[e.vendor]){ seenB[e.vendor]=1; hints.push({type:'other', inv:e.vendor, vbiz:e.vbiz||'', other:other}); }
    });""", 1, 'NOSUPPRESS')

    # (2) 안내 표시 조건: 미등록 후보가 있어도 타사업장 안내는 보여야 함
    s = rep(s, "    if(q && !inv.length){",
            "    if(q){", 1, 'HINTCOND')

    # (3) 사업장 이동 배정 — 직접 배정 방식으로 재작성
    s = rep(s, r"""  window.fxPickCrossVend = function(i, name, vbiz, other){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 지정할 수 없습니다.'); return; }
    var d=_fxUnList[i]; if(!d) return;
    fxUnDdHide();
    showConfirmModal('사업장 이동 배정',
      d.date+' · '+_fxFmt(d.amount)+'원 · 입금자 "'+(d.payer||'')+'"\n\n'
      + d.biz+' 계좌로 들어온 입금이지만 '+other+' 거래처 "'+name+'" 의 수금입니다.\n'
      + '이 입금의 사업장을 '+other+'(으)로 바꿔 배정할까요?\n'
      + '(원장·엑셀에는 "'+d.biz+' 계좌" 표기가 남습니다)',
      function(){
        d.obiz=d.biz;
        d.biz=other;
        fxPickNewVend(i, name, vbiz);
      }, other+'(으)로 배정', '#b45309');
  };""",
            r"""  window.fxPickCrossVend = function(i, name, vbiz, other){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 지정할 수 없습니다.'); return; }
    var d=_fxUnList[i]; if(!d) return;
    fxUnDdHide();
    var dup=(typeof _findClientByBiz==='function' && vbiz) ? _findClientByBiz(vbiz, null) : null;
    var nameReg=(allClients()||[]).some(function(c){ return c && c[0]===name; });
    var extra='';
    if(dup && dup!==name) extra='\n※ 업체 목록에는 같은 사업자번호가 "'+dup+'"(으)로 등록되어 있습니다 — 입금은 "'+name+'" 이름으로 '+other+' 원장에 연결됩니다.';
    else if(!dup && !nameReg) extra='\n※ "'+name+'" 은(는) 일정 > 업체에 함께 등록됩니다.';
    showConfirmModal('사업장 이동 배정',
      d.date+' · '+_fxFmt(d.amount)+'원 · 입금자 "'+(d.payer||'')+'"\n\n'
      + d.biz+' 계좌로 들어온 입금이지만 '+other+' 거래처 "'+name+'" 의 수금입니다.\n'
      + '이 입금의 사업장을 '+other+'(으)로 바꿔 배정할까요?\n'
      + '(원장·엑셀에는 "'+d.biz+' 계좌" 표기가 남습니다)'+extra,
      function(){
        d.obiz=d.biz;
        d.biz=other;
        if(!dup && !nameReg){
          try{ ensureClientList(); }catch(_e){}
          clientList.push([name, vbiz||'']);
          _saveClients();
        }
        d.vendor=name;
        d.vbiz=vbiz || _fxVbizOf(other, name) || '';
        // 별칭 학습 없음: 교차 입금은 예외 케이스라 자동 배정하면 오배정 위험
        _fxSaveBig().catch(function(_e){});
        _fxMetaRefresh();
        _fxRenderUnasg();
      }, other+'(으)로 배정', '#b45309');
  };""", 1, 'CROSS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r142(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r141 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r141 2026-08-24 -->', '<!-- test build r142 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
