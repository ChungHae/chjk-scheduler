# -*- coding: utf-8 -*-
# r143: [카드·결제 정산 입금 자동 제외]
#  미배정에 카드사 정산("○○카드 + 번호")과 "결+숫자" 표기 입금이 대량으로 잡히는
#  문제. 이런 입금자명은 거래처 수금이 아니므로 자동 제외 처리.
#  - 규칙: 입금자명에 '카드' 포함, 또는 '결' 바로 뒤 숫자 나열(결:12345…, 결20260821…)
#  - 은행 업로드 시: 별칭·업체명으로 매칭되지 않은 건 중 규칙에 걸리면 자동 제외
#    (제외 목록에 들어가며 언제든 복원 가능) — 결과 메시지에 건수 표시
#  - 소급 적용: 미배정 헤더의 [카드·결제 자동 제외] 버튼(관리자) →
#    현재 미배정·보류 건에 같은 규칙 일괄 적용

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R143 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r143(s, path):
    # (1) 판정 헬퍼 (+소급 적용 핸들러) — _fxRenderUnasg 관련 코드 앞(fxUnDdRender 앞)에 삽입
    s = rep(s, "  window.fxPickCrossVend = function(i, name, vbiz, other){",
            r"""  // r143: 카드·결제 정산 입금자명 판정
  function _fxAutoExclPayer(p){
    p=String(p||'');
    if(/카드/.test(p)) return true;             // 카드사 정산 (신한카드1234, 비씨카드(주) 등)
    if(/결[\s:\-]?\d{4,}/.test(p)) return true; // 결+숫자 나열 (결:12345678, 결20260821 등)
    return false;
  }
  window.fxAutoExclRun = function(){
    if(!_isAdmin()) return;
    var targets=fxDeposits.filter(function(e){ return !e.vendor && !e.excluded && _fxAutoExclPayer(e.payer); });
    if(!targets.length){ showInfoModal('자동 제외','카드·결제 정산 규칙에 걸리는 미배정·보류 입금이 없습니다.'); return; }
    showConfirmModal('카드·결제 정산 자동 제외',
      '입금자명에 "카드" 또는 "결+숫자"가 포함된 미배정·보류 입금 '+targets.length+'건을 제외 처리합니다.\n(제외 목록에서 언제든 복원할 수 있습니다)\n\n계속할까요?',
      function(){
        targets.forEach(function(e){ e.excluded=true; delete e.held; });
        _fxSaveBig().catch(function(_e){});
        _fxMetaRefresh();
        _fxRenderUnasg();
        showInfoModal('자동 제외', targets.length+'건을 제외 처리했습니다. 하단 "제외한 입금"에서 확인·복원할 수 있습니다.');
      }, '제외', '#dc2626');
  };
  window.fxPickCrossVend = function(i, name, vbiz, other){""", 1, 'HELPER')

    # (2) 은행 업로드 시 자동 제외 (미매칭 + 규칙 일치 → excluded)
    s = rep(s, "      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, errs=[], lines=[];",
            "      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, nAx=0, errs=[], lines=[];", 1, 'CNT')
    s = rep(s, r"""            var v6=_fxResolveVendor(biz, payer);
            fxDeposits.push({ id:id6, biz:biz, date:d6, amount:amt6, payer:payer,
                              vendor:v6||'', vbiz:v6?_fxVbizOf(biz,v6):'', kind:'bank', bank:bank, src:'upload' });
            nDep++; fN3++;
            if(v6){ nAuto++; } else { nUn++; fU3++; }""",
            r"""            var v6=_fxResolveVendor(biz, payer);
            var ax6=(!v6 && _fxAutoExclPayer(payer));
            fxDeposits.push({ id:id6, biz:biz, date:d6, amount:amt6, payer:payer,
                              vendor:v6||'', vbiz:v6?_fxVbizOf(biz,v6):'', kind:'bank', bank:bank,
                              excluded:ax6||undefined, src:'upload' });
            nDep++; fN3++;
            if(v6){ nAuto++; } else if(ax6){ nAx++; } else { nUn++; fU3++; }""", 1, 'PUSH')
    s = rep(s, "        + (nAuto?(' · 자동 배정 '+nAuto):'') + (nDup?(' · 중복 제외 '+nDup):'');",
            "        + (nAuto?(' · 자동 배정 '+nAuto):'') + (nAx?(' · 카드·결제 자동 제외 '+nAx):'') + (nDup?(' · 중복 제외 '+nDup):'');", 1, 'MSG')

    # (3) 미배정 헤더에 소급 적용 버튼
    s = rep(s, """        + '<div style="padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706">미배정 입금 '+_fxUnList.length+'건'
        + ' <span style="font-weight:400;color:#8a94a6">— 거래처를 지정하면 같은 입금자명은 다음부터 자동 배정됩니다. 회사 수금이 아니면 제외하세요.</span></div>'""",
            """        + '<div style="padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706;display:flex;align-items:center;gap:8px;flex-wrap:wrap">미배정 입금 '+_fxUnList.length+'건'
        + ' <span style="font-weight:400;color:#8a94a6">— 거래처를 지정하면 같은 입금자명은 다음부터 자동 배정됩니다. 회사 수금이 아니면 제외하세요.</span>'
        + '<span style="flex:1"></span>'
        + (_isAdmin()?'<button type="button" class="btn" onclick="fxAutoExclRun()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#dc2626;background:#fff;font-weight:400" title="입금자명에 카드/결+숫자가 포함된 건을 일괄 제외">카드·결제 자동 제외</button>':'')
        + '</div>'""", 1, 'BTN')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r143(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r142 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r142 2026-08-24 -->', '<!-- test build r143 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
