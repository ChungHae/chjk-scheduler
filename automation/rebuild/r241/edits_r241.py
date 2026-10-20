# -*- coding: utf-8 -*-
# r241 (사용자 요청 2026-10-19): 메모장(내 일정) 상단의 안내 배너(SMC 가격 확인 대기·업체 정보 등록 대기·내 담당 업체 매출·업무회의 필요·신규 영업 응원)를
#   메모 목록 **아래**로. r240 '내 목표' 카드는 작업용이라 위에 그대로.
import io, sys, json

OLD_TOP = """    try{ h+=_mmSmcBanner(); }catch(_e){}   // r181 SMC 확인 대기 배너
    try{ h+=_pendBanner(); }catch(_e){}   // r217 업체 정보 등록 대기 배너
    try{ h+=_cuBanner(); }catch(_e){}   // r224 내 카드 미분류 배너
    try{ h+=_coBanner(); }catch(_e){}   // r226 내 담당 업체 매출 카드
    try{ h+=_mtDueBanner(); }catch(_e){}   // r227 업무회의 2주 주기
    try{ h+=_nbBanner(); }catch(_e){}   // r227 신규 영업 응원
"""
NEW_TOP = """    var _hb='';   // r241: 안내 배너는 메모 목록 아래에
    try{ _hb+=_mmSmcBanner(); }catch(_e){}   // r181 SMC 확인 대기 배너
    try{ _hb+=_pendBanner(); }catch(_e){}   // r217 업체 정보 등록 대기 배너
    try{ _hb+=_cuBanner(); }catch(_e){}   // r224 내 카드 미분류 배너
    try{ _hb+=_coBanner(); }catch(_e){}   // r226 내 담당 업체 매출 카드
    try{ _hb+=_mtDueBanner(); }catch(_e){}   // r227 업무회의 2주 주기
    try{ _hb+=_nbBanner(); }catch(_e){}   // r227 신규 영업 응원
"""
OPS = [
  [OLD_TOP, NEW_TOP, 1, "BANNERS"],
  ["    if(!h) h='<div class=\"mm-empty\">아직 적은 메모가 없습니다. 아래 줄에 적고 Enter.</div>';\n    list.innerHTML=h;",
   "    if(!h) h='<div class=\"mm-empty\">아직 적은 메모가 없습니다. 아래 줄에 적고 Enter.</div>';\n    list.innerHTML=h+(_hb?('<div class=\"mm-banners-bottom\">'+_hb+'</div>'):'');   // r241", 1, "TAIL"],
  [".mt-goal-rep > div.nm small {", ".mm-banners-bottom { margin-top:14px; padding-top:8px; border-top:1px dashed #e5e7eb; }\n    .mt-goal-rep > div.nm small {", 1, "CSS"],
  ["<!-- test build r240 2026-10-19 -->", "<!-- test build r241 2026-10-19 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R241 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r241(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r241 브라우저 적용기 — edits_r241.py 의 OPS. r240 적용본 위에 적용.",
             "function r241Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R241 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r241Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r241(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r241 applied:', path)
