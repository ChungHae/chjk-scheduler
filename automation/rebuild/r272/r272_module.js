  // ─── r272: 휴대폰 견적 — 표 대신 카드(규격·품목·수량±·판매가·금액, 펼치면 E가·구매가·DC·마진) ───
  function _qMobOn(){ try{ return window.matchMedia('(max-width:700px)').matches; }catch(_e){ return false; } }
  function _qmN(v){ if(v==null||v==='') return null; var n=Number(String(v).replace(/,/g,'')); return isNaN(n)?null:n; }
  function _qmA(s){ return esc(String(s==null?'':s)).replace(/"/g,'&quot;'); }
  function _qMobRender(){
    var box=document.getElementById('qCart'); if(!box) return;
    var on=_qMobOn(); box.classList.toggle('qmob-on', on);
    var old=document.getElementById('qMobCards'); if(!on){ if(old) old.remove(); return; }
    if(!old){ old=document.createElement('div'); old.id='qMobCards'; box.appendChild(old); }
    var vendorSel=!!(_qCurId && (typeof quoteVendors!=='undefined'&&quoteVendors) && quoteVendors.find(function(v){ return v.id===_qCurId; }));
    if(!vendorSel){ old.innerHTML='<div class="qmc-empty">위에서 <b>거래처</b>를 먼저 고르세요.</div>'; return; }
    var rows=(_qCart||[]).map(function(c,i){ return {c:c,i:i}; }).filter(function(x){ var c=x.c; return c && (String(c.spec||'').trim()!=='' || String(c.name||'').trim()!==''); });
    var supply=0;
    var cards=rows.map(function(x,k){ var c=x.c, i=x.i, q=Number(c.qty)||1, s=_qmN(c.sell), e=_qmN(c.e), b=_qmN(c.buy);
      var amt=(s!=null)?s*q:null; if(amt!=null) supply+=amt;
      var dc=(e&&b)?Math.round((1-b/e)*1000)/10:null, mg=(s&&b)?Math.round((1-b/s)*1000)/10:null;
      var tags=[]; if(c.small) tags.push('소물'); if(c.pl) tags.push('확판'); if(c.altOf) tags.push('변경 제안'); if(c.altOff) tags.push('재고 없음'); if(c.disc) tags.push(String(c.disc).slice(0,18)); if(c.eta) tags.push('납기 '+String(c.eta).slice(0,16));
      return '<div class="qmc" data-i="'+i+'"><div class="qmc-h"><span class="qmc-no">'+(k+1)+'</span><div class="qmc-t"><div class="qmc-spec">'+esc(c.spec||'(규격 없음)')+'</div>'+(c.name?'<div class="qmc-name">'+esc(c.name)+'</div>':'')+(tags.length?'<div class="qmc-tags">'+tags.map(function(t){ return '<span class="qmc-tag">'+esc(t)+'</span>'; }).join('')+'</div>':'')+'</div><button class="qmc-del" onclick="qCartDel('+i+')" aria-label="빼기">×</button></div>'
        +'<div class="qmc-r"><span class="qmc-qty"><button onclick="qCartQty('+i+','+Math.max(1,q-1)+')" aria-label="수량 빼기">−</button><input type="number" inputmode="numeric" min="1" value="'+q+'" onchange="qCartQty('+i+',this.value)"><button onclick="qCartQty('+i+','+(q+1)+')" aria-label="수량 더하기">+</button></span>'
        +'<div class="qmc-f"><label>판매가</label><input inputmode="numeric" value="'+(s!=null?_qmA(s.toLocaleString()):'')+'" onchange="qCartField('+i+',\'sell\',this.value)"></div>'
        +'<div class="qmc-amt"><b>'+(amt!=null?amt.toLocaleString():'-')+'</b><div>금액</div></div></div>'
        +'<details><summary>E가 '+(e!=null?e.toLocaleString():'-')+' · 구매가 '+(b!=null?b.toLocaleString():'-')+(dc!=null?' · DC '+dc+'%':'')+(mg!=null?' · 마진 '+mg+'%':'')+' ▾</summary><div class="qmc-g">'
          +'<div class="qmc-f"><label>E가</label><input inputmode="numeric" value="'+(e!=null?_qmA(e.toLocaleString()):'')+'" onchange="qCartField('+i+',\'e\',this.value)"></div>'
          +'<div class="qmc-f"><label>구매가</label><input inputmode="numeric" value="'+(b!=null?_qmA(b.toLocaleString()):'')+'" onchange="qCartField('+i+',\'buy\',this.value)"></div>'
          +'<div class="qmc-f"><label>DC율 %</label><input inputmode="decimal" value="'+(dc!=null?dc:'')+'" onchange="qCartField('+i+',\'dc\',this.value)"></div>'
          +'<div class="qmc-f"><label>마진율 %</label><input inputmode="decimal" value="'+(mg!=null?mg:'')+'" onchange="qCartField('+i+',\'margin\',this.value)"></div>'
        +'</div></details></div>';
    }).join('');
    // 품목 추가: 표의 빈 줄과 같은 자동완성(qCartSpecInput)을 그대로 쓴다
    var bi=-1; for(var z=0; z<(_qCart||[]).length; z++){ var cz=_qCart[z]; if(cz && String(cz.spec||'').trim()==='' && String(cz.name||'').trim()===''){ bi=z; break; } }
    if(bi<0){ _qCart.push({vid:_qCurId, vname:_qVName(_qCurId), spec:'', name:'', qty:1}); bi=_qCart.length-1; }
    var addBox='<div class="qmc qmc-add"><div style="font-size:12px;font-weight:700;color:#1B3A6B;margin-bottom:6px">+ 품목 추가</div><input class="qc-in" data-mf="spec" autocomplete="off" autocapitalize="characters" placeholder="규격(품번) 입력 → 목록에서 고르기" oninput="qCartSpecInput('+bi+',this)" onchange="qCartSpecChanged('+bi+',this)" onkeydown="qCartSpecKey(event,'+bi+')" style="width:100%;height:42px;border:1.5px solid #1B3A6B;border-radius:10px;padding:0 12px;font-size:15px;box-sizing:border-box"></div>';
    var nego=(typeof _qNego!=='undefined'&&_qNego)?Number(_qNego):0;
    old.innerHTML=(cards||'')+addBox
      +(rows.length?'<div class="qmc-sum"><div class="row"><span style="font-size:12.5px;color:#64748b">공급가 '+supply.toLocaleString()+'원 · '+rows.length+'건</span></div>'
        +'<div class="row"><span style="font-size:13px;font-weight:700;color:#dc2626">NEGO(할인)</span><input inputmode="numeric" value="'+(nego?_qmA(nego.toLocaleString()):'')+'" placeholder="0" onchange="qNegoSet(this.value)" style="width:130px;text-align:right"></div>'
        +'<div class="row"><span style="font-size:13px;font-weight:700;color:#1B3A6B">합계 <span style="font-weight:400;font-size:11px;color:#64748b">부가세 별도</span></span><span class="qmc-total">'+(supply-nego).toLocaleString()+'원</span></div>'
        +'<textarea rows="2" placeholder="비고 (견적서에 표시 — 납기·결제 조건 등)" oninput="qMemoSet(this.value)">'+esc((typeof _qMemo!=='undefined'&&_qMemo)||'')+'</textarea></div>':'');
  }
  (function(){
    var base=renderQCart;
    renderQCart=function(){ var r=base.apply(this, arguments); try{ _qMobRender(); }catch(_e){} return r; };
    window.renderQCart=renderQCart;
    var mq; try{ mq=window.matchMedia('(max-width:700px)'); var h=function(){ try{ renderQCart(); }catch(_e){} }; if(mq.addEventListener) mq.addEventListener('change', h); else if(mq.addListener) mq.addListener(h); }catch(_e){}
  })();
