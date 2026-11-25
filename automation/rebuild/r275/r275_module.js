  // ─── r275: 회의록 쉽게 — 한 칸에 막 적고 저장 → 줄마다 이름만 눌러 담당 지정 ───
  (function(){ try{ var st=document.createElement('style'); st.textContent='.mt-who{display:inline-flex;gap:4px;flex-wrap:wrap;align-items:center;flex-shrink:0;margin-left:6px}.mt-who button{border:1px solid #cbd5e1;background:#fff;border-radius:12px;padding:1px 8px;font-size:11.5px;cursor:pointer;font-family:inherit;color:#1B3A6B;font-weight:600;line-height:1.5}.mt-who button:hover{background:#1B3A6B;color:#fff;border-color:#1B3A6B}.mt-who select{border:1px solid #cbd5e1;border-radius:12px;padding:1px 4px;font-size:11.5px;font-family:inherit;color:#475569;background:#fff;max-width:92px}.mt-who .lb{font-size:11px;color:#9ca3af}.mt-quick textarea{min-height:120px;font-size:14px}.mt-more{margin-top:14px}.mt-more>summary{cursor:pointer;font-size:12.5px;color:#6b7280;padding:6px 2px}@media print{.mt-who{display:none}}'; document.head.appendChild(st); }catch(_e){} })();
  function _mtAllNames(m){ var a=(m.attendees||[]).slice(); (members||[]).forEach(function(x){ if(x&&x.name&&a.indexOf(x.name)<0) a.push(x.name); }); return a; }
  function _mtWhoHtml(m, it, isAgenda){
    var att=(m.attendees||[]).slice(), all=_mtAllNames(m), rest=all.filter(function(n){ return att.indexOf(n)<0; });
    var q=function(n){ return _mtEsc(n).replace(/'/g,'&#39;'); };
    if(isAgenda){
      return '<span class="mt-who"><span class="lb">담당</span>'+att.map(function(n){ return '<button type="button" onclick="mtAssign(\''+m.id+'\',\''+it.id+'\',\''+q(n)+'\')" title="'+q(n)+' 담당으로 — 그 사람 일정에도 올라갑니다">'+_mtEsc(n)+'</button>'; }).join('')
        +(rest.length?('<select onchange="if(this.value) mtAssign(\''+m.id+'\',\''+it.id+'\',this.value)"><option value="">'+(att.length?'다른 사람':'담당 선택')+'</option>'+rest.map(function(n){ return '<option>'+_mtEsc(n)+'</option>'; }).join('')+'</select>'):'')+'</span>';
    }
    var cur=''; (m.reports||[]).forEach(function(r){ if((r.items||[]).some(function(i){ return i.id===it.id; })) cur=r.name; });
    return '<span class="mt-who"><select title="담당 바꾸기" onchange="mtAssign(\''+m.id+'\',\''+it.id+'\',this.value)">'+all.map(function(n){ return '<option'+(n===cur?' selected':'')+'>'+_mtEsc(n)+'</option>'; }).join('')+'<option value="">담당 없음</option></select></span>';
  }
  function _mtPutRep(m, name, it){
    var r=(m.reports||[]).find(function(x){ return x.name===name; }); if(!r){ r={ name:name, items:[] }; m.reports=m.reports||[]; m.reports.push(r); }
    if((m.attendees||[]).indexOf(name)<0 && (members||[]).some(function(x){ return x.name===name; })){ m.attendees=m.attendees||[]; m.attendees.push(name); }
    r.items.push(it); return r;
  }
  window.mtAssign = function(mid, iid, name){
    var m=_mtFind(mid); if(!m) return; if(typeof _guardW==='function' && !_guardW()) return; if(_mtLocked(m)) return;
    name=String(name||'').trim();
    var it=(m.agenda||[]).find(function(x){ return x.id===iid; }), isAg=!!it, cur='';
    if(!it){ (m.reports||[]).forEach(function(r){ (r.items||[]).forEach(function(i){ if(i.id===iid){ it=i; cur=r.name; } }); }); }
    if(!it || name===cur){ renderMeetingPage(true); return; }
    var text=(isAg && it.title)?(it.title+': '+(it.text||'')):(it.text||'');
    var lines=[]; try{ lines=_mtMemoLinesOf(it); }catch(_e){}
    m.del=m.del||{}; m.del[iid]=Date.now();
    m.agenda=(m.agenda||[]).filter(function(x){ return x.id!==iid; });
    (m.reports||[]).forEach(function(r){ r.items=(r.items||[]).filter(function(i){ return i.id!==iid; }); });
    var ni={ id:_mtId(name?'mi':'ma'), text:text, done:!!it.done, by:it.by||_mtMe(), at:it.at||Date.now(), upd:Date.now() };
    if(it.done){ ni.doneBy=it.doneBy; ni.doneAt=it.doneAt; } if(it.from) ni.from=it.from;
    if(name){
      _mtPutRep(m, name, ni);
      if(!isAg && lines.length===1 && _mtMemberName(name)){ lines[0].owner=name; lines[0].mtRef={ mid:m.id, iid:ni.id }; ni.memoId=lines[0].id; try{ _mmSave(); }catch(_e){} }   // 담당 바꾸기: 일정 줄을 새 담당자에게 넘긴다
      else { if(lines.length){ var ids=lines.map(function(l){ return l.id; }); memoLines=(memoLines||[]).filter(function(x){ return ids.indexOf(x.id)<0 || x.done; }); try{ _mmSave(); }catch(_e){} } try{ _mtMakeMemo(m, name, ni); }catch(_e){} }
    } else {
      ni.title=''; m.agenda.push(ni);
      if(lines.length){ var ids2=lines.map(function(l){ return l.id; }); memoLines=(memoLines||[]).filter(function(x){ return ids2.indexOf(x.id)<0 || x.done; }); try{ _mmSave(); }catch(_e){} }
    }
    m.updatedAt=Date.now(); _mtSave(); renderMeetingPage(true);
    _mtToast(name?('담당: '+name+(_mtMemberName(name)?' — 일정에 올렸습니다':'')):'담당 없음으로 돌렸습니다');
  };
  window.mtSaveAgenda = function(id){
    var el=document.getElementById('mtAgIn'); if(!el) return; var lines=_mtLines(el);
    if(!lines.length){ _mtToast('적힌 내용이 없습니다.'); return; }
    var m=_mtFind(id); if(!m) return; if(typeof _guardW==='function' && !_guardW()) return; if(_mtLocked(m)) return;
    var names=_mtAllNames(m), na=0, cnt={}, nr=0, me=_mtMe();
    lines.forEach(function(t){
      t=t.replace(/^[-·•*]\s*/, '');
      var sp=_mtSplitName(t, names), s0=t.replace(/^\[\s*/, '');
      if(sp && sp.text && /^[\s\]:\uFF1A\-·]/.test(s0.slice(sp.name.length))){   // "함현식 ○○" 처럼 이름으로 시작하면 바로 그 사람 담당
        var it={ id:_mtId('mi'), text:sp.text, done:false, by:me, at:Date.now() }; _mtPutRep(m, sp.name, it); try{ _mtMakeMemo(m, sp.name, it); }catch(_e){} cnt[sp.name]=(cnt[sp.name]||0)+1; nr++; return;
      }
      m.agenda.push({ id:_mtId('ma'), title:'', text:t, done:false, by:me, at:Date.now() }); na++;
    });
    m.updatedAt=Date.now(); _mtSave(); el.value=''; try{ mtDraftKeep(el, id); }catch(_e){}
    renderMeetingPage(true);
    _mtToast((na+nr)+'줄 저장'+(na?(' — '+na+'줄은 이름을 눌러 담당을 정하세요'):'')+(nr?(' · 담당 지정 '+Object.keys(cnt).map(function(k){ return k+' '+cnt[k]; }).join(' · ')):''));
    setTimeout(function(){ var e2=document.getElementById('mtAgIn'); if(e2) e2.focus(); }, 30);
  };
