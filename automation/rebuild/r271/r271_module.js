  // ─── r271: 최근 작업한 견적 바로 찾기 — 불러오기 '최근 작업순' 정렬 + 툴바 [최근 작업] 목록 ───
  function _qWorkAt(q){ return Math.max(Number(q&&q.upd)||0, Number(q&&q.savedAt)||0); }
  function _qLoadSortMode(){ try{ return localStorage.getItem('q_load_sort')||'work'; }catch(_e){ return 'work'; } }
  window.qLoadSortSet=function(v){ try{ localStorage.setItem('q_load_sort', v); }catch(_e){} _qLoadPage=1; _qRenderLoadList(); };
  function _qLoadSorted(_qd){
    var L=quoteSaved.slice();
    if(_qLoadSortMode()==='work') return L.sort(function(a,b){ return _qWorkAt(b)-_qWorkAt(a); });
    return L.sort(function(a,b){ var da=_qd(a), db=_qd(b); if(da!==db) return db<da?-1:1; return (b.savedAt||0)-(a.savedAt||0); });
  }
  function _qAgo(t){ if(!t) return ''; var s=(Date.now()-t)/1000; if(s<60) return '방금'; if(s<3600) return Math.floor(s/60)+'분 전'; if(s<86400) return Math.floor(s/3600)+'시간 전'; var d=new Date(t); var y=new Date(); y.setDate(y.getDate()-1); if(d.toDateString()===y.toDateString()) return '어제 '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); return (d.getMonth()+1)+'/'+d.getDate()+' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); }
  var _qRecentAll=false;
  window.qOpenRecent=function(ev){
    if(ev) ev.stopPropagation();
    var pop=document.getElementById('qRecentPop');
    if(pop && pop.style.display==='block'){ pop.style.display='none'; return; }
    if(!pop){ pop=document.createElement('div'); pop.id='qRecentPop'; pop.style.cssText='position:fixed;z-index:100071;background:#fff;border:1px solid #d6e0ec;border-radius:10px;box-shadow:0 12px 32px rgba(15,23,42,.18);width:420px;max-width:calc(100vw - 24px);display:none'; document.body.appendChild(pop);
      document.addEventListener('click', function(e){ var p=document.getElementById('qRecentPop'); if(p && p.style.display==='block' && !p.contains(e.target) && !(e.target.closest&&e.target.closest('#qRecentBtn'))) p.style.display='none'; }); }
    _qRecentRender();
    var b=document.getElementById('qRecentBtn'); var r=b?b.getBoundingClientRect():{left:20,bottom:120};
    pop.style.display='block';
    var left=Math.min(Math.max(12, r.left), window.innerWidth-pop.offsetWidth-12);
    pop.style.left=left+'px'; pop.style.top=(r.bottom+6)+'px';
  };
  window.qRecentToggle=function(v){ _qRecentAll=!!v; _qRecentRender(); };
  window.qRecentLoad=function(id){ var p=document.getElementById('qRecentPop'); if(p) p.style.display='none'; qLoadSaved(id); };
  function _qRecentRender(){
    var pop=document.getElementById('qRecentPop'); if(!pop) return;
    var me=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)?_authUser.name:'';
    var L=quoteSaved.filter(function(q){ return q && q.id && (_qRecentAll || !me || (q.savedBy||'')===me); }).sort(function(a,b){ return _qWorkAt(b)-_qWorkAt(a); }).slice(0,12);
    var tab=function(on,lab,v){ return '<button class="btn" onclick="qRecentToggle('+v+')" style="padding:3px 10px;font-size:11.5px;'+(on?'background:#1B3A6B;color:#fff;border-color:#1B3A6B':'')+'">'+lab+'</button>'; };
    pop.innerHTML='<div style="padding:9px 12px;border-bottom:1px solid #eef1f4;display:flex;align-items:center;gap:6px"><span style="font-size:13px;font-weight:700;color:#14305c;flex:1">최근 작업한 견적</span>'+tab(!_qRecentAll,'내 견적','false')+tab(_qRecentAll,'전체','true')+'</div>'
      +(L.length?L.map(function(q){
        return '<div onclick="qRecentLoad(\''+q.id+'\')" style="padding:8px 12px;border-bottom:1px solid #f3f5f8;cursor:pointer;display:flex;gap:8px;align-items:center" onmouseover="this.style.background=\'#f6f9fd\'" onmouseout="this.style.background=\'\'">'
          +'<div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:700;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+esc(q.vname||'')+(q.note?' <span style="font-weight:500;color:#1B3A6B;font-size:11.5px">· '+esc(q.note)+'</span>':'')+'</div>'
          +'<div style="font-size:11px;color:#9ca3af">'+esc(q.title||'')+' · '+(q.count||0)+'건'+(_qRecentAll&&q.savedBy?' · '+esc(q.savedBy):'')+'</div></div>'
          +'<div style="text-align:right;white-space:nowrap"><div style="font-size:12px;font-weight:700;color:#334155">'+(q.total!=null?_qFmt(q.total-(q.nego||0)):'-')+'</div><div style="font-size:10.5px;color:#6b7280">'+_qAgo(_qWorkAt(q))+'</div></div></div>';
      }).join(''):'<div style="padding:22px;text-align:center;color:#9ca3af;font-size:12.5px">저장한 견적이 없습니다.</div>')
      +'<div style="padding:7px 12px;text-align:right"><a href="javascript:;" onclick="document.getElementById(\'qRecentPop\').style.display=\'none\'; qOpenLoad()" style="font-size:12px;color:#1B3A6B">전체 목록(검색) →</a></div>';
  }
