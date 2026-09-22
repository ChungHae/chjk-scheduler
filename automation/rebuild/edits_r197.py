# -*- coding: utf-8 -*-
# r197(회계): iM뱅크(구 대구은행) 어음 = '채권명세조회' 파일 인식
#  헤더: NO | 발행구분 | 구매업체명 | 등록일 | 결제일 | 공급가액 | 매출채권금액 | 기대출취급액 | 채권번호 | 입금계좌
#  하나채권(채권번호+구매'기업'명)과 달리 구매'업체'명 → 겹치지 않는다.
#  2026-09-22 실자료 10건(신진엠텍, 결제일 2021-09~2022-07) 대조: 서울·화성 입금·어음 어디에도 같은 금액 없음
#  → 대금이 iM 계좌(입금계좌)로 들어가고 그 통장은 업로드 대상이 아니므로 이 파일이 유일한 수금 기록. 받는다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OPS = [
 ("detect",
  "            if(rr.indexOf('채권번호')>=0 && rr.indexOf('구매기업명')>=0){ noteKind='하나채권'; hIdx=r; H=rr; break; }\n",
  "            // r197: iM뱅크 채권명세조회 — 구매'업체'명 + 채권번호 + 매출채권금액\n"
  "            if(rr.indexOf('채권번호')>=0 && rr.indexOf('구매업체명')>=0 && rr.indexOf('매출채권금액')>=0){ noteKind='iM어음'; hIdx=r; H=rr; break; }\n"
  "            if(rr.indexOf('채권번호')>=0 && rr.indexOf('구매기업명')>=0){ noteKind='하나채권'; hIdx=r; H=rr; break; }\n"),
 ("cols",
  "            } else {\n"
  "              iNo=H.indexOf('채권번호'); iVen=H.indexOf('구매기업명');\n",
  "            } else if(noteKind==='iM어음'){\n"
  "              // r197: 상태 열이 없다(목록 전체가 유효 채권). 등록일=수취일, 결제일=만기일.\n"
  "              iNo=H.indexOf('채권번호'); iVen=H.indexOf('구매업체명');\n"
  "              iAmt=H.indexOf('매출채권금액');\n"
  "              iDt=H.indexOf('등록일'); iSt=-1;\n"
  "              iDue=H.indexOf('결제일');\n"
  "            } else {\n"
  "              iNo=H.indexOf('채권번호'); iVen=H.indexOf('구매기업명');\n"),
  ("comment",
  "            //  신한은 통장에 어음번호로 찍혀 제외로 빠지므로 겹치지 않는다 → 신한어음만 받는다.\n",
  "            //  신한은 통장에 어음번호로 찍혀 제외로 빠지므로 겹치지 않는다 → 신한어음은 받는다.\n"
  "            //  iM뱅크(r197)는 대금이 업로드하지 않는 iM 계좌로 들어가므로 이 파일이 유일한 기록 → 받는다.\n"
  "            //   (나중에 iM 입출금 내역까지 올리게 되면 그때는 하나·기업처럼 막아야 한다.)\n"),
]

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    for label, old, new in OPS:
        s = rep(s, old, new, 1, 'r197 %s (%s)' % (label, path))
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r197 2026-09-22 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
