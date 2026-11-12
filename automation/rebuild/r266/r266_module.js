  // ─── r266: 견적 → 대성산업(WMIS) 발주 — Cloudflare Worker(wmis/worker.js) 중계 ───
  //  견적 줄 → [대성 발주] → Worker /lookup 으로 대성 상품코드·대리점가·재고 확인 → 배송지(직원 지점: 서울/화성) → 확인 후 /order 저장
  //  Worker 주소·열쇠 = Firebase <_AUTH_BASE>/sched_ds_cfg {url,key} (관리자가 [대성 설정]에서 입력). 대성 아이디·비밀번호는 Worker 비밀에만.
  var _dsCfg=null, _ds=null;
  async function _dsLoadCfg(force){
    if(_dsCfg && !force) return _dsCfg;
    for(var _t=0;_t<2;_t++){
      try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_ds_cfg.json'); if(r&&r.ok){ _dsCfg=(await r.json())||{}; return _dsCfg; } }catch(_e){}
      await new Promise(function(res){ setTimeout(res,700); });
    }
    _dsCfg=null; return {_loadErr:true};
  }
  async function _dsCall(path, body){
    var cfg=await _dsLoadCfg();
    if(!cfg||!cfg.url||!cfg.key) throw new Error('대성 설정 필요 — 관리자가 [대성 설정]에서 Worker 주소와 열쇠를 넣어야 합니다');
    var r=await fetch(String(cfg.url).replace(/\/+$/,'')+path, body?{method:'POST', headers:{'Content-Type':'application/json','X-Wmis-Key':cfg.key}, body:JSON.stringify(body)}:{headers:{'X-Wmis-Key':cfg.key}});
    var j=null; try{ j=await r.json(); }catch(_e){}
    if(!j) throw new Error('Worker 응답 이상 (HTTP '+r.status+')');
    if(!j.ok) throw new Error(j.error||('HTTP '+r.status));
    return j;
  }
  function _dsBranch(){
    var staff=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)?_authUser.name:'';
    var me=(typeof members!=='undefined'&&members)?members.find(function(x){ return (x.name||'').trim()===staff; }):null;
    return (me&&me.group==='화성')?'화성':'서울';
  }
  // 대성 주문등록 화면의 배송 칸: 납품처(deliType) · 운송업체(deliCmpy) · 도착지(deliPlace) · 전화번호(deliTel)
  var _DS_SEOUL={ type:'충해전기', cmpy:'구로정기배송', addr:'서울특별시 구로구 구로중앙로 198, 13동 103호(구로동,공구상가B블럭)', tel:'010-5228-2922' };   // 대성 기본 배송지(2026-11-12 확인)
  function _dsDeliOf(branch, def){
    if(branch==='화성'){ var S=_qSupplierInfo('화성'); return { branch:'화성', type:'충해전기 화성영업소', cmpy:'택배', addr:String(S.addr||'').replace(/\s*\n\s*/g,' '), tel:S.tel }; }
    var D=(def&&def.deliPlace)?{type:def.deliType||'', cmpy:def.deliCmpy||'', addr:def.deliPlace||'', tel:def.deliTel||''}:_DS_SEOUL;
    return { branch:'서울', type:D.type, cmpy:D.cmpy, addr:D.addr, tel:D.tel };
  }
  function _dsFmt(n){ return (n==null||n==='')?'':Number(n).toLocaleString('ko-KR'); }
  function _dsTomorrow(){ var d=new Date(Date.now()+86400000); if(d.getDay()===6) d=new Date(d.getTime()+2*86400000); else if(d.getDay()===0) d=new Date(d.getTime()+86400000); return d.toISOString().slice(0,10); }
  window.qDsOpen=async function(){
    var lines=(_qCart||[]).map(function(c,i){ return {i:i, pn:String((c&&c.spec)||'').trim(), qty:Math.max(1,Number(c&&c.qty)||1), alt:!!(c&&c.altOff)}; }).filter(function(x){ return x.pn && !x.alt; });
    if(!lines.length){ showInfoModal('대성 발주','견적 목록에 품번이 없습니다.'); return; }
    var br=_dsBranch();
    _ds={ lines:lines.map(function(x){ return {pn:x.pn, qty:x.qty, on:true, st:'wait'}; }), deli:_dsDeliOf(br), deliDate:_dsTomorrow(),
      remk:'충해전기 '+((typeof _qQuoteNo!=='undefined'&&_qQuoteNo)?_qQuoteNo+' ':'')+(((_qCart[0]||{}).vname)?'/ '+_qCart[0].vname:''), busy:false, msg:'' };
    _dsRender(); _dsLookup();
  };
  async function _dsLookup(){
    if(!_ds) return; _ds.busy=true; _ds.msg='대성에서 품번 확인 중…'; _dsRender();
    try{
      var j=await _dsCall('/lookup', {items:_ds.lines.map(function(l){ return {pn:l.pn, qty:l.qty}; })});
      (j.items||[]).forEach(function(it, k){ var l=_ds.lines[k]; if(!l) return;
        if(it.found){ l.st='ok'; l.code=it.code; l.name=it.name||''; l.price=it.price; l.stock=it.stock||null; }
        else { l.st='none'; l.on=false; l.cands=it.cands||[]; } });
      if(j.deliv&&j.deliv.deliPlace){ _ds.def=j.deliv; if(_ds.deli.branch==='서울'&&!_ds.deliEdited) _ds.deli=_dsDeliOf('서울', j.deliv); }
      var nf=_ds.lines.filter(function(l){ return l.st==='none'; }).length;
      _ds.msg=nf?('<span style="color:#b45309">대성에서 못 찾은 품번 '+nf+'개는 빼고 발주합니다.</span>'):'<span style="color:#15803d">모든 품번을 대성에서 찾았습니다.</span>';
    }catch(e){ _ds.msg='<span style="color:#dc2626">'+esc(e.message||String(e))+'</span>'; _ds.lines.forEach(function(l){ if(l.st==='wait') l.st='err'; }); }
    _ds.busy=false; _dsRender();
  }
  function _dsStockTxt(s){ if(!s) return ''; return Object.keys(s).filter(function(k){ return s[k]!=null&&s[k]!==''; }).map(function(k){ return esc(k)+' '+esc(String(s[k])); }).join(' · '); }
  function _dsRender(){
    if(!_ds) return; var d=_ds; var I='box-sizing:border-box;padding:7px 9px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:12.5px;font-family:inherit';
    var sum=0, cnt=0; d.lines.forEach(function(l){ if(l.on&&l.st==='ok'){ cnt++; sum+=(Number(l.price)||0)*l.qty; } });
    var rows=d.lines.map(function(l,k){
      var st=l.st==='ok'?'<span style="color:#15803d">✔ '+esc(l.code||'')+'</span>':l.st==='none'?'<span style="color:#dc2626">대성에 없음</span>'+((l.cands&&l.cands.length)?'<div style="font-size:10.5px;color:#6b7280">비슷한 품번: '+l.cands.slice(0,3).map(function(c){ return '<a href="javascript:;" onclick="dsPickCand('+k+',\''+_qa(c.code)+'\')" style="color:#1B3A6B">'+esc(c.pn||c.code)+'</a>'; }).join(', ')+'</div>':''):l.st==='err'?'<span style="color:#dc2626">확인 실패</span>':'<span style="color:#9ca3af">확인 중…</span>';
      return '<tr style="border-top:1px solid #eef2f7'+(l.on?'':';opacity:.55')+'">'
        +'<td style="padding:6px 4px;text-align:center"><input type="checkbox" '+(l.on?'checked':'')+(l.st==='ok'?'':' disabled')+' onchange="dsToggle('+k+',this.checked)"></td>'
        +'<td style="padding:6px 6px;font-weight:700;color:#14305c">'+esc(l.pn)+(l.name?'<div style="font-size:10.5px;font-weight:400;color:#6b7280">'+esc(l.name)+'</div>':'')+'</td>'
        +'<td style="padding:6px 4px"><input type="number" min="1" value="'+l.qty+'" onchange="dsQty('+k+',this.value)" style="'+I+';width:64px;text-align:right"></td>'
        +'<td style="padding:6px 6px;text-align:right">'+_dsFmt(l.price)+'</td>'
        +'<td style="padding:6px 6px;font-size:11px;color:#374151">'+_dsStockTxt(l.stock)+'</td>'
        +'<td style="padding:6px 6px;font-size:11.5px">'+st+'</td></tr>';
    }).join('');
    var html='<div style="padding:15px 20px;border-bottom:2px solid #c2410c;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#c2410c">대성산업 발주 <span style="font-size:12px;font-weight:400;color:#6b7280">WMIS · SMC</span></span>'
      +'<span>'+(_isAdmin()?'<button class="btn" onclick="dsOpenCfg()" style="margin-right:6px">대성 설정</button>':'')+'<button class="btn" onclick="document.getElementById(\'dsOverlay\').style.display=\'none\'">닫기</button></span></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:12px">'
      +'<div style="overflow:auto;border:1px solid #e5eaf1;border-radius:9px"><table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f6f8fb;color:#14305c;font-size:11.5px"><th style="padding:7px 4px;width:30px"></th><th style="padding:7px 6px;text-align:left">품번</th><th style="padding:7px 4px;text-align:left">수량</th><th style="padding:7px 6px;text-align:right">대리점가</th><th style="padding:7px 6px;text-align:left">재고</th><th style="padding:7px 6px;text-align:left">대성 코드</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
      +'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px">'
      +'<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">배송지 <span style="font-weight:400;color:#6b7280">(지점)</span></div><div style="display:flex;gap:6px">'
        +['서울','화성'].map(function(b){ return '<button class="btn" onclick="dsBranch(\''+b+'\')" style="flex:1;'+(d.deli.branch===b?'background:#c2410c;color:#fff;border-color:#c2410c':'')+'">'+b+'</button>'; }).join('')+'</div></div>'
      +'<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">납품요청일</div><input type="date" id="dsDate" value="'+esc(d.deliDate)+'" onchange="_ds.deliDate=this.value" style="'+I+';width:100%"></div>'
      +'</div>'
      +'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 10px">'
        +[['type','납품처','dsType'],['cmpy','운송업체','dsCmpy'],['tel','전화번호','dsTel']].map(function(f){ return '<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">'+f[1]+(f[0]==='cmpy'&&d.deli.branch==='화성'?' <span style="font-weight:400;color:#b45309">(화성 — 확인 필요)</span>':'')+'</div><input id="'+f[2]+'" value="'+esc(d.deli[f[0]]||'')+'" onchange="dsDeli(\''+f[0]+'\',this.value)" style="'+I+';width:100%"></div>'; }).join('')
      +'</div>'
      +'<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">도착지</div><input id="dsAddr" value="'+esc(d.deli.addr)+'" onchange="dsDeli(\'addr\',this.value)" style="'+I+';width:100%"></div>'
      +'<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">기타요청사항</div><input id="dsRemk" value="'+esc(d.remk)+'" onchange="_ds.remk=this.value" style="'+I+';width:100%"></div>'
      +'<div id="dsMsg" style="font-size:12px;min-height:18px">'+(d.msg||'')+'</div>'
      +'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap"><span style="font-size:13px;color:#14305c">발주 <b>'+cnt+'</b>품목 · 대리점가 합계 <b>'+_dsFmt(sum)+'</b>원 <span style="font-size:11px;color:#6b7280">(부가세 별도)</span></span>'
      +'<span><button class="btn" onclick="_dsLookup()" '+(d.busy?'disabled':'')+'>다시 확인</button> <button class="btn btn-primary" id="dsGo" onclick="dsSubmit()" style="background:#c2410c;border-color:#c2410c" '+((d.busy||!cnt||d.done)?'disabled':'')+'>'+(d.done?'발주 완료':'대성에 발주')+'</button></span></div>'
      +'</div>';
    _mailOverlay('dsOverlay', html, 860);
  }
  window._dsLookup=_dsLookup;
  window.dsToggle=function(k,v){ if(_ds&&_ds.lines[k]){ _ds.lines[k].on=!!v; _dsRender(); } };
  window.dsQty=function(k,v){ if(_ds&&_ds.lines[k]){ _ds.lines[k].qty=Math.max(1,parseInt(v,10)||1); _dsRender(); } };
  window.dsBranch=function(b){ if(!_ds) return; _ds.deli=_dsDeliOf(b, _ds.def); _ds.deliEdited=false; _dsRender(); };
  window.dsDeli=function(k,v){ if(!_ds) return; _ds.deli[k]=String(v||'').trim(); _ds.deliEdited=true; };
  window.dsPickCand=function(k,code){ if(!_ds||!_ds.lines[k]) return; var c=(_ds.lines[k].cands||[]).find(function(x){ return x.code===code; }); if(!c) return; var l=_ds.lines[k]; l.st='ok'; l.on=true; l.code=c.code; l.name=c.name||''; l.price=c.price; l.stock=c.stock||null; l.pnUsed=c.pn||''; _dsRender(); };
  window.dsSubmit=async function(){
    if(!_ds||_ds.busy||_ds.done) return; var d=_ds;
    var items=d.lines.filter(function(l){ return l.on&&l.st==='ok'; }).map(function(l){ return {code:l.code, qty:l.qty, pn:l.pn}; });
    if(!items.length) return;
    if(!d.deli.addr||!d.deli.tel){ d.msg='<span style="color:#dc2626">배송지 주소와 연락처를 넣어 주세요.</span>'; _dsRender(); return; }
    var sum=0; d.lines.forEach(function(l){ if(l.on&&l.st==='ok') sum+=(Number(l.price)||0)*l.qty; });
    if(!confirm('대성산업에 발주합니다. 저장하면 바로 대성에 접수됩니다.\n\n'+items.length+'품목 · 대리점가 합계 '+_dsFmt(sum)+'원 (부가세 별도)\n납품처: '+d.deli.type+' / '+d.deli.cmpy+'\n도착지: '+d.deli.addr+'\n납품요청일: '+d.deliDate+'\n\n발주할까요?')) return;
    d.busy=true; d.msg='대성에 저장 중…'; _dsRender();
    try{
      var j=await _dsCall('/order', {deli:{type:d.deli.type, cmpy:d.deli.cmpy, addr:d.deli.addr, tel:d.deli.tel}, deliDate:d.deliDate, remk:d.remk, items:items});
      try{ if(_qCartHasContent() && typeof _qPersistQuote==='function') await _qPersistQuote(); }catch(_e){}
      _dsLog(j.orderNo||'', items, sum, d.deli.branch);
      d.done=true; d.msg='<span style="color:#15803d;font-weight:700">대성에 저장했습니다'+(j.orderNo?' — 주문번호 '+esc(j.orderNo):'')+'.</span> <span style="color:#6b7280">대성 사이트 주문현황에서 확인할 수 있습니다.</span>';
      try{ _mtToast('대성 발주 저장 완료'+(j.orderNo?' · '+j.orderNo:'')); }catch(_e2){}
    }catch(e){ d.msg='<span style="color:#dc2626">발주 실패: '+esc(e.message||String(e))+'</span>'; }
    d.busy=false; _dsRender();
  };
  function _dsLog(no, items, sum, branch){
    var who=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)||'';
    var q=(_qLoadedId?quoteSaved.find(function(x){ return x.id===_qLoadedId; }):null)||(_qQuoteNo?quoteSaved.find(function(x){ return x.title===_qQuoteNo; }):null);
    if(!q) return;
    q.dsOrders=(q.dsOrders||[]).concat([{at:Date.now(), no:no, by:who, branch:branch, n:items.length, sum:sum, items:items.map(function(x){ return x.pn+'×'+x.qty; })}]);
    saveAll();
  }
  window.dsOpenCfg=async function(){
    if(!_isAdmin()){ showInfoModal('권한','대성 설정은 관리자만 할 수 있습니다.'); return; }
    var cfg=await _dsLoadCfg(true);
    if(cfg._loadErr){ showInfoModal('대성 설정','저장된 설정을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'); return; }
    var I='width:100%;box-sizing:border-box;padding:8px 10px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:13px;font-family:inherit';
    _mailOverlay('dsCfgOverlay',
      '<div style="padding:15px 20px;border-bottom:2px solid #c2410c;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#c2410c">대성 설정</span><button class="btn" onclick="document.getElementById(\'dsCfgOverlay\').style.display=\'none\'">닫기</button></div>'
      +'<div style="padding:16px 20px;display:flex;flex-direction:column;gap:12px">'
      +'<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:9px;padding:10px 13px;font-size:11.5px;color:#374151;line-height:1.8">대성 WMIS 로그인은 <b>Cloudflare Worker</b>(wmis/worker.js)가 합니다. 대성 아이디·비밀번호는 Worker 의 보안 비밀(WMIS_ID · WMIS_PW)에만 넣고, 여기에는 Worker 주소와 열쇠(WMIS_KEY)만 넣습니다.</div>'
      +'<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">Worker 주소</div><input id="dsCfgUrl" placeholder="https://chjk-daesung.xxxx.workers.dev" value="'+esc(cfg.url||'')+'" style="'+I+'"></div>'
      +'<div><div style="font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px">열쇠 (WMIS_KEY)</div><input id="dsCfgKey" type="password" value="'+esc(cfg.key||'')+'" style="'+I+'"></div>'
      +'<div id="dsCfgMsg" style="font-size:12px;color:#6b7280;min-height:18px"></div>'
      +'<div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn" onclick="dsCfgPing()">연결 확인</button><button class="btn btn-primary" onclick="dsCfgSave()">저장</button></div></div>', 520);
  };
  window.dsCfgPing=async function(){
    var m=document.getElementById('dsCfgMsg'); var url=(document.getElementById('dsCfgUrl').value||'').trim(), key=(document.getElementById('dsCfgKey').value||'').trim();
    if(!url||!key){ m.textContent='주소와 열쇠를 넣으세요.'; return; }
    m.textContent='대성에 로그인해 보는 중…';
    try{ var r=await fetch(url.replace(/\/+$/,'')+'/ping',{headers:{'X-Wmis-Key':key}}); var j=await r.json();
      m.innerHTML=j.ok?('<span style="color:#15803d">연결됨</span> · 계정 '+esc(j.user||'')+(j.cust?' · '+esc(j.cust):'')):('<span style="color:#dc2626">'+esc(j.error||'실패')+'</span>'); }
    catch(e){ m.innerHTML='<span style="color:#dc2626">연결 실패: '+esc(e.message||String(e))+'</span>'; }
  };
  window.dsCfgSave=async function(){
    var m=document.getElementById('dsCfgMsg');
    var obj={ url:(document.getElementById('dsCfgUrl').value||'').trim(), key:(document.getElementById('dsCfgKey').value||'').trim() };
    if(!/^https:\/\//.test(obj.url)){ m.textContent='Worker 주소는 https:// 로 시작해야 합니다.'; return; }
    try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_ds_cfg.json',{method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(obj)});
      if(!r||!r.ok) throw new Error('저장 실패 (HTTP '+(r?r.status:'네트워크')+')'); _dsCfg=obj; m.innerHTML='<span style="color:#15803d">저장했습니다.</span>'; }
    catch(e){ m.innerHTML='<span style="color:#dc2626">'+esc(e.message||String(e))+'</span>'; }
  };
