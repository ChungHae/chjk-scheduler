  // ─── r267: 발주 페이지 — 대성산업(WMIS) 발주 (r266 의 견적 화면 버튼을 발주 탭으로 옮김) ───
  //  업체명 → 그 업체 저장 견적 → [불러오기] → 품목 → Worker /lookup(대성 코드·대리점가·재고) → 배송지 → 확인 후 /order 저장
  //  Worker 주소·열쇠 = Firebase <_AUTH_BASE>/sched_ds_cfg {url,key}. 대성 아이디·비밀번호는 Worker 비밀에만.
  var _dsCfg=null, _ds=null;
  async function _dsLoadCfg(force){
    if(_dsCfg && !force) return _dsCfg;
    for(var _t=0;_t<2;_t++){
      try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_ds_cfg.json'); if(r&&r.ok){ _dsCfg=(await r.json())||{}; return _dsCfg; } }catch(_e){}
      await new Promise(function(res){ setTimeout(res,700); });
    }
    _dsCfg=null; return {_loadErr:true};
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
  function _dsStockTxt(s){ if(!s) return ''; return Object.keys(s).filter(function(k){ return s[k]!=null&&s[k]!==''; }).map(function(k){ return esc(k)+' '+esc(String(s[k])); }).join(' · '); }
  function _poYmd(t){ var d=new Date(t||0); if(!t||isNaN(d)) return ''; return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2); }
  function _poQuotes(){ return (typeof quoteSaved!=='undefined'&&Array.isArray(quoteSaved))?quoteSaved.filter(function(q){ return q&&q.id; }):[]; }
  function _poVendors(){   // 저장 견적의 업체명 — 최근 견적 순
    var seen={}, out=[];
    _poQuotes().slice().sort(function(a,b){ return (b.upd||b.savedAt||0)-(a.upd||a.savedAt||0); }).forEach(function(q){ var v=String(q.vname||'').trim(); if(v&&!seen[v]){ seen[v]=1; out.push(v); } });
    return out;
  }
  function _poA(s){ return esc(String(s==null?'':s)).replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
  function _poLS(k,def){ try{ var v=localStorage.getItem(k); if(v!=null&&v!=='') return Number(v); }catch(_e){} return def; }
  function _poDsRate(){ var v=_poLS('po_ds_rate',35); return (v>=0&&v<90)?v:35; }   // 대성 DC율 (기본 35%)
  function _poThr(){ var v=_poLS('po_dc_thr',35); return (v>=0&&v<90)?v:35; }
  function _poDc(l){ var e=Number(l.e)||Number(l.price)||0, b=Number(l.buy)||0; if(!(e>0)||!(b>0)) return null; return Math.round((1-b/e)*1000)/10; }
  function _poDsPrice(l){ var p=Number(l.price)||Number(l.e)||0; if(!(p>0)) return null; return Math.round(p*(1-_poDsRate()/100)); }
  window.poSetRate=function(v){ v=Number(v); if(!(v>=0&&v<90)) return; try{ localStorage.setItem('po_ds_rate', String(v)); }catch(_e){} renderOrderPage(); };
  window.poSetThr=function(v){ v=Number(v); if(!(v>=0&&v<90)) return; try{ localStorage.setItem('po_dc_thr', String(v)); }catch(_e){} renderOrderPage(); };
  window.poSelectThr=function(){ if(!_ds) return; var t=_poThr(); _ds.lines.forEach(function(l){ var dc=_poDc(l); l.on=(l.st==='ok' && dc!=null && dc>=t); }); renderOrderPage(); };
  window.poSelectAll=function(v){ if(!_ds) return; _ds.lines.forEach(function(l){ l.on=!!v && l.st==='ok'; }); renderOrderPage(); };
  window.dsDel=function(k){ if(!_ds||_ds.done||!_ds.lines[k]) return; _ds.lines.splice(k,1); renderOrderPage(); };
  function _poNew(){
    var br=_dsBranch();
    _ds={ vname:'', qid:'', qno:'', lines:[], deli:_dsDeliOf(br), deliDate:_dsTomorrow(), remk:'', busy:false, msg:'', done:false, def:null, deliEdited:false };
  }
  window.renderOrderPage=function(){
    var pg=document.getElementById('pageOrder'); if(!pg) return;
    if(!_ds) _poNew();
    var d=_ds, I='box-sizing:border-box;padding:7px 9px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:12.5px;font-family:inherit';
    var H='font-size:14px;font-weight:700;color:#14305c;margin:0 0 8px;display:flex;align-items:center;gap:8px';
    var CARD='background:#fff;border:1px solid #e5eaf1;border-radius:12px;padding:14px 16px;margin-bottom:14px';
    // ① 업체 + 견적
    var vlist=_poVendors();
    var q=String(d.vname||'').trim(), ql=q.toLowerCase().replace(/\s+/g,'');
    var quotes=_poQuotes().filter(function(x){ if(!ql) return true; return String(x.vname||'').toLowerCase().replace(/\s+/g,'').indexOf(ql)>=0; })
      .sort(function(a,b){ return (b.upd||b.savedAt||0)-(a.upd||a.savedAt||0); }).slice(0, ql?40:15);
    var qrows=quotes.map(function(x){
      var ds=(x.dsOrders||[]).length;
      return '<tr style="border-top:1px solid #eef2f7'+(x.id===d.qid?';background:#fff7ed':'')+'">'
        +'<td style="padding:7px 8px;white-space:nowrap">'+esc(_poYmd(x.savedAt||x.upd))+'</td>'
        +'<td style="padding:7px 8px;font-weight:700;color:#14305c">'+esc(x.title||'')+'</td>'
        +'<td style="padding:7px 8px">'+esc(x.vname||'')+'</td>'
        +'<td style="padding:7px 8px;text-align:right">'+(x.count||0)+'</td>'
        +'<td style="padding:7px 8px;text-align:right">'+_dsFmt(x.total||0)+'</td>'
        +'<td style="padding:7px 8px">'+esc(x.savedBy||'')+'</td>'
        +'<td style="padding:7px 8px">'+(ds?'<span style="font-size:11px;font-weight:700;color:#c2410c;background:#fff7ed;border:1px solid #fed7aa;border-radius:999px;padding:1px 8px" title="'+_poA((x.dsOrders||[]).map(function(o){ return _poYmd(o.at)+' '+(o.no||'')+' '+(o.n||0)+'품목'; }).join('\n'))+'">대성 발주 '+ds+'</span>':'')+'</td>'
        +'<td style="padding:5px 8px;text-align:right"><button class="btn" onclick="poLoadQuote(\''+_poA(x.id)+'\')" style="padding:4px 12px">'+(x.id===d.qid?'다시 불러오기':'불러오기')+'</button></td></tr>';
    }).join('');
    var sec1='<div style="'+CARD+'"><div style="'+H+'">① 업체 · 견적 선택</div>'
      +'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px"><span style="font-size:12.5px;font-weight:700;color:#14305c">업체명</span>'
      +'<input id="poVendor" list="poVendorList" value="'+esc(d.vname)+'" placeholder="업체명 입력 (견적을 저장한 업체)" autocomplete="off" oninput="poVendorInput(this.value)" style="'+I+';width:320px;max-width:100%">'
      +'<datalist id="poVendorList">'+vlist.slice(0,300).map(function(v){ return '<option value="'+_poA(v)+'">'; }).join('')+'</datalist>'
      +'<span style="font-size:11.5px;color:#6b7280">'+(ql?('견적 '+quotes.length+'건'):'최근 견적 15건')+'</span></div>'
      +'<div style="overflow:auto;border:1px solid #eef2f7;border-radius:9px;max-height:320px"><table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f6f8fb;color:#14305c;font-size:11.5px;position:sticky;top:0"><th style="padding:7px 8px;text-align:left">날짜</th><th style="padding:7px 8px;text-align:left">견적번호</th><th style="padding:7px 8px;text-align:left">업체</th><th style="padding:7px 8px;text-align:right">품목</th><th style="padding:7px 8px;text-align:right">공급가</th><th style="padding:7px 8px;text-align:left">작성</th><th style="padding:7px 8px;text-align:left"></th><th></th></tr></thead><tbody>'
      +(qrows||'<tr><td colspan="8" style="padding:18px;text-align:center;color:#9ca3af">'+(ql?'이 업체의 저장된 견적이 없습니다.':'저장된 견적이 없습니다.')+'</td></tr>')+'</tbody></table></div></div>';
    // ② 발주 품목
    var dsRate=_poDsRate(), thr=_poThr();
    var sum=0, sumDs=0, cnt=0; d.lines.forEach(function(l){ if(l.on&&l.st==='ok'){ cnt++; sum+=(Number(l.price)||0)*l.qty; sumDs+=(_poDsPrice(l)||0)*l.qty; } });
    var TD='padding:6px 6px;text-align:right;white-space:nowrap';
    var rows=d.lines.map(function(l,k){
      var st=l.st==='ok'?'<span style="color:#15803d">✔ '+esc(l.code||'')+'</span>'+(l.pnUsed?'<div style="font-size:10.5px;color:#6b7280">'+esc(l.pnUsed)+' 로 발주</div>':''):l.st==='none'?'<span style="color:#dc2626">대성에 없음</span>'+((l.cands&&l.cands.length)?'<div style="font-size:10.5px;color:#6b7280">비슷한 품번: '+l.cands.slice(0,3).map(function(c){ return '<a href="javascript:;" onclick="dsPickCand('+k+',\''+_poA(c.code)+'\')" style="color:#1B3A6B">'+esc(c.pn||c.code)+'</a>'; }).join(', ')+'</div>':''):l.st==='err'?'<span style="color:#9ca3af">대성 미확인</span>':'<span style="color:#9ca3af">확인 중…</span>';
      var dc=_poDc(l), dsP=_poDsPrice(l), hi=(dc!=null&&dc>=thr);
      var dcTxt=dc==null?'<span style="color:#cbd5e1">-</span>':'<span style="font-weight:700;padding:1px 7px;border-radius:999px;'+(hi?'background:#dcfce7;color:#15803d':'background:#f1f5f9;color:#64748b')+'">'+dc+'%</span>';
      var gain=(dsP!=null&&l.buy>0)?(l.buy-dsP):null;
      return '<tr style="border-top:1px solid #eef2f7'+(l.on?'':';opacity:.55')+'">'
        +'<td style="padding:6px 4px;text-align:center"><input type="checkbox" '+(l.on?'checked':'')+(l.st==='ok'?'':' disabled')+' onchange="dsToggle('+k+',this.checked)"></td>'
        +'<td style="padding:6px 6px;font-weight:700;color:#14305c">'+esc(l.pn)+(l.alt?' <span style="font-size:10.5px;font-weight:400;color:#7c3aed">변경 제안</span>':'')+(l.small?' <span style="font-size:10.5px;font-weight:400;color:#b45309">소물</span>':'')+'</td>'
        +'<td style="padding:6px 4px"><input type="number" min="1" value="'+l.qty+'" onchange="dsQty('+k+',this.value)" style="'+I+';width:64px;text-align:right"></td>'
        +'<td style="'+TD+'">'+_dsFmt(l.e)+'</td>'
        +'<td style="'+TD+'">'+_dsFmt(l.buy)+'</td>'
        +'<td style="'+TD+'">'+dcTxt+'</td>'
        +'<td style="'+TD+'">'+_dsFmt(l.sell)+'</td>'
        +'<td style="'+TD+';color:#c2410c;font-weight:700" title="대리점가 '+_dsFmt(l.price||l.e)+' × (1−'+dsRate+'%)">'+_dsFmt(dsP)+(gain!=null&&gain!==0?'<div style="font-size:10.5px;font-weight:400;color:'+(gain>0?'#15803d':'#dc2626')+'">구매가보다 '+_dsFmt(Math.abs(gain))+(gain>0?' 싸게':' 비싸게')+'</div>':'')+'</td>'
        +'<td style="padding:6px 6px;font-size:11px;color:#374151">'+_dsStockTxt(l.stock)+'</td>'
        +'<td style="padding:6px 6px;font-size:11.5px">'+st+'</td>'
        +'<td style="padding:6px 4px;text-align:center"><button class="btn po-del" onclick="dsDel('+k+')" title="이 줄 빼기" style="padding:2px 8px;color:#dc2626;border-color:#fecaca">×</button></td></tr>';
    }).join('');
    var TH='padding:7px 6px;text-align:right;white-space:nowrap';
    var tools='<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 8px;font-size:12.5px">'
      +'<span style="color:#14305c;font-weight:700">대성 DC</span><input type="number" id="poDsRate" value="'+dsRate+'" min="0" max="89" onchange="poSetRate(this.value)" style="'+I+';width:62px;text-align:right">%'
      +'<span style="width:1px;height:18px;background:#e5e7eb;margin:0 4px"></span>'
      +'<span style="color:#14305c;font-weight:700">견적 DC</span><input type="number" id="poThr" value="'+thr+'" min="0" max="89" onchange="poSetThr(this.value)" style="'+I+';width:62px;text-align:right">% 이상'
      +'<button class="btn" onclick="poSelectThr()">이상만 선택</button><button class="btn" onclick="poSelectAll(true)">전체 선택</button><button class="btn" onclick="poSelectAll(false)">선택 해제</button>'
      +'<span style="flex:1"></span><span style="font-size:11.5px;color:#6b7280">견적 DC = 1 − 구매가 ÷ E가 · 대성가 = 대리점가 × (1 − 대성 DC)</span></div>';
    var sec2='<div style="'+CARD+'"><div style="'+H+'">② 발주 품목 '+(d.qno?'<span style="font-size:12px;font-weight:400;color:#6b7280">'+esc(d.qno)+' · '+esc(d.vname||'')+'</span>':'')+'</div>'
      +(d.lines.length?(tools+'<div style="overflow:auto;border:1px solid #eef2f7;border-radius:9px"><table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f6f8fb;color:#14305c;font-size:11.5px"><th style="padding:7px 4px;width:30px"></th><th style="padding:7px 6px;text-align:left">품번</th><th style="padding:7px 4px;text-align:left">수량</th><th style="'+TH+'">E가</th><th style="'+TH+'">구매가</th><th style="'+TH+'">견적 DC</th><th style="'+TH+'">판매가</th><th style="'+TH+'">대성가</th><th style="padding:7px 6px;text-align:left">대성 재고</th><th style="padding:7px 6px;text-align:left">대성 코드</th><th></th></tr></thead><tbody>'+rows+'</tbody></table></div>')
        :'<div style="padding:18px;text-align:center;color:#9ca3af;font-size:12.5px;border:1px dashed #d6e0ec;border-radius:9px">위에서 견적을 [불러오기] 하면 품목이 여기에 나옵니다.</div>')
      +'</div>';
    // ③ 배송 · 발주
    var sec3=!d.lines.length?'':('<div style="'+CARD+'"><div style="'+H+'">③ 배송 · 발주</div><div style="display:flex;flex-direction:column;gap:10px">'
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
      +'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap"><span style="font-size:13px;color:#14305c">발주 <b>'+cnt+'</b>품목 · 대성가 합계 <b>'+_dsFmt(sumDs)+'</b>원 <span style="font-size:11px;color:#6b7280">(대리점가 '+_dsFmt(sum)+' · 부가세 별도)</span></span>'
      +'<span><button class="btn" onclick="_dsLookup()" '+(d.busy?'disabled':'')+'>대성 다시 확인</button> <button class="btn btn-primary" id="dsGo" onclick="dsSubmit()" style="background:#c2410c;border-color:#c2410c" '+((d.busy||!cnt||d.done)?'disabled':'')+'>'+(d.done?'발주 완료':'대성에 발주')+'</button></span></div>'
      +'</div></div>');
    // ④ 최근 대성 발주
    var hist=[]; _poQuotes().forEach(function(x){ (x.dsOrders||[]).forEach(function(o){ hist.push({o:o, q:x}); }); });
    hist.sort(function(a,b){ return (b.o.at||0)-(a.o.at||0); });
    var sec4='<div style="'+CARD+'"><div style="'+H+'">최근 대성 발주</div>'
      +(hist.length?('<div style="overflow:auto"><table style="width:100%;border-collapse:collapse;font-size:12px"><thead><tr style="color:#6b7280;font-size:11px"><th style="padding:5px 8px;text-align:left">날짜</th><th style="padding:5px 8px;text-align:left">대성 주문번호</th><th style="padding:5px 8px;text-align:left">업체</th><th style="padding:5px 8px;text-align:left">견적번호</th><th style="padding:5px 8px;text-align:right">품목</th><th style="padding:5px 8px;text-align:right">대리점가 합계</th><th style="padding:5px 8px;text-align:left">배송</th><th style="padding:5px 8px;text-align:left">담당</th></tr></thead><tbody>'
        +hist.slice(0,20).map(function(h){ var o=h.o; return '<tr style="border-top:1px solid #eef2f7"><td style="padding:5px 8px">'+esc(_poYmd(o.at))+'</td><td style="padding:5px 8px;font-weight:700;color:#c2410c">'+esc(o.no||'')+'</td><td style="padding:5px 8px">'+esc(h.q.vname||'')+'</td><td style="padding:5px 8px">'+esc(h.q.title||'')+'</td><td style="padding:5px 8px;text-align:right" title="'+_poA((o.items||[]).join('\n'))+'">'+(o.n||0)+'</td><td style="padding:5px 8px;text-align:right">'+_dsFmt(o.sum||0)+'</td><td style="padding:5px 8px">'+esc(o.branch||'')+'</td><td style="padding:5px 8px">'+esc(o.by||'')+'</td></tr>'; }).join('')
        +'</tbody></table></div>'):'<div style="font-size:12px;color:#9ca3af">아직 없습니다.</div>')+'</div>';
    var top='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap"><div style="font-size:17px;font-weight:700;color:#c2410c">대성산업 발주 <span style="font-size:12px;font-weight:400;color:#6b7280">WMIS · SMC · 저장하면 바로 접수</span></div>'
      +'<span>'+(d.lines.length?'<button class="btn" onclick="poReset()" style="margin-right:6px">새 발주</button>':'')+(_isAdmin()?'<button class="btn" onclick="dsOpenCfg()">대성 설정</button>':'')+'</span></div>';
    var keep=document.activeElement&&document.activeElement.id==='poVendor'?document.activeElement.selectionStart:null;
    pg.innerHTML='<div style="max-width:1100px;margin:0 auto">'+top+sec1+sec2+sec3+sec4+'</div>';
    if(keep!=null){ var vi=document.getElementById('poVendor'); if(vi){ vi.focus(); try{ vi.setSelectionRange(keep,keep); }catch(_e){} } }
  };
  var _poVT=null;
  window.poVendorInput=function(v){ if(!_ds) _poNew(); _ds.vname=v; clearTimeout(_poVT); _poVT=setTimeout(function(){ renderOrderPage(); }, 180); };
  window.poReset=function(){ var v=_ds?_ds.vname:''; _poNew(); _ds.vname=v; renderOrderPage(); };
  window.poLoadQuote=async function(id){
    var meta=_poQuotes().find(function(x){ return x.id===id; }); if(!meta) return;
    if(!_ds) _poNew();
    if(_ds.busy) return;
    _ds.busy=true; _ds.msg='견적 품목 불러오는 중…'; renderOrderPage();
    var items=await _qsBlobGet(id);
    if(!Array.isArray(items)){ _ds.busy=false; _ds.msg='<span style="color:#dc2626">이 견적의 품목을 불러오지 못했습니다.</span>'; renderOrderPage(); return; }
    var v=_ds.vname; _poNew(); _ds.vname=v||meta.vname||'';
    _ds.qid=id; _ds.qno=meta.title||''; _ds.qvname=meta.vname||'';
    var _n=function(v){ if(v==null||v==='') return null; var x=Number(String(v).replace(/[^\d.\-]/g,'')); return isNaN(x)?null:x; };
    _ds.lines=items.map(function(c){ return {pn:String((c&&c.spec)||'').trim(), qty:Math.max(1,Math.round(_n(c&&c.qty)||1)), alt:!!(c&&c.altOf), off:!!(c&&c.altOff), e:_n(c&&c.e), buy:_n(c&&c.buy), sell:_n(c&&c.sell), small:!!(c&&c.small)}; })
      .filter(function(x){ return x.pn && !x.off; }).map(function(x){ return {pn:x.pn, qty:x.qty, alt:x.alt, e:x.e, buy:x.buy, sell:x.sell, small:x.small, on:true, st:'wait'}; });
    _ds.remk='';   // r270: 기타요청사항은 비워 둔다 (사용자 11-13)
    if(!_ds.lines.length){ _ds.msg='<span style="color:#b45309">이 견적에 품번이 있는 줄이 없습니다.</span>'; renderOrderPage(); return; }
    _dsLookup();
  };
  async function _dsLookup(){
    if(!_ds||!_ds.lines.length) return; _ds.busy=true; _ds.msg='대성에서 품번 확인 중…'; renderOrderPage();
    try{
      var j=await _dsCall('/lookup', {items:_ds.lines.map(function(l){ return {pn:l.pn, qty:l.qty}; })});
      (j.items||[]).forEach(function(it, k){ var l=_ds.lines[k]; if(!l) return;
        if(it.found){ l.st='ok'; l.code=it.code; l.name=it.name||''; l.price=it.price; l.stock=it.stock||null; l.cands=null; l.pnUsed=''; }
        else { l.st='none'; l.on=false; l.cands=it.cands||[]; } });
      if(j.deliv&&j.deliv.deliPlace){ _ds.def=j.deliv; if(_ds.deli.branch==='서울'&&!_ds.deliEdited) _ds.deli=_dsDeliOf('서울', j.deliv); }
      var nf=_ds.lines.filter(function(l){ return l.st==='none'; }).length;
      _ds.msg=nf?('<span style="color:#b45309">대성에서 못 찾은 품번 '+nf+'개는 빼고 발주합니다. (비슷한 품번을 누르면 포함)</span>'):'<span style="color:#15803d">모든 품번을 대성에서 찾았습니다.</span>';
    }catch(e){ var em=String(e&&e.message||e); _ds.msg='<span style="color:#dc2626">대성 확인 실패: '+esc(em)+'</span>'+(/설정|아이디|로그인/.test(em)?' <span style="color:#6b7280">— 관리자가 [대성 설정]에 대성 아이디·비밀번호를 넣은 뒤 [대성 다시 확인]. 견적의 E가·구매가·판매가는 그대로 볼 수 있습니다.</span>':''); _ds.lines.forEach(function(l){ if(l.st==='wait') l.st='err'; }); }
    _ds.busy=false; renderOrderPage();
  }
  window._dsLookup=_dsLookup;
  window.dsToggle=function(k,v){ if(_ds&&_ds.lines[k]){ _ds.lines[k].on=!!v; renderOrderPage(); } };
  window.dsQty=function(k,v){ if(_ds&&_ds.lines[k]){ _ds.lines[k].qty=Math.max(1,parseInt(v,10)||1); renderOrderPage(); } };
  window.dsBranch=function(b){ if(!_ds) return; _ds.deli=_dsDeliOf(b, _ds.def); _ds.deliEdited=false; renderOrderPage(); };
  window.dsDeli=function(k,v){ if(!_ds) return; _ds.deli[k]=String(v||'').trim(); _ds.deliEdited=true; };
  window.dsPickCand=function(k,code){ if(!_ds||!_ds.lines[k]) return; var c=(_ds.lines[k].cands||[]).find(function(x){ return x.code===code; }); if(!c) return; var l=_ds.lines[k]; l.st='ok'; l.on=true; l.code=c.code; l.name=c.name||''; l.price=c.price; l.stock=c.stock||null; l.pnUsed=c.pn||''; renderOrderPage(); };
  window.dsSubmit=async function(){
    if(!_ds||_ds.busy||_ds.done) return; var d=_ds;
    var items=d.lines.filter(function(l){ return l.on&&l.st==='ok'; }).map(function(l){ return {code:l.code, qty:l.qty, pn:l.pnUsed||l.pn}; });
    if(!items.length) return;
    var codes={}; for(var i=0;i<items.length;i++){ if(codes[items[i].code]){ d.msg='<span style="color:#dc2626">같은 대성 코드가 두 줄 있습니다 ('+esc(items[i].pn)+'). 한 줄로 합쳐 주세요.</span>'; renderOrderPage(); return; } codes[items[i].code]=1; }
    if(!d.deli.addr||!d.deli.tel){ d.msg='<span style="color:#dc2626">도착지와 전화번호를 넣어 주세요.</span>'; renderOrderPage(); return; }
    var sum=0; d.lines.forEach(function(l){ if(l.on&&l.st==='ok') sum+=(Number(l.price)||0)*l.qty; });
    if(!confirm('대성산업에 발주합니다. 저장하면 바로 대성에 접수됩니다.\n\n'+items.length+'품목 · 대리점가 합계 '+_dsFmt(sum)+'원 (부가세 별도) · 대성가 '+_dsFmt(d.lines.reduce(function(a,l){ return a+((l.on&&l.st==='ok')?(_poDsPrice(l)||0)*l.qty:0); },0))+'원\n납품처: '+d.deli.type+' / '+d.deli.cmpy+'\n도착지: '+d.deli.addr+'\n납품요청일: '+d.deliDate+'\n\n발주할까요?')) return;
    d.busy=true; d.msg='대성에 저장 중…'; renderOrderPage();
    try{
      var j=await _dsCall('/order', {deli:{type:d.deli.type, cmpy:d.deli.cmpy, addr:d.deli.addr, tel:d.deli.tel}, deliDate:d.deliDate, remk:d.remk, items:items});
      _dsLog(d.qid, j.orderNo||'', items, sum, d.deli.branch);
      d.done=true; d.msg='<span style="color:#15803d;font-weight:700">대성에 발주했습니다'+(j.orderNo?' — 주문번호 '+esc(j.orderNo):'')+'.</span> <span style="color:#6b7280">대성 사이트 주문현황에서 확인할 수 있습니다.</span>';
      try{ _mtToast('대성 발주 완료'+(j.orderNo?' · '+j.orderNo:'')); }catch(_e2){}
    }catch(e){ d.msg='<span style="color:#dc2626">발주 실패: '+esc(e.message||String(e))+'</span>'; }
    d.busy=false; renderOrderPage();
  };
  function _dsLog(qid, no, items, sum, branch){
    var who=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)||'';
    var q=_poQuotes().find(function(x){ return x.id===qid; });
    if(!q) return;
    q.dsOrders=(q.dsOrders||[]).concat([{at:Date.now(), no:no, by:who, branch:branch, n:items.length, sum:sum, items:items.map(function(x){ return x.pn+'×'+x.qty; })}]);
    q.upd=Date.now(); try{ _qsPend[q.id]=Date.now(); }catch(_e){}   // 서버 병합(r250) 때 이 기록이 이기도록
    saveAll();
    try{ _qsScheduleVerify(); }catch(_e2){}
  }
  // r270: 대성 연결 = 메일 발송 서버(Worker v3)의 /wmis/* 를 같이 쓴다 → 관리자는 [대성 설정]에 대성 아이디·비밀번호만 넣으면 된다.
  //  서버 주소·열쇠는 메일 설정(sched_mail_cfg)의 것을 그대로 쓰고, 따로 둘 때만 고급 칸에 넣는다.
  async function _dsConn(){
    var cfg=await _dsLoadCfg(); if(!cfg||cfg._loadErr) throw new Error('대성 설정을 불러오지 못했습니다. 잠시 후 다시 시도하세요');
    var url=cfg.url, key=cfg.key;
    if(!url||!key){ var m=null; try{ m=await _mailLoadCfg(); }catch(_e){} if(m&&!m._loadErr){ url=url||m.url; key=key||m.key; } }
    if(!url||!key) throw new Error('서버 연결 설정 필요 — 관리자가 견적 > 다운로드 > [메일 설정]에 서버 주소·열쇠를 넣어야 합니다');
    if(!cfg.id||!cfg.pw) throw new Error('대성 아이디·비밀번호 설정 필요 — 관리자가 [대성 설정]에서 넣어 주세요');
    return { url:String(url).replace(/\/+$/,''), key:key, cred:{id:cfg.id, pw:cfg.pw} };
  }
  async function _dsPost(c, path, body){
    var r=await fetch(c.url+'/wmis'+path, {method:'POST', headers:{'Content-Type':'application/json','X-Mail-Key':c.key}, body:JSON.stringify(Object.assign({cred:c.cred}, body||{}))});
    var j=null; try{ j=await r.json(); }catch(_e){}
    if(!j) throw new Error(r.status===404?'서버가 옛 버전입니다 — Cloudflare 의 메일 Worker 코드를 저장소 mail/worker.js(v3)로 바꿔 주세요':('서버 응답 이상 (HTTP '+r.status+')'));
    if(!j.ok) throw new Error(j.error||('HTTP '+r.status));
    return j;
  }
  async function _dsCall(path, body){ return _dsPost(await _dsConn(), path, body); }
  window.dsOpenCfg=async function(){
    if(!_isAdmin()){ showInfoModal('권한','대성 설정은 관리자만 할 수 있습니다.'); return; }
    var cfg=await _dsLoadCfg(true);
    if(cfg._loadErr){ showInfoModal('대성 설정','저장된 설정을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'); return; }
    var I='width:100%;box-sizing:border-box;padding:8px 10px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:13px;font-family:inherit';
    var L='font-size:12px;font-weight:700;color:#14305c;margin-bottom:4px';
    _mailOverlay('dsCfgOverlay',
      '<div style="padding:15px 20px;border-bottom:2px solid #c2410c;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#c2410c">대성 설정</span><button class="btn" onclick="document.getElementById(\'dsCfgOverlay\').style.display=\'none\'">닫기</button></div>'
      +'<div style="padding:16px 20px;display:flex;flex-direction:column;gap:12px">'
      +'<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:9px;padding:10px 13px;font-size:11.5px;color:#374151;line-height:1.8">대성 WMIS(customer.wmis.co.kr) <b>아이디·비밀번호</b>만 넣으면 됩니다. 접속은 메일 발송 서버가 대신 합니다(서버 주소는 메일 설정 것을 그대로 씀).<br>비밀번호는 로그인한 직원만 읽을 수 있는 회사 설정에 저장되고, 화면에는 다시 보이지 않습니다.</div>'
      +'<div><div style="'+L+'">대성 아이디</div><input id="dsCfgId" value="'+_poA(cfg.id||'')+'" autocomplete="off" style="'+I+'"></div>'
      +'<div><div style="'+L+'">대성 비밀번호</div><input id="dsCfgPw" type="password" autocomplete="new-password" placeholder="'+(cfg.pw?'저장됨 — 바꿀 때만 입력':'비밀번호')+'" style="'+I+'"></div>'
      +'<details style="font-size:12px;color:#6b7280"><summary style="cursor:pointer">고급 — 서버를 따로 쓸 때만</summary><div style="display:flex;flex-direction:column;gap:8px;margin-top:8px">'
        +'<input id="dsCfgUrl" placeholder="서버 주소 (비우면 메일 설정 것)" value="'+_poA(cfg.url||'')+'" style="'+I+'">'
        +'<input id="dsCfgKey" type="password" placeholder="열쇠 (비우면 메일 설정 것)" value="'+_poA(cfg.key||'')+'" style="'+I+'"></div></details>'
      +'<div id="dsCfgMsg" style="font-size:12px;color:#6b7280;min-height:18px"></div>'
      +'<div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn" onclick="dsCfgPing()">연결 확인</button><button class="btn btn-primary" onclick="dsCfgSave()">저장</button></div></div>', 520);
  };
  function _dsCfgForm(){
    var g=function(id){ var e=document.getElementById(id); return e?String(e.value||'').trim():''; };
    var obj={ id:g('dsCfgId'), url:g('dsCfgUrl'), key:g('dsCfgKey') }; var pw=document.getElementById('dsCfgPw'); pw=pw?pw.value:'';
    obj.pw=pw || ((_dsCfg&&_dsCfg.pw)||'');
    return obj;
  }
  window.dsCfgPing=async function(){
    var m=document.getElementById('dsCfgMsg'); var f=_dsCfgForm();
    if(!f.id||!f.pw){ m.textContent='아이디와 비밀번호를 넣으세요.'; return; }
    m.textContent='대성에 로그인해 보는 중…';
    try{
      var url=f.url, key=f.key; if(!url||!key){ var mc=await _mailLoadCfg(); if(mc&&!mc._loadErr){ url=url||mc.url; key=key||mc.key; } }
      if(!url||!key) throw new Error('메일 설정(서버 주소·열쇠)이 없습니다 — 견적 > 다운로드 > [메일 설정] 먼저');
      var j=await _dsPost({url:String(url).replace(/\/+$/,''), key:key, cred:{id:f.id, pw:f.pw}}, '/ping');
      m.innerHTML='<span style="color:#15803d">연결됨</span> · '+esc(j.user||'')+(j.cust?' · '+esc(j.cust):'')+' <span style="color:#6b7280">— [저장]을 누르세요</span>';
    }catch(e){ m.innerHTML='<span style="color:#dc2626">'+esc(e.message||String(e))+'</span>'; }
  };
  window.dsCfgSave=async function(){
    var m=document.getElementById('dsCfgMsg'); var f=_dsCfgForm();
    if(!f.id||!f.pw){ m.textContent='아이디와 비밀번호를 넣으세요.'; return; }
    if(f.url && !/^https:\/\//.test(f.url)){ m.textContent='서버 주소는 https:// 로 시작해야 합니다.'; return; }
    try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_ds_cfg.json',{method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(f)});
      if(!r||!r.ok) throw new Error('저장 실패 (HTTP '+(r?r.status:'네트워크')+')'); _dsCfg=f; m.innerHTML='<span style="color:#15803d">저장했습니다.</span>'; try{ if(_ds&&_ds.lines.length) _dsLookup(); }catch(_e){} }
    catch(e){ m.innerHTML='<span style="color:#dc2626">'+esc(e.message||String(e))+'</span>'; }
  };
