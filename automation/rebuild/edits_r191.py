# -*- coding: utf-8 -*-
# r191: 적요에서 가져온 입금자명 옆에 '적요' 표시
#
#  사용자 요청: "하나은행 내역은 의뢰인/수취인 칸이 빈칸일 경우 적요의 내용을 표시하게 해줘.
#               그리고 옆에 적요라고 표시해줘."
#
#  적요를 대신 쓰는 것 자체는 r190 에서 이미 들어갔다. 이번에는 '어디서 온 이름인지'를 화면에 남긴다.
#  왜 필요한가: 적요에는 상대방 이름 말고 다른 것(계좌번호·수수료 설명 등)이 들어오기도 한다.
#  이름 옆에 출처가 보이면, 배정 전에 이 이름을 믿어도 되는지 사용자가 바로 판단할 수 있다.
#
#  방식:
#   · 업로드 때 적요로 채운 건에만 e.pRem=1 표식을 남긴다 (의뢰인/수취인에서 온 건은 표식 없음).
#   · _fxPayerHtml(e) 하나로 네 곳의 입금자명 표시를 통일한다:
#       미배정 입금 · 보류한 입금 · 제외한 입금 · 사업자번호 없는 배정 목록
#   · 표식은 각진 회색 배지(디자인 규칙: 모서리 둥글림 없음). 마우스를 올리면 설명이 뜬다.
#
#  ※ 표식은 '앞으로 올리는 자료'에만 붙는다. 이미 들어가 있는 건에는 표식이 없다
#    (r190 이전에 들어간 건은 애초에 이름 자체가 비어 있다).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R191 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r191(s, path):
    # (1) 적요로 채운 건에 표식을 남긴다
    s = rep(s,
        "            if(!payer && iRem>=0) payer=_fxCell(row6[iRem]);   // r190\n",
        "            var _fromRem=false;                                   // r191: 이름의 출처를 기억해 둔다\n"
        "            if(!payer && iRem>=0){ payer=_fxCell(row6[iRem]); _fromRem=!!payer; }   // r190\n",
        1, 'FLAGSET')

    s = rep(s,
        "            fxDeposits.push({ id:id6, biz:biz, date:d6, amount:amt6, payer:payer,\n"
        "                              vendor:v6||'', vbiz:v6?_fxClientVbiz(v6,biz):'', kind:'bank', bank:bank,\n"
        "                              excluded:ax6||undefined, src:'upload' });\n",
        "            fxDeposits.push({ id:id6, biz:biz, date:d6, amount:amt6, payer:payer,\n"
        "                              vendor:v6||'', vbiz:v6?_fxClientVbiz(v6,biz):'', kind:'bank', bank:bank,\n"
        "                              excluded:ax6||undefined, pRem:(_fromRem?1:undefined), src:'upload' });   // r191: pRem = 적요에서 가져온 이름\n",
        1, 'FLAGSAVE')

    # (2) 입금자명 표시 도우미
    s = rep(s,
        "  // r189: 같은 뜻의 열 이름이 은행·화면마다 달라서, 후보를 순서대로 찾는다 (앞쪽이 우선).\n",
        "  // r191: 입금자명 표시 — 적요에서 가져온 이름이면 옆에 '적요' 를 붙인다.\n"
        "  //  적요에는 상대방 이름이 아닌 것(계좌번호·수수료 설명 등)이 들어오기도 해서,\n"
        "  //  배정 전에 이 이름을 믿어도 되는지 바로 알 수 있게 출처를 남긴다.\n"
        "  function _fxPayerHtml(e, muted){\n"
        "    var t = esc((e&&e.payer)||'');\n"
        "    if(!e || !e.pRem) return t;\n"
        "    var c = muted ? '#b6bec9' : '#8a94a6';\n"
        "    return t + ' <span title=\"의뢰인/수취인 칸이 비어 있어 적요의 내용을 표시합니다\"'\n"
        "      + ' style=\"font-size:10.5px;font-weight:600;color:'+c+';border:1px solid #cdd8e6;padding:0 4px;margin-left:4px;vertical-align:1px;white-space:nowrap\">적요</span>';\n"
        "  }\n"
        "  // r189: 같은 뜻의 열 이름이 은행·화면마다 달라서, 후보를 순서대로 찾는다 (앞쪽이 우선).\n",
        1, 'HELPER')

    # (3) 네 곳의 표시를 도우미로 교체
    #  미배정 입금
    s = rep(s,
        "\n          + '<td style=\"'+TD+';font-weight:700;color:#14305c\">'+esc(e.payer||'')+'</td>'\n",
        "\n          + '<td style=\"'+TD+';font-weight:700;color:#14305c\">'+_fxPayerHtml(e)+'</td>'\n",
        1, 'RENDER_UN')
    #  보류한 입금
    s = rep(s,
        "\n            + '<td style=\"'+TD+';font-weight:700;color:#14305c\">'+esc(e.payer||'')+'</td>'\n",
        "\n            + '<td style=\"'+TD+';font-weight:700;color:#14305c\">'+_fxPayerHtml(e)+'</td>'\n",
        1, 'RENDER_HELD')
    #  제외한 입금 (흐린 색)
    s = rep(s,
        "            + '<td style=\"'+TD+';color:#9ca3af\">'+esc(e.payer||'')+'</td>'\n",
        "            + '<td style=\"'+TD+';color:#9ca3af\">'+_fxPayerHtml(e, true)+'</td>'\n",
        1, 'RENDER_EXCL')
    #  사업자번호 없는 배정 목록
    s = rep(s,
        "        + '<td style=\"'+TD+';color:#374151\">'+esc(e.payer||'')+'</td>'\n",
        "        + '<td style=\"'+TD+';color:#374151\">'+_fxPayerHtml(e)+'</td>'\n",
        1, 'RENDER_NOBIZ')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r191(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r190 2026-09-17 -->') == 1
            s = s.replace('<!-- test build r190 2026-09-17 -->', '<!-- test build r191 2026-09-17 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
