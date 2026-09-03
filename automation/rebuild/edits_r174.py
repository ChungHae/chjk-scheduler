# -*- coding: utf-8 -*-
# r174: 업체명을 바꾸면 매입매출(미수현황)의 거래처명도 같이 바뀌게
#
#  사용자 사례: '삼광엔지어링' 으로 잘못 등록된 업체를 견적 > 업체에서 '삼광엔지니어링' 으로 고쳤는데
#    미수현황에는 여전히 옛 이름이 뜬다. 오타 수정이므로 이름이 같이 바뀌어야 맞다.
#    단, 매칭·배정(연결)은 그대로 유지되어야 한다.
#
#  왜 자동으로 안 따라갔나(실측 확인):
#    미수현황에 뜨는 이름은 업체 목록에서 가져오는 게 아니라 계산서·입금 레코드 안에 문자열로
#    저장된 vendor 값이다. 원장은 사업자번호로 묶으므로(_fxLedgersOne 의 slot()) 이름이 달라도
#    잔액·매칭은 멀쩡하지만, 표시 이름만 옛것으로 남는다.
#
#  수정: _fxRenameVendor(oldName, newName) 신설. 업체명이 바뀌는 두 경로에서 호출한다.
#    · clxSave        — 일정 > 업체 상세 저장
#    · openAddClient  — 거래처 수정 창(견적 > 업체의 [수정]이 이 창을 쓴다)
#  바꾸는 대상(이름이 저장돼 있는 곳 전부):
#    fxSalesInv.vendor / fxPurchInv.vendor / fxDeposits.vendor / fxAdjusts.vendor /
#    fxAlias 의 값 / fxTerms·fxOpenings 의 '사업장|이름' 키 / fxExcluded.vendor
#  건드리지 않는 것: vbiz(사업자번호), id, 금액, 날짜, 배정 상태 — 즉 매칭·배정·잔액은 그대로다.
#
#  안전장치 (중요):
#    ① 자료를 안 받은 상태에서 저장하면 빈 배열로 서버를 덮어쓴다 → 반드시 _fxEnsureData() 로
#       먼저 받아온 뒤에 바꾸고 저장한다.
#    ② 옛 이름이 업체 목록에 아직 남아 있으면(같은 이름이 다른 지점에도 있는 경우) 어느 쪽 자료인지
#       확정할 수 없으므로 매입매출은 건드리지 않고 안내만 한다(r162 의 '같은 이름 2곳' 원칙과 동일).
#    ③ 조회 전용 계정이거나 동기화 연결이 없으면 아무것도 하지 않는다.
#    ④ 바꾼 건수를 안내창으로 보여준다(조용히 회계 자료를 고치지 않는다). 바꿀 게 없으면 안 띄운다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R174 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r174(s, path):
    # (1) 이름 일괄 변경 함수
    s = rep(s,
        "  // ── r172: 조정 날짜 입력 (연/월/일 세 칸) ──",
        "  // ── r174: 업체명이 바뀌면 매입매출 자료의 거래처명도 같이 바꾼다 ──\n"
        "  //  이름은 계산서·입금 레코드마다 문자열로 박혀 있어 자동으로 따라가지 않는다.\n"
        "  //  원장은 사업자번호로 묶으므로 이 작업은 '표시 이름'만 바꾼다 — 매칭·배정·잔액은 불변.\n"
        "  async function _fxRenameVendor(oldName, newName){\n"
        "    var o=String(oldName==null?'':oldName).trim(), n=String(newName==null?'':newName).trim();\n"
        "    if(!o || !n || o===n) return null;\n"
        "    try{ if(_isViewer()) return null; }catch(_e){}\n"
        "    if(!_fbDbUrl) return null;                    // 동기화 연결이 없으면 저장할 수 없다\n"
        "    // 옛 이름이 업체 목록에 아직 있으면(다른 지점 등) 어느 쪽 자료인지 확정 불가 -> 손대지 않는다\n"
        "    try{\n"
        "      if((allClients()||[]).some(function(c){ return c && String(c[0]).trim()===o; })) return {ambiguous:true};\n"
        "    }catch(_e2){}\n"
        "    await _fxEnsureData();   // ★ 먼저 받아오지 않고 저장하면 빈 자료로 덮어쓴다\n"
        "    var cnt={inv:0, dep:0, adj:0, alias:0, term:0, open:0, excl:0};\n"
        "    fxSalesInv.forEach(function(e){ if(e && e.vendor===o){ e.vendor=n; cnt.inv++; } });\n"
        "    fxPurchInv.forEach(function(e){ if(e && e.vendor===o){ e.vendor=n; cnt.inv++; } });\n"
        "    fxDeposits.forEach(function(e){ if(e && e.vendor===o){ e.vendor=n; cnt.dep++; } });\n"
        "    fxAdjusts.forEach(function(a){ if(a && a.vendor===o){ a.vendor=n; cnt.adj++; } });\n"
        "    fxExcluded.forEach(function(x){ if(x && x.vendor===o){ x.vendor=n; cnt.excl++; } });\n"
        "    Object.keys(fxAlias).forEach(function(k){ if(fxAlias[k]===o){ fxAlias[k]=n; cnt.alias++; } });\n"
        "    CLI_BR.forEach(function(b){\n"
        "      var ko=b+'|'+o, kn=b+'|'+n;\n"
        "      if(fxTerms[ko]!==undefined){ fxTerms[kn]=fxTerms[ko]; delete fxTerms[ko]; cnt.term++; }\n"
        "      if(fxOpenings[ko]!==undefined){\n"
        "        if(fxOpenings[kn]!==undefined){   // 새 이름 자리에 이미 있으면 합친다(기간은 이른 쪽)\n"
        "          var a1=Number(fxOpenings[kn].amount)||0, a2=Number(fxOpenings[ko].amount)||0;\n"
        "          var s1=fxOpenings[kn].asOf||'', s2=fxOpenings[ko].asOf||'';\n"
        "          fxOpenings[kn]={ amount:a1+a2, asOf:(s1&&s2)?(s1<s2?s1:s2):(s1||s2) };\n"
        "        } else { fxOpenings[kn]=fxOpenings[ko]; }\n"
        "        delete fxOpenings[ko]; cnt.open++;\n"
        "      }\n"
        "    });\n"
        "    var total=cnt.inv+cnt.dep+cnt.adj+cnt.alias+cnt.term+cnt.open+cnt.excl;\n"
        "    if(!total) return cnt;\n"
        "    _fxCacheBump++;\n"
        "    _fxSave();               // 별칭·결제조건·기초이월·조정·제외 (소용량 설정)\n"
        "    await _fxSaveBig();      // 계산서·입금 (블롭)\n"
        "    return cnt;\n"
        "  }\n"
        "  //  이름 변경 뒤에 부르는 마무리 — 결과를 사람이 볼 수 있게 안내한다.\n"
        "  function _fxRenameVendorAfter(oldName, newName){\n"
        "    var o=String(oldName==null?'':oldName).trim(), n=String(newName==null?'':newName).trim();\n"
        "    if(!o || !n || o===n) return;\n"
        "    _fxRenameVendor(o, n).then(function(cnt){\n"
        "      if(!cnt) return;\n"
        "      if(cnt.ambiguous){\n"
        "        showInfoModal('매입매출 거래처명',\n"
        "          '\"'+o+'\" 이(가) 업체 목록에 아직 남아 있어(다른 지점 등) 매입매출 자료의 이름은 바꾸지 않았습니다.\\n'\n"
        "          + '어느 쪽 자료인지 확정할 수 없기 때문입니다.');\n"
        "        return;\n"
        "      }\n"
        "      var total=cnt.inv+cnt.dep+cnt.adj+cnt.alias+cnt.term+cnt.open+cnt.excl;\n"
        "      if(!total) return;\n"
        "      var parts=[];\n"
        "      if(cnt.inv) parts.push('계산서 '+cnt.inv);\n"
        "      if(cnt.dep) parts.push('입금 '+cnt.dep);\n"
        "      if(cnt.adj) parts.push('조정 '+cnt.adj);\n"
        "      if(cnt.alias) parts.push('별칭 '+cnt.alias);\n"
        "      if(cnt.term) parts.push('결제조건 '+cnt.term);\n"
        "      if(cnt.open) parts.push('기초이월 '+cnt.open);\n"
        "      if(cnt.excl) parts.push('제외 '+cnt.excl);\n"
        "      showInfoModal('매입매출 거래처명 변경',\n"
        "        '\"'+o+'\" → \"'+n+'\" 으로 매입매출 자료 '+total+'건의 거래처명도 함께 바꿨습니다.\\n'\n"
        "        + '(' + parts.join(' · ') + ')\\n\\n'\n"
        "        + '사업자번호로 묶는 방식은 그대로라 미수 잔액과 배정은 바뀌지 않았습니다.');\n"
        "      try{ if(_fxTab) renderFxPage(); }catch(_e){}\n"
        "    }).catch(function(e){\n"
        "      showInfoModal('매입매출 거래처명', '매입매출 자료의 거래처명을 바꾸지 못했습니다.\\n'+(e&&e.message||e)\n"
        "        + '\\n\\n업체 목록의 이름은 정상적으로 바뀌었습니다.');\n"
        "    });\n"
        "  }\n"
        "  // ── r172: 조정 날짜 입력 (연/월/일 세 칸) ──",
        1, 'RENAMEFN')

    # (2) 일정 > 업체 상세 저장(clxSave) 에서 호출
    s = rep(s,
        "    _clxPersist();\n"
        "    _clxExp=_newKey;   // r162\n"
        "    _clxRender();\n"
        "  };",
        "    _clxPersist();\n"
        "    _clxExp=_newKey;   // r162\n"
        "    _clxRender();\n"
        "    // r174: 업체명이 바뀌었으면 매입매출 자료의 거래처명도 같이 바꾼다\n"
        "    if(orig && _op.name && _op.name!==nm){ try{ _fxRenameVendorAfter(_op.name, nm); }catch(_e){} }\n"
        "  };",
        1, 'CLXHOOK')

    # (3) 거래처 수정 창(openAddClient) 에서 호출 — 견적 > 업체의 [수정]이 이 창을 쓴다
    s = rep(s,
        "      _saveClients();\n"
        "      ov.style.display='none';\n"
        "      if(typeof _refreshClientMgr==='function') _refreshClientMgr();",
        "      _saveClients();\n"
        "      ov.style.display='none';\n"
        "      // r174: 이름이 바뀐 수정이면 매입매출 자료의 거래처명도 같이 바꾼다\n"
        "      if(isEdit && editOrig && editOrig!==nm){ try{ _fxRenameVendorAfter(editOrig, nm); }catch(_e){} }\n"
        "      if(typeof _refreshClientMgr==='function') _refreshClientMgr();",
        1, 'ACHOOK')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r174(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r173 2026-08-31 -->') == 1
            s = s.replace('<!-- test build r173 2026-08-31 -->', '<!-- test build r174 2026-09-03 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
