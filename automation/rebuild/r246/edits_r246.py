# -*- coding: utf-8 -*-
# r246 (사용자 요청 2026-10-22): "일정은 한 일을 적는 게 아니라 세운 목표의 이수로" — 목표 → 일정 (답: 목표→일정만 · 일반 줄 허용 · 자동 기록 유지)
#  - 목표의 세부 항목을 추가하면(회의록 3절 · 메모장 '내 목표' 카드) 그 담당자의 일정(메모장)에 한 줄이 생긴다: "목표 · <목표> — <세부 항목>", goalRef{mid,gid,sid}.
#    세부 항목마다 날짜(due)를 정할 수 있고(추가할 때 또는 나중에), 날짜가 있으면 그 날 주간 일정에 올라간다.
#  - 일정에서 완료(☐) ↔ 세부 항목 체크가 서로 맞춰져 이수율에 반영. 세부 항목·목표를 지우면 일정 줄도 지운다.
#  - 일정 줄에 [목표] 배지(누르면 그 회의록).
import io, sys, json

JS = r"""
  // ─── r246: 목표 세부 항목 ↔ 담당자 일정(메모) 연동 ───
  function _mtGoalMemoText(it, s){ return '목표 · '+String(it.title||'')+' — '+String(s.text||''); }
  function _mtGoalMemo(m, name, it, s){   // 세부 항목 → 담당자 일정에 한 줄 (연결)
    if(!_mtMemberName(name) || !s) return null;
    var now=Date.now();
    var line={ id:'mm'+now.toString(36)+Math.random().toString(36).slice(2,6), owner:name, text:_mtGoalMemoText(it, s), parent:'',
               kind:'memo', vendor:'', to:'', name:'', phone:'', when:{date:(s.due||''), time:''},
               date:_mmToday(), createdAt:now, done:!!s.done, doneAt:(s.done?(s.doneAt||now):0), feedback:[], card:'', linked:{},
               goalRef:{ mid:m.id, gid:it.id, sid:s.id } };
    memoLines.push(line); s.memoId=line.id; return line;
  }
  function _mtGoalLineOf(s){ return (s&&s.memoId)?(memoLines||[]).find(function(x){ return x.id===s.memoId; }):null; }
  function _mtGoalSyncToMemo(m, name, it, s){   // 세부 항목 변경(체크·날짜·글) → 일정 줄
    var l=_mtGoalLineOf(s);
    if(!l){ if(!s.done){ _mtGoalMemo(m, name, it, s); _mmSave(); } return; }
    l.text=_mtGoalMemoText(it, s); l.when=l.when||{date:'',time:''}; l.when.date=s.due||'';
    if(s.done){ if(!l.done){ l.done=true; l.doneAt=s.doneAt||Date.now(); } } else { if(l.done){ l.done=false; l.doneAt=0; } }
    _mmSave();
  }
  function _mtGoalSyncFromMemo(l, done){   // 일정 줄 완료/취소 → 세부 항목
    if(!l || !l.goalRef) return;
    var m=_mtFind(l.goalRef.mid); if(!m) return; var f=_mtGoalFind(m, l.goalRef.gid); if(!f) return;
    var s=(f.item.subs||[]).find(function(x){ return x.id===l.goalRef.sid; }); if(!s) return;
    if(!!s.done===!!done) return;
    s.done=!!done; s.doneAt=done?(l.doneAt||Date.now()):0; s.upd=Date.now(); _mtGoalTouch(m, f.item);
    try{ if(document.getElementById('pageMeeting') && document.getElementById('pageMeeting').classList.contains('active')) renderMeetingPage(true); }catch(_e){}
  }
  function _mtGoalDropLines(subs){   // 세부 항목(들) 삭제 → 일정 줄 제거
    var ids=(subs||[]).map(function(s){ return s&&s.memoId; }).filter(Boolean); if(!ids.length) return;
    memoLines=(memoLines||[]).filter(function(x){ return ids.indexOf(x.id)<0 && ids.indexOf(x.parent)<0; }); _mmSave();
  }
  window.mtGoalSubDue = function(mid, gid, sid, val){
    var m=_mtFind(mid); if(!m) return; var f=_mtGoalFind(m, gid); if(!f) return; if(!_mtGoalCan(f.block.name)) return;
    var s=(f.item.subs||[]).find(function(x){ return x.id===sid; }); if(!s) return;
    var v=String(val||''); if(v && !/^\d{4}-\d{2}-\d{2}$/.test(v)) return;
    s.due=v; s.upd=Date.now(); _mtGoalTouch(m, f.item); _mtGoalSyncToMemo(m, f.block.name, f.item, s); _mtGoalRerender();
  };
  window.mmGoGoal = function(mid){ try{ switchPage('meeting'); }catch(_e){} try{ mtOpen(mid); }catch(_e){} };
"""

OPS = [
  # 세부 항목 줄: 날짜 표시 + 날짜 입력
  ["      subs.forEach(function(s){ h+='<label class=\"mt-goal-sub'+(s.done?' done':'')+'\">'+(can?'<input type=\"checkbox\"'+(s.done?' checked':'')+' onchange=\"mtGoalSubToggle(\\''+m.id+'\\',\\''+it.id+'\\',\\''+s.id+'\\',this.checked)\">':(s.done?'☑ ':'☐ '))+'<span>'+_mtEsc(s.text||'')+'</span>'+(can?'<a onclick=\"mtGoalSubDel(\\''+m.id+'\\',\\''+it.id+'\\',\\''+s.id+'\\')\" title=\"세부 항목 삭제\">✕</a>':'')+'</label>'; });",
   "      subs.forEach(function(s){ h+='<label class=\"mt-goal-sub'+(s.done?' done':'')+'\">'+(can?'<input type=\"checkbox\"'+(s.done?' checked':'')+' onchange=\"mtGoalSubToggle(\\''+m.id+'\\',\\''+it.id+'\\',\\''+s.id+'\\',this.checked)\">':(s.done?'☑ ':'☐ '))+'<span>'+_mtEsc(s.text||'')+'</span>'"
   "+(can?'<input type=\"date\" class=\"mt-goal-date\" value=\"'+_mtEsc(s.due||'')+'\" title=\"일정 날짜 — 정하면 그 날 주간 일정에 올라갑니다\" onfocus=\"_mtGoalFocus(true)\" onblur=\"_mtGoalFocus(false)\" onchange=\"mtGoalSubDue(\\''+m.id+'\\',\\''+it.id+'\\',\\''+s.id+'\\',this.value)\">':(s.due?'<small class=\"mt-goal-due\">'+_mtEsc(s.due.slice(5).replace('-','/'))+'</small>':''))"
   "+(can?'<a onclick=\"mtGoalSubDel(\\''+m.id+'\\',\\''+it.id+'\\',\\''+s.id+'\\')\" title=\"세부 항목 삭제\">✕</a>':'')+'</label>'; });   // r246: 날짜", 1, "SUB_ROW"],
  # 추가칸: 날짜 입력 같이
  ["      if(can) h+='<div class=\"mt-goal-add\"><input placeholder=\"세부 항목 추가 — 적고 Enter\" onfocus=\"_mtGoalFocus(true)\" onblur=\"_mtGoalFocus(false)\" onkeydown=\"if(event.key===\\'Enter\\'&&!event.isComposing){ event.preventDefault(); mtGoalSubAdd(\\''+m.id+'\\',\\''+it.id+'\\',this); }\"></div>';",
   "      if(can) h+='<div class=\"mt-goal-add\"><input placeholder=\"세부 항목 추가 — 적고 Enter (내 일정에 올라갑니다)\" onfocus=\"_mtGoalFocus(true)\" onblur=\"_mtGoalFocus(false)\" onkeydown=\"if(event.key===\\'Enter\\'&&!event.isComposing){ event.preventDefault(); mtGoalSubAdd(\\''+m.id+'\\',\\''+it.id+'\\',this); }\"><input type=\"date\" class=\"mt-goal-date\" title=\"일정 날짜(선택)\" onfocus=\"_mtGoalFocus(true)\" onblur=\"_mtGoalFocus(false)\"></div>';   // r246", 1, "ADD_ROW"],
  # 세부 항목 추가 → 일정 줄 생성
  ["    f.item.subs=f.item.subs||[]; f.item.subs.push({ id:_mtId('ms'), text:t, done:false, at:Date.now(), upd:Date.now() });\n    _mtGoalTouch(m, f.item); inp.value=''; _mtGoalRerender();",
   "    var _de=inp.parentNode?inp.parentNode.querySelector('input[type=date]'):null; var due=(_de&&/^\\d{4}-\\d{2}-\\d{2}$/.test(_de.value||''))?_de.value:'';\n"
   "    var _s={ id:_mtId('ms'), text:t, done:false, due:due, at:Date.now(), upd:Date.now() };\n"
   "    f.item.subs=f.item.subs||[]; f.item.subs.push(_s);\n"
   "    try{ if(_mtGoalMemo(m, f.block.name, f.item, _s)) _mmSave(); }catch(_e){}   // r246: 담당자 일정에 한 줄\n"
   "    _mtGoalTouch(m, f.item); inp.value=''; _mtGoalRerender();", 1, "SUB_ADD"],
  # 체크 → 일정 줄
  ["    s.done=!!on; s.doneAt=on?Date.now():0; s.upd=Date.now(); _mtGoalTouch(m, f.item); _mtGoalRerender();",
   "    s.done=!!on; s.doneAt=on?Date.now():0; s.upd=Date.now(); _mtGoalTouch(m, f.item); try{ _mtGoalSyncToMemo(m, f.block.name, f.item, s); }catch(_e){} _mtGoalRerender();   // r246", 1, "SUB_TOGGLE"],
  # 세부 항목 삭제 → 일정 줄 제거
  ["    f.item.subs=(f.item.subs||[]).filter(function(x){ return x.id!==sid; }); f.item.del=f.item.del||{}; f.item.del[sid]=Date.now();",
   "    try{ _mtGoalDropLines((f.item.subs||[]).filter(function(x){ return x.id===sid; })); }catch(_e){}   // r246\n    f.item.subs=(f.item.subs||[]).filter(function(x){ return x.id!==sid; }); f.item.del=f.item.del||{}; f.item.del[sid]=Date.now();", 1, "SUB_DEL"],
  # 목표 삭제 → 일정 줄 제거
  ["      f.block.items=f.block.items.filter(function(x){ return x.id!==gid; }); m.del=m.del||{}; m.del[gid]=Date.now();",
   "      try{ _mtGoalDropLines(f.item.subs||[]); }catch(_e){}   // r246\n      f.block.items=f.block.items.filter(function(x){ return x.id!==gid; }); m.del=m.del||{}; m.del[gid]=Date.now();", 1, "GOAL_DEL"],
  # 일정 완료/취소 → 세부 항목
  ["  function _mtSyncFromMemo(l, done){   // 메모 줄 완료/취소 → 회의록 항목도 같이\n    if(!l || !l.mtRef) return;",
   "  function _mtSyncFromMemo(l, done){   // 메모 줄 완료/취소 → 회의록 항목도 같이\n    if(l && l.goalRef){ try{ _mtGoalSyncFromMemo(l, done); }catch(_e){} return; }   // r246: 목표 세부 항목\n    if(!l || !l.mtRef) return;", 1, "SYNC_FROM"],
  # JS 블록
  ["  var _mtGoalFocusN=0;\n  window._mtGoalFocus = function(on){",
   JS + "  var _mtGoalFocusN=0;\n  window._mtGoalFocus = function(on){", 1, "JS"],
  # 메모 배지
  ["    if(l.qRef) h+='<span class=\"mm-chip mm-qt\" onclick=\"mmGoQuote(\\''+_mmEsc(l.qRef.id)+'\\')\" title=\"저장된 견적 — 누르면 그 견적을 불러옵니다\">견적</span>';   // r222",
   "    if(l.qRef) h+='<span class=\"mm-chip mm-qt\" onclick=\"mmGoQuote(\\''+_mmEsc(l.qRef.id)+'\\')\" title=\"저장된 견적 — 누르면 그 견적을 불러옵니다\">견적</span>';   // r222\n    if(l.goalRef) h+='<span class=\"mm-chip mm-mt\" onclick=\"mmGoGoal(\\''+_mmEsc(l.goalRef.mid)+'\\')\" title=\"목표 이수 항목 — 완료하면 이수율에 반영 · 누르면 그 회의록으로\">목표</span>';   // r246", 1, "CHIP"],
  # CSS
  ["    .mt-goal-add input { width:100%; box-sizing:border-box; font-size:12.5px; padding:4px 8px; border:1px dashed #cbd5e1; border-radius:6px; font-family:inherit; }",
   "    .mt-goal-add { display:flex; gap:6px; align-items:center; }\n    .mt-goal-add input { width:100%; box-sizing:border-box; font-size:12.5px; padding:4px 8px; border:1px dashed #cbd5e1; border-radius:6px; font-family:inherit; }\n    .mt-goal-add input.mt-goal-date, .mt-goal-sub input.mt-goal-date { width:auto; flex:0 0 auto; font-size:11px; padding:2px 4px; border:1px solid #e5e7eb; border-radius:4px; color:#6b7280; margin-left:auto; }\n    .mt-goal-sub input.mt-goal-date + a { margin-left:0; }\n    .mt-goal-due { font-size:10.5px; color:#2563eb; background:#eaf1fb; padding:0 5px; border-radius:3px; margin-left:auto; }", 1, "CSS"],
  ["<!-- test build r245 2026-10-20 -->", "<!-- test build r246 2026-10-22 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R246 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r246(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r246 브라우저 적용기 — edits_r246.py 의 OPS. r245 적용본 위에 적용.",
             "function r246Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R246 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r246Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r246(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r246 applied:', path)
