# -*- coding: utf-8 -*-
# r178: 붙여넣은 규격의 가격 채우기 기준을 '직접 입력할 때와 동일'하게
#
#  사용자 지적: 가격표에 있는 규격도 지금 이미 그렇게 처리하고 있지 않나 — 맞다.
#  실측 확인: 규격칸에 직접 입력해 고르는 경로(qCartSpecPick)는 _qResolveMatches 를 쓰므로
#    ① 내 원장 → ② 타 거래처 원장 → ③ 가격표 순으로 찾아 채운다(SMC 는 별도 규칙).
#    그런데 붙여넣기(_qgFillFromLedger)만 ①만 보고 있었다. 같은 규격인데 넣는 방법에 따라
#    결과가 달라지는 셈이라, 기준을 하나로 맞춘다.
#
#  왜 _qResolveMatches 를 그냥 부르지 않았나:
#    그 함수는 '부분 일치 검색'이라 호출마다 전체 색인(_qAllIdx·_qPriceIdx)의 키를 전수 스캔하고
#    정렬까지 한다. 붙여넣기는 행마다 불러야 하므로 100행이면 그 스캔이 100번, 2,000행이면 2,000번이다.
#    붙여넣기는 규격이 이미 정해져 있으니 부분 일치가 필요 없다 → 우선순위 '규칙'만 그대로 옮기고
#    키로 바로 찾는다(_qgResolveOne). 결과는 완전일치 기준에서 _qResolveMatches 의 첫 행과 같다.
#    (엔터로 고를 때도 선택을 따로 안 하면 첫 행이 담긴다 — qCartSpecKey)
#
#  SMC 불변 조건도 그대로 옮긴다: SMC 규격은 내 원장에 있으면 그것, 없으면 확판/소물 가격이 있는
#    가격표만 쓴다. 타 거래처 원장은 쓰지 않는다.
#
#  색인이 아직 안 만들어졌을 때(_qAllReady=false):
#    기다리게 하지 않고 우선 내 원장으로 채운 뒤, 색인이 준비되면 '아직 빈 행'만 다시 채우고
#    화면을 갱신한다. 사용자가 직접 입력해 넣은 값은 덮지 않는다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R178 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

OLD_FILL = "  function _qgFillFromLedger(i){ var c=_qCart[i]; if(!c) return false; var key=_qNorm(c.spec); if(!key) return false; var r=(_qRows||[]).find(function(x){ return _qNorm(x.spec)===key; }); if(!r) return false; c.name=r.name||''; c.e=(r.e!=null&&r.e!=='')?Number(r.e):null; c.buy=(r.buy!=null&&r.buy!=='')?Number(r.buy):null; c.small=(r.small!=null&&r.small!=='')?Number(r.small):null; c.pl=r.pl?true:false; c.sell=(r.sell!=null&&r.sell!=='')?Number(r.sell):null; c.disc=r.disc||''; c.eta=r.eta||''; return true; }\n"

NEW_FILL = r'''  // ── r178: 붙여넣은 규격의 가격 채우기 — 규격칸에 직접 입력할 때와 같은 기준 ──
  //  ① 내 원장 → ② 타 거래처 원장(구매가 최저) → ③ 가격표.  SMC 는 ①, 없으면 확판/소물 있는 가격표만.
  //  _qResolveMatches 는 부분 일치 검색이라 호출마다 전체 색인을 훑는다(행마다 부르면 느리다).
  //  붙여넣기는 규격이 정해져 있으므로 같은 우선순위 규칙만 옮겨 키로 바로 찾는다.
  var _qgObk=null;   // 이번 붙여넣기 동안 쓰는 '내 원장 규격 색인' (한 번만 만든다)
  function _qgOwnByKey(){
    var m={};
    (_qRows||[]).forEach(function(r){ var k=_qNorm(r.spec); if(!k) return; (m[k]=m[k]||[]).push(r); });
    return m;
  }
  function _qgPriceRow(k, p){
    return { spec:p.spec||k, name:p.name||'', e:(p.e!=null?p.e:null), buy:(p.buy!=null?p.buy:null),
             small:(p.small!=null?p.small:null), pl:p.pl?true:false, sell:null, disc:'', eta:'' };
  }
  function _qgResolveOne(key, ownByKey){
    if(!key) return null;
    var own=ownByKey[key]||[];
    var others=((_qAllIdx&&_qAllIdx[key])||[]).filter(function(e){ return e.vid!==_qCurId; });
    var price=_qPriceIdx?_qPriceIdx[key]:null;
    var smc = own.some(function(r){ return _qIsSmc(r,key); })
           || others.some(function(e){ return _qIsSmc(e.r,key); })
           || !!(price && price.isSMC);
    if(smc){
      if(own.length) return _qCheapest(own).item||own[0];
      if(price && price.hasSmcPrice) return _qgPriceRow(key, price);
      return null;                                  // SMC 는 타 거래처 원장을 쓰지 않는다(불변 조건)
    }
    if(own.length) return _qCheapest(own).item||own[0];        // 내 원장이 항상 우선
    if(others.length){ var pk=_qCheapest(others).item; return pk?pk.r:null; }
    if(price) return _qgPriceRow(key, price);
    return null;
  }
  function _qgFillFromLedger(i){
    var c=_qCart[i]; if(!c) return false;
    var key=_qNorm(c.spec); if(!key) return false;
    if(!_qgObk) _qgObk=_qgOwnByKey();
    var r=_qgResolveOne(key, _qgObk);
    if(!r) return false;
    c.name=r.name||'';
    c.e   =(r.e!=null&&r.e!=='')?Number(r.e):null;
    c.buy =(r.buy!=null&&r.buy!=='')?Number(r.buy):null;
    c.small=(r.small!=null&&r.small!=='')?Number(r.small):null;
    c.pl  =r.pl?true:false;
    c.sell=(r.sell!=null&&r.sell!=='')?Number(r.sell):null;
    c.disc=r.disc||''; c.eta=r.eta||'';
    return true;
  }
'''

def apply_r178(s, path):
    s = rep(s, OLD_FILL, NEW_FILL, 1, 'FILLFN')

    # 붙여넣기 시작마다 원장 색인 캐시를 새로 만든다 (그 사이 원장이 바뀌었을 수 있다)
    s = rep(s,
        "    _qPushUndo();   // 붙여넣기 전체를 한 단계로 — 100행을 되돌릴 방법이 있어야 한다",
        "    _qgObk=null;    // r178: 원장 색인 캐시 초기화\n"
        "    _qPushUndo();   // 붙여넣기 전체를 한 단계로 — 100행을 되돌릴 방법이 있어야 한다",
        1, 'OBKRESET')

    # 색인이 아직이면 먼저 원장으로 채우고, 준비되면 빈 행만 다시 채운다
    s = rep(s,
        "    try{ _qcsHide(); }catch(e){}\n"
        "    _qgPasting=true;\n"
        "    _qCartSave(); renderQCart(); _qgPaint();\n"
        "    _qgPasting=false;",
        "    try{ _qcsHide(); }catch(e){}\n"
        "    _qgPasting=true;\n"
        "    _qCartSave(); renderQCart(); _qgPaint();\n"
        "    _qgPasting=false;\n"
        "    // r178: 전체 색인(타 거래처·가격표)이 아직이면 기다리지 않고, 준비되는 대로 빈 행만 다시 채운다\n"
        "    if(!_qAllReady && typeof _qEnsureAllIdx==='function'){\n"
        "      var _pend=Object.keys(specRows).map(Number);\n"
        "      if(_pend.length){\n"
        "        _qEnsureAllIdx().then(function(){\n"
        "          _qgObk=null; var _n=0;\n"
        "          _pend.forEach(function(ri){\n"
        "            var c2=_qCart[ri]; if(!c2 || !String(c2.spec||'').trim()) return;\n"
        "            if(c2.e!=null || c2.buy!=null || c2.sell!=null) return;   // 이미 값이 있으면 덮지 않는다\n"
        "            if(_qgFillFromLedger(ri)) _n++;\n"
        "          });\n"
        "          if(_n){ _qgPasting=true; _qCartSave(); renderQCart(); _qgPaint(); _qgPasting=false; }\n"
        "        }).catch(function(){});\n"
        "      }\n"
        "    }",
        1, 'DEFERFILL')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r178(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r177 2026-09-07 -->') == 1
            s = s.replace('<!-- test build r177 2026-09-07 -->', '<!-- test build r178 2026-09-07 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
