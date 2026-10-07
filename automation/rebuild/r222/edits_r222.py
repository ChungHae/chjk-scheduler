# -*- coding: utf-8 -*-
# r222 (사용자 요청 2026-10-07):
#   ① 회의록 안건을 저장하면 참석자 각자의 개인 일정(메모장)에 그 안건이 올라간다 (r189 업무 보고 연동과 같은 틀, 회의 날짜로).
#   ② 견적서를 저장(내보내기)하면 작성자의 일정에 "견적서 작성 …" 이 완료된 업무로 들어간다 (완료 탭에서 보임, [견적] 칩으로 바로 열기).
import io, sys, json

AGENDA_FUNCS = r"""  function _mtAgendaMemo(m, a){   // r222: 안건 → 참석자 각자의 일정(메모)에 한 줄씩. 참석자 중 멤버가 없으면 작성자 본인.
    var who=(m.attendees||[]).filter(function(n){ return !!_mtMemberName(n); });
    if(!who.length){ var me=_mtMemberName(_mtMe()); if(me) who=[me]; }
    if(!who.length) return;
    var txt='회의 안건'+(m.title?'('+m.title+')':'')+' · '+(a.title?(a.title+': '):'')+(a.text||'');
    var now=Date.now(); a.memoIds=a.memoIds||[];
    who.forEach(function(name, i){
      var line={ id:'mm'+(now+i).toString(36)+Math.random().toString(36).slice(2,6), owner:name, text:txt, parent:'',
                 kind:'meeting', vendor:'', to:'', name:'', phone:'', when:{date:(m.date||''), time:''},
                 date:_mmToday(), createdAt:now, done:false, doneAt:0, feedback:[], card:'', linked:{},
                 mtRef:{ mid:m.id, iid:a.id } };
      memoLines.push(line); a.memoIds.push(line.id);
    });
    _mmSave();
  }
  function _mtMemoLinesOf(it){   // r222: 항목에 연결된 메모 줄 전부 (업무 보고 memoId + 안건 memoIds)
    var ids=[]; if(it&&it.memoId) ids.push(it.memoId); if(it&&it.memoIds) ids=ids.concat(it.memoIds);
    return (memoLines||[]).filter(function(x){ return ids.indexOf(x.id)>=0; });
  }
"""

QUOTE_FUNCS = r"""  // r222: 견적서 저장 → 작성자 일정에 '완료된 업무'로 기록 (같은 견적을 다시 저장하면 그 줄을 갱신)
  function _qLogDoneMemo(no, vn, cnt, supply, who){
    try{
      if(!who || !(members||[]).some(function(x){ return x.name===who; })) return;
      var txt='견적서 작성 · '+(vn||'')+' · '+String(no||'')+' ('+cnt+'품목'+(supply>0?(' · '+Number(supply).toLocaleString('ko-KR')+'원'):'')+')';
      var now=Date.now();
      var ex=(memoLines||[]).find(function(l){ return l.qRef && l.qRef.id===_qLoadedId && l.owner===who; });
      if(ex){ ex.text=txt; ex.vendor=vn||''; ex.qRef.no=no||''; if(!ex.done){ ex.done=true; ex.doneAt=now; } }
      else {
        memoLines.push({ id:'mm'+now.toString(36)+Math.random().toString(36).slice(2,6), owner:who, text:txt, parent:'',
                         kind:'memo', vendor:(vn||''), to:'', name:'', phone:'', when:{date:'',time:''},
                         date:_mmToday(), createdAt:now, done:true, doneAt:now, feedback:[], card:'', linked:{},
                         qRef:{ id:_qLoadedId, no:(no||'') } });
      }
      _mmSave();
      try{ if(document.getElementById('pageMemo') && document.getElementById('pageMemo').classList.contains('active')) renderMemoPage(true); }catch(_e){}
    }catch(_e){}
  }
  window.mmGoQuote = function(id){ try{ switchPage('quote'); }catch(_e){} try{ qLoadSaved(id); }catch(_e){} };
"""

OPS = [
 # CSS: 견적 칩
 [
  "    .mm-chip.mm-mt { background:#e0e7ff; color:#3730a3; cursor:pointer; }   /* r189 회의록에서 온 업무 */\n",
  "    .mm-chip.mm-mt { background:#e0e7ff; color:#3730a3; cursor:pointer; }   /* r189 회의록에서 온 업무 */\n    .mm-chip.mm-qt { background:#dcfce7; color:#166534; cursor:pointer; }   /* r222 견적서 작성 기록 */\n",
  1, "CSS"
 ],
 # ① 안건 저장 → 참석자 일정
 [
  "    lines.forEach(function(t){ var p=_mtParseAgenda(t); m.agenda.push({ id:_mtId('ma'), title:p.title, text:p.text, done:false, by:_mtMe(), at:Date.now() }); });\n    m.updatedAt=Date.now(); _mtSave(); el.value=''; try{ mtDraftKeep(el, id); }catch(_e){}\n    renderMeetingPage(true); _mtToast('안건 '+lines.length+'건 저장');",
  "    var _mn=0;\n    lines.forEach(function(t){ var p=_mtParseAgenda(t); var a={ id:_mtId('ma'), title:p.title, text:p.text, done:false, by:_mtMe(), at:Date.now() }; m.agenda.push(a); try{ _mtAgendaMemo(m, a); _mn+=(a.memoIds||[]).length; }catch(_e){} });   // r222: 참석자 일정에도\n    m.updatedAt=Date.now(); _mtSave(); el.value=''; try{ mtDraftKeep(el, id); }catch(_e){}\n    renderMeetingPage(true); _mtToast('안건 '+lines.length+'건 저장'+(_mn?(' — 참석자 일정에 '+_mn+'건 등록'):''));",
  1, "AGENDA_SAVE"
 ],
 [
  "  function _mtSyncFromMemo(l, done){   // 메모 줄 완료/취소 → 회의록 항목도 같이\n",
  AGENDA_FUNCS + "  function _mtSyncFromMemo(l, done){   // 메모 줄 완료/취소 → 회의록 항목도 같이\n",
  1, "AGENDA_FUNCS"
 ],
 # 완료 동기화: 항목 → 연결된 메모 줄 전부
 [
  "  function _mtSyncToMemo(it){   // 회의록 항목 완료/취소 → 연결된 메모 줄도 같이\n    if(!it || !it.memoId) return;\n    var l=(memoLines||[]).find(function(x){ return x.id===it.memoId; }); if(!l) return;\n    if(it.done){ if(!l.done){ l.done=true; l.doneAt=it.doneAt||Date.now(); } }\n    else { if(l.done){ l.done=false; l.doneAt=0; } }\n    _mmSave();",
  "  function _mtSyncToMemo(it){   // 회의록 항목 완료/취소 → 연결된 메모 줄도 같이 (r222: 안건은 참석자 수만큼)\n    if(!it) return;\n    var ls=_mtMemoLinesOf(it); if(!ls.length) return;\n    ls.forEach(function(l){\n      if(it.done){ if(!l.done){ l.done=true; l.doneAt=it.doneAt||Date.now(); } }\n      else { if(l.done){ l.done=false; l.doneAt=0; } }\n    });\n    _mmSave();",
  1, "SYNC_TO"
 ],
 # 메모 줄 완료 → 항목 완료 → 다른 참석자 줄도
 [
  "    else { if(!it.done) return; it.done=false; it.doneAt=0; it.doneBy=''; }\n    m.updatedAt=Date.now(); _mtSave();\n",
  "    else { if(!it.done) return; it.done=false; it.doneAt=0; it.doneBy=''; }\n    m.updatedAt=Date.now(); _mtSave();\n    try{ _mtSyncToMemo(it); }catch(_e){}   // r222: 안건이면 다른 참석자의 일정 줄도 같이\n",
  1, "SYNC_FROM"
 ],
 # 삭제 시 연결 해제: memoIds 포함
 [
  "    try{ var _di=_mtItem(m, iid); if(_di && _di.memoId){ var _dl=(memoLines||[]).find(function(x){ return x.id===_di.memoId; }); if(_dl){ delete _dl.mtRef; _mmSave(); } } }catch(_e){}   // r189: 일정 줄은 남기고 연결만 해제\n",
  "    try{ var _di=_mtItem(m, iid); var _dls=_mtMemoLinesOf(_di); if(_dls.length){ _dls.forEach(function(_dl){ delete _dl.mtRef; }); _mmSave(); } }catch(_e){}   // r189: 일정 줄은 남기고 연결만 해제 (r222: 안건 줄들 포함)\n",
  1, "DEL_UNLINK"
 ],
 # 회의록 안건 줄에 '일정' 표시
 [
  "(it.memoId?'<span class=\"mt-by\" title=\"담당자 일정에 등록됨\">일정</span>':'')",
  "(it.memoId?'<span class=\"mt-by\" title=\"담당자 일정에 등록됨\">일정</span>':((it.memoIds&&it.memoIds.length)?'<span class=\"mt-by\" title=\"참석자 '+it.memoIds.length+'명의 일정에 등록됨\">일정 '+it.memoIds.length+'</span>':''))",
  1, "ITEM_BADGE"
 ],
 # ② 견적 저장 → 완료된 업무
 [
  "    else { quoteSaved.unshift({id:_qLoadedId, title:_qQuoteNo, vname:vn, vid:vid, count:_qCart.length, total:supply, nego:_qNego, memo:_qMemo, note:_qNote, savedBy:who, savedAt:Date.now(), cols:JSON.parse(JSON.stringify(_qCols||[]))}); }\n    saveAll();\n  }\n",
  "    else { quoteSaved.unshift({id:_qLoadedId, title:_qQuoteNo, vname:vn, vid:vid, count:_qCart.length, total:supply, nego:_qNego, memo:_qMemo, note:_qNote, savedBy:who, savedAt:Date.now(), cols:JSON.parse(JSON.stringify(_qCols||[]))}); }\n    saveAll();\n    try{ _qLogDoneMemo(_qQuoteNo, vn, _qCart.length, supply, who); }catch(_e){}   // r222: 작성자 일정에 완료된 업무로\n  }\n" + QUOTE_FUNCS,
  1, "QUOTE_LOG"
 ],
 # 메모 칩: [견적]
 [
  "    if(l.mtRef) h+='<span class=\"mm-chip mm-mt\" onclick=\"mmGoMeeting(\\''+l.mtRef.mid+'\\')\" title=\"회의록에서 온 업무 — 누르면 그 회의록으로\">회의</span>';   // r189\n",
  "    if(l.mtRef) h+='<span class=\"mm-chip mm-mt\" onclick=\"mmGoMeeting(\\''+l.mtRef.mid+'\\')\" title=\"회의록에서 온 업무 — 누르면 그 회의록으로\">회의</span>';   // r189\n    if(l.qRef) h+='<span class=\"mm-chip mm-qt\" onclick=\"mmGoQuote(\\''+_mmEsc(l.qRef.id)+'\\')\" title=\"저장된 견적 — 누르면 그 견적을 불러옵니다\">견적</span>';   // r222\n",
  1, "CHIP"
 ],
 # 회의 안건 줄에는 '업체?' 칩을 띄우지 않는다 (사내 회의)
 [
  "      else if(mine) h+='<span class=\"mm-chip mm-vend mm-vend-none\" onclick=\"mmVendorPick(\\''+l.id+'\\')\" title=\"업체 지정\">업체?</span>';\n",
  "      else if(mine && !l.mtRef) h+='<span class=\"mm-chip mm-vend mm-vend-none\" onclick=\"mmVendorPick(\\''+l.id+'\\')\" title=\"업체 지정\">업체?</span>';   // r222: 회의록에서 온 줄은 제외\n",
  1, "NO_VENDOR_CHIP"
 ],
 [
  "<!-- test build r221 2026-10-02 -->",
  "<!-- test build r222 2026-10-07 -->",
  1, "MARKER"
 ]
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R222 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r222(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r222 브라우저 적용기 — edits_r222.py 의 OPS. r221(live 47499345 / test e0fafb3f) 에 적용.",
             "function r222Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R222 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r222Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r222(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r222 applied:', path)
