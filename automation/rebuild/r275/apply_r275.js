// r275 적용기 — 회의록 쉽게: 작성란 하나(막 적고 저장) + 줄마다 이름 눌러 담당 지정. 업무 작성란 제거, 목표는 접어 둠. r274 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r275_module.js'),'utf8');
function r275Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R275 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  function cut(str, a, b, nw, label){ if(str.split(a).length!==2||str.split(b).length!==2) throw new Error('R275 FAIL '+label+' marker'); var i=str.indexOf(a), j=str.indexOf(b); if(j<i) throw new Error('R275 FAIL '+label+' order'); return str.slice(0,i)+nw+str.slice(j); }
  // 1) 회의 내용 구역: 작성란을 위로, 목록은 아래 (담당 미정)
  s=cut(s, "    h+='<div class=\"mt-sec\"><h3>1. 공통 추진 사항 및 협의 안건</h3>';", "    h+='<div class=\"mt-sec\"><h3>2. 담당자별 업무 보고</h3>';",
    "    h+='<div class=\"mt-sec\"><h3>1. 회의 내용'+((!print && m.status!=='final' && (m.agenda||[]).length)?' <span class=\"mt-goal-hint\">— 이름을 누르면 그 사람 담당이 됩니다</span>':'')+'</h3>';\n"
   +"    if(!print && m.status!=='final'){   // r275: 작성란 하나 — 막 적고 저장\n"
   +"      h+='<div class=\"mt-write mt-quick\"><textarea id=\"mtAgIn\" data-dk=\"ag\" data-mid=\"'+id+'\" rows=\"5\" placeholder=\"회의 내용을 편하게 적으세요. 한 줄에 하나씩.\\n담당은 저장한 뒤 이름만 누르면 됩니다.\" oninput=\"mtTaInput(this)\" onkeydown=\"mtTaKey(event,this)\"></textarea>'\n"
   +"        +'<div class=\"mt-write-bar\"><span class=\"mt-hint\">Enter 는 다음 줄 · 다 쓰면 [저장] (Ctrl+Enter)</span><button class=\"mt-btn pri\" onclick=\"mtSaveAgenda(\\''+id+'\\')\">저장</button></div></div>'; }\n"
   +"    if(!(m.agenda||[]).length && print) h+='<div style=\"font-size:12.5px;color:#9ca3af;padding:6px\">-</div>';\n"
   +"    (m.agenda||[]).forEach(function(a){ h+=_mtItemHtml(m, a, true, print); });\n"
   +"    h+='</div>';\n", "SEC1");
  // 2) 업무 작성란 제거
  s=cut(s, "    if(!print && m.status!=='final'){   // r213: 담당자별 업무를 한 작성란에 쭉 쓰고 저장", "    h+='</div>'+_mtGoalsSecHtml(m, print)+", "", "SEC2");
  var OPS=[
    ["    h+='<div class=\"mt-sec\"><h3>2. 담당자별 업무 보고</h3>';", "    h+='<div class=\"mt-sec\"><h3>2. 담당자별 업무</h3>';", 1, "H2"],
    ["아직 없음 — 아래 작성란에 \"'+_mtEsc(n)+' 업무내용\" 으로 적고 저장</div>';", "아직 없음</div>';", 1, "EMPTY"],
    ["      +(_lk?'':'<button class=\"mt-del\" onclick=\"mtDelItem(", "      +(_lk?'':_mtWhoHtml(m, it, isAgenda))\n      +(_lk?'':'<button class=\"mt-del\" onclick=\"mtDelItem(", 1, "WHO"],
    ["    h+='</div>'+_mtGoalsSecHtml(m, print)+'<div class=\"mt-foot\">", "    var _gHas=(m.goals||[]).some(function(b){ return b && (b.items||[]).length; });\n    h+='</div>'+((!print && !_gHas && m.status!=='final')?('<details class=\"mt-more\"><summary>＋ 담당자별 목표 적기 (선택)</summary>'+_mtGoalsSecHtml(m, print)+'</details>'):((print && !_gHas)?'':_mtGoalsSecHtml(m, print)))+'<div class=\"mt-foot\">", 1, "GOALS"],
    ["  // 줄 앞의 이름 → 담당자. \"함현식 …\" / \"함현식: …\" / \"[함현식] …\" 모두 인식.", "\x00ANCH", 1, "ANCH"]
  ];
  if(isTest) OPS.push([marker[0], marker[1], 1, "MARKER"]);
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  // 3) 옛 mtSaveAgenda 를 새 모듈로 교체
  s=cut(s, "  window.mtSaveAgenda = function(id){", "\x00ANCH", MOD, "SAVE");
  s=rep(s, "\x00ANCH", "  // 줄 앞의 이름 → 담당자. \"함현식 …\" / \"함현식: …\" / \"[함현식] …\" 모두 인식.", 1, "ANCH2");
  return s;
}
if(typeof module!=='undefined') module.exports=r275Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r275Apply(fs.readFileSync(src,'utf8'), isTest, ['<!-- test build r274 2026-11-23 -->','<!-- test build r275 2026-11-25 -->'])); console.log('ok →', out); }
