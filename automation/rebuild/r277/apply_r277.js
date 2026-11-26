// r277 적용기 — 견적 표: 한 칸(또는 작은 범위)을 복사해 여러 칸을 드래그 선택하고 Ctrl+V 하면 선택한 칸 전체에 채운다(엑셀식).
//  전에는 탭·줄바꿈이 없는 한 칸 값은 브라우저 기본 붙여넣기로 넘어가 첫 칸에만 들어갔다. r276 바탕.
var fs=require('fs');
function r277Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R277 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OLD="    var txt=''; try{ txt=(ev.clipboardData||window.clipboardData).getData('text'); }catch(e){}\n    if(txt && (txt.indexOf('\\t')>=0 || txt.indexOf('\\n')>=0)){ ev.preventDefault(); _qgPasteText(txt); }";
  var NEW="    var txt=''; try{ txt=(ev.clipboardData||window.clipboardData).getData('text'); }catch(e){}\n"
    +"    if(txt && _qgSel && _qgSel.set.size>1){ var _tt=_qgTileClip(txt); if(_tt!=null){ ev.preventDefault(); _qgPasteText(_tt); return; } }   // r277: 선택한 칸 전체에 채우기\n"
    +"    if(txt && (txt.indexOf('\\t')>=0 || txt.indexOf('\\n')>=0)){ ev.preventDefault(); _qgPasteText(txt); }";
  var A="  function _qgBuildTSV(){";
  var FN="  function _qgTileClip(txt){   // r277: 복사한 블록(R×C)이 선택 범위(h×w)보다 작고 배수로 맞으면 범위 전체에 반복해 채운다. 한 칸이면 항상.\n"
    +"    var b=_qgBounds(); if(!b) return null;\n"
    +"    var rows=String(txt).replace(/\\r/g,'').replace(/\\n+$/,'').split('\\n').map(function(ln){ return ln.split('\\t'); });\n"
    +"    var R=rows.length, C=0; rows.forEach(function(r){ if(r.length>C) C=r.length; }); if(!R||!C) return null;\n"
    +"    var h=b.r1-b.r0+1, w=b.c1-b.c0+1;\n"
    +"    if(R===h && C===w) return null; if(R>h || C>w || h%R || w%C) return null;\n"
    +"    var out=[]; for(var i=0;i<h;i++){ var ln=[]; for(var j=0;j<w;j++){ var v=rows[i%R][j%C]; ln.push(v==null?'':v); } out.push(ln.join('\\t')); }\n"
    +"    return out.join('\\n');\n  }\n";
  var OPS=[[OLD, NEW, 1, "PASTE"], [A, FN+A, 1, "FN"]];
  if(isTest) OPS.push([marker[0], marker[1], 1, "MARKER"]);
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r277Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r277Apply(fs.readFileSync(src,'utf8'), isTest, ['<!-- test build r276 2026-11-26 -->','<!-- test build r277 2026-11-26 -->'])); console.log('ok →', out); }
