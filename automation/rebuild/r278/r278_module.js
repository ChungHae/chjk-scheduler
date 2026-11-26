  // ─────────────────────────────────────────────────────────────
  //  r278  업무 > 감사 — SMC 유저특가 엑셀 → 거래명세표 (양식 용지에 글자만 인쇄)
  //   · 엑셀(special_price_excel.jsp, EUC-KR HTML 표)에서 유저명·품번·수량·유저특가·물류출하일을 읽는다
  //   · 유저명 ↔ 사내 업체를 한 번 이어 두면 그 뒤로는 자동 연결(sched_audit_usermap)
  //   · 발행일 = 물류출하일 + 2영업일 (토·일·한국 공휴일 건너뜀)
  //   · 품명 및 규격 = "<원장 품목>  <품번>" — 품목은 그 업체 원장에서 품번으로 찾는다
  //   · 한 장 13줄. 마지막 장이 12줄 이하면 그 아래 "- 이 하 여 백 -", 13줄이면 안 찍는다
  //   · 총금액(한글)은 첫 장에만, 공급가액·세액 계는 마지막 장에만
  //   · 2026-11-26 사용자 지시. 좌표는 샘플 스캔(300dpi) 실측값이며 [인쇄 보정]으로 조정한다
  // ─────────────────────────────────────────────────────────────
  var _AS_NODE = 'audit_stmt';                 // <_FB_PATH>_audit_stmt/<id>
  var _AS_PITCH = 3.5417;                      // 품목 줄 간격 mm (10pt)
  var _AS_ROWS  = 13;                          // 한 장 품목 줄 수
  // 전표 좌상단(0,0) 기준 mm. 샘플 실측 → [인쇄 보정]에서 덮어쓸 수 있다.
  var _AS_POS0 = {
    offX:0, offY:0,                            // 프린터 보정(전체 이동)
    slipX:26.2, slipY1:12.1, slipY2:150.4, slipW:171, slipH:127,
    fs:10,                                     // 기본 글자 크기(pt)
    noX:34.1,  headY:15.0,
    dyX:137.7, dmX:151.9, ddX:161.0,
    bizX:117.5, bizY:23.4,
    vnX:103.5, vnY:28.3, vnW:29, vnFs:9,
    ceoX:142.5, ceoY:28.3, ceoW:26, ceoFs:9,
    adX:103.6, adY:36.2, adW:66, adFs:9,
    totKoX:55.7, totNumX:102.3, totY:47.5,
    rowY:62.9,
    cNoR:6.6, cNameL:9.9, cQtyR:106.6, cPriceR:125.3, cSupR:149.4, cTaxR:169.8,
    emptyX:64.9,
    sumY:114.9,
    memoX:0.8, memoY:121.5
  };
  var _asPos = null, _asCfgLoaded = false;
  function _asAuthBase(){ try{ return (typeof _AUTH_BASE!=='undefined' && _AUTH_BASE) ? _AUTH_BASE : _FB_PATH; }catch(e){ return _FB_PATH; } }
  function _asKeyUrl(k){ return _fbDbUrl+'/'+_asAuthBase()+'/'+k+'.json'; }
  function _asDocUrl(id){ return _fbDbUrl+'/'+_FB_PATH+'_'+_AS_NODE+(id?('/'+id):'')+'.json'; }
  function P(){ return _asPos || _AS_POS0; }

  async function _asLoadCfg(){
    if(_asCfgLoaded) return;
    _asPos = Object.assign({}, _AS_POS0);
    if(!_fbDbUrl){ _asCfgLoaded=true; return; }
    try{
      var r = await _fbFetch(_asKeyUrl('sched_audit_cfg'));
      if(r.ok){ var d = await r.json(); if(d && typeof d==='object') Object.keys(d).forEach(function(k){ if(k in _AS_POS0 && typeof d[k]==='number') _asPos[k]=d[k]; }); }
    }catch(e){}
    _asCfgLoaded = true;
  }
  async function _asSaveCfg(){
    if(_isViewer()) throw new Error('보기 전용 계정입니다.');
    if(!_fbDbUrl) throw new Error('동기화 연결이 필요합니다.');
    var out={}; Object.keys(_AS_POS0).forEach(function(k){ out[k]=P()[k]; });
    await _fbPutOk(_asKeyUrl('sched_audit_cfg'), out, '감사 인쇄 보정');
  }

  // ── 유저명 ↔ 업체 연결 ───────────────────────────────────────
  var _asMap = null;
  function _asMapKey(code, name){ return String(code||'').trim().toUpperCase() + '|' + String(name||'').trim(); }
  async function _asLoadMap(){
    if(_asMap) return _asMap;
    _asMap = {};
    if(!_fbDbUrl) return _asMap;
    try{ var r=await _fbFetch(_asKeyUrl('sched_audit_usermap')); if(r.ok){ var d=await r.json(); if(d && typeof d==='object') _asMap=d; } }catch(e){}
    return _asMap;
  }
  async function _asSaveMap(key, vid, vname){
    _asMap = _asMap || {};
    _asMap[key] = { vid:vid, vname:vname, at:Date.now(), by:(_authUser&&_authUser.name)||'' };
    if(_isViewer() || !_fbDbUrl) return;
    // 자식 키만 PUT (11-02 사고 규칙 — 부모 노드는 건드리지 않는다)
    try{ await _fbPutOk(_fbDbUrl+'/'+_asAuthBase()+'/sched_audit_usermap/'+encodeURIComponent(key)+'.json', _asMap[key], '유저 연결'); }catch(e){}
  }

  // ── 공휴일 (date.nager.at · 열쇠 없음) + 캐시 + 수동 보정 ────
  var _asHolCache = {};
  async function _asHolidays(year){
    year = String(year);
    if(_asHolCache[year]) return _asHolCache[year];
    var list = null;
    if(_fbDbUrl){
      try{ var r=await _fbFetch(_asKeyUrl('sched_holidays/'+year)); if(r.ok){ var d=await r.json(); if(d && d.days && d.days.length) list=d.days; } }catch(e){}
    }
    if(!list){
      try{
        var res = await fetch('https://date.nager.at/api/v3/PublicHolidays/'+year+'/KR');
        if(res.ok){
          var arr = await res.json();
          list = (arr||[]).map(function(x){ return String(x.date||''); }).filter(Boolean);
          if(list.length && _fbDbUrl && !_isViewer()){
            try{ await _fbPutOk(_asKeyUrl('sched_holidays/'+year), { days:list, at:Date.now(), src:'date.nager.at' }, '공휴일'); }catch(e){}
          }
        }
      }catch(e){ list=null; }
    }
    _asHolCache[year] = list;   // null 이면 "확인 못 함"
    return list;
  }
  function _asYmd(d){ return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
  // 물류출하일(YYYYMMDD 또는 YYYY-MM-DD) + n 영업일
  async function _asAddBizDays(ymd, n){
    var s = String(ymd||'').replace(/[^0-9]/g,'');
    if(s.length!==8) return { date:'', warn:'날짜 형식을 알 수 없습니다 ('+ymd+')' };
    var d = new Date(+s.slice(0,4), +s.slice(4,6)-1, +s.slice(6,8));
    var warn = '', left = n;
    while(left>0){
      d.setDate(d.getDate()+1);
      var dow = d.getDay();
      if(dow===0 || dow===6) continue;
      var hol = await _asHolidays(d.getFullYear());
      if(hol===null){ if(!warn) warn='공휴일을 확인하지 못했습니다 — 날짜를 직접 확인하세요.'; }
      else if(hol.indexOf(_asYmd(d))>=0) continue;
      left--;
    }
    return { date:_asYmd(d), warn:warn };
  }

  // ── 엑셀(HTML 표) 읽기 ───────────────────────────────────────
  var _AS_COL = { user:'유저', uname:'유저명', spec:'품번', qty:'수량', price:'유저특가', ship:'물류출하일' };
  function _asParseFile(buf){
    // SMC 내보내기는 EUC-KR HTML 표다. 한글 머리글이 제대로 나오는 쪽을 고른다.
    var txt='', alt='';
    try{ txt = new TextDecoder('euc-kr').decode(buf); }catch(e){ txt=''; }
    try{ alt = new TextDecoder('utf-8').decode(buf); }catch(e){ alt=''; }
    if(txt.indexOf('물류출하일')<0 && alt.indexOf('물류출하일')>=0) txt=alt;
    if(!txt) txt=alt;
    if(!/<\s*tr/i.test(txt)) throw new Error('표를 찾지 못했습니다. SMC 유저특가 조회에서 받은 엑셀(.xls)인지 확인해 주세요.');
    var doc = new DOMParser().parseFromString(txt, 'text/html');
    var trs = Array.prototype.slice.call(doc.querySelectorAll('tr'));
    if(trs.length<2) throw new Error('자료 줄이 없습니다.');
    var head = Array.prototype.slice.call(trs[0].querySelectorAll('td,th')).map(function(c){ return (c.textContent||'').replace(/\s+/g,''); });
    var ix = {};
    Object.keys(_AS_COL).forEach(function(k){ ix[k] = head.indexOf(_AS_COL[k]); });
    var miss = Object.keys(ix).filter(function(k){ return ix[k]<0; }).map(function(k){ return _AS_COL[k]; });
    if(miss.length) throw new Error('엑셀에 다음 열이 없습니다: '+miss.join(', '));
    var out = [];
    for(var i=1;i<trs.length;i++){
      var c = Array.prototype.slice.call(trs[i].querySelectorAll('td,th')).map(function(x){ return (x.textContent||'').replace(/ /g,' ').trim(); });
      if(!c.length) continue;
      var spec = c[ix.spec]||'';
      if(!spec) continue;
      var qty = parseFloat(String(c[ix.qty]||'').replace(/[^0-9.\-]/g,''))||0;
      var price = parseFloat(String(c[ix.price]||'').replace(/[^0-9.\-]/g,''))||0;
      out.push({ ucode:c[ix.user]||'', uname:c[ix.uname]||'', spec:spec, qty:qty, price:price, ship:String(c[ix.ship]||'').replace(/[^0-9]/g,'') });
    }
    if(!out.length) throw new Error('읽을 품번이 없습니다.');
    return out;
  }

  // ── 한글 금액 (샘플: 1,811,007 → 일백팔십일만천칠원) ─────────
  function _asKoAmt(n){
    n = Math.round(Math.abs(+n||0));
    if(!n) return '영원';
    var D='영일이삼사오육칠팔구', U=['','십','백','천'], B=['','만','억','조','경'];
    var g=[], x=n;
    while(x>0){ g.push(x%10000); x=Math.floor(x/10000); }
    var lead = true, out='';
    for(var i=g.length-1;i>=0;i--){
      var v=g[i];
      if(!v){ continue; }
      var s='', t=String(v).padStart(4,'0');
      for(var j=0;j<4;j++){
        var d=+t[j], u=U[3-j];
        if(!d) continue;
        // 샘플(1,811,007 → 일백팔십일만천칠원) 규칙: 맨 앞 자리의 1 은 '일'을 적되 '일십'은 쓰지 않는다
        if(d===1 && u){ s += (lead && s==='' && u!=='십') ? ('일'+u) : u; }
        else s += D[d]+u;
      }
      out += s + B[i];
      lead = false;
    }
    return out+'원';
  }
  function _asNum(n){ return (Math.round(+n||0)).toLocaleString('en-US'); }

  // ── 거래명세표 묶음 만들기 ──────────────────────────────────
  var _asDraft = null;     // { vkey, vid, vname, info, docs:[{ship,date,warn,no,rows:[...],memo}] , missing:{spec:[rowRefs]} }
  function _asPickNo(used){
    var pool=[]; for(var i=1;i<=29;i++) if(used.indexOf(i)<0) pool.push(i);
    if(!pool.length) return null;
    return pool[Math.floor(Math.random()*pool.length)];
  }
  async function _asUsedNos(date){
    var used=[];
    if(!_fbDbUrl) return used;
    try{
      var r = await _fbFetch(_asDocUrl(null)+'?orderBy="date"&equalTo="'+date+'"');
      if(r.ok){ var d=await r.json(); if(d) Object.keys(d).forEach(function(k){ var v=d[k]; if(v && v.no) used.push(+v.no); }); }
    }catch(e){}
    if(!used.length){
      // 색인 규칙이 없으면 전체를 읽어 같은 날짜만 센다
      try{ var r2=await _fbFetch(_asDocUrl(null)); if(r2.ok){ var all=await r2.json(); if(all) Object.keys(all).forEach(function(k){ var v=all[k]; if(v && v.date===date && v.no) used.push(+v.no); }); } }catch(e){}
    }
    return used;
  }

  function _asLedgerIndex(rows){
    var ix={};
    (rows||[]).forEach(function(r){ var k=_qNorm(r && r.spec); if(k && !ix[k] && r.name) ix[k]=String(r.name).trim(); });
    return ix;
  }

  async function _asBuildDraft(list, vid, vname){
    var info = {};
    try{ var _ik=(typeof _ciKey==='function') ? _ciKey(vname,'서울') : vname; info = (clientInfo && (clientInfo[_ik] || clientInfo[vname])) || {}; }catch(e){ info={}; }
    var cli = null;
    try{ cli = (allClients()||[]).filter(function(c){ return c[0]===vname; })[0] || null; }catch(e){}
    var ledger = vid ? (await _qBlobGet(vid)) : null;
    var lix = _asLedgerIndex(ledger);
    var byShip = {};
    list.forEach(function(r){ (byShip[r.ship] = byShip[r.ship] || []).push(r); });
    var ships = Object.keys(byShip).sort();
    var docs = [];
    for(var i=0;i<ships.length;i++){
      var sh = ships[i];
      var bd = await _asAddBizDays(sh, 2);
      var used = await _asUsedNos(bd.date);
      var no = _asPickNo(used);
      var rows = byShip[sh].map(function(r){
        var nm = lix[_qNorm(r.spec)] || '';
        var sup = Math.round((+r.qty||0) * (+r.price||0));
        return { spec:r.spec, name:nm, qty:r.qty, price:r.price, supply:sup, tax:Math.round(sup*0.1) };
      });
      docs.push({ ship:sh, date:bd.date, warn:bd.warn, no:no, rows:rows, memo:'' });
    }
    return { vid:vid, vname:vname, biz:(cli&&cli[1])||info.bizNo||'', ceo:info.ceo||'', addr:((info.addr||'')+' '+(info.addr2||'')).trim(), docs:docs };
  }

  // ── 인쇄본 HTML ─────────────────────────────────────────────
  function _asSlipHtml(d, page, pages, head, grid){
    var p=P(), o=[];
    function F(x,y,txt,opt){
      opt=opt||{};
      var st='position:absolute;white-space:pre;top:'+(y+p.offY)+'mm;font-size:'+(opt.fs||p.fs)+'pt;line-height:'+(opt.fs||p.fs)+'pt;';
      if(opt.right) st+='right:'+((p.slipW-x)-p.offX)+'mm;text-align:right;';
      else st+='left:'+(x+p.offX)+'mm;';
      if(opt.w) st+='width:'+opt.w+'mm;overflow:hidden;';
      o.push('<div class="as-f" style="'+st+'">'+esc(txt==null?'':String(txt))+'</div>');
    }
    // 머리
    F(p.noX, p.headY, d.no==null?'':String(d.no));
    var dt=(d.date||'').split('-');
    if(dt.length===3){ F(p.dyX,p.headY,dt[0]); F(p.dmX,p.headY,String(+dt[1])); F(p.ddX,p.headY,String(+dt[2])); }
    F(p.bizX, p.bizY, head.biz||'');
    var vn=_asWrap(head.vname||'', p.vnW, p.vnFs);
    vn.forEach(function(t,i){ F(p.vnX, p.vnY+i*(p.vnFs*0.3528), t, {fs:p.vnFs, w:p.vnW}); });
    F(p.ceoX, p.ceoY, head.ceo||'', {fs:p.ceoFs, w:p.ceoW});
    var ad=_asWrap(head.addr||'', p.adW, p.adFs);
    ad.forEach(function(t,i){ F(p.adX, p.adY+i*(p.adFs*0.3528), t, {fs:p.adFs, w:p.adW}); });
    // 총금액 — 첫 장에만
    if(page===0){
      F(p.totKoX, p.totY, _asKoAmt(head.total)+'整');
      F(p.totNumX, p.totY, '(₩'+_asNum(head.total)+')');
    }
    // 품목
    var start = page*_AS_ROWS, part = d.rows.slice(start, start+_AS_ROWS);
    part.forEach(function(r,i){
      var y = p.rowY + i*_AS_PITCH;
      F(p.cNoR,  y, String(start+i+1), {right:1});
      F(p.cNameL,y, (r.name? (r.name+'  ') : '') + r.spec);
      F(p.cQtyR, y, r.qty? _asNum(r.qty):'', {right:1});
      F(p.cPriceR,y, r.price? _asNum(r.price):'', {right:1});
      F(p.cSupR, y, _asNum(r.supply), {right:1});
      F(p.cTaxR, y, _asNum(r.tax), {right:1});
    });
    // 이하 여백 — 마지막 장이 13줄을 채우지 않았을 때만
    if(page===pages-1 && part.length < _AS_ROWS){
      F(p.emptyX, p.rowY + part.length*_AS_PITCH, '- 이 하 여 백 -');
    }
    // 계 — 마지막 장에만
    if(page===pages-1){
      F(p.cSupR, p.sumY, _asNum(head.supply), {right:1});
      F(p.cTaxR, p.sumY, _asNum(head.tax), {right:1});
    }
    if(d.memo) F(p.memoX, p.memoY, d.memo);
    return '<div class="as-slip'+(grid?' as-grid':'')+'">'+o.join('')+'</div>';
  }
  // 칸 너비(mm)에 맞춰 줄바꿈 — 한글 1자 = 글자크기, 영숫자 1자 = 글자크기/2
  function _asWrap(s, wmm, fs){
    s=String(s||''); if(!s) return [''];
    var unit=(fs||10)*0.3528/2, max=Math.max(1, Math.floor(wmm/unit));
    var out=[], cur='', used=0;
    for(var i=0;i<s.length;i++){
      var ch=s[i], w=(ch.charCodeAt(0)>0x2000)?2:1;
      if(used+w>max && cur){ out.push(cur); cur=''; used=0; if(ch===' ') continue; }
      cur+=ch; used+=w;
    }
    if(cur) out.push(cur);
    return out.slice(0,3);
  }
  function _asDocHtml(draft, docs, grid){
    var p=P(), pagesHtml=[];
    docs.forEach(function(d){
      var supply=d.rows.reduce(function(a,r){ return a+r.supply; },0);
      var tax=d.rows.reduce(function(a,r){ return a+r.tax; },0);
      var head={ biz:draft.biz, vname:draft.vname, ceo:draft.ceo, addr:draft.addr, supply:supply, tax:tax, total:supply+tax };
      var pages=Math.max(1, Math.ceil(d.rows.length/_AS_ROWS));
      for(var pg=0; pg<pages; pg++){
        pagesHtml.push('<div class="as-page">'
          + '<div class="as-pos" style="top:'+p.slipY1+'mm">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'
          + '<div class="as-pos" style="top:'+p.slipY2+'mm">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'
          + '</div>');
      }
    });
    var css='@page{size:A4;margin:0}'
      +'html,body{margin:0;padding:0;background:#fff}'
      +'.as-page{position:relative;width:210mm;height:297mm;overflow:hidden;page-break-after:always;background:#fff}'
      +'.as-page:last-child{page-break-after:auto}'
      +'.as-pos{position:absolute;left:'+p.slipX+'mm;width:'+p.slipW+'mm;height:'+p.slipH+'mm}'
      +'.as-slip{position:relative;width:100%;height:100%;font-family:"바탕체",BatangChe,Batang,"바탕",serif;font-size:'+p.fs+'pt;line-height:'+p.fs+'pt;color:#000}'
      +'.as-f{position:absolute}'
      +'.as-grid{outline:1px dashed #9bb7dd}'
      +'.as-grid .as-f{outline:1px dotted #d9e2ef}';
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>거래명세표</title><style>'+css+'</style></head><body>'+pagesHtml.join('')+'</body></html>';
  }
  function _asPrintHtml(html){
    var old=document.getElementById('asPrintFrame'); if(old) old.remove();
    var f=document.createElement('iframe'); f.id='asPrintFrame';
    f.style.cssText='position:fixed;left:-10000px;top:0;width:210mm;height:297mm;border:0';
    document.body.appendChild(f);
    var d=f.contentWindow.document; d.open(); d.write(html); d.close();
    setTimeout(function(){ try{ f.contentWindow.focus(); f.contentWindow.print(); }catch(e){} }, 500);
  }

  // ── 저장 ────────────────────────────────────────────────────
  async function _asSaveDocs(draft){
    if(_isViewer()) throw new Error('보기 전용 계정입니다.');
    if(!_fbDbUrl) throw new Error('동기화 연결이 필요합니다.');
    var saved=[];
    for(var i=0;i<draft.docs.length;i++){
      var d=draft.docs[i];
      if(d.no==null) throw new Error((d.date||'')+' 에 쓸 수 있는 거래명세서 번호(1~29)가 남아 있지 않습니다.');
      var used=await _asUsedNos(d.date);
      if(used.indexOf(+d.no)>=0){ var nn=_asPickNo(used); if(nn==null) throw new Error((d.date||'')+' 번호가 모두 쓰였습니다.'); d.no=nn; }
      var supply=d.rows.reduce(function(a,r){ return a+r.supply; },0);
      var tax=d.rows.reduce(function(a,r){ return a+r.tax; },0);
      var id='as'+Date.now().toString(36)+Math.random().toString(36).slice(2,6);
      var rec={ id:id, no:+d.no, date:d.date, ship:d.ship, vid:draft.vid||'', vname:draft.vname||'',
                biz:draft.biz||'', ceo:draft.ceo||'', addr:draft.addr||'', memo:d.memo||'',
                rows:d.rows, supply:supply, tax:tax, total:supply+tax,
                by:(_authUser&&_authUser.name)||'', at:Date.now(), upd:Date.now() };
      await _fbPutOk(_asDocUrl(id), rec, '거래명세표');
      saved.push(rec);
    }
    return saved;
  }
  // 새로 적은 품목을 그 업체 원장에 등록 (없는 규격만 추가, 있는 건 품목만 채움)
  async function _asPushLedger(vid, pairs){
    if(!vid || !pairs.length || _isViewer() || !_fbDbUrl) return 0;
    var rows = (await _qBlobGet(vid)) || [];
    var ix={}; rows.forEach(function(r,i){ var k=_qNorm(r && r.spec); if(k && !(k in ix)) ix[k]=i; });
    var n=0;
    pairs.forEach(function(p){
      var k=_qNorm(p.spec); if(!k || !p.name) return;
      if(k in ix){ if(!rows[ix[k]].name){ rows[ix[k]].name=p.name; n++; } }
      else { rows.push({ spec:p.spec, name:p.name }); n++; }
    });
    if(n) await _qBlobPut(vid, rows);
    return n;
  }

  // ── 화면 ────────────────────────────────────────────────────
  var _asDrafts = [], _asRaw = [], _asFileName = '', _asShowInput = false;
  function _asBtn(label, fn, kind){
    var st = 'padding:5px 13px;border-radius:0;font-size:12.5px;font-weight:600;cursor:pointer;font-family:inherit;border:1px solid ';
    st += (kind==='primary') ? '#1B3A6B;background:#1B3A6B;color:#fff' : (kind==='warn' ? '#dc2626;background:#fff;color:#dc2626' : '#c8d2de;background:#fff;color:#1B3A6B');
    return '<button type="button" onclick="'+fn+'" style="'+st+'">'+label+'</button>';
  }
  window.renderAuditPage = async function(){
    var el = document.getElementById('pageAudit'); if(!el) return;
    if(!_asCfgLoaded){ el.innerHTML='<div style="padding:28px;color:#9ca3af">불러오는 중…</div>'; await _asLoadCfg(); await _asLoadMap(); }
    _asRender();
  };
  function _asRender(){
    var el = document.getElementById('pageAudit'); if(!el) return;
    var adm = (typeof _isAdmin==='function') ? _isAdmin() : ((_authUser&&(_authUser.role==='master'||_authUser.role==='admin'))||false);
    var h = '<div class="q-toolbar inv-toolbar">'
      + '<span class="inv-flat-label">감사</span>'
      + '<span style="font-size:12px;color:#6b7280">SMC 유저특가 엑셀 → 거래명세표 (양식 용지에 글자만 인쇄)</span>'
      + '<span style="flex:1"></span>'
      + _asBtn('엑셀 올리기','asPick()','primary')
      + ' ' + _asBtn('저장된 명세표','asOpenList()')
      + (adm ? (' ' + _asBtn('인쇄 보정','asCalib()')) : '')
      + '<input type="file" id="asFile" accept=".xls,.xlsx,.htm,.html" style="display:none" onchange="asOnFile(event)">'
      + '</div><div style="padding:14px 16px 40px">';
    if(!_asDrafts.length){
      h += '<div style="border:1px solid #e5e7eb;background:#fafbfc;padding:22px;font-size:13px;color:#374151;line-height:1.9">'
        + '<b style="color:#1B3A6B">쓰는 방법</b><br>'
        + '① SMC UbiCom 에서 <b>유저특가 조회 → 엑셀</b> 로 받은 파일을 [엑셀 올리기] 로 넣습니다.<br>'
        + '② 엑셀의 <b>유저명</b>에 우리 업체를 한 번 이어 주면 그 뒤로는 자동으로 연결됩니다.<br>'
        + '③ <b>물류출하일</b>마다 거래명세표가 한 묶음씩 생기고, 발행일은 <b>물류출하일 + 2영업일</b>(토·일·공휴일 건너뜀)로 잡힙니다.<br>'
        + '④ 품명은 그 업체 <b>원장</b>에서 품번으로 찾아 "품목 품번" 으로 적습니다. 못 찾으면 직접 넣을 수 있고, 넣은 값은 원장에도 등록됩니다.<br>'
        + '⑤ [저장하고 인쇄] 를 누르면 누적 저장되고, <b>양식 용지</b>에 글자만 찍힙니다.'
        + '</div>';
      el.innerHTML = h + '</div>';
      return;
    }
    h += '<div style="font-size:12px;color:#6b7280;margin-bottom:10px">파일: <b>'+esc(_asFileName)+'</b> · 품번 '+_asRaw.length+'줄</div>';
    _asDrafts.forEach(function(dr, di){
      h += '<div style="border:1px solid #c8d2de;margin-bottom:18px">';
      h += '<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:#f4f8fe;border-bottom:1px solid #c8d2de">'
         + '<b style="font-size:13.5px;color:#1B3A6B">'+esc(dr.uname||'(유저명 없음)')+'</b>'
         + '<span style="font-size:11.5px;color:#8a94a6">'+esc(dr.ucode||'')+'</span>';
      if(dr.vname){
        h += '<span style="font-size:12.5px">→ <b>'+esc(dr.vname)+'</b>'+(dr.biz?(' <span style="color:#8a94a6">'+esc(dr.biz)+'</span>'):'')+'</span>'
           + ' <button type="button" onclick="asUnlink('+di+')" style="border:none;background:none;color:#5b7ba6;font-size:11.5px;cursor:pointer;text-decoration:underline">업체 바꾸기</button>';
      } else {
        h += '<span style="font-size:12.5px;color:#b45309">업체를 이어 주세요</span>'
           + ' <input list="asClients" id="asV'+di+'" placeholder="업체명" style="height:28px;padding:0 8px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit;min-width:220px">'
           + ' ' + _asBtn('연결','asLink('+di+')','primary');
      }
      h += '</div>';
      if(!dr.vname){ h += '<div style="padding:16px;font-size:12.5px;color:#6b7280">업체를 이어야 원장에서 품목을 찾아 올 수 있습니다.</div></div>'; return; }
      var miss = _asMissing(dr);
      if(miss.length){
        h += '<div style="padding:10px 12px;background:#fff8ef;border-bottom:1px solid #f0d9b5;font-size:12.5px;color:#b45309">'
          + '원장에서 <b>품목을 찾지 못한 품번 '+miss.length+'종</b> 입니다. '
          + (_asShowInput ? '아래 칸에 품목을 적으면 같은 품번 줄에 바로 반영되고, 저장할 때 원장에도 등록됩니다.'
                          : '그대로 두면 품번만 찍힙니다.')
          + ' ' + (_asShowInput ? _asBtn('공란으로 두기','asToggleInput(0)') : _asBtn('품목 입력하기','asToggleInput(1)','primary'))
          + '</div>';
        if(_asShowInput){
          h += '<div style="padding:10px 12px;border-bottom:1px solid #eef2f7;display:flex;flex-wrap:wrap;gap:8px">';
          miss.forEach(function(sp){
            h += '<span style="display:inline-flex;align-items:center;gap:6px;border:1px solid #c8d2de;padding:4px 8px">'
              + '<span style="font-size:12px;color:#1a1a1a">'+esc(sp)+'</span>'
              + '<input value="" placeholder="품목" oninput="asSetName('+di+',this.value,this.dataset.sp)" data-sp="'+esc(sp)+'" style="height:26px;width:150px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit">'
              + '</span>';
          });
          h += '</div>';
        }
      }
      dr.docs.forEach(function(d, ci){
        var supply=d.rows.reduce(function(a,r){return a+r.supply;},0), tax=d.rows.reduce(function(a,r){return a+r.tax;},0);
        var pages=Math.max(1, Math.ceil(d.rows.length/_AS_ROWS));
        h += '<div style="border-top:1px solid #eef2f7;padding:10px 12px">'
          + '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:12.5px">'
          + '<span style="color:#8a94a6">물류출하일 '+esc(_asDot(d.ship))+'</span>'
          + '<span>발행일 <b>'+esc(d.date)+'</b></span>'
          + '<span>번호 <input value="'+(d.no==null?'':d.no)+'" oninput="asSetNo('+di+','+ci+',this.value)" style="width:48px;height:26px;text-align:center;padding:0 4px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></span>'
          + '<span style="color:#8a94a6">'+d.rows.length+'품목 · '+pages+'장</span>'
          + '<span>공급가액 <b>'+_asNum(supply)+'</b> · 세액 <b>'+_asNum(tax)+'</b> · 합계 <b>'+_asNum(supply+tax)+'</b></span>'
          + '<span style="flex:1"></span>'
          + '<span>비고 <input value="'+esc(d.memo||'')+'" oninput="asSetMemo('+di+','+ci+',this.value)" placeholder="(선택)" style="width:150px;height:26px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit"></span>'
          + '</div>'
          + (d.warn ? ('<div style="margin-top:5px;font-size:11.5px;color:#b45309">'+esc(d.warn)+'</div>') : '')
          + '<table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:12px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'
          + '<th style="padding:4px 6px;text-align:right;width:36px">번호</th><th style="padding:4px 6px;text-align:left">품명 및 규격</th>'
          + '<th style="padding:4px 6px;text-align:right;width:60px">수량</th><th style="padding:4px 6px;text-align:right;width:90px">단가</th>'
          + '<th style="padding:4px 6px;text-align:right;width:100px">공급가액</th><th style="padding:4px 6px;text-align:right;width:90px">세액</th></tr></thead><tbody>';
        d.rows.forEach(function(r,i){
          h += '<tr style="border-bottom:1px solid #f1f4f8">'
            + '<td style="padding:3px 6px;text-align:right;color:#8a94a6">'+(i+1)+'</td>'
            + '<td style="padding:3px 6px">'+(r.name?('<b>'+esc(r.name)+'</b>  '):'<span style="color:#dc2626">(품목 없음) </span>')+esc(r.spec)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.qty)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.price)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.supply)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.tax)+'</td></tr>';
        });
        h += '</tbody></table></div>';
      });
      h += '<div style="padding:10px 12px;display:flex;gap:8px;justify-content:flex-end;border-top:1px solid #eef2f7;background:#fafbfc">'
        + _asBtn('미리보기','asPreview('+di+')')
        + ' ' + _asBtn('저장하고 인쇄','asSavePrint('+di+')','primary')
        + '</div></div>';
    });
    var opts=''; try{ opts=(allClients()||[]).slice(0,4000).map(function(c){ return '<option value="'+esc(c[0])+'">'; }).join(''); }catch(e){}
    h += '<datalist id="asClients">'+opts+'</datalist></div>';
    el.innerHTML = h;
  }
  function _asDot(s){ s=String(s||''); return s.length===8 ? (s.slice(0,4)+'.'+s.slice(4,6)+'.'+s.slice(6,8)) : s; }
  function _asMissing(dr){
    var seen={}, out=[];
    dr.docs.forEach(function(d){ d.rows.forEach(function(r){ if(!r.name){ var k=_qNorm(r.spec); if(!seen[k]){ seen[k]=1; out.push(r.spec); } } }); });
    return out;
  }
  window.asToggleInput = function(on){ _asShowInput = !!on; _asRender(); };
  window.asSetNo = function(di,ci,v){ var n=parseInt(String(v).replace(/[^0-9]/g,''),10); _asDrafts[di].docs[ci].no = (n>=1&&n<=29)?n:null; };
  window.asSetMemo = function(di,ci,v){ _asDrafts[di].docs[ci].memo = String(v||''); };
  window.asSetName = function(di, val, spec){
    var dr=_asDrafts[di], k=_qNorm(spec), v=String(val||'').trim();
    dr.docs.forEach(function(d){ d.rows.forEach(function(r){ if(_qNorm(r.spec)===k) r.name=v; }); });
    dr._newNames = dr._newNames || {};
    if(v) dr._newNames[spec]=v; else delete dr._newNames[spec];
    // 표의 같은 품번 줄만 즉시 갱신(전체 재렌더는 입력 포커스를 잃는다)
    var el=document.getElementById('pageAudit'); if(!el) return;
    Array.prototype.forEach.call(el.querySelectorAll('tbody tr'), function(tr){
      var td=tr.children[1]; if(!td) return;
      var txt=td.textContent||'';
      if(_qNorm(txt).indexOf(k)>=0){ td.innerHTML = (v?('<b>'+esc(v)+'</b>  '):'<span style="color:#dc2626">(품목 없음) </span>')+esc(spec); }
    });
  };
  window.asPick = function(){ var i=document.getElementById('asFile'); if(i) i.click(); };
  window.asOnFile = async function(ev){
    var f = ev.target.files && ev.target.files[0]; ev.target.value='';
    if(!f) return;
    try{
      var buf = await f.arrayBuffer();
      _asRaw = _asParseFile(buf); _asFileName = f.name; _asShowInput=false;
      await _asLoadMap();
      var byU={}; _asRaw.forEach(function(r){ var k=_asMapKey(r.ucode,r.uname); (byU[k]=byU[k]||[]).push(r); });
      _asDrafts=[];
      var keys=Object.keys(byU);
      for(var i=0;i<keys.length;i++){
        var k=keys[i], list=byU[k], m=_asMap[k];
        var dr;
        if(m && m.vname){ dr = await _asBuildDraft(list, m.vid, m.vname); }
        else dr = { vid:'', vname:'', biz:'', ceo:'', addr:'', docs:[] };
        dr.key=k; dr.ucode=list[0].ucode; dr.uname=list[0].uname; dr.list=list;
        _asDrafts.push(dr);
      }
      _asRender();
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }
  };
  window.asLink = async function(di){
    var inp=document.getElementById('asV'+di); if(!inp) return;
    var nm=(inp.value||'').trim(); if(!nm){ showInfoModal('업체 연결','업체명을 고르세요.'); return; }
    var row=null; try{ row=(allClients()||[]).filter(function(c){ return c[0]===nm; })[0]||null; }catch(e){}
    if(!row){ showInfoModal('업체 연결','"'+nm+'" 은(는) 등록된 업체가 아닙니다. 일정 > 업체에서 먼저 등록해 주세요.'); return; }
    var v=null; try{ v=(quoteVendors||[]).filter(function(x){ return x.name===nm; })[0]||null; }catch(e){}
    var dr=_asDrafts[di];
    var nd = await _asBuildDraft(dr.list, v?v.id:'', nm);
    nd.key=dr.key; nd.ucode=dr.ucode; nd.uname=dr.uname; nd.list=dr.list;
    _asDrafts[di]=nd;
    await _asSaveMap(dr.key, v?v.id:'', nm);
    if(!v) showInfoModal('업체 연결','"'+esc(nm)+'" 에는 견적 원장이 없어 품목을 찾아오지 못합니다. 품목은 직접 넣으면 원장이 새로 만들어집니다.');
    _asRender();
  };
  window.asUnlink = function(di){ _asDrafts[di].vname=''; _asDrafts[di].vid=''; _asDrafts[di].docs=[]; _asRender(); };
  window.asPreview = function(di){
    var dr=_asDrafts[di];
    var w=window.open('','_blank'); if(!w){ showInfoModal('미리보기','팝업이 막혀 있습니다.'); return; }
    w.document.write(_asDocHtml(dr, dr.docs, true)); w.document.close();
  };
  window.asSavePrint = function(di){
    var dr=_asDrafts[di];
    if(!dr.vname){ showInfoModal('거래명세표','업체를 먼저 이어 주세요.'); return; }
    var n=dr.docs.length, miss=_asMissing(dr).length;
    showConfirmModal('거래명세표 저장·인쇄',
      '거래명세표 '+n+'건을 저장하고 인쇄합니다.' + (miss?('\n품목을 찾지 못한 품번 '+miss+'종은 품번만 찍힙니다.'):'')
      + '\n양식 용지를 프린터에 넣고 진행하세요.',
      async function(){
        try{
          var pairs=Object.keys(dr._newNames||{}).map(function(s){ return { spec:s, name:dr._newNames[s] }; });
          var added = await _asPushLedger(dr.vid, pairs);
          await _asSaveDocs(dr);
          _asPrintHtml(_asDocHtml(dr, dr.docs, false));
          showInfoModal('저장 완료', '거래명세표 '+n+'건을 저장했습니다.' + (added?('\n원장에 품목 '+added+'건을 등록했습니다.'):''));
          _asDrafts.splice(di,1); _asRender();
        }catch(e){ showInfoModal('저장 실패', String(e && e.message || e)); }
      }, '저장하고 인쇄', '#1B3A6B');
  };
  // ── 저장된 명세표 ───────────────────────────────────────────
  window.asOpenList = async function(){
    var ov=_asOverlay('asListOv');
    ov.innerHTML='<div style="width:100%;max-width:860px;background:#fff;border:1px solid #c8d2de;max-height:86vh;display:flex;flex-direction:column">'
      + '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:2px solid #1B3A6B"><b style="font-size:15px;color:#1B3A6B">저장된 거래명세표</b>'
      + '<button class="btn" onclick="document.getElementById(\'asListOv\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      + '<div id="asListBody" style="padding:14px 18px;overflow:auto;font-size:13px">불러오는 중…</div></div>';
    ov.style.display='flex';
    var body=document.getElementById('asListBody');
    try{
      var r=await _fbFetch(_asDocUrl(null)); var d=r.ok ? (await r.json()) : null;
      var arr=d ? Object.keys(d).map(function(k){ return d[k]; }).filter(Boolean) : [];
      arr.sort(function(a,b){ return String(b.date||'').localeCompare(String(a.date||'')) || (b.at||0)-(a.at||0); });
      if(!arr.length){ body.innerHTML='<div style="color:#9ca3af;padding:20px 0">저장된 거래명세표가 없습니다.</div>'; return; }
      window._asList = arr;
      body.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'
        + '<th style="padding:5px 7px;text-align:left">발행일</th><th style="padding:5px 7px;text-align:right">번호</th>'
        + '<th style="padding:5px 7px;text-align:left">업체</th><th style="padding:5px 7px;text-align:right">품목</th>'
        + '<th style="padding:5px 7px;text-align:right">합계</th><th style="padding:5px 7px;text-align:left">작성</th><th></th></tr></thead><tbody>'
        + arr.map(function(v,i){ return '<tr style="border-bottom:1px solid #f1f4f8">'
            + '<td style="padding:4px 7px">'+esc(v.date||'')+'</td>'
            + '<td style="padding:4px 7px;text-align:right">'+esc(String(v.no||''))+'</td>'
            + '<td style="padding:4px 7px">'+esc(v.vname||'')+'</td>'
            + '<td style="padding:4px 7px;text-align:right">'+((v.rows||[]).length)+'</td>'
            + '<td style="padding:4px 7px;text-align:right">'+_asNum(v.total)+'</td>'
            + '<td style="padding:4px 7px;color:#8a94a6">'+esc(v.by||'')+'</td>'
            + '<td style="padding:4px 7px;text-align:right"><button type="button" onclick="asReprint('+i+')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer">다시 인쇄</button></td></tr>'; }).join('')
        + '</tbody></table>';
    }catch(e){ body.innerHTML='<div style="color:#dc2626">불러오지 못했습니다: '+esc(String(e&&e.message||e))+'</div>'; }
  };
  window.asReprint = function(i){
    var v=(window._asList||[])[i]; if(!v) return;
    var dr={ vid:v.vid, vname:v.vname, biz:v.biz, ceo:v.ceo, addr:v.addr };
    _asPrintHtml(_asDocHtml(dr, [{ ship:v.ship, date:v.date, no:v.no, rows:v.rows||[], memo:v.memo||'' }], false));
  };
  function _asOverlay(id){
    var ov=document.getElementById(id);
    if(!ov){ ov=document.createElement('div'); ov.id=id;
      ov.style.cssText='position:fixed;inset:0;z-index:100002;background:rgba(15,23,42,.45);display:none;align-items:center;justify-content:center;padding:16px';
      document.body.appendChild(ov);
      ov.addEventListener('click',function(e){ if(e.target===ov) ov.style.display='none'; });
    }
    return ov;
  }
  // ── 인쇄 보정 (관리자) ──────────────────────────────────────
  window.asCalib = function(){
    var p=P(), ov=_asOverlay('asCalOv');
    function fld(k,label,step){ return '<label style="display:flex;align-items:center;gap:6px;font-size:12.5px"><span style="width:118px;color:#5b7ba6">'+label+'</span>'
      + '<input id="asC_'+k+'" type="number" step="'+(step||0.1)+'" value="'+p[k]+'" style="width:92px;height:28px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"> mm</label>'; }
    ov.innerHTML='<div style="width:100%;max-width:560px;background:#fff;border:1px solid #c8d2de;max-height:86vh;display:flex;flex-direction:column">'
      + '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:2px solid #1B3A6B"><b style="font-size:15px;color:#1B3A6B">인쇄 보정</b>'
      + '<button class="btn" onclick="document.getElementById(\'asCalOv\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      + '<div style="padding:16px 18px;overflow:auto;display:flex;flex-direction:column;gap:9px">'
      + '<div style="font-size:12.5px;color:#6b7280;line-height:1.8">양식 용지에 글자가 칸에서 벗어나면 아래 값을 조금씩 바꿔 맞춥니다. 오른쪽·아래로 밀려면 <b>+</b>, 왼쪽·위로 당기려면 <b>−</b> 입니다. [시험 인쇄]는 칸 위치를 점선으로 같이 찍습니다.</div>'
      + fld('offX','가로 이동') + fld('offY','세로 이동')
      + '<div style="height:1px;background:#eef2f7;margin:4px 0"></div>'
      + fld('slipX','전표 왼쪽') + fld('slipY1','첫째 전표 위') + fld('slipY2','둘째 전표 위')
      + fld('rowY','품목 첫 줄') + fld('fs','글자 크기(pt)',0.5)
      + '</div>'
      + '<div style="display:flex;gap:8px;justify-content:flex-end;padding:13px 18px;border-top:1px solid #e5e5e5">'
      + _asBtn('시험 인쇄','asCalTest()') + ' ' + _asBtn('저장','asCalSave()','primary') + '</div></div>';
    ov.style.display='flex';
  };
  function _asCalRead(){
    ['offX','offY','slipX','slipY1','slipY2','rowY','fs'].forEach(function(k){
      var e=document.getElementById('asC_'+k); if(!e) return;
      var v=parseFloat(e.value); if(!isNaN(v)) _asPos[k]=v;
    });
  }
  window.asCalTest = function(){
    _asCalRead();
    var rows=[]; for(var i=1;i<=13;i++) rows.push({ spec:'SAMPLE-'+i, name:'품목'+i, qty:i, price:1000*i, supply:1000*i*i, tax:100*i*i });
    var dr={ vid:'', vname:'시험 업체 주식회사', biz:'000-00-00000', ceo:'홍길동', addr:'서울특별시 구로구 구로중앙로 198 13동 103호' };
    _asPrintHtml(_asDocHtml(dr, [{ ship:'20260101', date:'2026-01-01', no:29, rows:rows, memo:'시험' }], true));
  };
  window.asCalSave = async function(){
    _asCalRead();
    try{ await _asSaveCfg(); showInfoModal('인쇄 보정','저장했습니다.'); var o=document.getElementById('asCalOv'); if(o) o.style.display='none'; }
    catch(e){ showInfoModal('인쇄 보정', String(e && e.message || e)); }
  };

