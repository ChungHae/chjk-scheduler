# -*- coding: utf-8 -*-
# r156: [견적 자동완성 안내문이 안 닫혀 아래 입력칸을 가리는 문제]
#
#  증상: 견적 > 견적관리에서 규격을 입력할 때 일치하는 규격이 없으면
#        "일치하는 규격이 없습니다. (그대로 두면 새 규격으로 등록됩니다)" 안내문이 뜨는데,
#        엔터를 쳐서 다음 줄로 내려가도 그 안내문이 그대로 남아 아래 규격 입력칸을 덮는다.
#
#  원인: qCartSpecKey 의 "목록이 열려 있는가" 판정이 후보 개수까지 보고 있었다.
#          var open = !!(b && b.style.display!=='none' && _qcsCur.length);
#        후보가 0건이면 안내문 상자는 화면에 떠 있는데도 _qcsCur.length===0 이라 open=false 가 되고,
#        엔터가 아래 qCartGridKey(격자 이동)로 그냥 흘러가 버린다. 상자를 닫는 코드가 없다.
#        (_qcsHide 는 Escape 와 항목 선택 시에만 호출됨)
#        품목(qCartNameKey)·예상납기(qCartEtaKey) 자동완성도 완전히 같은 구조라 같은 증상이 있다.
#
#  수정 1: 칸을 벗어나는 키(Enter·Tab·ArrowDown·ArrowUp)를 눌렀을 때, 후보 없이 안내문만
#          떠 있는 상태면 격자 이동 전에 상자를 닫는다. 세 핸들러 모두 동일 적용.
#          (글자 입력 키에는 손대지 않으므로 타이핑 중 깜빡임 없음 — 안내문은 계속 보인다)
#
#  수정 2: 마우스로 다른 줄의 입력칸을 클릭해 옮길 때도 같은 문제가 있었다.
#          바깥 클릭 감지가 data-mf 가 spec/name/eta 인 요소는 무조건 예외 처리해서,
#          "다른 줄의 규격칸" 을 눌러도 상자가 안 닫혔다. 상자를 띄운 그 입력칸(owner)일 때만
#          예외로 두도록 좁힌다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R156 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

GUARD = (
    "    // r156: 후보가 없어 안내문만 떠 있는 상태 — 칸을 벗어나는 키에서는 먼저 닫는다\n"
    "    //  (안 닫으면 안내문이 그대로 남아 아래 줄 입력칸을 가린다)\n"
    "    if(b && b.style.display!=='none' && !_qcsCur.length\n"
    "       && (ev.key==='Enter'||ev.key==='Tab'||ev.key==='ArrowDown'||ev.key==='ArrowUp')) _qcsHide();\n"
)

def apply_r156(s, path):
    # ── 1. 규격 ──
    s = rep(s,
        "      if(ev.key==='Enter'){     ev.preventDefault(); qCartSpecPick(i, _qcsSel>=0?_qcsSel:0, true); return; }\n"
        "    }\n"
        "    qCartGridKey(ev, ev.target);   // 닫혀 있으면 엑셀식 격자 이동",
        "      if(ev.key==='Enter'){     ev.preventDefault(); qCartSpecPick(i, _qcsSel>=0?_qcsSel:0, true); return; }\n"
        "    }\n"
        + GUARD +
        "    qCartGridKey(ev, ev.target);   // 닫혀 있으면 엑셀식 격자 이동",
        1, 'SPECKEY')

    # ── 2. 품목(이름) ──
    s = rep(s,
        "      if(ev.key==='Enter'){     ev.preventDefault(); qCartNamePick(i, _qcsSel>=0?_qcsSel:0); return; }\n"
        "    }\n"
        "    qCartGridKey(ev, ev.target);",
        "      if(ev.key==='Enter'){     ev.preventDefault(); qCartNamePick(i, _qcsSel>=0?_qcsSel:0); return; }\n"
        "    }\n"
        + GUARD +
        "    qCartGridKey(ev, ev.target);",
        1, 'NAMEKEY')

    # ── 3. 예상납기 ──
    s = rep(s,
        "      if(ev.key==='Enter'){     ev.preventDefault(); qCartEtaPick(i, _qcsSel>=0?_qcsSel:0); return; }\n"
        "    }\n"
        "    qCartGridKey(ev, ev.target);",
        "      if(ev.key==='Enter'){     ev.preventDefault(); qCartEtaPick(i, _qcsSel>=0?_qcsSel:0); return; }\n"
        "    }\n"
        + GUARD +
        "    qCartGridKey(ev, ev.target);",
        1, 'ETAKEY')

    # ── 4. 마우스로 다른 줄 입력칸을 눌러 옮길 때도 닫히도록 (상자를 띄운 칸일 때만 예외) ──
    s = rep(s,
        "        if(e.target && e.target.getAttribute && (e.target.getAttribute('data-mf')==='spec'||e.target.getAttribute('data-mf')==='name'||e.target.getAttribute('data-mf')==='eta')) return;",
        "        // r156: 상자를 띄운 그 입력칸일 때만 예외. 다른 줄의 규격/품목/납기칸을 누르면 닫는다\n"
        "        //  (예전에는 data-mf 만 보고 무조건 예외라 안내문이 남아 아래 칸을 가렸다)\n"
        "        if(e.target===b.__qcsOwner) return;",
        1, 'OUTSIDE')

    # 상자를 띄운 입력칸 기억
    s = rep(s,
        "  function _qcsShow(el, html){\n    var b=_qcsBox(); b.innerHTML=html;",
        "  function _qcsShow(el, html){\n    var b=_qcsBox(); b.innerHTML=html;\n    b.__qcsOwner=el;   // r156: 이 상자를 띄운 입력칸",
        1, 'OWNER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r156(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r155 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r155 2026-08-26 -->', '<!-- test build r156 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
