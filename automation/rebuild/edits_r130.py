# -*- coding: utf-8 -*-
# r130: [매입매출 전면 재적재 지원]
#  - 자료 업로드 탭에 관리자 전용 "거래 자료 초기화" 카드:
#    삭제 = 매출·매입 계산서 / 입금·어음 / 조정(상계·예외) / 기초이월
#    유지 = 입금자명 별칭 / 결제조건 / 제외거래처
#    (앱 자체 showConfirmModal 경유 — 네이티브 confirm 사용 안 함)
#  - 원장 병합 보강: 사업자번호 없는 슬롯(N|이름)을 같은 이름의 사업자번호 슬롯에 병합
#    (홈택스 상호명 ↔ 별칭 거래처명이 달라 입금이 갈라지는 문제 방지)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R130 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r130(s, path):
    # ── (1) 업로드 탭: 초기화 카드 (관리자 전용) ──
    s = rep(s, """      + _upCard('기존 앱 누적본 가져오기',
                '입출금 앱 누적자료 zip (거래처 파일·설정표 자동 인식, 재업로드 안전)',
                _lblBtn('fxImportLegacy','.zip',false))
      + '</div>'""",
            """      + _upCard('기존 앱 누적본 가져오기',
                '입출금 앱 누적자료 zip (거래처 파일·설정표 자동 인식, 재업로드 안전)',
                _lblBtn('fxImportLegacy','.zip',false))
      + (_isAdmin() ? _upCard('거래 자료 초기화',
                '계산서(매출·매입)·입금·어음·조정(상계/예외)·기초이월을 모두 삭제하고 처음부터 다시 올릴 때 사용합니다. 별칭·결제조건·제외거래처 설정은 유지됩니다.',
                '<button type="button" class="btn" onclick="fxResetData()" style="font-size:12px;padding:5px 14px;border:1px solid #dc2626;color:#dc2626;background:#fff">초기화…</button>') : '')
      + '</div>'""", 1, 'CARD')

    # ── (2) 초기화 동작 ──
    s = rep(s, "  function parseExcelDate(excelDate) {",
            """  window.fxResetData = function(){
    if(!_isAdmin()){ showInfoModal('매입매출','관리자만 초기화할 수 있습니다.'); return; }
    showConfirmModal('거래 자료 초기화',
      '매입매출의 거래 자료를 모두 삭제합니다.\\n\\n삭제: 매출·매입 세금계산서, 입금·어음 내역, 조정(상계·예외처리), 기초이월\\n유지: 입금자명 별칭, 결제조건, 제외거래처\\n\\n삭제 후에는 되돌릴 수 없습니다. 계속할까요?',
      async function(){
        try{
          _fxUpLog('초기화 중… (Firebase)');
          fxSalesInv=[]; fxPurchInv=[]; fxDeposits=[];
          fxAdjusts=[]; fxOpenings={};
          await _fxSaveBig();
          _fxSave();
          _fxLoaded=true;
          _fxMetaRefresh();
          _fxRenderUnasg();
          _fxUpLog('<b style="color:#15803d">초기화 완료</b> — 계산서·입금·어음·조정·기초이월이 삭제되었습니다. 설정(별칭·결제조건·제외거래처)은 유지됩니다.<br>'
            + '<span style="color:#8a94a6">이제 홈택스 세금계산서(매출·매입, 2021~현재)와 은행 입금·어음 파일을 올려주세요. 같은 파일을 여러 번 올려도 중복되지 않습니다.</span>');
        }catch(e){ _fxUpLog('<b style="color:#dc2626">초기화 실패:</b> '+esc(String(e&&e.message||e))); }
      }, '초기화', '#dc2626');
  };
  function parseExcelDate(excelDate) {""", 1, 'RESET')

    # ── (3) 원장 병합 보강: N|이름 슬롯 → 같은 이름의 사업자번호 슬롯 ──
    s = rep(s, """    var excl={}; fxExcluded.forEach(function(x){ if(x.biz===region){ excl[x.vbiz||'']=1; excl['N:'+x.vendor]=1; } });""",
            """    // 사업자번호 없는 슬롯(N|이름)은 같은 이름의 사업자번호 슬롯에 병합
    // (홈택스 상호명과 별칭 거래처명이 같으면 입금·계산서가 한 원장으로 합쳐진다)
    Object.keys(map).forEach(function(mk){
      if(mk.indexOf('N|')!==0) return;
      var nm=map[mk].name; if(!nm) return;
      var tgt=null;
      Object.keys(map).forEach(function(ok){ if(!tgt && ok.indexOf('N|')!==0 && map[ok].name===nm) tgt=map[ok]; });
      if(tgt){
        var src=map[mk];
        tgt.invs=tgt.invs.concat(src.invs);
        tgt.deps=tgt.deps.concat(src.deps);
        tgt.adjs=tgt.adjs.concat(src.adjs);
        if(src.opening){ tgt.opening+=src.opening; if(!tgt.openDate) tgt.openDate=src.openDate; }
        delete map[mk];
      }
    });
    var excl={}; fxExcluded.forEach(function(x){ if(x.biz===region){ excl[x.vbiz||'']=1; excl['N:'+x.vendor]=1; } });""", 1, 'MERGE')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r130(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r129 2026-08-22 -->') == 1
            s = s.replace('<!-- test build r129 2026-08-22 -->', '<!-- test build r130 2026-08-22 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
