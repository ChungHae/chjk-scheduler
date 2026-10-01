# -*- coding: utf-8 -*-
# r216 (사용자 보고 2026-10-01): 저장 견적을 불러온 뒤 마지막 줄에서 엔터·행 삽입이 안 됨 — r200 의 규격변경 정리가
#   psrc 없는 줄(불러온 견적)을 '규격이 바뀐 줄'로 오인해 엔터 대기용 change 에서 가격을 지우고(또는 원장값으로 바꾸고) 안내창을 열음.
import io, sys, json

OPS = [
 [
  "oninput=\"qCartSpecInput('+i+',this)\" onchange=\"qCartSpecChanged('+i+',this)\" onkeydown=\"qCartSpecKey(event,'+i+')\"",
  "data-orig=\"'+esc(c.spec||'')+'\" oninput=\"qCartSpecInput('+i+',this)\" onchange=\"qCartSpecChanged('+i+',this)\" onkeydown=\"qCartSpecKey(event,'+i+')\"",
  1,
  "ORIG"
 ],
 [
  "  window.qCartSpecChanged = function(i, el){\n    qCartCommit(i);\n    var act='';",
  "  window.qCartSpecChanged = function(i, el){\n    qCartCommit(i);\n    // r216: 규격이 그릴 때 값(data-orig)과 같으면 '바뀐 것'이 아니다 — 마지막 줄 엔터 대기용 가짜 change, 칸 드나들기 등에서\n    //       불러온 견적(psrc 없는 줄)의 가격을 원장값으로 바꾸거나 지우고 안내창을 열던 문제(사용자 보고 2026-10-01).\n    try{ var _og=el&&el.getAttribute?el.getAttribute('data-orig'):null; var _c0=_qCart[i];\n      if(_og!=null && _c0 && _qNorm(_og)===_qNorm(el.value||'')){ if(_c0.psrc==null && String(_c0.spec||'').trim() && _qHasAnyPrice(_c0)) _qMarkPriceSrc(_c0); return; } }catch(_e0){}\n    var act='';",
  1,
  "GUARD"
 ],
 [
  "  function renderQCart(){\n    var el=document.getElementById('qCart'); if(!el) return;\n    if(_qgSuspend) return;",
  "  function renderQCart(){\n    var el=document.getElementById('qCart'); if(!el) return;\n    if(_qgSuspend) return;\n    try{ (_qCart||[]).forEach(function(c){ if(c && c.psrc==null && String(c.spec||'').trim() && _qHasAnyPrice(c)) c.psrc=_qNorm(c.spec); }); }catch(_e){}   // r216: 저장 견적을 불러온 줄도 가격 출처 표시",
  1,
  "ADOPT"
 ],
 [
  "<!-- test build r215 2026-09-30 -->",
  "<!-- test build r216 2026-10-01 -->",
  1,
  "MARKER"
 ]
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R216 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r216(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r216 브라우저 적용기 — edits_r216.py 의 OPS. r215(live 99cb981a / test 5d21e749) 에 적용.",
             "function r216Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R216 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r216Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r216(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r216 applied:', path)
