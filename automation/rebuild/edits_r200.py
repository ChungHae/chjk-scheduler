# -*- coding: utf-8 -*-
# r200(견적): 규격을 바꾸면 이전 규격의 가격이 그대로 남던 문제
#  증상(사용자 보고 2026-09-23): 서로 다른 규격인데 구매가·판매가가 윗줄과 똑같이 들어가 있고
#   E가만 제 값이라 DC율이 93.6% 같은 말이 안 되는 값으로 나온다.
#   예) KQ2T06-00A(E 2,220·구매 890·판매 990) / CJ2L10-20Z(E 13,860·구매 890·판매 990)
#  재현(하니스): 값이 있는 줄의 규격만 바꾸면(qCartSpecChanged) e·buy·sell·small 이 전부 옛 규격 값으로 남는다.
#   붙여넣기도 새 규격을 원장·가격표에서 못 찾으면(_qgFillFromLedger 가 false) 옛 값이 그대로 남는다.
#   렌더에서 가격표 잠금(확판/소물) 규격이면 E가·구매가를 덮어쓰므로 'E가만 새 값'인 화면이 만들어진다.
#  해결: 가격이 어느 규격에서 온 것인지 psrc 에 기록하고, 규격이 바뀌면
#   ① 새 규격으로 다시 채우고 ② 못 찾으면 옛 가격을 지운다(다른 규격 값을 남기지 않는다).
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

HELPER = '''  // ── r200: 가격의 출처 규격(psrc)을 기록해, 규격이 바뀌면 옛 가격이 남지 않게 한다 ──
  function _qMarkPriceSrc(c){ if(c) c.psrc=_qNorm(c.spec||''); }
  function _qHasAnyPrice(c){
    if(!c) return false;
    return (c.e!=null&&c.e!=='') || (c.buy!=null&&c.buy!=='') || (c.sell!=null&&c.sell!=='') || (c.small!=null&&c.small!=='');
  }
  function _qClearRowPrices(c){
    if(!c) return;
    c.e=null; c.buy=null; c.sell=null; c.small=null; c.pl=false;
    c.name=''; c.disc=''; c.eta=''; c.psrc='';
    if('dc' in c) delete c.dc;
  }
  // 규격이 바뀐 줄을 정리한다. 반환: '' | 'filled' | 'cleared'
  function _qCartOnSpecChanged(i){
    var c=_qCart[i]; if(!c) return '';
    var key=_qNorm(c.spec||'');
    if(key && key===String(c.psrc==null?'':c.psrc)) return '';   // 가격이 온 규격 그대로면 건드리지 않는다
    if(!key){   // 규격을 지운 줄 — 자동으로 채워졌던 가격만 지운다
      if(c.psrc && _qHasAnyPrice(c)){ _qClearRowPrices(c); return 'cleared'; }
      return '';
    }
    try{ if(_qgFillFromLedger(i)){ _qMarkPriceSrc(c); return 'filled'; } }catch(_e){}
    try{ if(_qCartCopyAbove(i)){ _qMarkPriceSrc(c); return 'filled'; } }catch(_e){}
    if(_qHasAnyPrice(c)){ _qClearRowPrices(c); return 'cleared'; }   // 이전 규격 값은 남기지 않는다
    return '';
  }
'''

OPS = [
 # (1) 헬퍼 삽입 — _qCartCopyAbove 앞
 ("helper",
  "  function _qCartCopyAbove(i){",
  HELPER + "  function _qCartCopyAbove(i){"),
 # (2) 규격 칸을 직접 고쳤을 때: 다시 채우거나 지운다
 ("specChanged",
  "  window.qCartSpecChanged = function(i, el){ qCartCommit(i); try{ if(_qCartCopyAbove(i)){ _qCartSave(); renderQCart(); } }catch(_e){} };\n",
  "  window.qCartSpecChanged = function(i, el){\n"
  "    qCartCommit(i);\n"
  "    var act='';\n"
  "    try{ act=_qCartOnSpecChanged(i); }catch(_e){}\n"
  "    if(act){ _qCartSave(); renderQCart(); }\n"
  "    if(act==='cleared') showInfoModal('규격 변경',\n"
  "      '규격이 바뀌어서 이전 규격의 가격을 지웠습니다.\\n'\n"
  "      + '새 규격은 원장·가격표에 없어 자동으로 채울 값이 없습니다 — 가격을 직접 입력해 주세요.');\n"
  "  };\n"),
 # (3) 붙여넣기: 못 찾은 규격 줄에 옛 가격이 남지 않게
 ("paste",
  "      Object.keys(specRows).forEach(function(rk){ _qgFillFromLedger(+rk); });\n",
  "      Object.keys(specRows).forEach(function(rk){ try{ _qCartOnSpecChanged(+rk); }catch(_e){ _qgFillFromLedger(+rk); } });   // r200\n"),
 # (4) 자동 채움 경로마다 출처 기록
 ("fillLedger",
  "    c.disc=r.disc||''; c.eta=r.eta||'';\n"
  "    return true;\n"
  "  }\n",
  "    c.disc=r.disc||''; c.eta=r.eta||'';\n"
  "    _qMarkPriceSrc(c);   // r200\n"
  "    return true;\n"
  "  }\n"),
 ("specPick",
  "    try{ _qCartCopyAbove(i); }catch(_e){}   // r194: 위에 같은 규격이 있으면 그 가격으로\n"
  "    _qCartSave(); _qcsHide(); renderQCart();\n",
  "    _qMarkPriceSrc(c);   // r200\n"
  "    try{ _qCartCopyAbove(i); }catch(_e){}   // r194: 위에 같은 규격이 있으면 그 가격으로\n"
  "    _qCartSave(); _qcsHide(); renderQCart();\n"),
 ("copyAbove",
  "      if(p.name && !c.name) c.name=p.name;\n"
  "      return ch;\n",
  "      if(p.name && !c.name) c.name=p.name;\n"
  "      if(ch) _qMarkPriceSrc(c);   // r200\n"
  "      return ch;\n"),
 ("sync",
  "        if(!p.eta && src.eta) p.eta=src.eta;\n",
  "        if(!p.eta && src.eta) p.eta=src.eta;\n"
  "        _qMarkPriceSrc(p);   // r200\n"),
 ("pushNew",
  "    _qCart.push({vid:_qCurId, vname:_qVName(_qCurId), spec:r.spec, name:r.name||'', e:r.e, buy:r.buy, small:(r.small!=null?r.small:null), pl:r.pl?true:false, sell:r.sell, disc:r.disc||'', eta:r.eta||'', qty:1});\n",
  "    _qCart.push({vid:_qCurId, vname:_qVName(_qCurId), spec:r.spec, name:r.name||'', e:r.e, buy:r.buy, small:(r.small!=null?r.small:null), pl:r.pl?true:false, sell:r.sell, disc:r.disc||'', eta:r.eta||'', qty:1, psrc:_qNorm(r.spec||'')});   // r200\n"),
]

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    for label, old, new in OPS:
        s = rep(s, old, new, 1, 'r200 %s (%s)' % (label, path))
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r200 2026-09-23 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
