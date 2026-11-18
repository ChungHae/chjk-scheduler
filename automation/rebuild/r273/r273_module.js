  // ─── r273: 거래명세서 — 직접 입력·견적 불러오기·인쇄·PDF·메일, 홈택스 세금계산서 일괄발급 엑셀(무료) ───
  var _st={ list:null, cur:null, q:'', sel:{}, msg:'', busy:false, quotes:false };
  var _ST_SUP={ '서울':{ corp:'충해전기(주)', ceo:'김해식', biz:'1138114978', addr:'서울시 구로구 구로중앙로 198, 구로기계공구상가 B-13, 103', uptae:'도소매', jongmok:'공압기기', tel:'02-2671-4474', fax:'02-2672-3157', mail:'chjk@chjk.co.kr' },
                 '화성':{ corp:'충해전기(주) 화성영업소', ceo:'김재성', biz:'4068502616', addr:'경기도 화성시 팔탄면 푸른들판로 642-5, G-103, 104, 202 (유일공구상가)', uptae:'도소매', jongmok:'공압기기', tel:'031-352-4475', fax:'031-353-4470', mail:'hs-chjk@chjk.co.kr' } };
  function _stSup(br){ var b=_ST_SUP[br==='화성'?'화성':'서울'], o={}, k; for(k in b) o[k]=b[k]; try{ var s=JSON.parse(localStorage.getItem('st_sup_'+(br==='화성'?'hs':'se'))||'null'); if(s){ for(k in s){ if(s[k]) o[k]=s[k]; } } }catch(_e){} return o; }
  function _stA(s){ return esc(String(s==null?'':s)).replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
  function _stN(v){ if(v==null||v==='') return 0; var x=Number(String(v).replace(/[^\d.\-]/g,'')); return isNaN(x)?0:x; }
  function _stF(n){ return (n==null||n==='')?'':Math.round(Number(n)).toLocaleString('ko-KR'); }
  function _stToday(){ var d=new Date(); return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2); }
  function _stBiz(b){ b=String(b||'').replace(/\D/g,''); return b.length===10?(b.slice(0,3)+'-'+b.slice(3,5)+'-'+b.slice(5)):b; }
  function _stBranch(){ try{ var n=(_authUser&&_authUser.name)||''; var m=(members||[]).find(function(x){ return (x.name||'').trim()===n; }); return (m&&m.group==='화성')?'화성':'서울'; }catch(_e){ return '서울'; } }
  function _stUrl(id){ return _fbDbUrl+'/'+_FB_PATH+'_stmt'+(id?('/'+id):'')+'.json'; }
  function _stLine(l){ var s=Math.round(_stN(l.qty)*_stN(l.price)); return { supply:s, tax:Math.round(s*0.1) }; }
  function _stTot(d){ var s=0,t=0; (d.lines||[]).forEach(function(l){ if(!String(l.name||'').trim()&&!String(l.spec||'').trim()) return; var x=_stLine(l); s+=x.supply; t+=x.tax; }); if(d.taxFree) t=0; return { supply:s, tax:t, total:s+t }; }
  function _stRealLines(d){ return (d.lines||[]).filter(function(l){ return String(l.name||'').trim()||String(l.spec||'').trim(); }); }
  function _stNew(){ return { id:'', no:'', date:_stToday(), branch:_stBranch(), vname:'', biz:'', sub:'', ceo:'', addr:'', uptae:'', jongmok:'', email:'', lines:[{name:'',spec:'',qty:1,price:'',note:''}], memo:'', claim:'02', qid:'', qno:'', tax:null }; }
  function _stNextNo(date){ var p='T'+String(date||_stToday()).replace(/-/g,'')+'-', mx=0; (_st.list||[]).forEach(function(x){ if(x&&String(x.no||'').indexOf(p)===0){ var n=Number(String(x.no).slice(p.length))||0; if(n>mx) mx=n; } }); return p+('0'+(mx+1)).slice(-2); }
  async function _stLoad(force){
    if(_st.list&&!force) return; if(!_fbDbUrl){ _st.list=[]; return; }
    try{ var r=await _fbFetch(_stUrl()); var j=(r&&r.ok)?await r.json():null; _st.list=j?Object.keys(j).map(function(k){ return j[k]; }).filter(function(x){ return x&&x.id; }):[]; }
    catch(e){ _st.list=_st.list||[]; _st.msg='<span style="color:#dc2626">목록을 불러오지 못했습니다.</span>'; }
  }
  function _stFillClient(d, nm){
    var row=_cliFind(nm, d.branch)||_cliFind(nm); if(!row) return false;
    var inf=_clxInfo(row)||{};
    d.vname=String(row[0]); d.biz=String(row[1]||'').replace(/\D/g,''); d.sub=String(row[3]||inf.subBiz||'').replace(/\D/g,'');
    d.ceo=inf.ceo||''; d.addr=[inf.addr,inf.addr2].filter(Boolean).join(' '); d.uptae=inf.uptae||''; d.jongmok=inf.jongmok||''; d.email=inf.taxEmail||inf.email||'';
    return true;
  }
  function _stCollect(){   // 화면 입력값 → _st.cur
    var d=_st.cur, pg=document.getElementById('pageStmt'); if(!d||!pg) return d;
    pg.querySelectorAll('[data-sf]').forEach(function(el){ var f=el.getAttribute('data-sf'); d[f]=(el.type==='checkbox')?el.checked:String(el.value||'').trim(); });
    d.biz=String(d.biz||'').replace(/\D/g,''); d.sub=String(d.sub||'').replace(/\D/g,'');
    pg.querySelectorAll('tr[data-sl]').forEach(function(tr){ var l=d.lines[Number(tr.getAttribute('data-sl'))]; if(!l) return; tr.querySelectorAll('[data-lf]').forEach(function(el){ var f=el.getAttribute('data-lf'); l[f]=(f==='qty'||f==='price')?(el.value===''?'':_stN(el.value)):String(el.value||'').trim(); }); });
    return d;
  }
  window.stNew=function(){ _st.cur=_stNew(); _st.msg=''; _st.quotes=false; renderStmtPage(); };
  window.stBack=function(){ _st.cur=null; _st.msg=''; renderStmtPage(); };
  window.stOpen=function(id){ var x=(_st.list||[]).find(function(s){ return s.id===id; }); if(!x) return; _st.cur=JSON.parse(JSON.stringify(x)); if(!_st.cur.lines||!_st.cur.lines.length) _st.cur.lines=[{name:'',spec:'',qty:1,price:'',note:''}]; _st.msg=''; _st.quotes=false; renderStmtPage(); };
  window.stCopy=function(id){ var x=(_st.list||[]).find(function(s){ return s.id===id; }); if(!x) return; var c=JSON.parse(JSON.stringify(x)); c.id=''; c.no=''; c.date=_stToday(); c.tax=null; _st.cur=c; _st.msg='복사했습니다 — 날짜·품목을 고친 뒤 [저장] 하세요.'; renderStmtPage(); };
  window.stAddLine=function(){ _stCollect(); _st.cur.lines.push({name:'',spec:'',qty:1,price:'',note:''}); renderStmtPage(); var r=document.querySelectorAll('#pageStmt tr[data-sl]'); var el=r.length&&r[r.length-1].querySelector('[data-lf="name"]'); if(el) el.focus(); };
  window.stDelLine=function(k){ _stCollect(); _st.cur.lines.splice(k,1); if(!_st.cur.lines.length) _st.cur.lines.push({name:'',spec:'',qty:1,price:'',note:''}); renderStmtPage(); };
  window.stRecalc=function(){ _stCollect(); var d=_st.cur, t=_stTot(d); document.querySelectorAll('#pageStmt tr[data-sl]').forEach(function(tr){ var l=d.lines[Number(tr.getAttribute('data-sl'))]; var x=_stLine(l||{}); var a=tr.querySelector('.st-sup'), b=tr.querySelector('.st-tax'); if(a) a.textContent=_stF(x.supply); if(b) b.textContent=d.taxFree?'0':_stF(x.tax); }); var el=document.getElementById('stTotBox'); if(el) el.innerHTML=_stTotHtml(t); };
  window.stVendorPick=function(v){ setTimeout(function(){ if(!_st.cur) return; _stCollect(); var d=_st.cur; d.vname=String(v||'').trim(); if(d.vname) _stFillClient(d, d.vname); renderStmtPage(); }, 0); };
  window.stBranchSet=function(v){ _stCollect(); _st.cur.branch=(v==='화성')?'화성':'서울'; renderStmtPage(); };
  window.stQuotesToggle=function(){ _stCollect(); _st.quotes=!_st.quotes; renderStmtPage(); };
  window.stLoadQuote=async function(id){
    _stCollect(); var d=_st.cur; var meta=_poQuotes().find(function(x){ return x.id===id; }); if(!meta) return;
    _st.msg='견적 품목 불러오는 중…'; renderStmtPage();
    var items=await _qsBlobGet(id);
    if(!Array.isArray(items)){ _st.msg='<span style="color:#dc2626">이 견적의 품목을 불러오지 못했습니다.</span>'; renderStmtPage(); return; }
    var L=items.filter(function(c){ return c&&!c.altOff&&(String(c.spec||'').trim()||String(c.name||'').trim()); }).map(function(c){ return { name:String(c.name||'').trim(), spec:String(c.spec||'').trim(), qty:Math.max(1,Math.round(_stN(c.qty)||1)), price:_stN(c.sell)||'', note:'' }; });
    if(!L.length){ _st.msg='<span style="color:#b45309">이 견적에 품목이 없습니다.</span>'; renderStmtPage(); return; }
    var keep=_stRealLines(d); d.lines=keep.concat(L); d.qid=id; d.qno=meta.title||'';
    if(!d.vname&&meta.vname){ d.vname=meta.vname; _stFillClient(d, meta.vname); }
    _st.quotes=false; _st.msg='<span style="color:#15803d">견적 '+esc(meta.title||'')+' 에서 '+L.length+'줄을 불러왔습니다. 판매가 = 견적 판매가.</span>'; renderStmtPage();
  };
  function _stCheck(d){
    if(!d.vname) return '업체명을 넣어 주세요.';
    if(!/^\d{4}-\d{2}-\d{2}$/.test(d.date||'')) return '거래일자를 넣어 주세요.';
    if(!_stRealLines(d).length) return '품목을 한 줄 이상 넣어 주세요.';
    return '';
  }
  window.stSave=async function(silent){
    if(typeof _guardW==='function' && !_guardW()) return false;
    var d=_stCollect(); var er=_stCheck(d); if(er){ _st.msg='<span style="color:#dc2626">'+er+'</span>'; renderStmtPage(); return false; }
    if(!_fbDbUrl){ showInfoModal('동기화 필요','팀 동기화 연결 후 저장할 수 있습니다.'); return false; }
    await _stLoad();
    d.lines=_stRealLines(d); var now=Date.now(), who=(_authUser&&_authUser.name)||'';
    if(!d.id){ d.id='st'+now.toString(36)+Math.random().toString(36).slice(2,6); d.by=who; d.at=now; }
    if(!d.no) d.no=_stNextNo(d.date);
    d.upd=now; d.updBy=who; var t=_stTot(d); d.supply=t.supply; d.taxAmt=t.tax; d.total=t.total;
    try{ await _fbPutOk(_stUrl(d.id), d, '거래명세서'); }catch(e){ _st.msg='<span style="color:#dc2626">'+esc(e.message||String(e))+'</span>'; renderStmtPage(); return false; }
    var i=(_st.list||[]).findIndex(function(x){ return x.id===d.id; }); var cp=JSON.parse(JSON.stringify(d)); if(i>=0) _st.list[i]=cp; else _st.list.push(cp);
    if(!silent){ _st.msg='<span style="color:#15803d">저장했습니다 — '+esc(d.no)+'</span>'; renderStmtPage(); }
    return true;
  };
  window.stDelete=async function(id){
    if(typeof _guardW==='function' && !_guardW()) return;
    var x=(_st.list||[]).find(function(s){ return s.id===id; }); if(!x) return;
    if(x.tax&&x.tax.st==='issued'){ showInfoModal('거래명세서','세금계산서 발행 완료로 표시된 명세서는 지울 수 없습니다. 먼저 발행 표시를 풀어 주세요.'); return; }
    if(!confirm('거래명세서 '+(x.no||'')+' ('+(x.vname||'')+') 를 삭제할까요?')) return;
    try{ var r=await _fbFetch(_stUrl(id), {method:'DELETE'}); if(!r||!r.ok) throw new Error('삭제 실패'); }catch(e){ showInfoModal('거래명세서', e.message||String(e)); return; }
    _st.list=_st.list.filter(function(s){ return s.id!==id; }); delete _st.sel[id]; if(_st.cur&&_st.cur.id===id) _st.cur=null; renderStmtPage();
  };
  // ── 인쇄용 HTML (공급받는자 보관용 + 공급자 보관용, A4 한 장) ──
  function _stDocHtml(d){
    var S=_stSup(d.branch), t=_stTot(d), L=_stRealLines(d), rows='', N=Math.max(10, L.length);
    for(var i=0;i<N;i++){ var l=L[i]; if(l){ var x=_stLine(l); rows+='<tr><td class="c">'+(i+1)+'</td><td>'+esc(l.name||'')+'</td><td>'+esc(l.spec||'')+'</td><td class="r">'+_stF(l.qty)+'</td><td class="r">'+_stF(l.price)+'</td><td class="r">'+_stF(x.supply)+'</td><td class="r">'+(d.taxFree?'0':_stF(x.tax))+'</td><td>'+esc(l.note||'')+'</td></tr>'; } else rows+='<tr><td>&nbsp;</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>'; }
    var one=function(tag){ return '<div class="doc"><div class="ttl">거 래 명 세 서 <span>('+tag+')</span></div>'
      +'<div class="meta"><span>거래일자 '+esc(d.date||'')+'</span><span>No. '+esc(d.no||'')+'</span></div>'
      +'<table class="hd"><tr><th rowspan="4" class="v">공<br>급<br>자</th><th>등록번호</th><td colspan="3"><b>'+esc(_stBiz(S.biz))+'</b></td><th rowspan="4" class="v">공<br>급<br>받<br>는<br>자</th><th>등록번호</th><td colspan="3"><b>'+esc(_stBiz(d.biz))+(d.sub?(' ('+esc(d.sub)+')'):'')+'</b></td></tr>'
      +'<tr><th>상호</th><td>'+esc(S.corp)+'</td><th>성명</th><td>'+esc(S.ceo)+'</td><th>상호</th><td>'+esc(d.vname||'')+'</td><th>성명</th><td>'+esc(d.ceo||'')+'</td></tr>'
      +'<tr><th>주소</th><td colspan="3">'+esc(S.addr)+'</td><th>주소</th><td colspan="3">'+esc(d.addr||'')+'</td></tr>'
      +'<tr><th>업태</th><td>'+esc(S.uptae)+'</td><th>종목</th><td>'+esc(S.jongmok)+'</td><th>업태</th><td>'+esc(d.uptae||'')+'</td><th>종목</th><td>'+esc(d.jongmok||'')+'</td></tr></table>'
      +'<table class="sum"><tr><th>합계금액</th><td><b>₩ '+_stF(t.total)+'</b> <span>(공급가액 '+_stF(t.supply)+' + 세액 '+_stF(t.tax)+')</span></td></tr></table>'
      +'<table class="it"><thead><tr><th style="width:5%">No</th><th style="width:22%">품목</th><th style="width:24%">규격</th><th style="width:7%">수량</th><th style="width:11%">단가</th><th style="width:12%">공급가액</th><th style="width:10%">세액</th><th>비고</th></tr></thead><tbody>'+rows+'</tbody>'
      +'<tfoot><tr><th colspan="5">합 계</th><td class="r"><b>'+_stF(t.supply)+'</b></td><td class="r"><b>'+_stF(t.tax)+'</b></td><td class="r"><b>'+_stF(t.total)+'</b></td></tr></tfoot></table>'
      +'<div class="ft"><span>'+(d.memo?('비고: '+esc(d.memo)):'')+'</span><span>TEL '+esc(S.tel)+' · FAX '+esc(S.fax)+'</span><span>인수자 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; (인)</span></div></div>'; };
    var two=L.length<=10;
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>거래명세서 '+esc(d.no||'')+' '+esc(d.vname||'')+'</title><style>'
      +'@page{size:A4;margin:9mm}*{box-sizing:border-box}body{margin:0;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;font-size:10.5px;color:#111}'
      +'.doc{padding:2mm 0}.doc+.doc{border-top:1px dashed #999;margin-top:5mm;padding-top:6mm}.ttl{text-align:center;font-size:20px;font-weight:700;letter-spacing:6px}.ttl span{font-size:10.5px;font-weight:400;letter-spacing:0}'
      +'.meta{display:flex;justify-content:space-between;margin:3px 0 4px}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #333;padding:3px 5px;height:19px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}'
      +'th{background:#eef2f7;font-weight:600}.hd th{width:8%}.hd th.v{width:3.2%;padding:2px}.sum{margin-top:-1px}.sum th{width:14%}.sum td{font-size:13px}.sum span{font-size:10px;color:#444}.it{margin-top:-1px}.r{text-align:right}.c{text-align:center}'
      +'.ft{display:flex;justify-content:space-between;margin-top:5px;font-size:10px}@media screen{body{background:#e5e7eb}.page{background:#fff;width:210mm;min-height:290mm;margin:10px auto;padding:9mm}}'
      +'</style></head><body><div class="page">'+one('공급받는자 보관용')+(two?one('공급자 보관용'):'')+'</div></body></html>';
  }
  window.stPrint=async function(){
    var d=_stCollect(); var er=_stCheck(d); if(er){ _st.msg='<span style="color:#dc2626">'+er+'</span>'; renderStmtPage(); return; }
    await stSave(true);
    var w=window.open('', '_blank'); if(!w){ showInfoModal('거래명세서','팝업이 차단되었습니다. 이 사이트의 팝업을 허용해 주세요.'); return; }
    w.document.open(); w.document.write(_stDocHtml(_st.cur)); w.document.close(); setTimeout(function(){ try{ w.focus(); w.print(); }catch(_e){} }, 400); renderStmtPage();
  };
  // ── PDF (pdfmake — 견적서 PDF 와 같은 글꼴) ──
  function _stPdfDoc(d, FONT){
    var S=_stSup(d.branch), t=_stTot(d), L=_stRealLines(d);
    var H=function(x){ return { text:x, bold:true, fillColor:'#eef2f7', alignment:'center' }; }, R=function(x){ return { text:String(x), alignment:'right' }; };
    var body=[[H('No'),H('품목'),H('규격'),H('수량'),H('단가'),H('공급가액'),H('세액'),H('비고')]];
    L.forEach(function(l,i){ var x=_stLine(l); body.push([{text:String(i+1),alignment:'center'}, l.name||'', l.spec||'', R(_stF(l.qty)), R(_stF(l.price)), R(_stF(x.supply)), R(d.taxFree?'0':_stF(x.tax)), l.note||'']); });
    body.push([{text:'합 계',colSpan:5,bold:true,alignment:'center',fillColor:'#eef2f7'},{},{},{},{}, R(_stF(t.supply)), R(_stF(t.tax)), R(_stF(t.total))]);
    var LY={ hLineWidth:function(){ return .6; }, vLineWidth:function(){ return .6; }, hLineColor:function(){ return '#333'; }, vLineColor:function(){ return '#333'; } };
    return { pageSize:'A4', pageMargins:[28,28,28,28], defaultStyle:{ font:FONT, fontSize:8.5, color:'#111' },
      info:{ title:'거래명세서 '+(d.no||'') },
      content:[ { text:'거 래 명 세 서', fontSize:18, bold:true, alignment:'center', characterSpacing:3, margin:[0,0,0,6] },
        { columns:[{ text:'거래일자 '+(d.date||'') }, { text:'No. '+(d.no||''), alignment:'right' }], margin:[0,0,0,4] },
        { table:{ widths:[46,'*',28,56,46,'*',28,56], body:[
          [H('공급자'),{text:_stBiz(S.biz),colSpan:3,bold:true},{},{},H('공급받는자'),{text:_stBiz(d.biz)+(d.sub?(' ('+d.sub+')'):''),colSpan:3,bold:true},{},{}],
          [H('상호'),S.corp,H('성명'),S.ceo,H('상호'),d.vname||'',H('성명'),d.ceo||''],
          [H('주소'),{text:S.addr,colSpan:3},{},{},H('주소'),{text:d.addr||'',colSpan:3},{},{}],
          [H('업태'),S.uptae,H('종목'),S.jongmok,H('업태'),d.uptae||'',H('종목'),d.jongmok||''] ] }, layout:LY },
        { table:{ widths:[70,'*'], body:[[H('합계금액'),{ text:[{text:'₩ '+_stF(t.total),bold:true,fontSize:11},{text:'   (공급가액 '+_stF(t.supply)+' + 세액 '+_stF(t.tax)+')'}] }]] }, layout:LY, margin:[0,-0.6,0,0] },
        { table:{ headerRows:1, widths:[18,'*','*',28,48,56,46,60], body:body }, layout:LY, margin:[0,-0.6,0,0] },
        { columns:[{ text:d.memo?('비고: '+d.memo):'' }, { text:'TEL '+S.tel+' · FAX '+S.fax, alignment:'right' }], margin:[0,5,0,0], fontSize:8 } ] };
  }
  async function _stPdfBlob(d){ var pm=await _ensurePdfMake(); var FONT=await _qPdfFontLoad(pm); var dd=_stPdfDoc(d, FONT); return new Promise(function(res){ pm.createPdf(dd).getBlob(res); }); }
  function _stFileName(d){ return ('거래명세서 '+(d.vname||'')+' '+(d.no||'')).replace(/[<>:"/\\|?*]/g,' ').replace(/\s+/g,' ').trim(); }
  function _stDown(blob, name){ var a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; document.body.appendChild(a); a.click(); setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 800); }
  window.stPdf=async function(){
    var d=_stCollect(); var er=_stCheck(d); if(er){ _st.msg='<span style="color:#dc2626">'+er+'</span>'; renderStmtPage(); return; }
    await stSave(true); _st.msg='PDF 만드는 중…'; renderStmtPage();
    try{ _stDown(await _stPdfBlob(_st.cur), _stFileName(_st.cur)+'.pdf'); _st.msg='<span style="color:#15803d">PDF 를 내려받았습니다.</span>'; }catch(e){ _st.msg='<span style="color:#dc2626">PDF 실패: '+esc(e.message||String(e))+' — [인쇄] 에서 "PDF로 저장"을 쓰세요.</span>'; }
    renderStmtPage();
  };
  // ── 메일 ──
  window.stMailOpen=async function(){
    var d=_stCollect(); var er=_stCheck(d); if(er){ _st.msg='<span style="color:#dc2626">'+er+'</span>'; renderStmtPage(); return; }
    if(!(await stSave(true))) return; d=_st.cur; renderStmtPage();
    var to=[]; try{ to=_mailClientEmails(d.vname,'')||[]; }catch(_e){} if(d.email&&to.indexOf(d.email)<0) to.unshift(d.email);
    var S=_stSup(d.branch), t=_stTot(d);
    var ov=document.getElementById('stMailOv'); if(!ov){ ov=document.createElement('div'); ov.id='stMailOv'; ov.style.cssText='position:fixed;inset:0;z-index:100060;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;padding:16px'; document.body.appendChild(ov); }
    var I='width:100%;box-sizing:border-box;padding:8px 10px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:13px;font-family:inherit';
    ov.innerHTML='<div style="width:100%;max-width:520px;background:#fff;border-radius:14px;box-shadow:0 14px 44px rgba(27,58,107,.22)"><div style="padding:14px 18px;border-bottom:2px solid #1B3A6B;font-size:15px;font-weight:700;color:#1B3A6B">거래명세서 메일 · '+esc(d.vname)+'</div>'
      +'<div style="padding:14px 18px;display:flex;flex-direction:column;gap:9px"><input id="stMlTo" placeholder="받는 사람 (쉼표로 여러 명)" value="'+_stA(to.slice(0,2).join(', '))+'" style="'+I+'">'
      +'<input id="stMlSubj" value="'+_stA('['+S.corp+'] 거래명세서 송부 ('+d.date+')')+'" style="'+I+'">'
      +'<textarea id="stMlBody" rows="8" style="'+I+';resize:vertical">'+esc('안녕하세요, '+S.corp+' 입니다.\n\n'+d.date+' 거래분 거래명세서를 첨부하여 보내드립니다.\n합계금액: '+_stF(t.total)+'원 (공급가액 '+_stF(t.supply)+'원 + 세액 '+_stF(t.tax)+'원)\n\n확인 부탁드립니다.\n감사합니다.\n\n'+S.corp+'\nTEL '+S.tel+' / FAX '+S.fax)+'</textarea>'
      +'<div style="font-size:12px;color:#6b7280">첨부: '+esc(_stFileName(d))+'.pdf</div><div id="stMlSt" style="font-size:12.5px;min-height:18px"></div></div>'
      +'<div style="display:flex;gap:8px;justify-content:flex-end;padding:0 18px 16px"><button class="btn" onclick="document.getElementById(\'stMailOv\').style.display=\'none\'">닫기</button><button class="btn btn-primary" id="stMlBtn" onclick="stMailSend()">보내기</button></div></div>';
    ov.style.display='flex';
  };
  window.stMailSend=async function(){
    var d=_st.cur, st=document.getElementById('stMlSt'), btn=document.getElementById('stMlBtn'); if(!d) return;
    var to=(document.getElementById('stMlTo').value||'').trim(), subj=(document.getElementById('stMlSubj').value||'').trim(), body=document.getElementById('stMlBody').value||'';
    if(!to){ st.innerHTML='<span style="color:#dc2626">받는 사람을 입력하세요.</span>'; return; }
    var bad=to.split(/[,;\s]+/).filter(Boolean).find(function(a){ return !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(a); });
    if(bad){ st.innerHTML='<span style="color:#dc2626">주소 형식이 이상합니다: '+esc(bad)+'</span>'; return; }
    btn.disabled=true; btn.textContent='보내는 중…';
    try{
      var cfg=await _mailLoadCfg(); if(!cfg||!cfg.url||!cfg.key) throw new Error('메일 서버 설정이 없습니다 (견적 메일 설정과 같은 곳)');
      st.textContent='PDF 만드는 중…'; var pb=await _stPdfBlob(d);
      st.textContent='발송 중…';
      var html='<div style="font-family:\'Malgun Gothic\',\'맑은 고딕\',sans-serif;font-size:14px;line-height:1.7;color:#1f2937;white-space:pre-wrap">'+esc(body)+'</div>';
      var r=await fetch(_mailUrl(cfg,'/send'), {method:'POST', headers:{'Content-Type':'application/json','X-Mail-Key':cfg.key}, body:JSON.stringify({account:_mailAcctOf(d.branch), to:to, subject:subj, text:body, html:html, fromName:_stSup(d.branch).corp, attachments:[{name:_stFileName(d)+'.pdf', type:'application/pdf', b64:await _blobToB64(pb)}]})});
      var j=null; try{ j=await r.json(); }catch(_j){}
      if(!r.ok||!j||!j.ok) throw new Error((j&&j.error)||('HTTP '+r.status));
      d.mails=(d.mails||[]).concat([{at:Date.now(), to:to, by:(_authUser&&_authUser.name)||''}]); await stSave(true);
      document.getElementById('stMailOv').style.display='none'; _st.msg='<span style="color:#15803d">메일을 보냈습니다 → '+esc(to)+'</span>'; renderStmtPage();
    }catch(e){ st.innerHTML='<span style="color:#dc2626">발송 실패: '+esc(e&&e.message||String(e))+'</span>'; }
    finally{ btn.disabled=false; btn.textContent='보내기'; }
  };
  // ── 홈택스 전자세금계산서 일괄발급 엑셀 (무료 — 홈택스에 올려 인증서로 발급) ──
  function _stHtRow(d){
    var S=_stSup(d.branch), t=_stTot(d), L=_stRealLines(d), dt=String(d.date||'').replace(/-/g,''), dd=dt.slice(6,8);
    var row=[ d.taxFree?'02':'01', dt, S.biz, '', S.corp, S.ceo, S.addr, S.uptae, S.jongmok, S.mail,
      String(d.biz||''), String(d.sub||''), d.vname||'', d.ceo||'', d.addr||'', d.uptae||'', d.jongmok||'', d.email||'', '', t.supply, t.tax, d.memo||'' ];
    var items;
    if(L.length<=4) items=L.map(function(l){ var x=_stLine(l); return [dd, l.name||l.spec||'', l.name?(l.spec||''):'', _stN(l.qty), _stN(l.price), x.supply, d.taxFree?0:x.tax, l.note||'']; });
    else items=[[dd, (L[0].name||L[0].spec||'품목')+' 외 '+(L.length-1)+'건', '', '', '', t.supply, t.tax, '']];   // 홈택스는 계산서 1장에 품목 4줄까지 → 5줄 이상은 '외 N건' 한 줄
    if(items.length){ var ds=0, dx=0; items.forEach(function(it){ ds+=it[5]; dx+=it[6]; }); items[items.length-1][6]+= (t.tax-dx); }   // 품목 세액 합 = 머리 세액
    for(var i=0;i<4;i++){ row=row.concat(items[i]||['','','','','','','','']); }
    return row.concat(['','','','', (d.claim==='01')?'01':'02']);
  }
  var _ST_HT_HEAD=['전자(세금)계산서 종류\n(01:일반, 02:영세율)','작성일자','공급자 등록번호\n("-" 없이 입력)','공급자\n종사업장번호','공급자 상호','공급자 성명','공급자 사업장주소','공급자 업태','공급자 종목','공급자 이메일',
    '공급받는자 등록번호\n("-" 없이 입력)','공급받는자\n종사업장번호','공급받는자 상호','공급받는자 성명','공급받는자 사업장주소','공급받는자 업태','공급받는자 종목','공급받는자 이메일1','공급받는자 이메일2','공급가액','세액','비고']
    .concat([1,2,3,4].reduce(function(a,n){ return a.concat(['일자'+n+'\n(2자리, 작성년월 제외)','품목'+n,'규격'+n,'수량'+n,'단가'+n,'공급가액'+n,'세액'+n,'품목비고'+n]); },[]))
    .concat(['현금','수표','어음','외상미수금','영수(01),\n청구(02)']);
  function _stHtProblems(d){ var p=[]; if(String(d.biz||'').replace(/\D/g,'').length!==10) p.push('사업자번호'); if(!d.ceo) p.push('대표자'); if(!d.vname) p.push('상호'); if(!_stTot(d).supply) p.push('금액'); return p; }
  window.stHtExport=async function(){
    if(typeof _guardW==='function' && !_guardW()) return;
    var ids=Object.keys(_st.sel).filter(function(k){ return _st.sel[k]; }); var L=(_st.list||[]).filter(function(x){ return ids.indexOf(x.id)>=0; });
    if(!L.length){ showInfoModal('세금계산서','목록에서 세금계산서를 발행할 거래명세서를 체크해 주세요.'); return; }
    if(L.length>100){ showInfoModal('세금계산서','홈택스 일괄발급은 한 번에 100건까지입니다. 나누어 주세요.'); return; }
    var brs={}; L.forEach(function(x){ brs[x.branch==='화성'?'화성':'서울']=1; });
    if(Object.keys(brs).length>1){ showInfoModal('세금계산서','서울과 화성은 사업자가 달라 한 파일에 섞을 수 없습니다. 지점별로 따로 만들어 주세요.'); return; }
    var bad=L.map(function(x){ var p=_stHtProblems(x); return p.length?((x.no||'')+' '+(x.vname||'')+' — '+p.join('·')+' 없음'):''; }).filter(Boolean);
    if(bad.length){ showInfoModal('세금계산서 — 빠진 정보', '아래 명세서는 필수 정보가 없어 홈택스에서 오류가 납니다. 명세서를 열어 채워 주세요.\n\n'+bad.join('\n')); return; }
    var dup=L.filter(function(x){ return x.tax&&x.tax.st; });
    if(dup.length && !confirm('이미 엑셀을 만들었거나 발행 완료로 표시된 명세서가 '+dup.length+'건 있습니다. 중복 발행에 주의하세요. 계속할까요?')) return;
    try{
      await _ensureXlsxLib();
      var aoa=[['엑셀 업로드 양식(전자세금계산서-일반(영세율))'],['★ 홈택스 > 전자(세금)계산서 > 일괄발급 에 올리는 자료입니다. 7행부터 1줄 = 계산서 1장.'],['★ 충해전기 사내전산 거래명세서에서 만든 파일 · '+Object.keys(brs)[0]+' · '+L.length+'건'],[],[],_ST_HT_HEAD];
      L.sort(function(a,b){ return String(a.date).localeCompare(String(b.date))||String(a.no).localeCompare(String(b.no)); }).forEach(function(x){ aoa.push(_stHtRow(x)); });
      var ws=XLSX.utils.aoa_to_sheet(aoa);
      for(var r=6;r<aoa.length;r++){ [1,2,3,10,11].forEach(function(c){ var a=XLSX.utils.encode_cell({r:r,c:c}); if(ws[a]){ ws[a].t='s'; ws[a].v=String(ws[a].v); ws[a].z='@'; } }); var a0=XLSX.utils.encode_cell({r:r,c:0}), a1=XLSX.utils.encode_cell({r:r,c:58}); [a0,a1].forEach(function(a){ if(ws[a]){ ws[a].t='s'; ws[a].z='@'; } }); }
      ws['!cols']=_ST_HT_HEAD.map(function(h,i){ return { wch:(i===6||i===14)?34:(i===4||i===12)?20:13 }; });
      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, '엑셀업로드양식');
      var arr=XLSX.write(wb, {type:'array', bookType:'xls'});
      _stDown(new Blob([arr],{type:'application/vnd.ms-excel'}), '홈택스_세금계산서_'+Object.keys(brs)[0]+'_'+_stToday().replace(/-/g,'')+'_'+L.length+'건.xls');
      var now=Date.now(), who=(_authUser&&_authUser.name)||'';
      for(var i=0;i<L.length;i++){ var x=L[i]; if(!(x.tax&&x.tax.st==='issued')){ x.tax={ st:'exported', at:now, by:who }; try{ await _fbPutOk(_stUrl(x.id), x, '거래명세서'); }catch(_e){} } }
      _st.sel={}; _st.msg='<span style="color:#15803d">홈택스 일괄발급 엑셀을 내려받았습니다 ('+L.length+'건).</span> 홈택스에서 발급을 마친 뒤 [발행 완료]를 눌러 표시해 주세요.'; renderStmtPage();
    }catch(e){ showInfoModal('세금계산서 엑셀 실패', (e&&e.message)||String(e)); }
  };
  window.stTaxMark=async function(id, st){
    if(typeof _guardW==='function' && !_guardW()) return;
    var x=(_st.list||[]).find(function(s){ return s.id===id; }); if(!x) return;
    if(st==='issued'){ var n=prompt('홈택스 승인번호 (없으면 비워 두고 확인)', (x.tax&&x.tax.nts)||''); if(n===null) return; x.tax={ st:'issued', at:Date.now(), by:(_authUser&&_authUser.name)||'', nts:String(n).trim() }; }
    else x.tax=null;
    try{ await _fbPutOk(_stUrl(id), x, '거래명세서'); }catch(e){ showInfoModal('거래명세서', e.message||String(e)); }
    renderStmtPage();
  };
  window.stSel=function(id, v){ _st.sel[id]=!!v; var n=Object.keys(_st.sel).filter(function(k){ return _st.sel[k]; }).length; var b=document.getElementById('stHtBtn'); if(b) b.textContent='홈택스 세금계산서 엑셀'+(n?(' ('+n+'건)'):''); };
  window.stSelAll=function(v){ _stListView().forEach(function(x){ if(!(x.tax&&x.tax.st==='issued')) _st.sel[x.id]=!!v; }); renderStmtPage(); };
  window.stSearch=function(v){ _st.q=String(v||''); renderStmtPage(); var el=document.getElementById('stQ'); if(el){ el.focus(); try{ el.setSelectionRange(el.value.length, el.value.length); }catch(_e){} } };
  window.stHtHelp=function(){ showInfoModal('홈택스 세금계산서 발급 순서 (무료)', '1) 이 목록에서 발행할 거래명세서를 체크 → [홈택스 세금계산서 엑셀]\n2) 홈택스 로그인(공동인증서) → 전자(세금)계산서 → 발급 → 일괄발급\n3) [찾아보기]로 내려받은 엑셀 선택 → [엑셀파일 변환] → 오류 없으면 [일괄발급]\n4) 인증서 암호 입력 → 발급 완료 (공급받는자 메일로 자동 전송)\n5) 사내전산 목록에서 [발행 완료] 를 눌러 표시\n\n· 한 번에 100건까지, 계산서 1장에 품목 4줄까지 (5줄 이상은 "○○ 외 N건" 한 줄로 들어갑니다)\n· 서울·화성은 사업자가 달라 파일을 따로 만듭니다\n· 홈택스에서 양식 오류가 나면 홈택스의 [양식 내려받기] 파일을 알려 주세요 — 그 양식에 맞춰 조정합니다'); };
  function _stListView(){ var ql=String(_st.q||'').toLowerCase().replace(/\s+/g,''); return (_st.list||[]).filter(function(x){ if(!ql) return true; return (String(x.vname||'')+String(x.no||'')+String(x.date||'')).toLowerCase().replace(/\s+/g,'').indexOf(ql)>=0; }).sort(function(a,b){ return String(b.date).localeCompare(String(a.date))||((b.upd||0)-(a.upd||0)); }); }
  function _stTotHtml(t){ return '공급가액 <b>'+_stF(t.supply)+'</b> · 세액 <b>'+_stF(t.tax)+'</b> · 합계 <b style="font-size:16px;color:#1B3A6B">'+_stF(t.total)+'</b>원'; }
  function _stTaxBadge(x){ var t=x.tax; if(t&&t.st==='issued') return '<span style="padding:2px 8px;border-radius:999px;background:#dcfce7;color:#15803d;font-weight:700" title="'+_stA(t.nts||'')+'">발행 완료</span>'; if(t&&t.st==='exported') return '<span style="padding:2px 8px;border-radius:999px;background:#fef3c7;color:#b45309;font-weight:700">엑셀 만듦</span>'; return '<span style="color:#9ca3af">미발행</span>'; }
  window.renderStmtPage=function(){
    var pg=document.getElementById('pageStmt'); if(!pg) return;
    if(!_st.list){ pg.innerHTML='<div style="padding:30px;text-align:center;color:#9ca3af">불러오는 중…</div>'; _stLoad().then(function(){ if(!_st.list) _st.list=[]; renderStmtPage(); }); return; }
    var I='box-sizing:border-box;padding:7px 9px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:12.5px;font-family:inherit';
    var CARD='background:#fff;border:1px solid #e5eaf1;border-radius:12px;padding:14px 16px;margin-bottom:14px';
    var msg=_st.msg?'<div style="margin:0 0 10px;font-size:12.5px">'+_st.msg+'</div>':'';
    if(!_st.cur){   // ── 목록 ──
      var L=_stListView(), nSel=Object.keys(_st.sel).filter(function(k){ return _st.sel[k]; }).length;
      var rows=L.slice(0,200).map(function(x){ var iss=x.tax&&x.tax.st==='issued';
        return '<tr style="border-top:1px solid #eef2f7"><td style="padding:7px 6px;text-align:center"><input type="checkbox" '+(_st.sel[x.id]?'checked':'')+' onchange="stSel(\''+x.id+'\',this.checked)"></td>'
          +'<td style="padding:7px 8px;white-space:nowrap">'+esc(x.date||'')+'</td><td style="padding:7px 8px;white-space:nowrap;color:#6b7280">'+esc(x.no||'')+'</td>'
          +'<td style="padding:7px 8px;font-weight:700;color:#14305c"><a href="javascript:;" onclick="stOpen(\''+x.id+'\')" style="color:inherit;text-decoration:none">'+esc(x.vname||'')+'</a> <span style="font-size:11px;font-weight:400;color:#6b7280">'+esc(x.branch||'')+'</span></td>'
          +'<td style="padding:7px 8px;color:#374151">'+esc(((x.lines||[])[0]||{}).name||((x.lines||[])[0]||{}).spec||'')+((x.lines||[]).length>1?(' 외 '+((x.lines||[]).length-1)+'건'):'')+'</td>'
          +'<td style="padding:7px 8px;text-align:right">'+_stF(x.supply)+'</td><td style="padding:7px 8px;text-align:right;font-weight:700">'+_stF(x.total)+'</td>'
          +'<td style="padding:7px 8px;font-size:11.5px;white-space:nowrap">'+_stTaxBadge(x)+'</td><td style="padding:7px 8px;color:#6b7280">'+esc(x.by||'')+'</td>'
          +'<td style="padding:7px 6px;white-space:nowrap"><button class="btn" style="padding:3px 9px" onclick="stOpen(\''+x.id+'\')">열기</button> <button class="btn" style="padding:3px 9px" onclick="stCopy(\''+x.id+'\')">복사</button> '
          +(iss?'<button class="btn" style="padding:3px 9px" onclick="stTaxMark(\''+x.id+'\',\'\')">발행 취소 표시</button>':'<button class="btn" style="padding:3px 9px;color:#15803d;border-color:#bbf7d0" onclick="stTaxMark(\''+x.id+'\',\'issued\')">발행 완료</button> <button class="btn" style="padding:3px 9px;color:#dc2626;border-color:#fecaca" onclick="stDelete(\''+x.id+'\')">삭제</button>')+'</td></tr>'; }).join('');
      pg.innerHTML='<div style="max-width:1280px;margin:0 auto;padding:4px 2px">'
        +'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px"><div style="font-size:18px;font-weight:800;color:#14305c">거래명세서</div>'
        +'<input id="stQ" value="'+_stA(_st.q)+'" placeholder="업체명·번호·날짜 검색" oninput="stSearch(this.value)" style="'+I+';width:220px"><span style="flex:1"></span>'
        +'<button class="btn" id="stHtBtn" onclick="stHtExport()" style="color:#0f766e;border-color:#99f6e4;font-weight:700">홈택스 세금계산서 엑셀'+(nSel?(' ('+nSel+'건)'):'')+'</button><button class="btn" onclick="stHtHelp()" title="홈택스 발급 순서">?</button>'
        +'<button class="btn btn-primary" onclick="stNew()">+ 새 거래명세서</button></div>'+msg
        +'<div style="'+CARD+';padding:0;overflow:auto">'+(L.length?('<table style="width:100%;border-collapse:collapse;font-size:12.5px;min-width:900px"><thead><tr style="background:#f6f8fb;color:#14305c;font-size:11.5px;text-align:left"><th style="padding:8px 6px;width:30px;text-align:center"><input type="checkbox" onchange="stSelAll(this.checked)" title="미발행 전체 선택"></th><th style="padding:8px">거래일자</th><th style="padding:8px">번호</th><th style="padding:8px">업체</th><th style="padding:8px">품목</th><th style="padding:8px;text-align:right">공급가액</th><th style="padding:8px;text-align:right">합계</th><th style="padding:8px">세금계산서</th><th style="padding:8px">작성</th><th></th></tr></thead><tbody>'+rows+'</tbody></table>')
          :'<div style="padding:34px;text-align:center;color:#9ca3af;font-size:13px">'+(_st.q?'검색 결과가 없습니다.':'아직 거래명세서가 없습니다. [+ 새 거래명세서] 로 시작하세요.')+'</div>')+'</div>'
        +'<div style="font-size:11.5px;color:#6b7280">세금계산서: 발행할 명세서를 체크 → [홈택스 세금계산서 엑셀] → 홈택스 일괄발급에 올려 발급 (수수료 없음). 순서는 [?] 참고.</div></div>';
      return;
    }
    // ── 작성 화면 ──
    var d=_st.cur, t=_stTot(d), S=_stSup(d.branch), lock=!!(d.tax&&d.tax.st==='issued');
    var cl=''; try{ cl=allClients().slice(0,4000).map(function(c){ return '<option value="'+_stA(c[0])+'">'; }).join(''); }catch(_e){}
    var F=function(lb, f, v, w, ph){ return '<label style="display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:#6b7280;'+(w||'flex:1 1 150px')+'">'+lb+'<input data-sf="'+f+'" value="'+_stA(v)+'" placeholder="'+(ph||'')+'" style="'+I+';width:100%"></label>'; };
    var lrows=d.lines.map(function(l,k){ var x=_stLine(l);
      return '<tr data-sl="'+k+'" style="border-top:1px solid #eef2f7"><td style="padding:5px 4px;text-align:center;color:#9ca3af">'+(k+1)+'</td>'
        +'<td style="padding:5px 4px"><input data-lf="name" value="'+_stA(l.name)+'" placeholder="품목" style="'+I+';width:100%"></td>'
        +'<td style="padding:5px 4px"><input data-lf="spec" value="'+_stA(l.spec)+'" placeholder="규격·품번" style="'+I+';width:100%"></td>'
        +'<td style="padding:5px 4px"><input data-lf="qty" inputmode="numeric" value="'+_stA(l.qty)+'" oninput="stRecalc()" style="'+I+';width:100%;text-align:right"></td>'
        +'<td style="padding:5px 4px"><input data-lf="price" inputmode="numeric" value="'+_stA(l.price)+'" oninput="stRecalc()" style="'+I+';width:100%;text-align:right"></td>'
        +'<td class="st-sup" style="padding:5px 8px;text-align:right;white-space:nowrap">'+_stF(x.supply)+'</td><td class="st-tax" style="padding:5px 8px;text-align:right;white-space:nowrap;color:#6b7280">'+(d.taxFree?'0':_stF(x.tax))+'</td>'
        +'<td style="padding:5px 4px"><input data-lf="note" value="'+_stA(l.note)+'" style="'+I+';width:100%"></td>'
        +'<td style="padding:5px 4px;text-align:center"><button class="btn" onclick="stDelLine('+k+')" title="이 줄 빼기" style="padding:2px 8px;color:#dc2626;border-color:#fecaca">×</button></td></tr>'; }).join('');
    var qbox='';
    if(_st.quotes){ var ql=String(d.vname||'').toLowerCase().replace(/\s+/g,'');
      var Q=_poQuotes().filter(function(x){ return !ql||String(x.vname||'').toLowerCase().replace(/\s+/g,'').indexOf(ql)>=0; }).sort(function(a,b){ return (b.upd||b.savedAt||0)-(a.upd||a.savedAt||0); }).slice(0,15);
      qbox='<div style="border:1px solid #d6e0ec;border-radius:9px;margin:0 0 10px;max-height:230px;overflow:auto">'+(Q.length?('<table style="width:100%;border-collapse:collapse;font-size:12.5px">'+Q.map(function(x){ return '<tr style="border-top:1px solid #eef2f7"><td style="padding:6px 8px;white-space:nowrap">'+esc(_poYmd(x.upd||x.savedAt))+'</td><td style="padding:6px 8px;font-weight:700">'+esc(x.vname||'')+'</td><td style="padding:6px 8px;color:#6b7280">'+esc(x.title||'')+'</td><td style="padding:6px 8px;text-align:right"><button class="btn" style="padding:3px 10px" onclick="stLoadQuote(\''+x.id+'\')">불러오기</button></td></tr>'; }).join('')+'</table>'):'<div style="padding:14px;text-align:center;color:#9ca3af;font-size:12.5px">'+(d.vname?('"'+esc(d.vname)+'" 의 저장 견적이 없습니다.'):'저장된 견적이 없습니다.')+'</div>')+'</div>'; }
    pg.innerHTML='<div style="max-width:1180px;margin:0 auto;padding:4px 2px"><datalist id="stClients">'+cl+'</datalist>'
      +'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px"><button class="btn" onclick="stBack()">← 목록</button><div style="font-size:18px;font-weight:800;color:#14305c">'+(d.id?('거래명세서 '+esc(d.no||'')):'새 거래명세서')+'</div>'+(d.tax?_stTaxBadge(d):'')
      +'<span style="flex:1"></span><button class="btn" onclick="stPrint()">인쇄</button><button class="btn" onclick="stPdf()">PDF</button><button class="btn" onclick="stMailOpen()">메일</button><button class="btn btn-primary" onclick="stSave()">저장</button></div>'+msg
      +(lock?'<div style="margin:0 0 10px;padding:8px 12px;border-radius:9px;background:#fef3c7;color:#92400e;font-size:12.5px">세금계산서 발행 완료로 표시된 명세서입니다. 내용을 고치면 발행한 계산서와 달라집니다.</div>':'')
      +'<div style="'+CARD+'"><div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">'
        +'<label style="display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:#6b7280;flex:0 0 150px">거래일자<input type="date" data-sf="date" value="'+_stA(d.date)+'" style="'+I+'"></label>'
        +'<label style="display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:#6b7280;flex:0 0 110px">공급자(지점)<select onchange="stBranchSet(this.value)" style="'+I+'"><option'+(d.branch!=='화성'?' selected':'')+'>서울</option><option'+(d.branch==='화성'?' selected':'')+'>화성</option></select></label>'
        +'<label style="display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:#6b7280;flex:2 1 240px">업체명 <span style="color:#9ca3af">— 고르면 사업자 정보가 채워집니다</span><input data-sf="vname" list="stClients" value="'+_stA(d.vname)+'" onchange="stVendorPick(this.value)" placeholder="업체명 입력/선택" style="'+I+';width:100%;font-weight:700"></label>'
        +F('사업자번호','biz',_stBiz(d.biz),'flex:0 0 140px','000-00-00000')+F('종사업장','sub',d.sub,'flex:0 0 80px')+F('대표자','ceo',d.ceo,'flex:0 0 110px')
        +'</div><div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:9px">'+F('주소','addr',d.addr,'flex:3 1 300px')+F('업태','uptae',d.uptae,'flex:1 1 110px')+F('종목','jongmok',d.jongmok,'flex:1 1 110px')+F('세금계산서 메일','email',d.email,'flex:1 1 190px')+'</div>'
        +'<div style="margin-top:8px;font-size:11.5px;color:#6b7280">공급자: '+esc(S.corp)+' · '+esc(_stBiz(S.biz))+' · '+esc(S.ceo)+'</div></div>'
      +'<div style="'+CARD+'"><div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><div style="font-size:14px;font-weight:700;color:#14305c">품목</div>'+(d.qno?'<span style="font-size:11.5px;color:#6b7280">견적 '+esc(d.qno)+'</span>':'')+'<span style="flex:1"></span><button class="btn" onclick="stQuotesToggle()">'+(_st.quotes?'견적 목록 닫기':'견적에서 불러오기')+'</button><button class="btn" onclick="stAddLine()">+ 줄 추가</button></div>'+qbox
        +'<div style="overflow:auto;border:1px solid #eef2f7;border-radius:9px"><table style="width:100%;border-collapse:collapse;font-size:12.5px;min-width:820px"><thead><tr style="background:#f6f8fb;color:#14305c;font-size:11.5px"><th style="padding:7px 4px;width:30px">No</th><th style="padding:7px 6px;text-align:left;width:22%">품목</th><th style="padding:7px 6px;text-align:left;width:24%">규격</th><th style="padding:7px 6px;width:70px">수량</th><th style="padding:7px 6px;width:110px">단가</th><th style="padding:7px 8px;text-align:right">공급가액</th><th style="padding:7px 8px;text-align:right">세액</th><th style="padding:7px 6px;text-align:left">비고</th><th style="width:36px"></th></tr></thead><tbody>'+lrows+'</tbody></table></div>'
        +'<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:10px"><label style="font-size:12px;color:#374151;display:flex;align-items:center;gap:5px"><input type="checkbox" data-sf="taxFree" '+(d.taxFree?'checked':'')+' onchange="stRecalc()">영세율(세액 0)</label>'
        +'<label style="font-size:12px;color:#374151;display:flex;align-items:center;gap:5px">계산서 <select data-sf="claim" style="'+I+';padding:4px 6px"><option value="02"'+(d.claim!=='01'?' selected':'')+'>청구</option><option value="01"'+(d.claim==='01'?' selected':'')+'>영수</option></select></label>'
        +'<span style="flex:1"></span><div id="stTotBox" style="font-size:13px;color:#14305c">'+_stTotHtml(t)+'</div></div>'
        +'<div style="margin-top:10px"><input data-sf="memo" value="'+_stA(d.memo)+'" placeholder="비고 (명세서·세금계산서 비고란에 들어갑니다)" style="'+I+';width:100%"></div></div></div>';
  };
