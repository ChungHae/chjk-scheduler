// r274 적용기 — 견적: 수량별 가격(MOQ). 같은 규격이라도 수량에 따라 구매가·판매가가 다른 줄은 '수량별' 로 표시해
//  같은 규격 자동 맞춤(r194/r195)에서 빼고, 원장(거래처 단가)에도 저장하지 않는다(일회성). r273 바탕.
var fs=require('fs');
function r274Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R274 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var ANCH="  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238";
  var MOD="  // ─── r274: 수량별 가격(MOQ) — 같은 규격이라도 줄마다 가격을 따로 둔다 ───\n"
    +"  function _qQpKeyRows(i){ var c=_qCart[i]; if(!c) return []; var k=_qRowKey(c.spec||''); if(!k) return [i]; var o=[]; for(var j=0;j<_qCart.length;j++){ var p=_qCart[j]; if(p&&!p.disc&&_qRowKey(p.spec||'')===k) o.push(j); } return o.length?o:[i]; }\n"
    +"  window.qCartQpToggle=function(i){ var c=_qCart[i]; if(!c) return; try{ _qPushUndo(); }catch(_e){} var on=!c.qp; _qQpKeyRows(i).forEach(function(j){ var p=_qCart[j]; if(on){ p.qp=true; p.once=true; } else { delete p.qp; } }); _qCartSave(); renderQCart(); var m=document.getElementById('qCartCtxMenu'); if(m) m.style.display='none'; };\n"
    +"  window.qCartQpSame=function(i){ var c=_qCart[i]; if(!c) return; try{ _qPushUndo(); }catch(_e){} _qQpKeyRows(i).forEach(function(j){ _qCart[j].qp=true; _qCart[j].once=true; }); _qCartSave(); renderQCart(); var ov=document.getElementById('confirmOverlay'); if(ov) ov.style.display='none'; };\n";
  var OPS=[
    ["vertical-align:middle\">단종/변경</span>':'');",
     "vertical-align:middle\">단종/변경</span>':'')+(c.qp?' <span class=\"q-qp\" onclick=\"qCartQpToggle('+i+')\" title=\"수량별 가격 — 같은 규격의 다른 줄과 가격을 맞추지 않고, 거래처 단가(원장)에도 저장하지 않습니다. 누르면 해제\" style=\"font-size:9px;color:#7c3aed;font-weight:700;background:#f5f3ff;border:1px solid #ddd6fe;border-radius:4px;padding:1px 4px;white-space:nowrap;vertical-align:middle;cursor:pointer\">수량별</span>':'');", 1, "BADGE"],
    ["    var c=_qCart[i]; if(!c) return false;\n    var key=_qRowKey(c.spec||''); if(!key) return false;\n    var same=function(a,b){ return (a==null?'':String(a))===(b==null?'':String(b)); };\n    for(var j=i-1;j>=0;j--){\n      var p=_qCart[j]; if(!p || p.disc) continue;\n      if(_qRowKey(p.spec||'')!==key) continue;\n      var ch=false;",
     "    var c=_qCart[i]; if(!c) return false;\n    if(c.qp) return false;   // r274\n    var key=_qRowKey(c.spec||''); if(!key) return false;\n    var same=function(a,b){ return (a==null?'':String(a))===(b==null?'':String(b)); };\n    for(var j=i-1;j>=0;j--){\n      var p=_qCart[j]; if(!p || p.disc) continue;\n      if(_qRowKey(p.spec||'')!==key) continue;\n      if(p.qp){ c.qp=true; c.once=true; if(p.e!=null&&p.e!==''&&(c.e==null||c.e==='')) c.e=p.e; if(p.name&&!c.name) c.name=p.name; _qMarkPriceSrc(c); return true; }   // r274: 수량별 가격 규격 — E가만 가져오고 구매가·판매가는 비워 둔다\n      var ch=false;", 1, "COPYABOVE"],
    ["      var c=_qCart[i]; if(!c || c.disc) continue;\n      var k=_qRowKey(c.spec||''); if(!k) continue;\n      if(!byKey[k]) byKey[k]=[]; byKey[k].push(i);",
     "      var c=_qCart[i]; if(!c || c.disc || c.qp) continue;   // r274\n      var k=_qRowKey(c.spec||''); if(!k) continue;\n      if(!byKey[k]) byKey[k]=[]; byKey[k].push(i);", 1, "SYNC"],
    ["    var c=_qCart[i]; if(!c) return [];\n    var key=_qRowKey(c.spec||''); if(!key) return [];",
     "    var c=_qCart[i]; if(!c || c.qp) return [];   // r274\n    var key=_qRowKey(c.spec||''); if(!key) return [];", 1, "SPREAD1"],
    ["      if(j===i) continue; var p=_qCart[j]; if(!p || p.disc) continue;\n      if(_qRowKey(p.spec||'')!==key) continue;\n      if(!same(p.sell,c.sell) || !same(p.buy,c.buy)) out.push(j);",
     "      if(j===i) continue; var p=_qCart[j]; if(!p || p.disc || p.qp) continue;\n      if(_qRowKey(p.spec||'')!==key) continue;\n      if(!same(p.sell,c.sell) || !same(p.buy,c.buy)) out.push(j);", 1, "SPREAD2"],
    ["(DC율·마진율 동일)로 같게 할까요?', function(){",
     "(DC율·마진율 동일)로 같게 할까요?<br><br><a href=\"javascript:;\" onclick=\"qCartQpSame('+i+')\" style=\"color:#7c3aed;font-weight:700\">아니요 — 수량(MOQ)에 따라 가격이 다릅니다</a><br><span style=\"font-size:11.5px;color:#6b7280\">이 규격은 줄마다 가격을 따로 두고 다시 묻지 않습니다.</span>', function(){", 1, "ASK"],
    ["      +it('행 삽입 (I)'+(_selR.length>1?",
     "      +it(_qCart[i].qp?'수량별 가격 해제':'수량별 가격 <span style=\"color:#9ca3af;font-size:11px\">· 같은 규격 가격 따로</span>','qCartQpToggle('+i+')','#7c3aed')\n      +it('행 삽입 (I)'+(_selR.length>1?", 1, "MENU"],
    [ANCH, MOD+ANCH, 1, "JS"]
  ];
  if(isTest) OPS.push([marker[0], marker[1], 1, "MARKER"]);
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r274Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r274Apply(fs.readFileSync(src,'utf8'), isTest, ['<!-- test build r273 2026-11-18 -->','<!-- test build r274 2026-11-23 -->'])); console.log('ok →', out); }
