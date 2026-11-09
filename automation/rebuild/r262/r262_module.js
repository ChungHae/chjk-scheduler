
  // ─── r262: 규격 옵션 설명(마우스 올리면 간단히 · 우클릭 → 옵션 보기) + 변경 제안(대체 품번) ───
  function _qa(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
  function _qOptD(){ if(typeof optDict==='undefined'||!optDict||typeof optDict!=='object') window.optDict={series:{},tok:{}}; if(!optDict.series) optDict.series={}; if(!optDict.tok) optDict.tok={}; return optDict; }
  var _QOPT_SEED={ tok:{ '*|25A':'이차전지(2차 전지) 대응 사양 — SMC 25A 시리즈' } };
  function _qOptTok(series, tok){ var d=_qOptD(), T=String(tok||'').toUpperCase(); var k1=series?(String(series).toUpperCase()+'|'+T):null;
    if(k1 && d.tok[k1]) return {text:d.tok[k1], scope:'series'}; if(d.tok['*|'+T]) return {text:d.tok['*|'+T], scope:'all'}; if(_QOPT_SEED.tok['*|'+T]) return {text:_QOPT_SEED.tok['*|'+T], scope:'seed'}; return null; }
  // 규격 → { segs:[{code, kind:'pre'|'body'|'opt', text}], series, seriesName }
  function _qOptParse(spec){ var s=String(spec||'').trim().toUpperCase(); if(!s) return null; var parts=s.split('-').filter(Boolean); var d=_qOptD(); var segs=[], series='', bodyAt=-1;
    for(var i=0;i<parts.length;i++){ if(bodyAt<0 && i<parts.length-1 && _qOptTok('',parts[i]) && /^\d{1,3}[A-Z]?$/.test(parts[i])){ segs.push({code:parts[i], kind:'pre'}); continue; } if(bodyAt<0){ bodyAt=i; segs.push({code:parts[i], kind:'body'}); continue; } segs.push({code:parts[i], kind:'opt'}); }
    var body=bodyAt>=0?parts[bodyAt]:''; var keys=Object.keys(d.series).sort(function(a,b){ return b.length-a.length; }); for(var k=0;k<keys.length;k++){ if(body.indexOf(keys[k].toUpperCase())===0){ series=keys[k].toUpperCase(); break; } }
    if(!series){ var m=body.match(/^[A-Z]+\d{0,2}[A-Z]?/); series=m?m[0]:body; }
    segs.forEach(function(g){ var t=_qOptTok(g.kind==='body'?'':series, g.code); g.text=t?t.text:''; g.scope=t?t.scope:''; });
    return { segs:segs, series:series, seriesName:d.series[series]||'' }; }
  function _qAltMem(){ if(typeof altSugg==='undefined'||!altSugg||typeof altSugg!=='object') window.altSugg={}; return altSugg; }
  function _qAltOf(spec){ var a=_qAltMem()[_qNorm(spec)]; return Array.isArray(a)?a:[]; }
  function _qSpecTitle(c){ if(!c || !String(c.spec||'').trim()) return ''; var p=_qOptParse(c.spec); var L=[String(c.spec)];
    if(c.name) L.push('품명: '+c.name); if(p && p.seriesName) L.push('시리즈: '+p.series+' — '+p.seriesName);
    if(p){ var o=p.segs.filter(function(g){ return g.kind!=='body'; }).map(function(g){ return g.code+(g.text?(' = '+g.text):' (설명 미등록)'); }); if(o.length) L.push('옵션: '+o.join(' · ')); }
    if(c.altOf) L.push('▶ 변경 제안 ('+c.altOf+' 대신)'); if(c.altOff) L.push('▶ 재고 없음 — 아래 변경 제안');
    var mem=_qAltOf(c.spec).slice(-2); mem.forEach(function(m){ L.push('이전 변경 제안: → '+m.alt+(m.reason?(' ('+m.reason+')'):'')+' · '+_qAltDate(m.at)+(m.by?(' '+m.by):'')+' — 재고 다시 확인'); });
    L.push('우클릭 → 옵션 보기 · 변경 제안'); return L.join('\n'); }
  function _qAltDate(t){ var d=new Date(t||0); return (d.getMonth()+1)+'/'+d.getDate(); }
  function _qSpecAttrs(c, i){ var t=_qSpecTitle(c); var a=' oncontextmenu="qSpecCtx(event,'+i+')"'; if(t) a+=' title="'+_qa(t)+'"'; if(c&&c.altOf) a+=' data-alt="1"'; if(c&&c.altOff) a+=' data-altoff="1"'; if(c&&!c.altOf&&!c.altOff&&_qAltOf(c.spec).length) a+=' data-althint="1"'; return a; }
  // ─ 우클릭 메뉴 ─
  window.qSpecCtx=function(ev, i){ var c=_qCart[i]; if(!c || !String(c.spec||'').trim()) return; ev.preventDefault(); ev.stopPropagation();
    var m=document.getElementById('qSpecMenu'); if(!m){ m=document.createElement('div'); m.id='qSpecMenu'; m.className='qsm'; document.body.appendChild(m); document.addEventListener('mousedown', function(e){ if(m.style.display!=='none' && !m.contains(e.target)) m.style.display='none'; }); document.addEventListener('keydown', function(e){ if(e.key==='Escape') m.style.display='none'; }); }
    var mem=_qAltOf(c.spec).slice(-1)[0];
    var it=function(fn,label,sub){ return '<div class="qsm-it" onclick="document.getElementById(\'qSpecMenu\').style.display=\'none\'; '+fn+'"><b>'+label+'</b>'+(sub?'<span>'+sub+'</span>':'')+'</div>'; };
    var h='<div class="qsm-h">'+esc(c.spec)+'</div>'+it('qOptView('+i+')','옵션 보기','시리즈·옵션 코드 설명');
    if(c.altOff) h+=it('qAltCancel('+i+')','변경 제안 취소','원래 품번으로 되돌리기');
    else if(!c.altOf){ h+=it('qAltOpen('+i+')','변경 제안 넣기','재고 없음 등 → 대체 품번 줄 추가'); if(mem) h+=it('qAltOpen('+i+',true)','이전 제안 다시 쓰기','→ '+_qa(mem.alt)+(mem.reason?(' · '+_qa(mem.reason)):'')); }
    h+=it('qAltListOpen()','변경 제안 목록','여러 개 한 번에 등록 · 이력');
    m.innerHTML=h; m.style.display='block'; var x=ev.clientX, y=ev.clientY; m.style.left=Math.min(x, window.innerWidth-260)+'px'; m.style.top=Math.min(y, window.innerHeight-m.offsetHeight-10)+'px'; };
  // ─ 옵션 보기 ─
  window.qOptView=function(i){ var c=_qCart[i]; if(!c) return; var p=_qOptParse(c.spec); if(!p) return; window._qovSpec=c.spec;
    var ro=(typeof _isViewer==='function'&&_isViewer());
    var rows=p.segs.map(function(g,gi){ var lab=g.kind==='body'?'본체(시리즈)':(g.kind==='pre'?'앞 사양':'옵션'); var val=g.kind==='body'?p.seriesName:g.text;
      return '<tr><td style="color:#6b7280;white-space:nowrap">'+lab+'</td><td style="font-weight:700;white-space:nowrap">'+esc(g.code)+'</td><td><input class="qov-in" data-kind="'+g.kind+'" data-code="'+_qa(g.code)+'" value="'+_qa(val||'')+'" placeholder="'+(g.kind==='body'?'시리즈 이름 (예: 디지털 플로우 스위치)':'이 코드의 뜻 (카탈로그 How to order 참고)')+'"'+(ro?' readonly':'')+'>'+(g.scope==='seed'?'<span class="qov-tag">기본</span>':(g.scope==='all'?'<span class="qov-tag">공통</span>':''))+'</td></tr>'; }).join('');
    var mem=_qAltOf(c.spec);
    var q=encodeURIComponent('SMC '+p.series+' How to order 카탈로그');
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">옵션 보기 <span style="font-size:13px;color:#334155;margin-left:6px">'+esc(c.spec)+'</span></span><button class="btn" onclick="document.getElementById(\'qOptOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:12px;font-size:13px">'
      +(c.name?'<div style="color:#374151">품명: <b>'+esc(c.name)+'</b></div>':'')
      +'<table class="qov-tbl"><thead><tr><th>구분</th><th>코드</th><th>설명 <span style="font-weight:400;color:#9ca3af">— 한 번 적어 두면 모두에게 보이고, 같은 시리즈의 다른 품번에도 나옵니다</span></th></tr></thead><tbody>'+rows+'</tbody></table>'
      +'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><a class="btn" href="https://www.google.com/search?q='+q+'" target="_blank" rel="noopener" style="padding:5px 10px;text-decoration:none">SMC 카탈로그 찾기 ↗</a>'
      +(p.segs.some(function(g){ return g.code==='25A'; })?'<a class="btn" href="https://smcworld.com/products/subject/en-jp/25a/25aSeries/fuzoku.html" target="_blank" rel="noopener" style="padding:5px 10px;text-decoration:none">25A 시리즈 안내 ↗</a>':'')
      +'<span style="flex:1"></span>'+(ro?'':'<button class="btn" onclick="qOptSave()" style="padding:6px 16px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">설명 저장</button>')+'</div>'
      +(mem.length?('<div><div style="'+_MLL+'">이 품번의 변경 제안 이력 <span style="font-weight:400;color:#9ca3af">— 재고는 수시로 바뀌니 다시 확인하세요</span></div>'+mem.slice().reverse().map(function(m){ return '<div style="font-size:12.5px;padding:3px 0">→ <b>'+esc(m.alt)+'</b> '+(m.reason?('· '+esc(m.reason)+' '):'')+'<span style="color:#9ca3af">· '+_qAltDate(m.at)+' '+esc(m.by||'')+'</span></div>'; }).join('')+'</div>'):'')
      +'</div>';
    _mailOverlay('qOptOverlay', h, 680); };
  window.qOptSave=function(){ if(typeof _guardW==='function' && !_guardW()) return; var p=_qOptParse(window._qovSpec); if(!p) return; var d=_qOptD(); var n=0;
    document.querySelectorAll('#qOptOverlay .qov-in').forEach(function(inp){ var v=String(inp.value||'').trim(), code=inp.getAttribute('data-code'), kind=inp.getAttribute('data-kind');
      if(kind==='body'){ if(v){ if(d.series[p.series]!==v){ d.series[p.series]=v; n++; } } else if(d.series[p.series]){ delete d.series[p.series]; n++; } return; }
      var key=(kind==='pre'?'*':p.series)+'|'+code; var seed=_QOPT_SEED.tok['*|'+code];
      if(v && v!==seed){ if(d.tok[key]!==v){ d.tok[key]=v; n++; } } else if(!v && d.tok[key]){ delete d.tok[key]; n++; } });
    if(n){ saveAll(); try{ _mtToast('옵션 설명 '+n+'건 저장'); }catch(_e){} renderQCart(); }
    document.getElementById('qOptOverlay').style.display='none'; };
  // ─ 변경 제안 ─
  var _QALT_REASONS=['재고 없음 · 일본 재고','재고 없음 · 납기 단축','단종 · 후속 품번','사양 변경(동등품)'];
  window.qAltOpen=function(i, reuse){ if(typeof _guardW==='function' && !_guardW()) return; var c=_qCart[i]; if(!c) return; var mem=_qAltOf(c.spec).slice(-1)[0]; var pre=(reuse&&mem)?mem:null; window._qaltI=i;
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">변경 제안 넣기</span><button class="btn" onclick="document.getElementById(\'qAltOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:12px;font-size:13px">'
      +'<div><div style="'+_MLL+'">원래 품번</div><div style="font-weight:700;color:#14305c">'+esc(c.spec)+(c.name?' <span style="font-weight:400;color:#6b7280">'+esc(c.name)+'</span>':'')+' · 수량 '+(Number(c.qty)||1)+'</div></div>'
      +'<div><div style="'+_MLL+'">제안 품번 <span style="font-weight:400;color:#9ca3af">— 둘 이상이면 OR 또는 쉼표로 (첫 번째로 가격을 넣고, 나머지는 "대안" 으로 적힘)</span></div><input id="qaltTo" value="'+_qa(pre?pre.alt:'')+'" placeholder="예: VP342R-5DZ1-01A-F" style="'+_MLI+'"></div>'
      +'<div><div style="'+_MLL+'">사유</div><div style="display:flex;gap:6px;flex-wrap:wrap">'+_QALT_REASONS.map(function(r){ return '<button type="button" class="btn" onclick="document.getElementById(\'qaltWhy\').value=this.textContent" style="padding:3px 9px;font-size:11.5px">'+esc(r)+'</button>'; }).join('')+'</div><input id="qaltWhy" value="'+_qa(pre?pre.reason:_QALT_REASONS[0])+'" style="'+_MLI+';margin-top:6px"></div>'
      +'<div><div style="'+_MLL+'">제안 품번 예상납기 <span style="font-weight:400;color:#9ca3af">(선택)</span></div><input id="qaltEta" placeholder="예: 2~3주" style="'+_MLI+';width:200px"></div>'
      +'<label style="display:flex;align-items:center;gap:6px;cursor:pointer"><input type="checkbox" id="qaltOff" checked> 원래 품번 줄은 금액에서 빼고 "재고 없음 · 아래 변경 제안" 으로 표시</label>'
      +'<div style="font-size:11.5px;color:#9ca3af;line-height:1.6">견적서(PDF·엑셀·HTML·메일)에는 원래 품번 줄에 안내 문구, 바로 아래 줄에 제안 품번이 "변경 제안 · 사유" 와 함께 나갑니다. 이 표시는 이 견적에만 쓰이고 원장(단가 기록)의 단종/납기 칸은 바꾸지 않습니다.</div>'
      +'<div style="display:flex;justify-content:flex-end;gap:8px;border-top:1px solid #eef1f4;padding-top:10px"><button class="btn" onclick="document.getElementById(\'qAltOverlay\').style.display=\'none\'" style="padding:7px 14px">취소</button><button class="btn" onclick="qAltApply()" style="padding:7px 18px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">넣기</button></div>'
      +'</div>';
    _mailOverlay('qAltOverlay', h, 560); setTimeout(function(){ var t=document.getElementById('qaltTo'); if(t) t.focus(); },30); };
  function _qAltSplit(s){ return String(s||'').split(/\s+OR\s+|\s*,\s*|\s*\/\s*|\s*\|\s*/i).map(function(x){ return x.replace(/변경\s*제안/g,'').trim(); }).filter(Boolean); }
  function _qAltRemember(orig, alt, reason){ var mm=_qAltMem(); var k=_qNorm(orig); if(!k) return; var arr=Array.isArray(mm[k])?mm[k]:[]; var who=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)||''; arr=arr.filter(function(x){ return _qNorm(x.alt)!==_qNorm(alt); }); arr.push({orig:orig, alt:alt, reason:reason||'', by:who, at:Date.now()}); mm[k]=arr.slice(-5); }
  window.qAltApply=function(){ var i=window._qaltI; var c=_qCart[i]; if(!c) return; var alts=_qAltSplit((document.getElementById('qaltTo')||{}).value); if(!alts.length){ document.getElementById('qaltTo').focus(); return; }
    var why=String((document.getElementById('qaltWhy')||{}).value||'').trim(), eta=String((document.getElementById('qaltEta')||{}).value||'').trim(), off=!!(document.getElementById('qaltOff')||{}).checked;
    try{ _qPushUndo(); }catch(_e){}
    if(_qNorm(alts[0])===_qNorm(c.spec)){ showInfoModal('변경 제안','제안 품번이 원래 품번과 같습니다. 다른 품번을 넣어 주세요.'); return; }
    if(off){ c.altOff=true; c.disc='재고 없음 · 아래 변경 제안'; c.altDiscPrev=(c.altDiscPrev!==undefined)?c.altDiscPrev:''; }
    var nr={ vid:c.vid, vname:c.vname, spec:alts[0], name:'', e:null, buy:null, small:null, pl:false, sell:null, disc:'', eta:'', qty:c.qty||1, manual:true, altOf:c.spec };
    _qCart.splice(i+1, 0, nr);
    try{ _qgObk=null; _qgFillFromLedger(i+1); }catch(_e2){}
    nr.eta='변경 제안'+(why?(' · '+why):'')+(eta?(' · 납기 '+eta):'')+(alts.length>1?(' · 대안: '+alts.slice(1).join(', ')):'');
    nr.altOf=c.spec;
    _qAltRemember(c.spec, alts.join(' OR '), why); saveAll();
    _qCartSave(); renderQCart(); document.getElementById('qAltOverlay').style.display='none';
    try{ _mtToast(c.spec+' → '+alts[0]+' 변경 제안 줄을 넣었습니다'+(nr.sell==null?' · 판매가를 넣어 주세요':'')); }catch(_e3){} };
  window.qAltCancel=function(i){ var c=_qCart[i]; if(!c||!c.altOff) return; try{ _qPushUndo(); }catch(_e){} c.altOff=false; delete c.altOff; c.disc=''; var j=i+1; while(j<_qCart.length && _qCart[j] && _qCart[j].altOf && _qNorm(_qCart[j].altOf)===_qNorm(c.spec)){ _qCart.splice(j,1); } _qCartSave(); renderQCart(); };
  // ─ 변경 제안 목록 (여러 줄 한 번에 등록) ─
  window.qAltListOpen=function(){ var mm=_qAltMem(); var all=[]; Object.keys(mm).forEach(function(k){ (mm[k]||[]).forEach(function(x){ all.push(x); }); }); all.sort(function(a,b){ return (b.at||0)-(a.at||0); });
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">변경 제안 목록</span><button class="btn" onclick="document.getElementById(\'qAltListOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:10px;font-size:13px">'
      +'<div style="'+_MLL+'">여러 개 붙여넣어 등록 <span style="font-weight:400;color:#9ca3af">— 한 줄에 "원래 품번 → 제안 품번" (OR 로 여러 개) · 견적에 넣을 때 그 품번에 마우스를 올리면 이력이 보이고, 우클릭 [이전 제안 다시 쓰기] 로 바로 넣습니다</span></div>'
      +'<textarea id="qaltBulk" style="'+_MLI+';min-height:120px;font-family:Consolas,monospace;font-size:12.5px" placeholder="VP342R-5DZ1-01B → VP342R-5DZ1-01A-F 변경 제안&#10;SRH3011-02 → SRH3011-02-R OR SRH4011-02"></textarea>'
      +'<div style="display:flex;gap:8px;align-items:center"><span style="'+_MLL+';margin:0">사유</span><input id="qaltBulkWhy" value="재고 없음 · 일본 재고" style="'+_MLI+';width:220px"><span style="flex:1"></span><button class="btn" onclick="qAltBulkSave()" style="padding:6px 16px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">등록</button></div>'
      +'<div id="qaltBulkMsg" style="font-size:12px;color:#6b7280"></div>'
      +'<div style="'+_MLL+';margin-top:6px">등록된 제안 '+all.length+'건</div><div style="max-height:260px;overflow:auto;border:1px solid #eef1f4;border-radius:8px">'
      +(all.length?all.map(function(x){ return '<div style="display:flex;gap:8px;align-items:center;padding:5px 10px;border-bottom:1px solid #f1f5f9;font-size:12.5px"><b>'+esc(x.orig)+'</b> → <span style="color:#b45309;font-weight:700">'+esc(x.alt)+'</span><span style="color:#6b7280">'+esc(x.reason||'')+'</span><span style="margin-left:auto;color:#9ca3af">'+_qAltDate(x.at)+' '+esc(x.by||'')+'</span><a style="color:#cbd5e1;cursor:pointer" title="지우기" onclick="qAltDel(\''+_qa(_qNorm(x.orig))+'\',\''+_qa(x.alt)+'\')">✕</a></div>'; }).join(''):'<div style="padding:16px;text-align:center;color:#9ca3af">아직 없습니다.</div>')
      +'</div></div>';
    _mailOverlay('qAltListOverlay', h, 720); };
  window.qAltBulkSave=function(){ if(typeof _guardW==='function' && !_guardW()) return; var txt=String((document.getElementById('qaltBulk')||{}).value||''); var why=String((document.getElementById('qaltBulkWhy')||{}).value||'').trim(); var ok=0, same=[], bad=[];
    txt.split(/\r?\n/).forEach(function(ln){ ln=ln.trim(); if(!ln) return; var m=ln.split(/\s*(?:→|->|=>|⇒)\s*/); if(m.length<2){ bad.push(ln); return; } var orig=m[0].trim(), alts=_qAltSplit(m.slice(1).join(' ')); if(!orig||!alts.length){ bad.push(ln); return; }
      if(alts.every(function(a){ return _qNorm(a)===_qNorm(orig); })){ same.push(orig); return; } _qAltRemember(orig, alts.filter(function(a){ return _qNorm(a)!==_qNorm(orig); }).join(' OR '), why); ok++; });
    if(ok) saveAll();
    qAltListOpen(); var msg=document.getElementById('qaltBulkMsg'); if(msg) msg.innerHTML='<b style="color:#15803d">'+ok+'건 등록</b>'+(same.length?(' · <span style="color:#b45309">원래 품번과 제안 품번이 같아 건너뜀: '+esc(same.join(', '))+'</span>'):'')+(bad.length?(' · <span style="color:#dc2626">형식 확인: '+esc(bad.join(' / '))+'</span>'):''); };
  window.qAltDel=function(k, alt){ if(typeof _guardW==='function' && !_guardW()) return; var mm=_qAltMem(); mm[k]=(mm[k]||[]).filter(function(x){ return x.alt!==alt; }); if(!mm[k].length) delete mm[k]; saveAll(); qAltListOpen(); };
  (function(){ var st=document.createElement('style'); st.textContent='.qsm{position:fixed;z-index:100100;display:none;min-width:230px;background:#fff;border:1px solid #d6e0ec;border-radius:8px;box-shadow:0 10px 30px rgba(15,23,42,.18);overflow:hidden;font-size:12.5px} .qsm-h{padding:7px 12px;background:#f8fafc;border-bottom:1px solid #eef1f4;font-weight:700;color:#14305c;font-size:12px} .qsm-it{padding:8px 12px;cursor:pointer;display:flex;flex-direction:column;gap:1px} .qsm-it:hover{background:#eaf1fb} .qsm-it span{color:#6b7280;font-size:11px} .qov-tbl{width:100%;border-collapse:collapse} .qov-tbl th{text-align:left;font-size:11.5px;color:#6b7280;font-weight:600;padding:4px 6px;border-bottom:1px solid #e5e7eb} .qov-tbl td{padding:4px 6px;border-bottom:1px solid #f1f5f9;vertical-align:middle} .qov-in{width:calc(100% - 44px);box-sizing:border-box;padding:5px 8px;border:1px solid #d6e0ec;border-radius:6px;font-size:12.5px;font-family:inherit} .qov-tag{display:inline-block;margin-left:4px;font-size:10px;color:#0f766e;background:#ccfbf1;border-radius:6px;padding:1px 5px} input.qc-in[data-alt="1"]{background:#fffbeb;box-shadow:inset 3px 0 0 #f59e0b} input.qc-in[data-altoff="1"]{color:#9ca3af;text-decoration:line-through} input.qc-in[data-althint="1"]{box-shadow:inset 0 -2px 0 #fdba74}'; document.head.appendChild(st); })();
