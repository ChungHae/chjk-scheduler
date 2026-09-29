# -*- coding: utf-8 -*-
# r210(회계): 미수현황에 '내용증명 작성' 버튼 + 문서 생성 (워드 .docx / 인쇄 PDF)
#  구 Streamlit 앱(ChungHae/chjk-manage · nyung.py)의 양식을 그대로 브라우저로 이식.
#  사용자 선택: ① 장기미수 거래처만 버튼 표시 ② 수신인은 일정>업체 상세에서 자동채움 ③ 워드+PDF 둘 다.
#
#  ★ 명판·인감 그림은 코드에 넣지 않는다 — 이 저장소는 공개라 회사 인감이 그대로 내려받아진다.
#    로그인해야 읽히는 Firebase(<db>/teamdata_test/sched_doc_assets)에 보관하고, 문서 만들 때만 읽는다.
#    등록은 내용증명 창 하단의 '명판·인감 등록'(마스터 전용)에서 PNG 3개를 고르면 된다.
#    원본 위치(사용자 PC): C:\Users\mycom\Claude\Projects\세금계산서 및 입출금 자동화 및 미수 확인\도장 및 미수금\
#      stamp_guro.png(서울 명판) / stamp_hwaseong.png(화성 명판) / 인감_보정_투명.png(인감)
#    올릴 때 캔버스로 명판 760px · 인감 240px 로 줄여 저장한다(원본 574KB → 약 57KB).
#
#  구성:
#   (1) 미수현황 표에 '내용증명' 열을 거래처와 미수 잔액 사이에 추가. 장기미수 행에만 버튼.
#       행 클릭(원장 펼치기)과 겹치지 않게 stopPropagation.
#   (2) fxNyOpen → 입력 창(거래처명·미수액·대표자·전화·주소·관할·작성일). 기본값은 원장과 업체 상세에서.
#   (3) fxNyPrint → 새 창에 A4 레이아웃으로 그려 인쇄(브라우저 'PDF로 저장').
#   (4) fxNyDocx → JSZip 으로 OOXML(.docx) 패키지를 직접 만들어 내려받기. 표·명판·인감 포함.
#   (5) 금액 한글(_nyWon)은 nyung.py won_hangul 이식.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

NY_JS = r"""  // ── r210: 내용증명(미수금 독촉) ─────────────────────────────────────────
  //  구 Streamlit 앱(chjk-manage / nyung.py)의 양식을 그대로 옮긴 것.
  //  발신자·계좌는 관할(서울/화성)에 따라 바뀐다.
  var _NY_KWON = {
    '서울': { corp:'충해전기 주식회사', tel:'010-5228-2922',
      addr:'서울특별시 구로구 구로중앙로198, B-13, 103',
      bank:'신한은행', acct:'100-001-944331', holder:'충해전기(주)', rep:'김해식', stamp:'stamp_서울' },
    '화성': { corp:'충해전기 주식회사 화성영업소', tel:'010-5228-2922',
      addr:'경기도 화성시 팔탄면 푸른들판로 642-5, G-103~104, 202',
      bank:'신한은행', acct:'140-013-471920', holder:'충해전기(주) 화성영업소', rep:'김재성', stamp:'stamp_화성' }
  };
  // 금액 한글 (nyung.py won_hangul 이식)
  function _nyWon(n){
    n=Math.round(Number(n)||0);
    if(n===0) return '영원';
    var units=['','만','억','조'], digit=['','일','이','삼','사','오','육','칠','팔','구'], pos=['','십','백','천'];
    var grp=[]; while(n>0){ grp.push(n%10000); n=Math.floor(n/10000); }
    var parts=[];
    for(var i=grp.length-1;i>=0;i--){
      var g=grp[i]; if(!g) continue; var gs='';
      for(var p=3;p>=0;p--){
        var d=Math.floor(g/Math.pow(10,p))%10; if(!d) continue;
        gs += (d===1 && p>0) ? pos[p] : (digit[d]+pos[p]);
      }
      parts.push(gs+units[i]);
    }
    return parts.join('')+'원';
  }
  function _nyXe(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  // 명판·인감 그림은 공개 저장소에 두지 않는다 — 로그인해야 읽히는 Firebase 에 보관한다.
  var _nyAssets=null;
  async function _nyLoadAssets(force){
    if(_nyAssets && !force) return _nyAssets;
    try{
      var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_doc_assets.json');
      _nyAssets=(r && r.ok ? (await r.json()) : null) || {};
    }catch(_e){ _nyAssets={}; }
    return _nyAssets;
  }
  function _nyB64ToU8(b64){
    var bin=atob(String(b64||'')); var u=new Uint8Array(bin.length);
    for(var i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i);
    return u;
  }
  // ── 내용증명 창 ──────────────────────────────────────────────────────
  var _nyOpen=null;   // {name, vbiz, rgn, bal}
  window.fxNyOpen = function(key, ev){
    try{ if(ev && ev.stopPropagation) ev.stopPropagation(); }catch(_e){}
    var row=null;
    (_fxLedgers(_fxRegion)||[]).forEach(function(x){ if(x.key===key) row=x; });
    if(!row){ showInfoModal('내용증명','거래처를 찾지 못했습니다.'); return; }
    _nyOpen=row;
    var inf={};
    try{
      var c=_cliFind(row.name, row.rgn) || _cliFind(row.name);
      if(c) inf=_clxInfo(c)||{};
    }catch(_e2){}
    var addr=[inf.addr||'', inf.addr2||''].filter(Boolean).join(' ');
    var host=document.getElementById('nyWrap');
    if(!host){ host=document.createElement('div'); host.id='nyWrap'; document.body.appendChild(host); }
    var F='width:100%;height:30px;box-sizing:border-box;padding:0 8px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;font-family:inherit;outline:none';
    var L='font-size:11.5px;font-weight:700;color:#14305c;display:block;margin-bottom:3px';
    host.innerHTML='<div id="nyOv" style="position:fixed;inset:0;background:rgba(10,20,40,.45);z-index:100080;display:flex;align-items:flex-start;justify-content:center;overflow:auto;padding:40px 16px">'
      + '<div style="background:#fff;border:1px solid #1B3A6B;width:640px;max-width:100%">'
      +   '<div style="padding:12px 18px;background:#1B3A6B;color:#fff;font-size:13.5px;font-weight:700;display:flex;align-items:center">내용증명 작성'
      +     '<span style="flex:1"></span><button type="button" class="btn" onclick="fxNyClose()" style="font-size:11.5px;padding:2px 10px;border:1px solid #fff;background:transparent;color:#fff">닫기</button></div>'
      +   '<div style="padding:16px 18px">'
      +     '<div style="display:grid;grid-template-columns:1fr 200px;gap:10px">'
      +       '<div><label style="'+L+'">거래처명 (정식 상호)</label><input type="text" id="nyCorp" style="'+F+'" value="'+esc(row.name)+'"></div>'
      +       '<div><label style="'+L+'">미수액 (원)</label><input type="text" id="nyAmt" style="'+F+';text-align:right" value="'+_fxFmt(Math.max(0,Math.round(row.bal)))+'" oninput="fxNyAmtFmt(this)"></div>'
      +     '</div>'
      +     '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px">'
      +       '<div><label style="'+L+'">대표자명 (수신 담당자)</label><input type="text" id="nyRep" style="'+F+'" value="'+esc(inf.ceo||'')+'"></div>'
      +       '<div><label style="'+L+'">수신 연락처</label><input type="text" id="nyTel" style="'+F+'" value="'+esc(inf.tel||'')+'"></div>'
      +     '</div>'
      +     '<div style="margin-top:10px"><label style="'+L+'">수신 주소</label><input type="text" id="nyAddr" style="'+F+'" value="'+esc(addr)+'"></div>'
      +     '<div style="display:grid;grid-template-columns:1fr 200px;gap:10px;margin-top:10px">'
      +       '<div><label style="'+L+'">관할 (명판·발신자·입금계좌가 바뀝니다)</label>'
      +         '<div style="display:flex;gap:4px">'
      +           '<button type="button" class="btn pf-btn'+(row.rgn==='서울'?' active':'')+'" id="nyRgn서울" onclick="fxNySetRgn(\'서울\')" style="font-size:11.5px;padding:4px 14px">서울</button>'
      +           '<button type="button" class="btn pf-btn'+(row.rgn==='화성'?' active':'')+'" id="nyRgn화성" onclick="fxNySetRgn(\'화성\')" style="font-size:11.5px;padding:4px 14px">화성</button>'
      +         '</div></div>'
      +       '<div><label style="'+L+'">작성일</label><input type="date" id="nyDate" style="'+F+'" value="'+dk(new Date())+'"></div>'
      +     '</div>'
      +     '<div id="nyWarn" style="margin-top:10px;font-size:11.5px;color:#b45309;line-height:1.6"></div>'
      +     '<div style="margin-top:14px;display:flex;gap:6px;align-items:center">'
      +       '<button type="button" class="btn" onclick="fxNyPrint()" style="font-size:12px;padding:6px 16px;border:1px solid #1B3A6B;color:#14305c;background:#fff;font-weight:700">미리보기 · 인쇄(PDF)</button>'
      +       '<button type="button" class="btn" onclick="fxNyDocx()" style="font-size:12px;padding:6px 16px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;font-weight:700">워드(.docx) 저장</button>'
      +       '<span style="flex:1"></span>'
      +       '<span id="nyMsg" style="font-size:11.5px;color:#6b7280"></span>'
      +     '</div>'
      +     (_fxUpAllowed() ? ('<div style="margin-top:14px;padding-top:12px;border-top:1px solid #eef2f7">'
      +       '<div style="font-size:11.5px;font-weight:700;color:#14305c;margin-bottom:6px">명판·인감 등록 <span style="font-weight:400;color:#9ca3af">(마스터 전용 · 한 번만 등록하면 됩니다)</span></div>'
      +       '<div id="nyAssetRow" style="display:flex;gap:10px;flex-wrap:wrap;font-size:11.5px;color:#6b7280"></div></div>') : '')
      +   '</div>'
      + '</div></div>';
    _nyRgn = row.rgn==='화성' ? '화성' : '서울';
    fxNySetRgn(_nyRgn);
    _nyLoadAssets(true).then(function(){ _nyAssetStatus(); });
  };
  var _nyRgn='서울';
  window.fxNySetRgn = function(b){
    _nyRgn=b;
    ['서울','화성'].forEach(function(k){
      var el=document.getElementById('nyRgn'+k); if(!el) return;
      if(k===b) el.classList.add('active'); else el.classList.remove('active');
    });
  };
  window.fxNyClose = function(){ var h=document.getElementById('nyWrap'); if(h) h.innerHTML=''; _nyOpen=null; };
  window.fxNyAmtFmt = function(el){
    var v=String(el.value||'').replace(/[^0-9]/g,'');
    el.value = v ? Number(v).toLocaleString() : '';
  };
  function _nyAssetStatus(){
    var box=document.getElementById('nyAssetRow');
    var warn=document.getElementById('nyWarn');
    var need=[]; var a=_nyAssets||{};
    if(!a['stamp_서울']) need.push('서울 명판');
    if(!a['stamp_화성']) need.push('화성 명판');
    if(!a.seal) need.push('인감');
    if(warn) warn.innerHTML = need.length
      ? ('&#9888;&#65039; 아직 등록되지 않은 그림: <b>'+need.join(', ')+'</b> — 그 자리는 비워둔 채로 만들어집니다.')
      : '';
    if(!box) return;
    var one=function(k,lbl){
      var ok=!!(a[k]);
      return '<label style="display:inline-flex;align-items:center;gap:5px;border:1px solid '+(ok?'#86efac':'#e3c8a0')+';background:'+(ok?'#f0fdf4':'#fff8ef')+';padding:4px 10px;cursor:pointer">'
        + '<span style="font-weight:700;color:'+(ok?'#15803d':'#b45309')+'">'+lbl+(ok?' 등록됨':' 없음')+'</span>'
        + '<input type="file" accept="image/png,image/jpeg" style="display:none" onchange="fxNyAssetPick(\''+k+'\', this)"></label>';
    };
    box.innerHTML = one('stamp_서울','서울 명판')+one('stamp_화성','화성 명판')+one('seal','인감');
  }
  window.fxNyAssetPick = async function(key, inp){
    var f=(inp.files||[])[0]; inp.value='';
    if(!f) return;
    var msg=document.getElementById('nyMsg'); if(msg) msg.textContent='그림 처리 중…';
    try{
      var W = (key==='seal') ? 240 : 760;
      var img=await new Promise(function(res,rej){ var im=new Image(); im.onload=function(){res(im);}; im.onerror=function(){rej(new Error('이미지를 읽지 못했습니다'));}; im.src=URL.createObjectURL(f); });
      var h=Math.round(img.naturalHeight*W/img.naturalWidth);
      var cv=document.createElement('canvas'); cv.width=W; cv.height=h;
      cv.getContext('2d').drawImage(img,0,0,W,h);
      var url=cv.toDataURL('image/png');
      var b64=url.split(',')[1];
      var obj={}; obj[key]={w:W, h:h, b64:b64};
      var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_doc_assets.json', {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(obj)});
      if(!r || !r.ok) throw new Error('저장 실패 ('+(r&&r.status)+')');
      await _nyLoadAssets(true); _nyAssetStatus();
      if(msg) msg.textContent=key+' 등록 완료';
    }catch(e){ if(msg) msg.textContent='실패: '+(e&&e.message||e); }
  };
  function _nyData(){
    var g=function(id){ var el=document.getElementById(id); return el?String(el.value||'').trim():''; };
    var amt=Number(String(g('nyAmt')).replace(/[^0-9]/g,''))||0;
    var d=g('nyDate')||dk(new Date());
    var K=_NY_KWON[_nyRgn]||_NY_KWON['서울'];
    return { corp:g('nyCorp'), rep:g('nyRep'), tel:g('nyTel'), addr:g('nyAddr'),
             amt:amt, rgn:_nyRgn, date:d, K:K };
  }
  function _nyBody(D){
    var K=D.K, amt=D.amt;
    return [
      '귀하(社)의 무궁한 발전을 기원합니다.',
      '본 내용증명은 발신인 '+K.corp+' (이하 “발신인”) 가 수신인 '+D.corp+' (이하 “수신인”) 에게 납품한 유공압 제품의 미지급 대금에 관한 것입니다.',
      '발신인은 수신인의 주문에 따라 유공압 제품을 정상적으로 납품하였으며, 이에 대한 납품대금은 부가세를 포함하여 금'+amt.toLocaleString()+'원('+_nyWon(amt)+')입니다.',
      '양 당사자는 위 납품대금을 약정 지급일까지 지급하기로 약정하였으나, 수신인은 약정 지급기일이 경과한 본 서면 작성일 현재까지도 위 대금을 지급하지 아니하고 있습니다.',
      '이에 발신인은 수신인에게 본 서면을 수령한 날로부터 7일 이내에 위 미지급 대금 '+amt.toLocaleString()+'원 전액을 아래 계좌로 지급하여 주실 것을 정중히 청구합니다.',
      '만약 위 기한 내에 대금이 지급되지 아니할 경우, 발신인은 부득이 민사소송 제기, 지급명령 신청 등 법적 절차에 착수할 수 밖에 없으며, 이 경우 지연손해금 및 소송비용 등이 추가로 수신인에게 부담될 수 있음을 미리 알려드립니다.',
      '원만한 해결을 진심으로 희망하오니, 기한 내에 성실히 이행하여 주시기 바랍니다.'
    ];
  }
  function _nyDateStr(d){
    var p=String(d||'').split('-');
    return p.length===3 ? (Number(p[0])+'년 '+Number(p[1])+'월 '+Number(p[2])+'일') : String(d||'');
  }
  // ── 미리보기 · 인쇄(PDF) ─────────────────────────────────────────────
  window.fxNyPrint = async function(){
    var D=_nyData();
    if(!D.corp){ showInfoModal('내용증명','거래처명을 입력해 주세요.'); return; }
    var a=await _nyLoadAssets();
    var K=D.K, items=_nyBody(D);
    var st=a[K.stamp], sl=a.seal;
    var recv=esc(D.corp)+(D.rep?(' 대표 '+esc(D.rep)):'');
    var send=esc(K.holder)+' 대표 '+esc(K.rep);
    var TB='border-collapse:collapse;width:100%;table-layout:fixed;margin:2px 0 0';
    var TD='border:1px solid #808080;padding:4px 7px;font-size:9.5pt;line-height:1.23;vertical-align:middle';
    var TH=TD+';background:#F2F2F2;font-weight:700;text-align:center';
    var info=function(l1,v1,l2,v2,l3,v3){
      return '<table style="'+TB+'"><colgroup><col style="width:2.2cm"><col style="width:7.6cm"><col style="width:2.2cm"><col></colgroup>'
        + '<tr><td style="'+TH+'">'+l1+'</td><td style="'+TD+'">'+v1+'</td><td style="'+TH+'">'+l2+'</td><td style="'+TD+'">'+v2+'</td></tr>'
        + '<tr><td style="'+TH+'">'+l3+'</td><td style="'+TD+'" colspan="3">'+v3+'</td></tr></table>';
    };
    var html='<!doctype html><html><head><meta charset="utf-8"><title>내용증명 '+esc(D.corp)+'</title>'
      + '<style>@page{size:A4;margin:1.1cm 2.0cm 0.9cm 2.0cm}'
      + 'body{font-family:"맑은 고딕","Malgun Gothic",sans-serif;font-size:9.5pt;line-height:1.23;color:#000;margin:0}'
      + '.t{text-align:center;font-size:22pt;font-weight:700;letter-spacing:.35em;margin:2pt 0 10pt}'
      + '.lb{font-size:10.5pt;font-weight:700;margin:6pt 0 2pt}'
      + '.hr{border-bottom:1px solid #000;padding-bottom:3pt;margin:9pt 0 5pt;font-size:10.5pt;font-weight:700}'
      + '.it{margin:0 0 3pt;text-indent:0;padding-left:1.1em;text-indent:-1.1em}'
      + '.dt{text-align:center;font-size:10.5pt;margin:15pt 0 14pt}'
      + '.hd{text-align:center;font-size:11.5pt;font-weight:700;margin:0 0 8pt}'
      + '@media print{.noprint{display:none}}</style></head><body>'
      + '<div class="noprint" style="position:fixed;top:0;left:0;right:0;background:#1B3A6B;color:#fff;padding:8px 14px;font-size:12px;z-index:9">'
      +   '이 창에서 인쇄(Ctrl+P) → 대상을 “PDF로 저장”으로 고르면 PDF가 됩니다. '
      +   '<button onclick="window.print()" style="margin-left:10px;padding:3px 12px;border:1px solid #fff;background:transparent;color:#fff;cursor:pointer">인쇄</button></div>'
      + '<div class="noprint" style="height:38px"></div>'
      + '<div class="t">내 용 증 명 서</div>'
      + '<div class="lb">수신자</div>' + info('수신인',recv,'전화번호',esc(D.tel),'주소',esc(D.addr))
      + '<div class="lb">발신자</div>' + info('발신인',send,'전화번호',esc(K.tel),'주소',esc(K.addr))
      + '<div class="hr">미수금 지불 촉구의 건</div>'
      + '<div style="height:6pt"></div>'
      + items.slice(0,5).map(function(t,i){ return '<div class="it">'+(i+1)+'. '+esc(t)+'</div>'; }).join('')
      + '<table style="'+TB+';margin:4pt 0"><colgroup><col style="width:3.2cm"><col style="width:5.0cm"><col style="width:4.6cm"><col></colgroup>'
      +   '<tr><td style="'+TH+'">입금은행</td><td style="'+TH+'">계좌번호</td><td style="'+TH+'">예금주</td><td style="'+TH+'">입금액</td></tr>'
      +   '<tr><td style="'+TD+';text-align:center">'+esc(K.bank)+'</td><td style="'+TD+';text-align:center">'+esc(K.acct)+'</td>'
      +   '<td style="'+TD+';text-align:center">'+esc(K.holder)+'</td><td style="'+TD+';text-align:center">'+D.amt.toLocaleString()+'원</td></tr></table>'
      + '<div style="height:4pt"></div>'
      + items.slice(5).map(function(t,i){ return '<div class="it">'+(i+6)+'. '+esc(t)+'</div>'; }).join('')
      + '<div style="border-bottom:1px solid #000;margin:6pt 0 0"></div>'
      + '<div class="dt">'+esc(_nyDateStr(D.date))+'</div>'
      + '<div class="hd">'+esc(K.holder)+'</div>'
      + '<table style="width:100%;table-layout:fixed;border-collapse:collapse"><colgroup><col><col style="width:6.7cm"><col style="width:2.0cm"></colgroup><tr>'
      +   '<td></td>'
      +   '<td style="text-align:center;vertical-align:middle">'+(st?('<img src="data:image/png;base64,'+st.b64+'" style="width:6cm">'):'')+'</td>'
      +   '<td style="text-align:center;vertical-align:middle">'+(sl?('<img src="data:image/png;base64,'+sl.b64+'" style="width:1.5cm">'):'')+'</td>'
      + '</tr></table></body></html>';
    var w=window.open('', '_blank');
    if(!w){ showInfoModal('내용증명','팝업이 차단되었습니다. 이 사이트의 팝업을 허용해 주세요.'); return; }
    w.document.open(); w.document.write(html); w.document.close();
  };
  // ── 워드(.docx) 저장 ────────────────────────────────────────────────
  var _NY_TW=567;   // 1cm = 567 twips
  function _nyRun(t,sz,bold){
    return '<w:r><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:sz w:val="'+sz+'"/><w:szCs w:val="'+sz+'"/>'+(bold?'<w:b/>':'')+'</w:rPr><w:t xml:space="preserve">'+_nyXe(t)+'</w:t></w:r>';
  }
  function _nyP(t,opt){
    opt=opt||{};
    var sz=opt.sz||19, al=opt.al, bf=opt.before||0, af=(opt.after==null?60:opt.after);
    var pPr='<w:pPr>'+(al?('<w:jc w:val="'+al+'"/>'):'')
      + (opt.ind?'<w:ind w:left="220" w:hanging="220"/>':'')
      + (opt.rule?'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="3" w:color="000000"/></w:pBdr>':'')
      + '<w:spacing w:before="'+bf+'" w:after="'+af+'" w:line="295" w:lineRule="auto"/>'
      + '<w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:sz w:val="'+sz+'"/>'+(opt.bold?'<w:b/>':'')+'</w:rPr></w:pPr>';
    return '<w:p>'+pPr+(t===''?'':_nyRun(t,sz,!!opt.bold))+'</w:p>';
  }
  function _nyCell(w,t,opt){
    opt=opt||{};
    return '<w:tc><w:tcPr><w:tcW w:w="'+w+'" w:type="dxa"/>'
      + (opt.span?'<w:gridSpan w:val="'+opt.span+'"/>':'')
      + (opt.shade?'<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>':'')
      + '<w:vAlign w:val="center"/></w:tcPr>'
      + _nyP(t,{sz:19,al:opt.al,bold:opt.bold,after:0}) + '</w:tc>';
  }
  function _nyTblPr(){
    return '<w:tblPr><w:tblLayout w:type="fixed"/><w:tblBorders>'
      + ['top','left','bottom','right','insideH','insideV'].map(function(e){ return '<w:'+e+' w:val="single" w:sz="4" w:space="0" w:color="808080"/>'; }).join('')
      + '</w:tblBorders></w:tblPr>';
  }
  function _nyGrid(ws){ return '<w:tblGrid>'+ws.map(function(w){ return '<w:gridCol w:w="'+w+'"/>'; }).join('')+'</w:tblGrid>'; }
  function _nyRow(cells){ return '<w:tr><w:trPr><w:trHeight w:hRule="atLeast" w:val="386"/></w:trPr>'+cells+'</w:tr>'; }
  function _nyDrawing(rid, cx, cy, name){
    return '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:drawing>'
      + '<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="'+cx+'" cy="'+cy+'"/><wp:docPr id="'+(rid==='rId10'?1:2)+'" name="'+name+'"/>'
      + '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
      + '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
      + '<pic:nvPicPr><pic:cNvPr id="0" name="'+name+'"/><pic:cNvPicPr/></pic:nvPicPr>'
      + '<pic:blipFill><a:blip r:embed="'+rid+'"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
      + '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="'+cx+'" cy="'+cy+'"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>';
  }
  window.fxNyDocx = async function(){
    var D=_nyData();
    if(!D.corp){ showInfoModal('내용증명','거래처명을 입력해 주세요.'); return; }
    var msg=document.getElementById('nyMsg'); if(msg) msg.textContent='워드 문서 만드는 중…';
    try{
      await _ensureJSZip();
      var a=await _nyLoadAssets();
      var K=D.K, items=_nyBody(D), st=a[K.stamp], sl=a.seal;
      var CW=Math.round(17*_NY_TW);                 // 본문 폭 17cm
      var W1=[Math.round(2.2*_NY_TW), Math.round(7.6*_NY_TW), Math.round(2.2*_NY_TW), CW-Math.round(12.0*_NY_TW)];
      var W2=[Math.round(3.2*_NY_TW), Math.round(5.0*_NY_TW), Math.round(4.6*_NY_TW), CW-Math.round(12.8*_NY_TW)];
      var W3=[CW-Math.round(8.7*_NY_TW), Math.round(6.7*_NY_TW), Math.round(2.0*_NY_TW)];
      var recv=D.corp+(D.rep?(' 대표 '+D.rep):'');
      var send=K.holder+' 대표 '+K.rep;
      var infoTbl=function(l1,v1,l2,v2,l3,v3){
        return '<w:tbl>'+_nyTblPr()+_nyGrid(W1)
          + _nyRow(_nyCell(W1[0],l1,{shade:1,bold:1,al:'center'})+_nyCell(W1[1],v1)+_nyCell(W1[2],l2,{shade:1,bold:1,al:'center'})+_nyCell(W1[3],v2))
          + _nyRow(_nyCell(W1[0],l3,{shade:1,bold:1,al:'center'})+_nyCell(W1[1]+W1[2]+W1[3],v3,{span:3}))
          + '</w:tbl>';
      };
      var body='';
      body += _nyP('내  용  증  명  서',{sz:44,bold:1,al:'center',before:40,after:160});
      body += _nyP('수신자',{sz:21,bold:1,before:40,after:40});
      body += infoTbl('수신인',recv,'전화번호',D.tel,'주소',D.addr);
      body += _nyP('발신자',{sz:21,bold:1,before:100,after:40});
      body += infoTbl('발신인',send,'전화번호',K.tel,'주소',K.addr);
      body += _nyP('미수금 지불 촉구의 건',{sz:21,bold:1,before:140,after:80,rule:1});
      items.slice(0,5).forEach(function(t,i){ body += _nyP((i+1)+'. '+t,{ind:1,before:(i===0?220:0),after:60}); });
      body += '<w:tbl>'+_nyTblPr()+_nyGrid(W2)
        + _nyRow(_nyCell(W2[0],'입금은행',{shade:1,al:'center'})+_nyCell(W2[1],'계좌번호',{shade:1,al:'center'})+_nyCell(W2[2],'예금주',{shade:1,al:'center'})+_nyCell(W2[3],'입금액',{shade:1,al:'center'}))
        + _nyRow(_nyCell(W2[0],K.bank,{al:'center'})+_nyCell(W2[1],K.acct,{al:'center'})+_nyCell(W2[2],K.holder,{al:'center'})+_nyCell(W2[3],D.amt.toLocaleString()+'원',{al:'center'}))
        + '</w:tbl>';
      items.slice(5).forEach(function(t,i){ body += _nyP((i+6)+'. '+t,{ind:1,after:(i===1?40:60)}); });
      body += _nyP('',{rule:1,after:40});
      body += _nyP(_nyDateStr(D.date),{sz:21,al:'center',before:240,after:280});
      body += _nyP(K.holder,{sz:23,bold:1,al:'center',after:120});
      var stCell = st ? _nyDrawing('rId10', Math.round(6*360000), Math.round(6*360000*st.h/st.w), '명판') : _nyP('',{after:0});
      var slCell = sl ? _nyDrawing('rId11', Math.round(1.5*360000), Math.round(1.5*360000), '인감') : _nyP('',{after:0});
      body += '<w:tbl><w:tblPr><w:tblLayout w:type="fixed"/><w:tblCellMar>'
        + '<w:top w:w="0" w:type="dxa"/><w:left w:w="0" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/>'
        + '</w:tblCellMar></w:tblPr>'+_nyGrid(W3)
        + '<w:tr>'
        +   '<w:tc><w:tcPr><w:tcW w:w="'+W3[0]+'" w:type="dxa"/></w:tcPr>'+_nyP('',{after:0})+'</w:tc>'
        +   '<w:tc><w:tcPr><w:tcW w:w="'+W3[1]+'" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'+stCell+'</w:tc>'
        +   '<w:tc><w:tcPr><w:tcW w:w="'+W3[2]+'" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'+slCell+'</w:tc>'
        + '</w:tr></w:tbl>';
      body += '<w:sectPr><w:pgSz w:w="11907" w:h="16839"/>'
        + '<w:pgMar w:top="624" w:right="1134" w:bottom="510" w:left="1134" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>';
      var doc='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        + ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
        + ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
        + '<w:body>'+body+'</w:body></w:document>';
      var rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        + (st?'<Relationship Id="rId10" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/stamp.png"/>':'')
        + (sl?'<Relationship Id="rId11" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/seal.png"/>':'')
        + '</Relationships>';
      var styles='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:rPrDefault>'
        + '<w:pPrDefault><w:pPr><w:spacing w:line="295" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
        + '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>';
      var ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        + '<Default Extension="xml" ContentType="application/xml"/>'
        + '<Default Extension="png" ContentType="image/png"/>'
        + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        + '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        + '</Types>';
      var root='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        + '</Relationships>';
      var zip=new JSZip();
      zip.file('[Content_Types].xml', ct);
      zip.folder('_rels').file('.rels', root);
      var w=zip.folder('word');
      w.file('document.xml', doc);
      w.file('styles.xml', styles);
      w.folder('_rels').file('document.xml.rels', rels);
      if(st) w.folder('media').file('stamp.png', _nyB64ToU8(st.b64));
      if(sl) w.folder('media').file('seal.png', _nyB64ToU8(sl.b64));
      var blob=await zip.generateAsync({type:'blob', mimeType:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});
      var safe=String(D.corp).replace(/[^가-힣A-Za-z0-9]/g,'_')||'내용증명';
      var url=URL.createObjectURL(blob);
      var el=document.createElement('a'); el.href=url; el.download='내용증명_'+safe+'.docx';
      document.body.appendChild(el); el.click();
      setTimeout(function(){ URL.revokeObjectURL(url); el.remove(); }, 4000);
      if(msg) msg.textContent='워드 파일을 내려받았습니다.';
    }catch(e){ if(msg) msg.textContent='실패: '+(e&&e.message||e); }
  };
"""

OLD_ANCHOR = "  function _fxRenderArBody(){\n"
NEW_ANCHOR = NY_JS + "  function _fxRenderArBody(){\n"

# 표: 열 추가
OLD_COL = "      + '<colgroup><col style=\"width:80px\"><col><col style=\"width:112px\">"
NEW_COL = "      + '<colgroup><col style=\"width:80px\"><col><col style=\"width:92px\"><col style=\"width:112px\">"

OLD_TH = "<th style=\"'+TH+'\" rowspan=\"2\">\uac70\ub798\ucc98</th><th style=\"'+TH+'\" rowspan=\"2\">\ubbf8\uc218 \uc794\uc561</th>"
NEW_TH = "<th style=\"'+TH+'\" rowspan=\"2\">\uac70\ub798\ucc98</th><th style=\"'+TH+'\" rowspan=\"2\">\ub0b4\uc6a9\uc99d\uba85</th><th style=\"'+TH+'\" rowspan=\"2\">\ubbf8\uc218 \uc794\uc561</th>"

OLD_TD = ("        + '<td style=\"'+TD+';text-align:right;font-weight:700;color:'+(x.bal>0?'#1a1a1a':'#9ca3af')+'\">'+_fxFmt(x.bal)+'</td>'\n")
NEW_TD = ("        + '<td style=\"'+TD+';text-align:center\">'"
          "+(x.status==='\uc7a5\uae30\ubbf8\uc218'"
          "? ('<button type=\"button\" class=\"btn\" onclick=\"fxNyOpen(\\''+x.key.replace(/'/g,\"\\\\'\")+'\\', event)\" '"
          "+ 'style=\"font-size:11px;padding:2px 9px;border:1px solid #dc2626;color:#dc2626;background:#fff;white-space:nowrap\" '"
          "+ 'title=\"\ub0b4\uc6a9\uc99d\uba85 \uc11c\ub958\ub97c \uc791\uc131\ud569\ub2c8\ub2e4\">\ub0b4\uc6a9\uc99d\uba85</button>')"
          ": '<span style=\"color:#d9dee6\">-</span>')+'</td>'\n"
          "        + '<td style=\"'+TD+';text-align:right;font-weight:700;color:'+(x.bal>0?'#1a1a1a':'#9ca3af')+'\">'+_fxFmt(x.bal)+'</td>'\n")

OLD_SPAN = "if(exp) tr += '<tr><td colspan=\"13\" style=\"padding:0;border-bottom:2px solid #1B3A6B;background:#fff\">'+_fxLedgerRows(x)+'</td></tr>';"
NEW_SPAN = "if(exp) tr += '<tr><td colspan=\"14\" style=\"padding:0;border-bottom:2px solid #1B3A6B;background:#fff\">'+_fxLedgerRows(x)+'</td></tr>';"

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD_ANCHOR, NEW_ANCHOR, 1, 'r210 \ubcf8\ubb38 \uc0bd\uc785 (%s)' % path)
    s = rep(s, OLD_COL, NEW_COL, 1, 'r210 colgroup (%s)' % path)
    s = rep(s, OLD_TH, NEW_TH, 1, 'r210 \ud5e4\ub354 (%s)' % path)
    s = rep(s, OLD_TD, NEW_TD, 1, 'r210 \ubc84\ud2bc \uc140 (%s)' % path)
    s = rep(s, OLD_SPAN, NEW_SPAN, 1, 'r210 colspan (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r210 2026-09-29 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
