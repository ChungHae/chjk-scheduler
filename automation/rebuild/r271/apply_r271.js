// r271 적용기 — 최근 작업한 견적: 불러오기 '최근 작업순' + 툴바 [최근 작업]. live·test 공용.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r271_module.js'),'utf8');
var BTN='      <button class="qic" id="qRecentBtn" onclick="qOpenRecent(event)" data-tip="최근 작업한 견적" aria-label="최근 작업한 견적" style="border-color:#1B3A6B;color:#1B3A6B"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg></button>\n';
function r271Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R271 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var load=s.match(/      <button class="qic" id="qLoadBtn"[^\n]*\n/); if(!load) throw new Error('R271 FAIL qLoadBtn');
  var OPS=[
    ["var list=quoteSaved.slice().sort(function(a,b){ var da=_qd(a), db=_qd(b); if(da!==db) return db<da?-1:1; return (b.savedAt||0)-(a.savedAt||0); });", "var list=_qLoadSorted(_qd);   // r271: 최근 작업순(기본) / 견적일순", 1, "SORT"],
    ["+'<button class=\"btn\" onclick=\"qLoadResetFilters()\" style=\"font-size:12px;padding:6px 10px\">초기화</button>'",
     "+'<select id=\"qLoadSort\" onchange=\"qLoadSortSet(this.value)\" title=\"정렬\" style=\"'+INP+'\"><option value=\"work\"'+(_qLoadSortMode()==='work'?' selected':'')+'>최근 작업순</option><option value=\"date\"'+(_qLoadSortMode()==='date'?' selected':'')+'>견적일순</option></select>'   // r271\n        +'<button class=\"btn\" onclick=\"qLoadResetFilters()\" style=\"font-size:12px;padding:6px 10px\">초기화</button>'", 1, "SELECT"],
    ["      var ds=dd?(dd.getFullYear()+'.'+String(dd.getMonth()+1).padStart(2,'0')+'.'+String(dd.getDate()).padStart(2,'0')):'';",
     "      var ds=dd?(dd.getFullYear()+'.'+String(dd.getMonth()+1).padStart(2,'0')+'.'+String(dd.getDate()).padStart(2,'0')):'';\n      if(_qLoadSortMode()==='work' && _qWorkAt(qq)) ds=(ds?ds+' · ':'')+'최근 작업 '+_qAgo(_qWorkAt(qq));   // r271", 1, "WHEN"],
    [load[0], load[0]+BTN, 1, "BTN"],
    ["  window.qLoadSaved = function(id){", MOD+"  window.qLoadSaved = function(id){", 1, "JS"]
  ];
  if(isTest) OPS.push([marker[0], marker[1], 1, "MARKER"]);
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r271Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r271Apply(fs.readFileSync(src,'utf8'), isTest, ['<!-- test build r270 2026-11-13 -->','<!-- test build r271 2026-11-17 -->'])); console.log('ok →', out); }
