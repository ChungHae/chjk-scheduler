  // ─── r269: SMC 확인 — SMC 품번조회에 안 나오는 품번 = 타사 제품 → '타사' 칸으로 따로 관리 (메이커 지정·가격표 등록) ───
  function _smcA(s){ return esc(String(s==null?'':s)).replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
  var _smcRenderBase=window.renderSmcPage;
  function _smcOtherList(){ var ql=_qNorm(_smcQ); return (smcQueue||[]).filter(function(q){ return q&&q.status==='other'; }).filter(function(q){ return !ql || _qNorm(q.spec).indexOf(ql)>=0 || _qNorm(q.name).indexOf(ql)>=0 || _qNorm(q.vname).indexOf(ql)>=0 || _qNorm(q.maker).indexOf(ql)>=0; }).sort(function(a,b){ return (b.okAt||b.at||0)-(a.okAt||a.at||0); }); }
  function _smcMakerNames(){ return (priceMakers||[]).map(function(m){ return String(m.name||'').trim(); }).filter(function(n){ return n && n.toUpperCase().indexOf('SMC')<0; }); }
  window.renderSmcPage=function(keepFocus){
    _smcRenderBase(keepFocus);
    var host=document.getElementById('qSubSmc'); if(!host) return;
    var nOther=(smcQueue||[]).filter(function(q){ return q&&q.status==='other'; }).length;
    var skipBtn=host.querySelector('button[onclick="smcSetFilter(\'skip\')"]');
    if(skipBtn && !host.querySelector('#smcOtherTab')){ var b=document.createElement('button'); b.id='smcOtherTab'; b.className='smc-f'+(_smcFilter==='other'?' on':''); b.setAttribute('onclick',"smcSetFilter('other')"); b.title='SMC 품번조회에 안 나오는 품번 — 타사 제품으로 따로 관리'; b.textContent='타사 '+nOther; skipBtn.parentNode.insertBefore(b, skipBtn.nextSibling); }
    if(_smcFilter==='wait'){   // 대기 줄마다 [타사] 버튼
      host.querySelectorAll('#smcResult tr[data-id]').forEach(function(tr){ var last=tr.lastElementChild; if(!last||last.querySelector('.smc-oth')) return; var b=document.createElement('button'); b.className='smc-btn smc-oth'; b.textContent='타사'; b.title='타사 제품으로 옮김'; b.setAttribute('onclick',"smcToOther('"+tr.getAttribute('data-id')+"')"); last.appendChild(b); });
    }
    if(_smcFilter==='other') _smcOtherRender();
  };
  function _smcOtherRender(){
    var box=document.getElementById('smcResult'); if(!box) return;
    var L=_smcOtherList(), mk=_smcMakerNames();
    if(!L.length){ box.innerHTML='<div class="smc-empty">타사 제품이 없습니다. SMC 품번조회에 안 나오는 품번은 [SMC 일괄 확인] 결과나 대기 줄의 [타사] 버튼으로 여기 모입니다.</div>'; return; }
    var h='<div style="padding:8px 12px;font-size:12px;color:#6b7280">SMC 품번조회에 안 나온 품번입니다. <b>메이커</b>를 적고 [가격표 등록]을 누르면 그 메이커 가격표에 E가·매입가(견적가)로 들어가 다음 견적부터 자동으로 나옵니다.</div>'
      +'<datalist id="smcMakerList">'+mk.map(function(n){ return '<option value="'+_smcA(n)+'">'; }).join('')+'</datalist>'
      +'<table><thead><tr><th>No.</th><th>규격</th><th>품목명</th><th>메이커</th><th>E가</th><th>매입가(견적가)</th><th>거래처</th><th>작성자</th><th>날짜</th><th>견적번호</th><th>SMC 조회</th><th>처리</th></tr></thead><tbody>';
    L.forEach(function(q,ix){
      var reg=q.otherReg;
      h+='<tr data-id="'+q.id+'"><td>'+(ix+1)+'</td><td><b>'+esc(q.spec)+'</b> <button class="smc-btn" title="규격 복사" onclick="smcCopy(\''+q.id+'\')" style="padding:1px 6px">복사</button></td><td>'+esc(q.name||'')+'</td>'
        +'<td><input class="smc-in" data-f="mk" list="smcMakerList" value="'+esc(q.maker||'')+'" placeholder="메이커" style="width:110px;text-align:left"></td>'
        +'<td><input class="smc-in" data-f="e" value="'+(q.e!=null?q.e:'')+'"></td>'
        +'<td><input class="smc-in" data-f="buy" value="'+(q.buy!=null?q.buy:'')+'"></td>'
        +'<td>'+esc(q.vname||'')+'</td><td>'+esc(q.by||'')+'</td><td>'+_smcFmtD(q.at)+'</td><td>'+esc(q.quoteNo||'')+'</td>'
        +'<td style="font-size:11px;color:#b91c1c">'+esc(q.smcNote||'')+'</td>'
        +'<td>'+(reg?'<span class="smc-st">등록 · '+esc(reg.maker||'')+' '+_smcFmtD(reg.at)+'</span> ':'<button class="smc-btn ok" onclick="smcOtherRegister(\''+q.id+'\')">가격표 등록</button>')+'<button class="smc-btn" onclick="smcOtherBack(\''+q.id+'\')">대기로</button></td></tr>';
    });
    box.innerHTML=h+'</tbody></table>';
  }
  window.smcToOther=function(id, note){
    var q=(smcQueue||[]).find(function(x){ return x.id===id; }); if(!q) return;
    q.status='other'; q.okBy=_smcWho(); q.okAt=Date.now(); if(note) q.smcNote=note;
    saveAll(); renderSmcPage();
  };
  window.smcOtherBack=function(id){
    var q=(smcQueue||[]).find(function(x){ return x.id===id; }); if(!q) return;
    q.status='wait'; delete q.otherReg; saveAll(); renderSmcPage();
  };
  window.smcOtherRegister=async function(id){
    if(typeof _guardW==='function' && !_guardW()) return;
    var q=(smcQueue||[]).find(function(x){ return x.id===id; }); if(!q) return;
    var row=document.querySelector('#smcResult tr[data-id="'+id+'"]');
    var gv=function(f){ var el=row&&row.querySelector('input[data-f="'+f+'"]'); return el?String(el.value).trim():''; };
    var num=function(v){ v=String(v).replace(/,/g,''); if(v==='') return null; var n=Number(v); return isNaN(n)?null:n; };
    var mk=gv('mk'), e=num(gv('e')), buy=num(gv('buy'));
    if(!mk){ showInfoModal('타사 제품','메이커를 적어 주세요.'); return; }
    if(mk.toUpperCase().indexOf('SMC')>=0){ showInfoModal('타사 제품','SMC 품번이면 [대기로] 옮겨 SMC 확인으로 등록하세요.'); return; }
    if(!(e>0) && !(buy>0)){ showInfoModal('타사 제품','E가나 매입가 중 하나는 있어야 합니다.'); return; }
    if(!_fbDbUrl){ showInfoModal('동기화 필요','팀 동기화 연결이 필요합니다.'); return; }
    try{
      var m=(priceMakers||[]).find(function(x){ return String(x.name||'').trim().toLowerCase()===mk.toLowerCase(); });
      var mid=m?m.id:('pm'+Date.now().toString(36)+Math.random().toString(36).slice(2,5));
      var rows=[]; if(m){ try{ delete _priceBlobCache[mid]; }catch(_e){} var eb=await _priceBlobGet(mid); if(Array.isArray(eb)) rows=eb; else if(m.count) throw new Error(mk+' 가격표를 읽지 못했습니다'); }
      var pk=function(z){ return String(z==null?'':z).toLowerCase().replace(/\s+/g,''); };
      var k=pk(q.spec), r=rows.find(function(x){ return pk(x.spec)===k && !x.qr; });
      if(!r){ r={ spec:q.spec, name:q.name||'', unit:'EA' }; rows.push(r); }
      if(e>0) r.ega=e; if(buy>0) r.buy=buy; if(q.name && !r.name) r.name=q.name;
      await _priceBlobPut(mid, rows);
      if(m) m.count=rows.length; else priceMakers.push({ id:mid, name:mk, count:rows.length });
      q.maker=mk; q.e=e; q.buy=buy; q.otherReg={ maker:mk, at:Date.now(), by:_smcWho() };
      saveAll();
      try{ _ensurePriceSyncMap(true); }catch(_e){}
      try{ _qInvalidateAllIdx(); }catch(_e){}
      renderSmcPage();
    }catch(err){ showInfoModal('가격표 등록 실패', (err&&err.message)||String(err)); }
  };
  // 일괄 확인 결과의 'SMC 에 없음' → 타사로 (r268 의 [없는 품번 제외로] 를 바꿈)
  window.smcBulkSkipNone=function(){
    var r=_smcBk.res; if(!r) return; var L=r.none.filter(function(o){ return o.st==='no' || (!o.st && !o.smcE); });
    if(!L.length||!confirm('SMC 품번조회에 안 나온 '+L.length+'건을 [타사] 로 옮깁니다. 진행할까요?')) return;
    var who=_smcWho(), now=Date.now(); L.forEach(function(o){ o.q.status='other'; o.q.okBy=who; o.q.okAt=now; o.q.smcNote=(o.st==='no'?'공급불가/품번 아님':'조회 안 됨')+' '+_smcFmtD(now); });
    saveAll(); _smcBk.res=_smcBkParse(_smcBk.text); _smcBk.msg='<span style="color:#15803d">'+L.length+'건을 타사로 옮겼습니다.</span>'; _smcBkRender(); try{ renderSmcPage(); }catch(_e){}
  };
  // 일괄 확인 창: 마지막으로 확인한 SMC 결과를 이 브라우저에 기억해 두고, 창을 다시 열면 채워 준다
  var _smcBkOpenBase=window.smcBulkOpen, _smcBkParseBase=window.smcBulkParse;
  window.smcBulkOpen=function(){
    if(!_smcBk.text){ try{ var last=localStorage.getItem('smc_bulk_last'); if(last){ _smcBk.text=last; } }catch(_e){} }
    _smcBkOpenBase();
    if(_smcBk.text){ try{ smcBulkParse(); }catch(_e){} }
  };
  window.smcBulkParse=function(){
    _smcBkParseBase();
    try{ if(_smcBk.text) localStorage.setItem('smc_bulk_last', _smcBk.text); }catch(_e){}
  };
