# -*- coding: utf-8 -*-
# r189: 기업은행 어음(고객보유채권조회) 업로드 오류 + '합계' 행 헛경고
#
#  사용자 보고: 회계 > 매입매출 > 자료 업로드에서 기업은행 어음·입출금을 올렸더니 오류.
#
#  실제 파일 7개를 받아 앱 파서를 그대로 재현해 실측한 결과:
#
#   ① 어음 파일(고객보유채권조회) — 진짜 오류. "기업어음 헤더 열을 찾지 못했습니다"
#      앱이 찾는 열 이름 : 채권금액 · 채권등록일 · 채권만기일
#      실제 파일의 열 이름: 어음금액 · 등록년월일 · 만기년월일
#      (형식 판별 자체는 성공한다 — '어음번호'+'구매기업명'이 있으므로 기업어음으로 인식하고,
#       그 다음 금액·날짜 열을 못 찾아 파일 전체를 버린다.)
#
#   ② 어음 날짜가 20221031 처럼 구분자 없는 8자리다. _fxD 는 YYYY-MM-DD 형태만 읽으므로
#      ①만 고치면 이번엔 "날짜를 못 읽어 전부 건너뜀"이 된다. 두 가지를 같이 고쳐야 한다.
#
#   ③ 입출금 파일 6개(2021~2026)는 사실 정상이었다 — 총 447건이 제대로 읽힌다
#      (2021:107 2022:92 2023:65 2024:79 2025:68 2026:36).
#      다만 파일 맨 끝 '합계' 행이 거래일시 자리에 '합계'가 들어 있어
#      "거래일시를 읽지 못해 1행을 건너뛰었습니다"라는 경고가 파일마다 떴다.
#      실제로 빠진 자료는 없는데 오류처럼 보인다 → 합계/소계 행은 세지 않는다.
#      (어음 쪽은 이미 '합계' 행을 건너뛰고 있었다. 은행 쪽에만 빠져 있었다.)
#
#  수정 3가지:
#   (A) _fxD 가 YYYYMMDD(8자리)도 읽는다. 월·일 범위를 검사해 엉뚱한 숫자는 거른다.
#   (B) 기업어음 금액·등록일·만기일 열 이름 후보를 넓힌다(기존 이름 우선, 없으면 새 이름).
#   (C) 은행 입금 행에서 '합계/소계/총계' 줄은 조용히 건너뛰고 '날짜 못읽음'으로 세지 않는다.
#
#  파싱 규칙 자체(입금만 반영·중복키·취소 제외)는 건드리지 않는다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R189 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r189(s, path):
    # (A) 날짜: 구분자 없는 8자리 허용
    s = rep(s,
        "    var s=String(v).trim().replace(/[./]/g,'-').replace(/\\s.*$/,'');\n"
        "    var m2=s.match(/^(\\d{4})-(\\d{1,2})-(\\d{1,2})$/);\n"
        "    if(!m2) return null;",
        "    var s=String(v).trim().replace(/[./]/g,'-').replace(/\\s.*$/,'');\n"
        "    // r189: 기업은행 어음처럼 20221031 (구분자 없는 8자리) 로 오는 날짜도 읽는다.\n"
        "    //  월·일 범위를 확인해 사업자번호 같은 엉뚱한 숫자가 날짜로 둔갑하지 않게 한다.\n"
        "    var m8=s.match(/^((?:19|20)\\d{2})(\\d{2})(\\d{2})$/);\n"
        "    if(m8){\n"
        "      var _mo=+m8[2], _dy=+m8[3];\n"
        "      if(_mo>=1 && _mo<=12 && _dy>=1 && _dy<=31) return m8[1]+'-'+m8[2]+'-'+m8[3];\n"
        "      return null;\n"
        "    }\n"
        "    var m2=s.match(/^(\\d{4})-(\\d{1,2})-(\\d{1,2})$/);\n"
        "    if(!m2) return null;",
        1, 'FXD8')

    # (B) 기업어음 열 이름 후보 확대
    s = rep(s,
        "            } else if(noteKind==='기업어음'){\n"
        "              iNo=H.indexOf('어음번호'); iVen=H.indexOf('구매기업명'); iAmt=H.indexOf('채권금액');\n"
        "              iDt=H.indexOf('채권등록일'); iSt=H.indexOf('상태');\n"
        "              iDue=H.indexOf('채권만기일');\n",
        "            } else if(noteKind==='기업어음'){\n"
        "              // r189: 기업은행은 화면마다 열 이름이 다르다.\n"
        "              //  전자채권 화면 : 채권금액 · 채권등록일 · 채권만기일\n"
        "              //  고객보유채권조회: 어음금액 · 등록년월일 · 만기년월일   ← 이 형식이 통째로 버려지고 있었다\n"
        "              iNo=H.indexOf('어음번호'); iVen=H.indexOf('구매기업명');\n"
        "              iAmt=_fxCol(H, ['채권금액','어음금액']);\n"
        "              iDt =_fxCol(H, ['채권등록일','등록년월일','발행년월일']);\n"
        "              iSt =H.indexOf('상태');\n"
        "              iDue=_fxCol(H, ['채권만기일','만기년월일']);\n",
        1, 'IBKNOTE')

    # 열 이름 후보 도우미
    s = rep(s,
        "  function _fxCell(v){ return v==null ? '' : String(v).trim(); }",
        "  function _fxCell(v){ return v==null ? '' : String(v).trim(); }\n"
        "  // r189: 같은 뜻의 열 이름이 은행·화면마다 달라서, 후보를 순서대로 찾는다 (앞쪽이 우선).\n"
        "  function _fxCol(H, names){ for(var i=0;i<names.length;i++){ var k=H.indexOf(names[i]); if(k>=0) return k; } return -1; }",
        1, 'FXCOL')

    # (C) 은행 입금: 합계 행은 '날짜 못읽음'으로 세지 않는다
    s = rep(s,
        "            if(!d6){\n"
        "              if(rawDt || payer || _fxCell(row6[iIn])){ fSkipD++; if(skipRows.length<5) skipRows.push(r6+1); }\n"
        "              continue;\n"
        "            }",
        "            if(!d6){\n"
        "              // r189: 파일 맨 끝의 합계/소계 줄은 원래 자료가 아니다. 경고로 세면\n"
        "              //  '1행을 건너뛰었습니다'가 파일마다 떠서 실제로 빠진 게 있는 것처럼 보인다.\n"
        "              var _sumRow = /^(합계|소계|총계|계)$/.test(rawDt) || /^(합계|소계|총계)$/.test(_fxCell(row6[0]));\n"
        "              if(!_sumRow && (rawDt || payer || _fxCell(row6[iIn]))){ fSkipD++; if(skipRows.length<5) skipRows.push(r6+1); }\n"
        "              continue;\n"
        "            }",
        1, 'SUMROW')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r189(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r188 2026-09-14 -->') == 1
            s = s.replace('<!-- test build r188 2026-09-14 -->', '<!-- test build r189 2026-09-17 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
