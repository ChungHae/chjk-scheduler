# -*- coding: utf-8 -*-
# r144: [카드·결제 자동 제외 규칙 확장 — 카드사명+숫자]
#  "신한12341231", "삼성124534234" 처럼 카드사 이름 바로 뒤에 숫자가 나열되는
#  입금자명이 제외되지 않던 문제. 판정 규칙에 카드사명 접두 + 숫자 4자리 이상 추가.
#  - 접두 목록: 신한 삼성 현대 롯데 국민 하나 우리 비씨 농협 씨티 카카오 / KB BC NH
#  - 이름 시작(^) 기준이라 "(주)신한테크" 같은 일반 업체명은 걸리지 않고,
#    "삼성이즈메디" 처럼 숫자가 붙지 않은 이름도 걸리지 않음.
#  - 별칭 매칭이 항상 우선이며, 제외 목록에서 언제든 복원 가능(기존과 동일).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R144 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r144(s, path):
    # (1) 판정 헬퍼 확장
    s = rep(s, r"""  function _fxAutoExclPayer(p){
    p=String(p||'');
    if(/카드/.test(p)) return true;             // 카드사 정산 (신한카드1234, 비씨카드(주) 등)
    if(/결[\s:\-]?\d{4,}/.test(p)) return true; // 결+숫자 나열 (결:12345678, 결20260821 등)
    return false;
  }""",
            r"""  function _fxAutoExclPayer(p){
    p=String(p||'').trim();
    if(/카드/.test(p)) return true;             // 카드사 정산 (신한카드1234, 비씨카드(주) 등)
    if(/결[\s:\-]?\d{4,}/.test(p)) return true; // 결+숫자 나열 (결:12345678, 결20260821 등)
    // 카드사명 접두 + 숫자 나열 (신한12341231, 삼성 124534234, KB1234567 등)
    if(/^(신한|삼성|현대|롯데|국민|하나|우리|비씨|농협|씨티|카카오|KB|BC|NH)[\s\-\.]?\d{4,}/.test(p)) return true;
    return false;
  }""", 1, 'HELPER')

    # (2) 소급 적용 확인창 문구 갱신
    s = rep(s, "      '입금자명에 \"카드\" 또는 \"결+숫자\"가 포함된 미배정·보류 입금 '+targets.length+'건을 제외 처리합니다.",
            "      '카드·결제 정산 형식(카드 / 카드사명+숫자 / 결+숫자)의 미배정·보류 입금 '+targets.length+'건을 제외 처리합니다.", 1, 'MSG')

    # (3) 버튼 툴팁 갱신
    s = rep(s, 'title="입금자명에 카드/결+숫자가 포함된 건을 일괄 제외"',
            'title="입금자명이 카드·결제 정산 형식(카드 / 카드사명+숫자 / 결+숫자)인 건을 일괄 제외"', 1, 'TIP')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r144(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r143 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r143 2026-08-24 -->', '<!-- test build r144 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
