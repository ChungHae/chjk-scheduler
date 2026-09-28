# -*- coding: utf-8 -*-
# r203(회계): 농협 입금자명 보조 — '거래기록사항'이 비면 '거래내용'으로 채운다
#  실자료(2026-09-28, 농협 076-01-121341 / 2021년): 입금 13건 중 11건은 거래기록사항에 '농협케미컬'이 들어오지만
#  예금이자 2건은 거래기록사항이 비어 있어 입금자명이 빈칸인 채로 미배정에 남았다.
#  하나은행(r190/r191)에서 '의뢰인/수취인'이 비면 '적요'로 보완한 것과 같은 처리.
#  보완한 이름에는 배지를 달아 원래 칸이 아님을 표시한다(하나=적요 / 농협=거래내용).
#  → 예금이자 행은 입금자명이 '예금이자'가 되어 r198 자동 제외 규칙에 걸린다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OPS = [
 # (1) 농협도 보조 칸을 쓴다
 ("iRem",
  "          var iRem = (bank==='하나') ? H.indexOf('적요') : -1;\n",
  "          // r203: 농협은 '거래기록사항'이 비는 행(예금이자 등)이 있어 '거래내용'으로 보완한다.\n"
  "          var iRem = (bank==='하나') ? H.indexOf('적요') : (bank==='농협' ? H.indexOf('거래내용') : -1);\n"
  "          var _remKind = (bank==='농협') ? 2 : 1;   // 배지 문구 구분 (1=적요 / 2=거래내용)\n"),
 # (2) 어느 칸에서 가져왔는지 기록
 ("pRem",
  "                              excluded:ax6||undefined, pRem:(_fromRem?1:undefined), src:'upload' });   // r191: pRem = 적요에서 가져온 이름\n",
  "                              excluded:ax6||undefined, pRem:(_fromRem?_remKind:undefined), src:'upload' });   // r191/r203: pRem = 보조 칸에서 가져온 이름(1=적요 2=거래내용)\n"),
 # (3) 배지 문구를 은행에 맞게
 ("badge",
  "    return t + ' <span title=\"의뢰인/수취인 칸이 비어 있어 적요의 내용을 표시합니다\"'\n"
  "      + ' style=\"font-size:10.5px;font-weight:600;color:'+c+';border:1px solid #cdd8e6;padding:0 4px;margin-left:4px;vertical-align:1px;white-space:nowrap\">적요</span>';\n",
  "    var lb = (e.pRem===2) ? '거래내용' : '적요';   // r203\n"
  "    var tip = (e.pRem===2) ? '거래기록사항 칸이 비어 있어 거래내용을 표시합니다' : '의뢰인/수취인 칸이 비어 있어 적요의 내용을 표시합니다';\n"
  "    return t + ' <span title=\"'+tip+'\"'\n"
  "      + ' style=\"font-size:10.5px;font-weight:600;color:'+c+';border:1px solid #cdd8e6;padding:0 4px;margin-left:4px;vertical-align:1px;white-space:nowrap\">'+lb+'</span>';\n"),
]

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    for label, old, new in OPS:
        s = rep(s, old, new, 1, 'r203 %s (%s)' % (label, path))
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r203 2026-09-28 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
