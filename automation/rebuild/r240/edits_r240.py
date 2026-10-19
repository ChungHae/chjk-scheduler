# -*- coding: utf-8 -*-
# r240 (사용자 요청 2026-10-19): 회의록 — ① 지난 회의를 접지 않고 전부 최신순으로 (일정의 지난 회의 안건 숨김도 해제)
#   ② 회의마다 직원별 '목표' 칸 (3. 담당자별 목표) ③ 목표마다 세부 항목(체크) + 상세 내용 — 이수율 = 세부 항목 완료 비율(자동)
#   ④ 메모장(내 일정) 맨 위 '내 목표' 카드에서 본인이 세부 항목 체크·추가, 상세 내용 수정 → 회의록에 그대로 반영
#   사용자 답(10-19): 목표 단위 = 회의마다 새로 / 이수율 = 세부 항목 완료 비율 자동 / 상세는 메모장 목표 카드 / 지난 회의 전부 펼쳐 최신순
#   자료: meetings[].goals = [{ name, items:[{ id, title, detail, subs:[{id,text,done,at,upd}], by, at, upd }] }]
#   동시 작성(r236) 병합: goals 도 이름별·id별 합집합, 같은 항목은 upd 큰 쪽, 세부 항목도 id 합집합·upd 큰 쪽, 묘비(m.del) 적용.
import io, sys, json

JS = r"""
  // ─── r240: 담당자별 목표 (회의마다) + 세부 항목 이수율 + 메모장 '내 목표' 카드 ───
  function _mtGoalsOf(m){ if(!m.goals || !Array.isArray(m.goals)) m.goals=[]; return m.goals; }
  function _mtGoalBlock(m, name, make){ var g=_mtGoalsOf(m).find(function(x){ return x && x.name===name; }); if(!g && make){ g={ name:name, items:[] }; m.goals.push(g); } return g; }
  function _mtGoalFind(m, gid){ var out=null; _mtGoalsOf(m).forEach(function(b){ (b.items||[]).forEach(function(it){ if(it.id===gid) out={ block:b, item:it }; }); }); return out; }
  function _mtGoalProg(it){ var s=(it&&it.subs||[]).filter(function(x){ return x && !(it.del&&it.del[x.id]); }); var d=s.filter(function(x){ return x.done; }).length; return { d:d, t:s.length, pct:(s.length?Math.round(d*100/s.length):0) }; }
  function _mtGoalBlockProg(b){ var d=0,t=0; (b.items||[]).forEach(function(it){ var p=_mtGoalProg(it); d+=p.d; t+=p.t; }); return { d:d, t:t, pct:(t?Math.round(d*100/t):0) }; }
  function _mtGoalCan(name){ var me=_mtMe(); return !!me && (me===name || (typeof _isAdmin==='function' && _isAdmin())); }
  function _mtGoalTouch(m, it){ var now=Date.now(); if(it) it.upd=now; m.updatedAt=now; _mtSave(); }
  function _mtGoalSubs(it){ return (it.subs||[]).filter(function(x){ return x && !(it.del&&it.del[x.id]); }); }
  // 목표 한 개 HTML — ctx: 'doc'(회의록) | 'card'(메모장)
  function _mtGoalItemHtml(m, name, it, print, ctx){
    var p=_mtGoalProg(it), can=!print && _mtGoalCan(name);
    var cls=p.t?(p.pct>=100?' done':(p.pct>0?' part':'')):'';
    var h='<div class="mt-goal'+cls+'" data-gid="'+it.id+'">';
    h+='<div class="mt-goal-h"><span class="mt-goal-t">'+_mtEsc(it.title||'')+'</span>'
      +'<span class="mt-goal-bar"><i style="width:'+p.pct+'%"></i></span><span class="mt-goal-pct">'+(p.t?(p.pct+'% ('+p.d+'/'+p.t+')'):'세부 항목 없음')+'</span>'
      +(can&&ctx==='doc'?'<a class="mt-goal-x" onclick="mtGoalDel(\''+m.id+'\',\''+it.id+'\')" title="목표 삭제">✕</a>':'')+'</div>';
    var subs=_mtGoalSubs(it);
    if(subs.length||can){
      h+='<div class="mt-goal-subs">';
      subs.forEach(function(s){ h+='<label class="mt-goal-sub'+(s.done?' done':'')+'">'+(can?'<input type="checkbox"'+(s.done?' checked':'')+' onchange="mtGoalSubToggle(\''+m.id+'\',\''+it.id+'\',\''+s.id+'\',this.checked)">':(s.done?'☑ ':'☐ '))+'<span>'+_mtEsc(s.text||'')+'</span>'+(can?'<a onclick="mtGoalSubDel(\''+m.id+'\',\''+it.id+'\',\''+s.id+'\')" title="세부 항목 삭제">✕</a>':'')+'</label>'; });
      if(can) h+='<div class="mt-goal-add"><input placeholder="세부 항목 추가 — 적고 Enter" onfocus="_mtGoalFocus(true)" onblur="_mtGoalFocus(false)" onkeydown="if(event.key===\'Enter\'&&!event.isComposing){ event.preventDefault(); mtGoalSubAdd(\''+m.id+'\',\''+it.id+'\',this); }"></div>';
      h+='</div>';
    }
    if(can) h+='<textarea class="mt-goal-detail" rows="2" placeholder="상세 내용 · 진행 상황 (수시로 적어 두세요 — 칸을 나가면 저장)" onfocus="_mtGoalFocus(true)" onblur="_mtGoalFocus(false); mtGoalDetail(\''+m.id+'\',\''+it.id+'\',this.value)">'+_mtEsc(it.detail||'')+'</textarea>';
    else if(it.detail) h+='<div class="mt-goal-detail-ro">'+_mtEsc(it.detail).replace(/\n/g,'<br>')+'</div>';
    h+='</div>';
    return h;
  }
  function _mtGoalsSecHtml(m, print){
    var id=m.id;
    var h='<div class="mt-sec"><h3>3. 담당자별 목표 <span class="mt-goal-hint">— 이번 회의에서 다음 회의까지의 목표 · 세부 항목을 체크하면 이수율이 올라갑니다 (본인만 수정)</span></h3>';
    var names=(m.attendees||[]).slice(); _mtGoalsOf(m).forEach(function(b){ if(b && names.indexOf(b.name)<0 && (b.items||[]).length) names.push(b.name); });
    if(!names.length) h+='<div style="font-size:12.5px;color:#9ca3af;padding:6px">참석자를 지정하면 담당자별 목표 칸이 생깁니다.</div>';
    names.forEach(function(n){
      var b=_mtGoalBlock(m, n, false)||{ name:n, items:[] }; var bp=_mtGoalBlockProg(b);
      h+='<div class="mt-rep mt-goal-rep"><div class="nm">'+_mtEsc(n)+(bp.t?'<small>이수율 '+bp.pct+'%</small>':'')+'</div><div>';
      if(!(b.items||[]).length) h+='<div style="font-size:12.5px;color:#9ca3af">'+(print?'-':'아직 목표 없음 — 아래 작성란에 "'+_mtEsc(n)+' 목표" 로 적고 저장')+'</div>';
      (b.items||[]).forEach(function(it){ h+=_mtGoalItemHtml(m, n, it, print, 'doc'); });
      h+='</div></div>';
    });
    if(!print && m.status!=='final'){
      var _nm=names.slice(); (members||[]).forEach(function(x){ if(_nm.indexOf(x.name)<0) _nm.push(x.name); });
      h+='<div class="mt-write"><div class="mt-names"><span>이름을 누르면 줄 앞에 들어갑니다:</span>'+_nm.map(function(n){ return '<button type="button" onclick="mtInsertNameTo(\'mtGoalIn\',\''+_mtEsc(n)+'\')">'+_mtEsc(n)+'</button>'; }).join('')+'</div>'
        +'<textarea id="mtGoalIn" data-dk="goal" data-mid="'+id+'" rows="3" placeholder="이름 목표   (예: 함현식 신규 거래처 3곳 발굴 / 김재성 SMC 가격표 10월분 갱신)\n세부 항목과 상세 내용은 저장 뒤 목표 아래에서 각자 적습니다." oninput="mtTaInput(this)" onkeydown="mtTaKey(event,this)"></textarea>'
        +'<div class="mt-write-bar"><span class="mt-hint">한 줄에 목표 하나 · Ctrl+Enter 저장 · 저장하면 각자 일정(메모장) 맨 위 \'내 목표\' 카드에 뜹니다</span><button class="mt-btn pri" onclick="mtSaveGoals(\''+id+'\')">목표 저장</button></div></div>';
    }
    h+='</div>';
    return h;
  }
  window.mtInsertNameTo = function(elId, nm){ var el=document.getElementById(elId); if(!el) return; var v=el.value||''; var s=el.selectionStart!=null?el.selectionStart:v.length; var lineStart=v.lastIndexOf('\n', s-1)+1; var before=v.slice(0,lineStart), rest=v.slice(lineStart); el.value=before+nm+' '+rest; el.focus(); var pos=lineStart+nm.length+1; try{ el.setSelectionRange(pos,pos); }catch(_e){} try{ mtTaInput(el); }catch(_e){} };
  window.mtSaveGoals = function(id){
    var el=document.getElementById('mtGoalIn'); if(!el) return; var lines=_mtLines(el);
    if(!lines.length){ _mtToast('적힌 목표가 없습니다.'); return; }
    var m=_mtFind(id); if(!m) return; if(typeof _guardW==='function' && !_guardW()) return; if(_mtLocked(m)) return;
    var names=(members||[]).map(function(x){ return x.name; }).filter(Boolean); (m.attendees||[]).forEach(function(n){ if(names.indexOf(n)<0) names.push(n); });
    var cur='', me=_mtMe(), cnt={}, n=0;
    lines.forEach(function(line){
      var sp=_mtSplitName(line, names); var who, text;
      if(sp){ cur=sp.name; who=sp.name; text=sp.text; if(!text) return; } else { who=cur||me; text=line; }
      if(!who) return;
      var b=_mtGoalBlock(m, who, true);
      if((m.attendees||[]).indexOf(who)<0 && (members||[]).some(function(x){ return x.name===who; })) m.attendees.push(who);
      b.items.push({ id:_mtId('mg'), title:text, detail:'', subs:[], by:me, at:Date.now(), upd:Date.now() });
      cnt[who]=(cnt[who]||0)+1; n++;
    });
    if(!n){ _mtToast('등록할 줄이 없습니다. 이름 뒤에 목표를 적어 주세요.'); return; }
    m.updatedAt=Date.now(); _mtSave(); el.value=''; try{ mtDraftKeep(el, id); }catch(_e){}
    renderMeetingPage(true); _mtToast('목표 '+n+'건 저장 — '+Object.keys(cnt).map(function(k){ return k+' '+cnt[k]; }).join(' · '));
  };
  window.mtGoalDel = function(mid, gid){
    var m=_mtFind(mid); if(!m) return; var f=_mtGoalFind(m, gid); if(!f) return; if(!_mtGoalCan(f.block.name)) return;
    showConfirmModal('목표 삭제', '"'+(f.item.title||'')+'" 목표를 지울까요? (세부 항목도 함께)', function(){
      f.block.items=f.block.items.filter(function(x){ return x.id!==gid; }); m.del=m.del||{}; m.del[gid]=Date.now();
      _mtGoalTouch(m, null); renderMeetingPage(true); try{ renderMemoPage(true); }catch(_e){}
    }, '삭제', '#dc2626');
  };
  window.mtGoalSubAdd = function(mid, gid, inp){
    var m=_mtFind(mid); if(!m) return; var f=_mtGoalFind(m, gid); if(!f) return; if(!_mtGoalCan(f.block.name)) return;
    var t=String(inp.value||'').trim(); if(!t) return;
    f.item.subs=f.item.subs||[]; f.item.subs.push({ id:_mtId('ms'), text:t, done:false, at:Date.now(), upd:Date.now() });
    _mtGoalTouch(m, f.item); inp.value=''; _mtGoalRerender();
  };
  window.mtGoalSubToggle = function(mid, gid, sid, on){
    var m=_mtFind(mid); if(!m) return; var f=_mtGoalFind(m, gid); if(!f) return; if(!_mtGoalCan(f.block.name)) return;
    var s=(f.item.subs||[]).find(function(x){ return x.id===sid; }); if(!s) return;
    s.done=!!on; s.doneAt=on?Date.now():0; s.upd=Date.now(); _mtGoalTouch(m, f.item); _mtGoalRerender();
  };
  window.mtGoalSubDel = function(mid, gid, sid){
    var m=_mtFind(mid); if(!m) return; var f=_mtGoalFind(m, gid); if(!f) return; if(!_mtGoalCan(f.block.name)) return;
    f.item.subs=(f.item.subs||[]).filter(function(x){ return x.id!==sid; }); f.item.del=f.item.del||{}; f.item.del[sid]=Date.now();
    _mtGoalTouch(m, f.item); _mtGoalRerender();
  };
  window.mtGoalDetail = function(mid, gid, val){
    var m=_mtFind(mid); if(!m) return; var f=_mtGoalFind(m, gid); if(!f) return; if(!_mtGoalCan(f.block.name)) return;
    var v=String(val||''); if(v===(f.item.detail||'')) return;
    f.item.detail=v; _mtGoalTouch(m, f.item); _mtGoalRerender();
  };
  var _mtGoalFocusN=0;
  window._mtGoalFocus = function(on){ if(on){ _mtGoalFocusN++; if(typeof _mmEditing!=='undefined') _mmEditing='mtgoal'; } else { _mtGoalFocusN=Math.max(0,_mtGoalFocusN-1); if(!_mtGoalFocusN && typeof _mmEditing!=='undefined' && _mmEditing==='mtgoal') _mmEditing=null; } };
  function _mtGoalRerender(){ try{ if(document.getElementById('mtBody') && _mtOpen) renderMeetingPage(true); }catch(_e){} try{ if(!_mtGoalFocusN) renderMemoPage(true); }catch(_e){} }
  // 메모장 '내 목표' 카드 — 내 목표가 있는 회의(최신순, 이수율 100% 인 회의는 가장 최근 1건만)
  function _mtGoalCard(){
    var me=_mmMe(); if(!me) return '';
    var ms=(meetings||[]).filter(function(m){ var b=m&&_mtGoalBlock(m, me, false); return b && (b.items||[]).length; })
      .sort(function(a,b){ return (b.date||'')<(a.date||'')?-1:((b.date||'')>(a.date||'')?1:(b.createdAt||0)-(a.createdAt||0)); });
    if(!ms.length) return '';
    var shown=[]; var doneSeen=false;
    ms.forEach(function(m){ var bp=_mtGoalBlockProg(_mtGoalBlock(m, me, false)); var fin=(bp.t>0 && bp.pct>=100); if(fin){ if(doneSeen) return; doneSeen=true; } shown.push(m); });
    shown=shown.slice(0,3);
    var h='<div class="mt-goal-card"><div class="mt-goal-card-h"><b>내 목표</b><span>회의마다 세운 목표 · 세부 항목을 체크하면 이수율이 올라갑니다</span><a onclick="switchPage(\'meeting\')">회의록 →</a></div>';
    shown.forEach(function(m){
      var b=_mtGoalBlock(m, me, false); var bp=_mtGoalBlockProg(b);
      h+='<div class="mt-goal-mt"><div class="mt-goal-mt-h"><span class="d">'+_mtEsc(_mtFmtD(m.date))+'</span><span class="t">'+_mtEsc(m.title||'업무회의')+'</span><span class="p'+(bp.t&&bp.pct>=100?' ok':'')+'">이수율 '+(bp.t?bp.pct+'%':'-')+'</span></div>';
      (b.items||[]).forEach(function(it){ h+=_mtGoalItemHtml(m, me, it, false, 'card'); });
      h+='</div>';
    });
    h+='</div>';
    return h;
  }
  // r236 병합 확장: goals (이름별 → 항목 id 별 → 세부 항목 id 별, upd 큰 쪽)
  function _mtMergeGoalItem(a, b){
    var base=(Number(a.upd||a.at||0)>=Number(b.upd||b.at||0))?a:b, other=(base===a)?b:a;
    var out=Object.assign({}, other, base); out.del=Object.assign({}, other.del||{}, base.del||{});
    var byId={}, order=[];
    _mtArr(other.subs).concat(_mtArr(base.subs)).forEach(function(s){ if(!s||!s.id||out.del[s.id]) return; if(!byId[s.id]){ byId[s.id]=s; order.push(s.id); } else { var c=byId[s.id]; byId[s.id]=(Number(s.upd||s.at||0)>=Number(c.upd||c.at||0))?s:c; } });
    out.subs=order.map(function(i){ return byId[i]; });
    return out;
  }
  function _mtMergeGoals(l, s, dm){
    var names=[], gmap={};
    _mtArr(l).concat(_mtArr(s)).forEach(function(b){ if(!b||!b.name) return; if(!gmap[b.name]){ gmap[b.name]={ name:b.name, items:[] }; names.push(b.name); }
      var tgt=gmap[b.name]; _mtArr(b.items).forEach(function(it){ if(!it||!it.id||dm[it.id]) return; var ex=tgt.items.find(function(x){ return x.id===it.id; }); if(!ex) tgt.items.push(it); else tgt.items[tgt.items.indexOf(ex)]=_mtMergeGoalItem(ex, it); }); });
    return names.map(function(n){ return gmap[n]; });
  }
"""

CSS = r"""
    .mt-goal-rep > div.nm small { display:block; font-weight:600; font-size:11px; color:#2563eb; margin-top:4px; }
    .mt-goal { border:1px solid #e5e7eb; border-radius:8px; padding:8px 10px; margin:4px 0 8px; background:#fff; }
    .mt-goal.part { border-color:#bfdbfe; background:#f8fbff; }
    .mt-goal.done { border-color:#bbf7d0; background:#f0fdf4; }
    .mt-goal-h { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
    .mt-goal-t { font-weight:700; color:#1f2937; font-size:13.5px; flex:1 1 200px; }
    .mt-goal-bar { flex:0 0 120px; height:8px; background:#e5e7eb; border-radius:4px; overflow:hidden; }
    .mt-goal-bar i { display:block; height:100%; background:#2563eb; }
    .mt-goal.done .mt-goal-bar i { background:#16a34a; }
    .mt-goal-pct { font-size:11.5px; color:#374151; min-width:70px; }
    .mt-goal-x { color:#9ca3af; cursor:pointer; font-size:12px; } .mt-goal-x:hover { color:#dc2626; }
    .mt-goal-subs { margin-top:6px; display:flex; flex-direction:column; gap:3px; }
    .mt-goal-sub { display:flex; align-items:center; gap:6px; font-size:12.5px; color:#374151; cursor:pointer; }
    .mt-goal-sub.done span { text-decoration:line-through; color:#9ca3af; }
    .mt-goal-sub a { color:#d1d5db; cursor:pointer; font-size:11px; margin-left:auto; } .mt-goal-sub a:hover { color:#dc2626; }
    .mt-goal-add input { width:100%; box-sizing:border-box; font-size:12.5px; padding:4px 8px; border:1px dashed #cbd5e1; border-radius:6px; font-family:inherit; }
    .mt-goal-detail { width:100%; box-sizing:border-box; margin-top:6px; font-size:12.5px; padding:6px 8px; border:1px solid #e5e7eb; border-radius:6px; font-family:inherit; resize:vertical; line-height:1.5; }
    .mt-goal-detail-ro { margin-top:6px; font-size:12.5px; color:#4b5563; white-space:pre-wrap; line-height:1.5; }
    .mt-goal-hint { font-weight:400; font-size:11.5px; color:#6b7280; margin-left:6px; }
    .mt-goal-card { margin:6px 10px 8px 116px; border:1px solid #bfdbfe; background:#eff6ff; border-radius:10px; padding:10px 14px; }
    .mt-goal-card-h { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:12.5px; color:#1e40af; margin-bottom:6px; }
    .mt-goal-card-h b { font-size:13.5px; color:#1B3A6B; } .mt-goal-card-h a { margin-left:auto; color:#1e40af; font-weight:700; text-decoration:underline; cursor:pointer; }
    .mt-goal-mt { margin-top:6px; }
    .mt-goal-mt-h { display:flex; gap:8px; align-items:center; font-size:12px; color:#374151; margin:4px 0; }
    .mt-goal-mt-h .d { font-weight:700; color:#1B3A6B; } .mt-goal-mt-h .t { flex:1; } .mt-goal-mt-h .p { font-weight:700; color:#2563eb; } .mt-goal-mt-h .p.ok { color:#16a34a; }
    .mt-printing .mt-goal-detail, .mt-printing .mt-goal-add, .mt-printing .mt-goal-x { display:none; }
"""

PAST_OLD = """    // r227: 지난 회의(날짜 지난 것)는 접어 두고 [지난 회의 N건 보기]로 펼친다 (검색·장소 필터 중에는 전부)
    var _pastTg='';
    if(!q && !plf){
      var _tdy=_mmToday(), _allL=list, _upL=_allL.filter(function(m){ return String(m.date||'')>=_tdy; }), _pastN=_allL.length-_upL.length;
      if(_mtShowPast){ if(_pastN) _pastTg='<div class="mt-past-tg"><a onclick="mtTogglePast()">지난 회의 접기</a></div>'; }
      else { list=_upL; if(_pastN) _pastTg='<div class="mt-past-tg"><a onclick="mtTogglePast()">지난 회의 '+_pastN+'건 보기</a></div>'; }
      if(cnt) cnt.textContent = list.length ? (list.length+'건') : '';
      if(!list.length){ host.innerHTML=_dueH+_pastTg+'<div class="mt-empty">예정된 회의가 없습니다. [+ 새 회의록] 으로 다음 회의를 잡아 주세요.</div>'; return; }
    }
"""
PAST_NEW = """    // r240: 지난 회의도 접지 않고 전부 최신순으로 보여준다 (r227 접기 제거 — 사용자 10-19 "지난 회의 부분도 없애지 말고 계속 볼 수 있게")
    var _pastTg='';
"""

OPS = [
  [PAST_OLD, PAST_NEW, 1, "PAST_LIST"],
  ["    if(_mmPastMeetingLine(l)) return false;   // r227 지난 회의 안건은 일정에서 숨김",
   "    // r240: 지난 회의 안건도 일정에 그대로 (r227 숨김 해제)", 1, "PAST_MEMO"],
  ["    h+='</div><div class=\"mt-foot\">충해전기(주) '+_mtEsc(m.place||'')+'영업소</div></div>';",
   "    h+='</div>'+_mtGoalsSecHtml(m, print)+'<div class=\"mt-foot\">충해전기(주) '+_mtEsc(m.place||'')+'영업소</div></div>';   // r240: 3. 담당자별 목표", 1, "DOC_GOALS"],
  ["    out.reports=names.map(function(n){ return rmap[n]; });",
   "    out.reports=names.map(function(n){ return rmap[n]; });\n    out.goals=_mtMergeGoals(l.goals, s.goals, dm);   // r240", 1, "MERGE_GOALS"],
  ["    try{ h+=_nbBanner(); }catch(_e){}   // r227 신규 영업 응원",
   "    try{ h+=_nbBanner(); }catch(_e){}   // r227 신규 영업 응원\n    try{ h+=_mtGoalCard(); }catch(_e){}   // r240 내 목표 카드", 1, "MEMO_CARD"],
  ["  function _mtMergeMeeting(l, s){", JS + "  function _mtMergeMeeting(l, s){", 1, "JS"],
  [".mt-rep { display:grid; grid-template-columns:110px 1fr; border:1px solid #cbd5e1; margin-top:6px; }",
   ".mt-rep { display:grid; grid-template-columns:110px 1fr; border:1px solid #cbd5e1; margin-top:6px; }" + CSS, 1, "CSS"],
  ["var mid=el.getAttribute('data-mid'); if(el.id==='mtAgIn') mtSaveAgenda(mid); else mtSaveReps(mid); } };",
   "var mid=el.getAttribute('data-mid'); if(el.id==='mtAgIn') mtSaveAgenda(mid); else if(el.id==='mtGoalIn') mtSaveGoals(mid); else mtSaveReps(mid); } };   // r240", 1, "TAKEY"],
  # r236 검증 강화: id 뿐 아니라 upd(마지막 조작 시각)도 비교 — 같은 순간 상대가 올린 사본에 내 체크/상세가 덮였으면 다시 합쳐 올린다. goals·세부 항목 포함.
  ["  function _mtIdSet(list){ var o={}; _mtArr(list).forEach(function(m){ if(!m||!m.id) return; o['m:'+m.id]=1; _mtArr(m.agenda).forEach(function(a){ if(a&&a.id) o[a.id]=1; }); _mtArr(m.reports).forEach(function(r){ _mtArr(r&&r.items).forEach(function(i){ if(i&&i.id) o[i.id]=1; }); }); }); return o; }",
   "  function _mtIdSet(list){ var o={}; var U=function(x){ return Number((x&&(x.upd||x.at))||1); }; _mtArr(list).forEach(function(m){ if(!m||!m.id) return; o['m:'+m.id]=1; _mtArr(m.agenda).forEach(function(a){ if(a&&a.id) o[a.id]=U(a); }); _mtArr(m.reports).forEach(function(r){ _mtArr(r&&r.items).forEach(function(i){ if(i&&i.id) o[i.id]=U(i); }); }); _mtArr(m.goals).forEach(function(b){ _mtArr(b&&b.items).forEach(function(g){ if(g&&g.id){ o[g.id]=U(g); _mtArr(g.subs).forEach(function(s){ if(s&&s.id) o[s.id]=U(s); }); } }); }); }); return o; }   // r240: id → upd", 1, "IDSET"],
  ["      Object.keys(mine).forEach(function(k){ if(!have[k] && !_mtDelMap[k.replace(/^m:/,'')]) miss++; });",
   "      Object.keys(mine).forEach(function(k){ if(_mtDelMap[k.replace(/^m:/,'')]) return; if(!have[k]) { miss++; return; } if(k.indexOf('m:')!==0 && Number(have[k])<Number(mine[k])) miss++; });   // r240: 서버 사본이 내 것보다 오래됐으면(덮임) 다시 합쳐 올림", 1, "VERIFY_UPD"],
  ["<!-- test build r239 2026-10-19 -->", "<!-- test build r240 2026-10-19 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R240 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r240(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r240 브라우저 적용기 — edits_r240.py 의 OPS. r239 적용본 위에 적용.",
             "function r240Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R240 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r240Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r240(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r240 applied:', path)
