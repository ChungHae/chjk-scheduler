# -*- coding: utf-8 -*-
# r233 (사용자 요청 2026-10-14): 견적서 HTML 내보내기 — 도면·카탈로그 연동
#   견적 다운로드 창에 [HTML 견적서] 추가. 파일 하나(.html)로 저장돼 카톡·메일로 보내면 받는 쪽이 클릭만 하면 된다.
#   구성(첨부 참고 견적서 HINTER-20261008 를 따름): 레터헤드 · 제목 · 수신 카드 + 견적금액 카드 · 품목표(No·품번/품목명·메이커·수량·자료·단가·금액)
#   · 합계 · 확인 사항(기본 문구) · 공급자(명판·인감 = Firebase sched_doc_assets) · 꼬리말.
#   자료 아이콘: SMC → smcworld 웹카탈로그 제품 페이지(사양·2D/3D CAD) + 품번조회 / CONVUM → 도면 DB(썸네일·제품 PDF·2D·3D, 파일 안 JS 가 열 때 조회)
#   + 시리즈 PDF · 전체 카탈로그 / 그 외 → 검색. 모든 줄에 [품번 복사].
#   품목 설명은 원장 품목명 한 줄만 (사양 해설·카탈로그 발췌는 넣지 않는다 — 품번이 많으면 감당 안 됨, 사용자 결정).
import io, sys, json

MENU_OLD = """          +'<button onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; qExportHitpan();" style="\'+_DLB+\'" onmouseover="this.style.background=\\'#f6f8fa\\'" onmouseout="this.style.background=\\'#fff\\'">히트판 엑셀</button>'
          +'</div></div>'
      +'</div></div>';"""
MENU_NEW = """          +'<button onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; qExportHitpan();" style="\'+_DLB+\'" onmouseover="this.style.background=\\'#f6f8fa\\'" onmouseout="this.style.background=\\'#fff\\'">히트판 엑셀</button>'
          +'</div></div>'
        +'<div><div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:9px">HTML 견적서 <span style="font-weight:500;color:#9ca3af;font-size:11px">· 도면·카탈로그 링크 포함 · 카톡/메일로 그대로 전달</span></div>'
          +'<div style="display:flex;gap:8px">'
          +'<button onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; qExportHtml();" style="\'+_DLB+\'" onmouseover="this.style.background=\\'#f6f8fa\\'" onmouseout="this.style.background=\\'#fff\\'">HTML 견적서</button>'
          +'</div></div>'
      +'</div></div>';"""

JS = r"""  // ─── r233: HTML 견적서 (도면·카탈로그 연동) ───
  var _QH_CV_API='https://rjilxlopauzwzwqmdcre.supabase.co', _QH_CV_KEY='sb_publishable_i3pCGKzhZigmcdzMLG5T4w_WytHiH1-';
  var _QH_CV_STORE=_QH_CV_API+'/storage/v1/object/public/';
  var _QH_CV_PDF_MAIN=_QH_CV_STORE+'catalogs/pdfs/1775023892314_PRODCUT_SELETION_2026_260211_____.pdf';
  var _QH_CV_PDF_SER={ 'CVD':'catalogs/pdfs/1775023871808_24_29_BCVZ.pdf','CVL':'catalogs/pdfs/1775023871808_24_29_BCVZ.pdf','CVG':'catalogs/pdfs/1775023871808_24_29_BCVZ.pdf','CVZ':'catalogs/pdfs/1775023871808_24_29_BCVZ.pdf','MC':'catalogs/pdfs/1775023872882_30_35_BMC22.pdf','MPV':'catalogs/pdfs/1775023551677_BMPV42.pdf' };
  function _qhMakerOf(c){
    var mk=String((c&&c.info&&c.info.maker)||'').trim();
    var key=_qNorm(c&&c.spec);
    if(!mk && key && typeof _qPriceIdx!=='undefined' && _qPriceIdx && _qPriceIdx[key]) mk=String(_qPriceIdx[key].maker||'').trim();
    if(!mk && typeof _qIsSmc==='function' && _qIsSmc(c, key)) mk='SMC';
    var up=mk.toUpperCase();
    var cls=/SMC/.test(up)?'SMC':(/CONVUM|컨범|콘범/.test(up)?'CONVUM':(/NITTA|닛다|니타/.test(up)?'NITTA':(/CDC/.test(up)?'CDC':'')));
    return {name:mk, cls:cls};
  }
  function _qhCvSeries(spec){ var core=String(spec||'').toUpperCase().replace(/^B/,''), best='', ser=null; for(var k in _QH_CV_PDF_SER){ if(core.indexOf(k)===0 && k.length>best.length){ best=k; ser=_QH_CV_PDF_SER[k]; } } return ser?{key:best, url:_QH_CV_STORE+ser}:null; }
  function _qhLinks(c, mk){
    var pn=String(c.spec||'').trim(), q=encodeURIComponent(pn), a=[];
    var A=function(href,label,title,cls){ return '<a class="ql'+(cls?' '+cls:'')+'" href="'+esc(href)+'" target="_blank" rel="noopener" title="'+esc(title||label)+'">'+esc(label)+'</a>'; };
    if(!pn) return '';
    if(mk.cls==='SMC'){
      a.push(A('https://www.smcworld.com/webcatalog/ko-jp/detail/?partNumber='+q,'카탈로그','SMC 웹카탈로그 — 사양·치수·2D/3D CAD'));
      a.push(A('https://www.smcworld.com/webcatalog/ko-jp/detail/?partNumber='+q,'2D/3D','SMC 웹카탈로그 제품 페이지에서 CAD 내려받기','cad'));
    } else if(mk.cls==='CONVUM'){
      var ser=_qhCvSeries(pn);
      a.push('<span class="qcv" data-pn="'+esc(pn)+'"></span>');
      if(ser) a.push(A(ser.url, ser.key+' PDF','CONVUM '+ser.key+' 시리즈 카탈로그'));
      a.push(A(_QH_CV_PDF_MAIN,'전체 카탈로그','CONVUM 제품 선정 카탈로그'));
    } else {
      a.push(A('https://www.google.com/search?q='+q+(mk.name?'+'+encodeURIComponent(mk.name):'')+'+%EC%B9%B4%ED%83%88%EB%A1%9C%EA%B7%B8','검색',(mk.name||'')+' '+pn+' 카탈로그 검색'));
    }
    a.push('<button type="button" class="ql cp" data-pn="'+esc(pn)+'" title="품번 복사">복사</button>');
    return a.join('');
  }
  async function _qBuildQuoteHtml(){
    if(typeof _qPriceIdx!=='undefined' && !_qPriceIdx && typeof _qBuildPriceIdx==='function'){ try{ await _qBuildPriceIdx(); }catch(_e){} }
    var vname=_qCart[0].vname||'';
    var _mgEl=document.getElementById('qManager'); var _mgr=(_mgEl&&!_mgEl.disabled&&_mgEl.value)?String(_mgEl.value).trim():'';
    var _qm=String(_qQuoteNo||'').match(/(\d{8})/); var d=_qm?new Date(Number(_qm[1].slice(0,4)), Number(_qm[1].slice(4,6))-1, Number(_qm[1].slice(6,8))):new Date();
    var ds=d.getFullYear()+'. '+String(d.getMonth()+1).padStart(2,'0')+'. '+String(d.getDate()).padStart(2,'0');
    var staff=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)?_authUser.name:'';
    var _me=(typeof members!=='undefined'&&members)?members.find(function(x){return (x.name||'').trim()===staff;}):null;
    var _branch=(_me&&_me.group)?_me.group:'서울';
    var _phMap={'김해식':'010-3723-5583'};
    var staffPhone=(_me&&_me.phone)?_me.phone:(_phMap[staff]||'');
    var SUP=_qSupplierInfo(_branch);
    var assets={}; try{ assets=(await _nyLoadAssets())||{}; }catch(_e){ assets={}; }
    var st=assets['stamp_'+_branch]||null, sl=assets.seal||null;
    var fmt=function(n){ return Math.round(Number(n)).toLocaleString(); };
    var _cxCols=((typeof _qCols!=='undefined'&&_qCols)?_qCols:[]).map(function(c){ var p=c.pos||'amt'; return (p==='e'||p==='dc'||p==='small'||p==='buy'||p==='margin')?{id:c.id,title:c.title,pos:'spec'}:c; });
    var hasEta=_qCart.some(function(c){ return c.eta&&String(c.eta).trim(); });
    var supply=0, qtySum=0, makers={}, hasCv=false, rows='';
    _qCart.forEach(function(c,i){
      var qty=Number(c.qty)||1; var _hasSpec=(c.spec!=null&&String(c.spec).trim()!=='');
      var unit=(c.sell!=null&&c.sell!=='')?Number(c.sell):null;
      var amt=unit!=null?unit*qty:null; if(amt!=null) supply+=amt; if(_hasSpec) qtySum+=qty;
      var mk=_qhMakerOf(c); if(mk.name) makers[mk.name]=1; if(mk.cls==='CONVUM') hasCv=true;
      var _dc=(unit==null&&c.disc!=null&&String(c.disc).trim()!=='')?'<span class="dc">'+esc(_qDiscLabel(c.disc))+'</span>':'';
      var cx=_cxCols.map(function(x){ var v=(c.cx&&c.cx[x.id]!=null)?String(c.cx[x.id]).trim():''; return v?'<span class="cx">'+esc(x.title)+' '+esc(v)+'</span>':''; }).join('');
      rows+='<tr><td class="c no">'+(i+1)+'</td>'
        +'<td class="pn"><div class="pnrow"><span class="thumb" data-pn="'+esc(c.spec||'')+'"></span><div><b>'+esc(c.spec||'')+'</b>'+(c.name?'<div class="nm">'+esc(c.name)+'</div>':'')+(cx?'<div class="cxs">'+cx+'</div>':'')+'</div></div></td>'
        +'<td class="c"><span class="mk '+esc(mk.cls||'x')+'">'+esc(mk.name||'-')+'</span></td>'
        +'<td class="r">'+(_hasSpec?qty.toLocaleString()+' <small>EA</small>':'')+'</td>'
        +'<td class="c links">'+_qhLinks(c, mk)+'</td>'
        +'<td class="r">'+(unit!=null?fmt(unit):'')+'</td>'
        +'<td class="r amt">'+(amt!=null?fmt(amt):_dc)+'</td>'
        +(hasEta?'<td class="c eta">'+esc(c.eta||'')+'</td>':'')+'</tr>';
    });
    var _nego=(typeof _qNego!=='undefined'&&_qNego!=null)?Number(_qNego):0;
    if(_nego) rows+='<tr class="nego"><td></td><td>NEGO 할인</td><td></td><td></td><td></td><td></td><td class="r amt">- '+fmt(_nego)+'</td>'+(hasEta?'<td></td>':'')+'</tr>';
    var finalSupply=supply-_nego, vat=Math.round(finalSupply*0.1), total=finalSupply+vat;
    var mkList=Object.keys(makers); var head=(mkList.length?mkList.join(' · ')+' ':'')+_qCart.length+'품목';
    var notes=[
      '상기 금액은 <b>부가가치세 별도</b>이며, 합계 수량 <b>'+qtySum.toLocaleString()+' EA</b> 기준입니다.',
      '유효기간은 발행일로부터 <b>30일</b>입니다. 납기는 발주 확정 후 안내드리며, 결제 조건은 협의에 따릅니다.',
      '품목표의 <b>자료</b> 칸을 누르면 메이커 카탈로그·제품 페이지·2D/3D 도면으로 바로 연결됩니다. (인터넷 연결 필요)',
      '표기 품번 외 옵션(오토스위치·포트 나사·스트로크 등) 변경이 필요하시면 알려주십시오. 추가 견적드리겠습니다.'
    ];
    var CSS='*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#1f2937;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;font-size:13px;line-height:1.5}'
      +'.pg{max-width:860px;margin:18px auto;background:#fff;padding:36px 40px 30px;box-shadow:0 2px 14px rgba(27,58,107,.10)}'
      +'.lh img{height:38px}.ttl{font-size:30px;font-weight:800;letter-spacing:10px;color:#1B3A6B;margin:14px 0 4px}.sub{color:#6b7280;font-size:12px;margin-bottom:16px}'
      +'.cards{display:flex;gap:14px;margin-bottom:18px}.cards>div{flex:1;border-radius:10px;padding:16px 18px}.cards .rc{border:1px solid #dbe3ee;background:#fff}.cards .ac{background:#1B3A6B;color:#fff}'
      +'.cards .k{font-size:11px;opacity:.75;margin-bottom:6px}.cards .rc .k{color:#6b7280;opacity:1}.cards .v{font-size:20px;font-weight:800}.cards .ac .big{font-size:26px;font-weight:800}.cards .ac .s{font-size:12px;opacity:.9;margin-top:4px}'
      +'.sec{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:700;color:#1B3A6B;margin:18px 0 8px;padding-top:14px;border-top:2px solid #1B3A6B}.sec:before{content:"";width:4px;height:16px;background:#1B3A6B;border-radius:2px}.sec small{font-weight:400;color:#6b7280}'
      +'table{width:100%;border-collapse:collapse}th{background:#f3f6fa;color:#334155;font-size:11.5px;font-weight:700;padding:8px 6px;border-bottom:1px solid #d6dee9;text-align:left}td{padding:9px 6px;border-bottom:1px solid #eef1f5;vertical-align:middle}'
      +'td.c,th.c{text-align:center}td.r,th.r{text-align:right;white-space:nowrap}td.no{color:#6b7280;width:34px}td.amt{font-weight:800;color:#1B3A6B}'
      +'.pnrow{display:flex;gap:10px;align-items:center}.pn b{font-family:Consolas,"D2Coding",monospace;font-size:14px;letter-spacing:.3px}.pn .nm{font-size:11.5px;color:#6b7280;margin-top:2px}.pn .cxs{font-size:11px;color:#0e7490;margin-top:2px}.pn .cx{margin-right:8px}'
      +'.thumb:empty{display:none}.thumb img{width:56px;height:56px;object-fit:contain;border:1px solid #e5e9f0;border-radius:6px;background:#fff;cursor:zoom-in}'
      +'.mk{display:inline-block;padding:2px 9px;border-radius:5px;font-size:11px;font-weight:700;color:#fff;background:#64748b;white-space:nowrap}.mk.SMC{background:#1B3A6B}.mk.CONVUM{background:#c0392b}.mk.NITTA{background:#d97706}.mk.CDC{background:#6d28d9}.mk.x{background:#cbd5e1;color:#475569}'
      +'td.links{white-space:nowrap}.ql{display:inline-block;margin:1px 2px;padding:3px 8px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;color:#1B3A6B;font-size:11px;font-weight:700;text-decoration:none;cursor:pointer;font-family:inherit;line-height:1.3}.ql:hover{background:#f1f5f9}.ql.cp{color:#475569}.ql.cad{color:#0e7490}'
      +'.dc{color:#dc2626;font-weight:700}tr.nego td{color:#dc2626}'
      +'.tot{margin-top:4px}.tot td{padding:9px 8px;font-size:13px}.tot .l{text-align:right;color:#374151}.tot .v{text-align:right;width:160px;font-weight:700}.tot tr.g td{border-top:2px solid #1B3A6B;border-bottom:0;color:#1B3A6B;font-size:15px;font-weight:800}'
      +'.note{background:#fff8e6;border:1px solid #f3dca0;border-radius:10px;padding:12px 18px 12px 30px;font-size:12.5px;color:#374151}.note li{margin:3px 0}'
      +'.sup{border:1px solid #dbe3ee;border-radius:10px;padding:16px 18px;display:flex;gap:16px;align-items:center}.sup .t{flex:1}.sup .corp{font-size:17px;font-weight:800;color:#1B3A6B;margin-bottom:4px}.sup .ln{font-size:12.5px;color:#374151}.sup .stf{margin-top:8px;padding-top:8px;border-top:1px dashed #dbe3ee;font-size:12.5px}.sup img.st{height:52px}.sup img.sl{height:46px}'
      +'.ft{margin-top:14px;padding-top:10px;border-top:1px solid #e5e9f0;color:#9ca3af;font-size:11px;line-height:1.7}'
      +'#zm{position:fixed;inset:0;background:rgba(15,23,42,.88);display:none;align-items:center;justify-content:center;z-index:99;cursor:zoom-out}#zm img{max-width:94vw;max-height:94vh;background:#fff;border-radius:6px}'
      +'.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}'
      +'@media (max-width:640px){.pg{padding:18px 14px;margin:0}.tw table{min-width:640px}.cards{flex-direction:column}.ttl{font-size:24px;letter-spacing:6px}td.links{white-space:normal}th.eta,td.eta{display:none}}'
      +'@media print{body{background:#fff}.pg{box-shadow:none;margin:0;max-width:none;padding:10mm 12mm}.ql.cp{display:none}}';
    var JSX='(function(){'
      +'var Q=function(s){return document.querySelectorAll(s)};'
      +'document.addEventListener("click",function(e){var b=e.target.closest(".ql.cp");if(b){var t=b.getAttribute("data-pn");var done=function(){b.textContent="복사됨";setTimeout(function(){b.textContent="복사";},1200);};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,function(){prompt("품번",t);});}else{prompt("품번",t);}return;}'
      +'var im=e.target.closest(".thumb img");if(im){var z=document.getElementById("zm");z.querySelector("img").src=im.getAttribute("data-full")||im.src;z.style.display="flex";return;}'
      +'if(e.target.closest("#zm")){document.getElementById("zm").style.display="none";}});'
      +(hasCv?('var API='+JSON.stringify(_QH_CV_API)+',KEY='+JSON.stringify(_QH_CV_KEY)+',STORE='+JSON.stringify(_QH_CV_STORE)+';'
      +'var norm=function(s){return String(s||"").toLowerCase().replace(/[\\s\\-_.]/g,"")};var abs=function(u){return /^https?:\\/\\//.test(u)?u:(STORE+u)};'
      +'var esc=function(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")};'
      +'var A=function(u,l,c){return u?"<a class=\\"ql"+(c?" "+c:"")+"\\" href=\\""+esc(abs(u))+"\\" target=\\"_blank\\" rel=\\"noopener\\">"+l+"</a>":""};'
      +'Q(".qcv").forEach(function(el){var pn=el.getAttribute("data-pn");(async function(){try{var hd={apikey:KEY,authorization:"Bearer "+KEY},q=encodeURIComponent(pn.trim()),sel="select=model_name,cad_2d_url,cad_3d_url,pdf_url,thumbnail_url&is_active=eq.true";'
      +'var r=await fetch(API+"/rest/v1/drawings?"+sel+"&model_name=eq."+q,{headers:hd});var rows=r.ok?await r.json():[];if(!rows.length){var r2=await fetch(API+"/rest/v1/drawings?"+sel+"&model_name=ilike."+q+"*&limit=8",{headers:hd});rows=r2.ok?await r2.json():[];}'
      +'var m={thumb:null,d2:null,d3:null,pdf:null,exact:false};rows.forEach(function(x){if(norm(x.model_name)===norm(pn))m.exact=true;if(x.thumbnail_url&&!m.thumb)m.thumb=x.thumbnail_url;if(x.cad_2d_url&&!m.d2)m.d2=x.cad_2d_url;if(x.cad_3d_url&&!m.d3)m.d3=x.cad_3d_url;if(x.pdf_url&&!m.pdf)m.pdf=x.pdf_url;});'
      +'if(!(m.thumb||m.d2||m.d3||m.pdf))return;el.innerHTML=A(m.pdf,"제품 PDF")+A(m.d2,"2D","cad")+A(m.d3,"3D","cad")+(m.exact?"":"<small style=\\"color:#9ca3af\\"> ※유사 형번</small>");'
      +'if(m.thumb){Q(".thumb[data-pn=\\""+pn.replace(/"/g,"\\\\\\"")+"\\"]").forEach(function(t){t.innerHTML="<img src=\\""+esc(abs(m.thumb))+"\\" data-full=\\""+esc(abs(m.thumb))+"\\" alt=\\"\\" loading=\\"lazy\\" title=\\"도면 보기\\">";});}'
      +'}catch(e){}})();});'):'')
      +'})();';
    var html='<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>견적서 '+esc(_qQuoteNo||'')+' · '+esc(vname)+'</title><style>'+CSS+'</style></head><body><div class="pg">'
      +'<div class="lh"><img src="'+_QPDF_IMG1+'" alt="충해전기㈜"></div>'
      +'<div class="ttl">견 적 서</div>'
      +'<div class="sub">'+esc(head)+' · 견적번호 <b>'+esc(_qQuoteNo||'')+'</b> · 견적일자 '+esc(ds)+' · 유효기간 발행일로부터 30일</div>'
      +'<div class="cards"><div class="rc"><div class="k">수신</div><div class="v">'+esc(vname)+' <small style="font-size:12px;font-weight:600;color:#475569">귀하</small></div>'+(_mgr?'<div style="margin-top:6px">담당자 <b>'+esc(_mgr)+'</b> 님</div>':'')+'<div style="margin-top:4px;color:#374151">아래와 같이 견적합니다.</div></div>'
      +'<div class="ac"><div class="k">견적금액</div><div class="big">'+fmt(finalSupply)+' 원 <small style="font-size:12px;font-weight:600">(부가세 별도)</small></div><div class="s"><b>'+fmt(total)+' 원</b> (부가세 포함)</div><div class="s">부가세 '+fmt(vat)+' 원 · '+_qCart.length+'품목 · 총 '+qtySum.toLocaleString()+' EA</div></div></div>'
      +'<div class="sec">견적 내역</div>'
      +'<div class="tw"><table><thead><tr><th class="c">No</th><th>품번 / 품목</th><th class="c">메이커</th><th class="r">수량</th><th class="c">자료</th><th class="r">단가(원)</th><th class="r">금액(원)</th>'+(hasEta?'<th class="c eta">예상납기</th>':'')+'</tr></thead><tbody>'+rows+'</tbody></table></div>'
      +'<table class="tot"><tr><td class="l">공급가액</td><td class="v">'+fmt(finalSupply)+'</td></tr><tr><td class="l">부가세 (10%)</td><td class="v">'+fmt(vat)+'</td></tr><tr class="g"><td class="l">합계 (부가세 포함)</td><td class="v">'+fmt(total)+'</td></tr></table>'
      +'<div class="sec">확인 사항</div><ul class="note">'+notes.map(function(t){ return '<li>'+t+'</li>'; }).join('')+'</ul>'
      +'<div class="sec">공급자</div><div class="sup"><div class="t"><div class="corp">'+esc(SUP.corp)+'</div><div class="ln">대표이사 '+esc(SUP.ceo.replace(/\s+/g,''))+' · 사업자등록번호 '+esc(SUP.biz)+'</div><div class="ln">'+esc(SUP.addr.replace(/\n/g,' '))+'</div><div class="ln">TEL '+esc(SUP.tel)+' · FAX '+esc(SUP.fax)+' · '+esc(SUP.mail)+'</div>'
      +(staff?'<div class="stf">담당 <b>'+esc(staff)+'</b>'+(staffPhone?' · '+esc(staffPhone):'')+'</div>':'')+'</div>'
      +(st&&st.b64?'<img class="st" src="data:image/png;base64,'+st.b64+'" alt="">':'')+(sl&&sl.b64?'<img class="sl" src="data:image/png;base64,'+sl.b64+'" alt="">':'')+'</div>'
      +'<div class="ft">· 본 견적서의 유효기간은 발행일로부터 30일입니다. · 상기 금액은 부가가치세 별도 금액입니다. · 결제 및 납기 조건은 협의에 따릅니다.<br>· 자료 링크는 각 메이커(SMC·CONVUM 등)의 공개 카탈로그·도면 자료로 연결됩니다. — '+esc(SUP.corp)+'</div>'
      +'</div><div id="zm"><img alt=""></div><script>'+JSX+'<\/script></body></html>';
    return html;
  }
  window.qExportHtml = async function(){
    if(!_qCart.length || !_qCartHasContent()){ showInfoModal('견적 목록', '견적 목록이 비어 있습니다.'); return; }
    try{
      try{ await _qPersistQuote(); }catch(_pe){ showInfoModal('견적 저장 실패', (_pe&&_pe.message||String(_pe))+'\n\nHTML 은 계속 만들지만, 이 견적은 저장되지 않았습니다.'); }
      var html=await _qBuildQuoteHtml();
      var _fn=('견적서 '+(_qQuoteNo||(_qCart[0].vname||'견적'))).replace(/[<>:"/\\|?*]/g,' ').replace(/\s+/g,' ').trim();
      var blob=new Blob([html],{type:'text/html;charset=utf-8'}); var url=URL.createObjectURL(blob);
      var a=document.createElement('a'); a.href=url; a.download=_fn+'.html'; document.body.appendChild(a); a.click(); setTimeout(function(){ try{ document.body.removeChild(a); URL.revokeObjectURL(url); }catch(_e){} }, 1500);
      if(_qQuoteNo) showInfoModal('HTML 견적서', '"'+esc(_fn)+'.html" 로 내려받았습니다. 카톡·메일에 파일 그대로 첨부하면 받는 쪽은 클릭만 하면 됩니다.\n이 견적은 "'+esc(_qQuoteNo)+'" 번호로 자동 저장되었습니다.');
    }catch(e){ showInfoModal('알림', 'HTML 내보내기 실패: '+(e&&e.message||String(e))); }
  };
"""

OPS = [
  [MENU_OLD, MENU_NEW, 1, "MENU"],
  ["  // r229: 고객용 견적서(_qBuildQuoteSheetWb)는 [일반 엑셀] 버튼이 쓴다.", JS + "  // r229: 고객용 견적서(_qBuildQuoteSheetWb)는 [일반 엑셀] 버튼이 쓴다.", 1, "JS"],
  ["<!-- test build r232 2026-10-14 -->", "<!-- test build r233 2026-10-14 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R233 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r233(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r233 브라우저 적용기 — edits_r233.py 의 OPS. r232+r226+r227(live bc775fcb / test 210192c2) 에 적용.",
             "function r233Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R233 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r233Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r233(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r233 applied:', path)
