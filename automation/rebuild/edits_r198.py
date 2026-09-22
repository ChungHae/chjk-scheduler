# -*- coding: utf-8 -*-
# r198(회계): iM뱅크 입출금 내역 자동 등록 + iM 어음 파일 차단 (통장 기준 — 사용자 결정 2026-09-22)
#  근거(실자료 대조): iM 통장(504-10-417569-9, 2021-01~2022-12)에 어음 10건이 전부 결제일에
#   같은 금액으로 '자동이체 · 신진엠텍(주)' 입금됨(9/25 토요일분만 9/27). 통장에는 어음 파일에 없는
#   신진엠텍 입금 2건(2021-08-25 17,869,335 / 2021-08-30 37,563,306)이 더 있음 → 통장이 더 완전.
#  iM 통장 헤더: NO | 거래일시 | 거래종류 | 출금금액 | 입금금액 | 거래후잔액 | 비고(=입금자) | 메모
#   거래일시 형식 '2022-12-25 [02:43:12]' (공백 뒤는 _fxD 가 버림)
#   예금이자 행은 비고에 '**이자 30 법인세 0 …' 이 들어온다 → 입금자를 '예금이자'로 정리하고 자동 제외.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OPS = [
 # (1) 어음 차단에 iM어음 추가 + 문구를 은행별 표로
 ("guard-comment",
  "            //  iM뱅크(r197)는 대금이 업로드하지 않는 iM 계좌로 들어가므로 이 파일이 유일한 기록 → 받는다.\n"
  "            //   (나중에 iM 입출금 내역까지 올리게 되면 그때는 하나·기업처럼 막아야 한다.)\n"
  "            if(noteKind==='하나채권' || noteKind==='기업어음'){\n"
  "              var _bkNm = (noteKind==='하나채권') ? '하나은행 어음(전자채권)' : '기업은행 어음(전자매출채권)';\n"
  "              var _bkWhy = (noteKind==='하나채권')\n"
  "                ? '하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어옵니다. '\n"
  "                : '기업은행은 어음이 만기결제되면 입출금 내역에 거래처명으로 그대로 입금됩니다. ';\n"
  "              var _bkNm2 = (noteKind==='하나채권') ? '하나은행' : '기업은행';\n"
  "              warns.push(esc(f.name)+': <b>'+_bkNm+' 파일은 올리지 않습니다 — 0건 등록하고 건너뛰었습니다.</b><br>'\n"
  "                + _bkWhy\n"
  "                + '이 파일을 올리면 같은 돈이 두 번 잡히므로, '+_bkNm2+'은 <b>입출금 내역만</b> 올려주세요.');\n"
  "              continue;\n"
  "            }\n",
  "            //   iM   : (r198) 통장에 「자동이체 · 거래처명」으로 입금 (10건 전수 대조, 통장이 2건 더 많음)\n"
  "            //  → r197 에서 받던 iM 어음도 r198 부터 차단. iM 은 입출금 내역으로 받는다.\n"
  "            var _BLK = {\n"
  "              '하나채권': ['하나은행 어음(전자채권)', '하나은행은', '하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어옵니다. '],\n"
  "              '기업어음': ['기업은행 어음(전자매출채권)', '기업은행은', '기업은행은 어음이 만기결제되면 입출금 내역에 거래처명으로 그대로 입금됩니다. '],\n"
  "              'iM어음':   ['iM뱅크 어음(채권명세)', 'iM뱅크는', 'iM뱅크는 어음이 결제되면 입출금 내역에 「자동이체」로 거래처명과 함께 그대로 입금됩니다. ']\n"
  "            };\n"
  "            if(_BLK[noteKind]){\n"
  "              var _bk=_BLK[noteKind];\n"
  "              warns.push(esc(f.name)+': <b>'+_bk[0]+' 파일은 올리지 않습니다 — 0건 등록하고 건너뛰었습니다.</b><br>'\n"
  "                + _bk[2]\n"
  "                + '이 파일을 올리면 같은 돈이 두 번 잡히므로, '+_bk[1]+' <b>입출금 내역만</b> 올려주세요.');\n"
  "              continue;\n"
  "            }\n"),
 # (2) iM 통장 판별 — PAYKEY 보다 먼저, 헤더 3개가 모두 있어야 iM 으로 본다
 ("detect-im",
  "            var rr5=(rows[r5]||[]).map(_fxCell);\n"
  "            for(var k=0;k<_FX_PAYKEY.length;k++){\n",
  "            var rr5=(rows[r5]||[]).map(_fxCell);\n"
  "            // r198: iM뱅크 — 입금자는 '비고' 열. 비고는 흔한 열 이름이라 거래종류·입금금액과 함께 있을 때만.\n"
  "            if(rr5.indexOf('거래종류')>=0 && rr5.indexOf('입금금액')>=0 && rr5.indexOf('비고')>=0){\n"
  "              bank='iM'; iPay=rr5.indexOf('비고'); hIdx=r5; H=rr5; break;\n"
  "            }\n"
  "            for(var k=0;k<_FX_PAYKEY.length;k++){\n"),
 # (3) 입금 열 이름에 '입금금액' 추가
 ("in-col",
  "          ['입금액(원)','입금금액(원)','입금(원)','입금액','입금'].some(",
  "          ['입금액(원)','입금금액(원)','입금(원)','입금액','입금금액','입금'].some("),
 # (4) iM 예금이자 행: 입금자를 '예금이자'로
 ("im-kind",
  "          var iRem = (bank==='하나') ? H.indexOf('적요') : -1;\n",
  "          var iRem = (bank==='하나') ? H.indexOf('적요') : -1;\n"
  "          var iKind = (bank==='iM') ? H.indexOf('거래종류') : -1;   // r198\n"),
 ("im-payer",
  "            if(!payer && iRem>=0){ payer=_fxCell(row6[iRem]); _fromRem=!!payer; }   // r190\n",
  "            if(!payer && iRem>=0){ payer=_fxCell(row6[iRem]); _fromRem=!!payer; }   // r190\n"
  "            if(iKind>=0 && _fxCell(row6[iKind])==='예금이자') payer='예금이자';   // r198: '**이자 30 법인세 0…' 정리\n"),
 # (5) 예금이자는 자동 제외 (수금이 아님)
 ("autoexcl",
  "    if(/카드/.test(p)) return true;             // 카드사 정산 (신한카드1234, 비씨카드(주) 등)\n",
  "    if(/카드/.test(p)) return true;             // 카드사 정산 (신한카드1234, 비씨카드(주) 등)\n"
  "    if(/^(예금)?이자$/.test(p)) return true;     // r198: 예금이자 (거래처 수금 아님)\n"),
]

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    for label, old, new in OPS:
        s = rep(s, old, new, 1, 'r198 %s (%s)' % (label, path))
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r198 2026-09-22 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
