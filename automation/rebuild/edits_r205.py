# -*- coding: utf-8 -*-
# r205(회계): 어음 상태가 '부도'면 자동 제외로 등록한다
#  화성 신한어음 자료(2026-01~04)에 `수취(부도)` 상태 1건(175,611,002원 / 유일에너테크)이 있었다.
#  기존 코드는 어음 상태에서 '취소'만 걸러내서, 부도 어음이 정상 수취로 등록돼 그대로 수금으로 잡혔다.
#  → 못 받은 돈인데 미수가 그만큼 줄어 보인다. 게다가 등록할 때 상태 값은 남지 않아
#    나중에 목록만 봐서는 부도 건인지 알 수 없다.
#  처리:
#   (1) 신규 등록 시 상태에 '부도'(또는 지급거절/지급거부)가 있으면 excluded=true 로 넣는다.
#       거래처(vendor)는 그대로 둔다 — 제외 목록에서 복원하면 원래대로 돌아온다.
#       excluded 면 수금 집계(17742행)와 받을어음 현황(18197행) 양쪽에서 함께 빠진다.
#   (2) 만기 전에 올려 둔 어음이 나중에 부도로 바뀐 경우, 같은 파일을 다시 올리면
#       중복(NN| 키)으로 건너뛰던 자리에서 부도 상태만 반영한다(만기일 백필과 같은 방식).
#       단 이미 제외된 건은 건드리지 않는다.
#   (3) 업로드 결과에 '부도 N건 자동 제외'를 빨간 글씨로 따로 표시한다.
#  사용자 지시: "부도라고 잡혀있으면 자동 제외를 시켜줘. 만기일 전에 업로드해서 부도라고
#   안 잡혀있다면 그런 것들은 내가 알아서 제외하도록 할게."
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

# ── (0) 부도 판정 정규식을 _BLK 옆에 둔다 ──────────────────────────────
OLD0 = """            if(_BLK[noteKind]){
"""
NEW0 = """            // r205: 어음 상태가 부도면 자동 제외로 넣는다 (받은 돈이 아니다)
            var _BAD = /부도|지급거절|지급거부/;
            if(_BLK[noteKind]){
"""

# ── (1) 재업로드 시 부도 반영 (만기일 백필과 같은 자리) ────────────────
OLD1 = """              if(seen['NN|'+biz+'|'+noteNo]){
                if(iDue>=0){
                  var nd0=_fxD(row4[iDue]);
                  if(nd0){ fxDeposits.forEach(function(e){ if(e.noteNo===noteNo && e.biz===biz && !e.due){ e.due=nd0; } }); }
                }
                nDup++; fD2++; continue;
              }
"""
NEW1 = """              if(seen['NN|'+biz+'|'+noteNo]){
                if(iDue>=0){
                  var nd0=_fxD(row4[iDue]);
                  if(nd0){ fxDeposits.forEach(function(e){ if(e.noteNo===noteNo && e.biz===biz && !e.due){ e.due=nd0; } }); }
                }
                // r205: 만기 전에 올려 둔 어음이 뒤에 부도로 바뀐 경우 — 다시 올리면 여기서 반영된다
                if(_BAD.test(st)){
                  var _bt=Date.now();
                  fxDeposits.forEach(function(e){
                    if(e.noteNo===noteNo && e.biz===biz && !e.excluded){
                      e.excluded=true; e.exAt=_bt; delete e.held; delete e.heldAt; nBad++; fB2++;
                    }
                  });
                }
                nDup++; fD2++; continue;
              }
"""

# ── (2) 신규 등록 시 부도면 excluded ────────────────────────────────
OLD2 = """              seen['NN|'+biz+'|'+noteNo]=1;
              var v4=_fxResolveVendor(biz, ven4);
              fxDeposits.push({ id:'NT|'+biz+'|'+noteNo, biz:biz, date:d4, amount:amt4, payer:ven4,
                                vendor:v4||'', vbiz:v4?_fxVbizOf(biz,v4):'', kind:'note', bank:noteKind,
                                noteNo:noteNo, due:(iDue>=0?_fxD(row4[iDue]):null), src:'upload' });
              nNote++; fN2++;
              if(v4){ nAuto++; } else { nUn++; fU2++; }
"""
NEW2 = """              seen['NN|'+biz+'|'+noteNo]=1;
              var v4=_fxResolveVendor(biz, ven4);
              var _bad4=_BAD.test(st);   // r205
              fxDeposits.push({ id:'NT|'+biz+'|'+noteNo, biz:biz, date:d4, amount:amt4, payer:ven4,
                                vendor:v4||'', vbiz:v4?_fxVbizOf(biz,v4):'', kind:'note', bank:noteKind,
                                noteNo:noteNo, due:(iDue>=0?_fxD(row4[iDue]):null), src:'upload',
                                excluded:_bad4||undefined, exAt:(_bad4?Date.now():undefined) });   // r205
              nNote++; fN2++;
              if(_bad4){ nBad++; fB2++; }        // r205: 부도는 배정/미배정으로 세지 않는다
              else if(v4){ nAuto++; } else { nUn++; fU2++; }
"""

# ── (3) 카운터 선언 ────────────────────────────────────────────────
OLD3 = "      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, nAx=0, errs=[], lines=[];\n"
NEW3 = "      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, nAx=0, nBad=0, errs=[], lines=[];   // r205: nBad = 부도 어음\n"

OLD4 = "            var fN2=0, fD2=0, fU2=0;\n"
NEW4 = "            var fN2=0, fD2=0, fU2=0, fB2=0;   // r205: fB2 = 이 파일의 부도 건수\n"

# ── (4) 파일별 결과 줄 ──────────────────────────────────────────────
OLD5 = """            lines.push(esc(f.name)+' → '+noteKind+' · 수취 '+fN2+'건'+(fU2?(' · 미배정 '+fU2):'')+(fD2?(' · 중복 '+fD2):''));
"""
NEW5 = """            lines.push(esc(f.name)+' → '+noteKind+' · 수취 '+fN2+'건'
              + (fB2?(' · <b style="color:#dc2626">부도 '+fB2+'건 자동 제외</b>'):'')   // r205
              + (fU2?(' · 미배정 '+fU2):'')+(fD2?(' · 중복 '+fD2):''));
"""

# ── (5) 전체 요약 ──────────────────────────────────────────────────
OLD6 = """      if(nUn) html+='<br><b style="color:#d97706">미배정 '+nUn+'건</b> — 아래 미배정 입금 패널에서 거래처를 지정해 주세요.';
"""
NEW6 = """      if(nBad) html+='<br><b style="color:#dc2626">부도 어음 '+nBad+'건을 자동 제외했습니다</b> — 받지 못한 돈이므로 수금에서 뺀습니다. 하단 "제외한 입금"에서 확인·복원할 수 있습니다.';   // r205
      if(nUn) html+='<br><b style="color:#d97706">미배정 '+nUn+'건</b> — 아래 미배정 입금 패널에서 거래처를 지정해 주세요.';
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD0, NEW0, 1, 'r205 _BAD (%s)' % path)
    s = rep(s, OLD1, NEW1, 1, 'r205 재업로드 부도 반영 (%s)' % path)
    s = rep(s, OLD2, NEW2, 1, 'r205 신규 등록 (%s)' % path)
    s = rep(s, OLD3, NEW3, 1, 'r205 nBad 선언 (%s)' % path)
    s = rep(s, OLD4, NEW4, 1, 'r205 fB2 선언 (%s)' % path)
    s = rep(s, OLD5, NEW5, 1, 'r205 파일별 결과줄 (%s)' % path)
    s = rep(s, OLD6, NEW6, 1, 'r205 전체 요약 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r205 2026-09-28 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
