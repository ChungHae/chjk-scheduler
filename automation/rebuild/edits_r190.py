# -*- coding: utf-8 -*-
# r190: 하나은행 입금자명을 '적요'에서도 읽는다 + 카드정산 자동제외 보강 + 합계행 판정
#
#  사용자 보고: 하나은행 7개 파일을 올렸더니 820건 중 미배정이 791건.
#              (기업은행은 447건 중 443건이 자동 배정됐다)
#
#  실제 파일 7개를 열어 확인한 결과:
#
#   ① 하나은행 엑셀 구조
#        No | 거래일시 | 적요 | 의뢰인/수취인 | 통화 | 입금 | 출금 | 잔액 | 구분 | 거래점
#      앱은 '의뢰인/수취인'을 입금자명으로 쓰는데 이 칸이 대부분 비어 있다.
#      실제 상대방 이름은 '적요'에 들어 있다.  (실측 채움 비율)
#        의뢰인/수취인  4~32%      적요  95%
#      예) 엘에스엠트론(주) 채권입금 25,907,191원 — 적요에만 이름, 의뢰인 칸은 빈칸 → 미배정
#      => 의뢰인/수취인이 비어 있을 때만 적요를 쓴다. 둘 다 있으면 종전대로 의뢰인/수취인 우선.
#         827건 중 이름 있는 건이 145건 -> 786건(95%)이 된다.
#      ★ 하나은행에서만 적용한다. 신한 등 다른 은행의 '적요'에는 '타행IB' 같은 값이 들어가므로
#        일괄 적용하면 쓰레기 이름이 미배정에 쌓인다. 근거가 있는 은행만 손댄다.
#
#   ② 카드 정산이 자동 제외에서 빠져나갔다
#      BC카드 정산이 두 표기로 온다:  BC-730827312 (107건) · 730827312BC (454건)
#      현행 규칙은 카드사명이 '앞'에 오는 형태만 본다 → 숫자가 앞인 730827312BC 가 통과.
#      => 숫자 나열 + 카드사 표기로 '끝나는' 형태도 카드 정산으로 본다. 561건이 자동 제외된다.
#      (사용자 결정: 카드매출은 별도 메뉴에서 관리하므로 은행 입금에서는 제외)
#      주의: 13291001654519 같은 순수 계좌번호는 걸리지 않아야 한다 → 카드사 표기가 붙은 것만.
#
#   ③ 합계 행이 '건너뛴 행'으로 잡혔다
#      2025·2026 형식의 합계 줄은 이렇게 생겼다:   ,,,합계,765350090,766199791,,,,
#      '합계' 글자가 의뢰인/수취인 칸에 있어서 r189 의 판정(거래일시·첫 칸)을 비껴갔다.
#      => 거래일시를 못 읽은 행은, 어느 칸이든 합계/소계/총계가 있으면 합계 줄로 본다.
#      (실측: 빠진 실제 거래는 없다. 헛경고만 사라진다)
#
#  사용자 결정으로 하지 않는 것: 자기 계좌 간 이체(충해전기(주) 명의 106건)는 미배정으로 둔다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R190 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r190(s, path):
    # ① 적요 열 위치를 찾아 둔다
    s = rep(s,
        "          var iDate=H.indexOf('거래일시'); if(iDate<0) iDate=H.indexOf('거래일자');\n",
        "          var iDate=H.indexOf('거래일시'); if(iDate<0) iDate=H.indexOf('거래일자');\n"
        "          // r190: 하나은행은 '의뢰인/수취인'이 대부분 비어 있고 실제 이름이 '적요'에 있다.\n"
        "          //  (실측 채움 비율 — 의뢰인/수취인 4~32% vs 적요 95%)\n"
        "          //  다른 은행의 적요에는 '타행IB' 같은 값이 들어가므로 하나에서만 보조로 쓴다.\n"
        "          var iRem = (bank==='하나') ? H.indexOf('적요') : -1;\n",
        1, 'IREM')

    # 입금자명: 비어 있으면 적요로 보충
    s = rep(s,
        "            var d6=_fxD(row6[iDate]), amt6=_fxN(row6[iIn]), payer=_fxCell(row6[iPay]);\n",
        "            var d6=_fxD(row6[iDate]), amt6=_fxN(row6[iIn]), payer=_fxCell(row6[iPay]);\n"
        "            if(!payer && iRem>=0) payer=_fxCell(row6[iRem]);   // r190\n",
        1, 'PAYFALLBACK')

    # ③ 합계 행: 어느 칸이든 합계/소계/총계면 합계 줄로 본다
    s = rep(s,
        "              var _sumRow = /^(합계|소계|총계|계)$/.test(rawDt) || /^(합계|소계|총계)$/.test(_fxCell(row6[0]));\n",
        "              // r190: 하나은행 2025·2026 형식은 '합계' 글자가 의뢰인/수취인 칸에 있다.\n"
        "              //  (,,,합계,765350090,766199791,,,,) → 어느 칸이든 합계면 합계 줄로 본다.\n"
        "              var _sumRow = (row6||[]).some(function(c){ return /^(합계|소계|총계|계)$/.test(_fxCell(c)); });\n",
        1, 'SUMROW2')

    # ② 카드 정산: 숫자 나열 + 카드사 표기로 끝나는 형태
    s = rep(s,
        "    if(/^(신한|삼성|현대|롯데|국민|하나|우리|비씨|농협|씨티|카카오|KB|BC|NH)[\\s\\-\\.]?\\d{4,}/.test(p)) return true;\n"
        "    return false;",
        "    if(/^(신한|삼성|현대|롯데|국민|하나|우리|비씨|농협|씨티|카카오|KB|BC|NH)[\\s\\-\\.]?\\d{4,}/.test(p)) return true;\n"
        "    // r190: 카드사 표기가 '뒤'에 오는 형태 (730827312BC 등 — 하나은행 BC카드 정산)\n"
        "    //  순수 계좌번호(13291001654519)는 걸리지 않게, 카드사 표기가 붙은 것만 본다.\n"
        "    if(/^\\d{6,}[\\s\\-\\.]?(BC|NH|KB|비씨|카드)$/i.test(p)) return true;\n"
        "    return false;",
        1, 'CARDSUFFIX')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r190(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r189 2026-09-17 -->') == 1
            s = s.replace('<!-- test build r189 2026-09-17 -->', '<!-- test build r190 2026-09-17 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
