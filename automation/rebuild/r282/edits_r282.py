# -*- coding: utf-8 -*-
# r282 — 감사 화면 개편 (사용자 지시 2026-11-26)
#   ① 감사 안에 소카테고리 두 개: [명세표 만들기] · [저장된 명세표] — 팝업을 없애고 현재 화면에서 본다
#   ② 툴바의 '감사' 글자 삭제
#   ③ [엑셀 올리기] 단추를 끌어다 놓는 칸 안으로
#   ④ 저장된 명세표: 업체 검색 · 기간 검색 · 품목/규격 검색(업체+기간을 정해야 열림)
#      · 과거 → 현재 순 · 한 쪽 20건 · 내역 펼쳐 보기 · 다시 인쇄 · 삭제
#   ⑤ 미리보기는 글자만이 아니라 양식(선·칸 이름)까지 그려서 보여 준다
#      ※ 인감은 그리지 않는다 — 종이 양식에 이미 찍혀 있고, 공개 저장소에 올리지 않는다(l 규칙)
#  사용:  python3 edits_r282.py <index.html> [--test]
import io, sys, re

path = sys.argv[1]
IS_TEST = ('--test' in sys.argv)
s = io.open(path, encoding='utf-8').read()
orig = len(s)

def rep(old, new, cnt, label):
    global s
    n = s.count(old)
    assert n == cnt, 'ANCHOR %s: expected %d, found %d' % (label, cnt, n)
    s = s.replace(old, new)
    print('  ok  %s' % label)

assert '_asTab' not in s, 'FORBIDDEN(이미 r282 적용됨)'

# ── CSS ──────────────────────────────────────────────────────
rep("""    #pageAudit .as-doc-row > * { min-width:0; }""",
    """    #pageAudit .as-doc-row > * { min-width:0; }
    /* r282: 감사 안 소카테고리 */
    #pageAudit .as-subtab { font-size:13px; font-weight:700; color:#8a94a6; padding:6px 12px; cursor:pointer; border-bottom:2px solid transparent; white-space:nowrap; }
    #pageAudit .as-subtab:hover { color:#1B3A6B; }
    #pageAudit .as-subtab.on { color:#1B3A6B; border-bottom-color:#1B3A6B; }
    #pageAudit .as-lrow:hover { background:#f7f9fc; }""",
    1, '① 소카테고리 CSS')

# ── ①②③ 툴바·드롭 칸 ────────────────────────────────────────
rep("""    var h = '<div class="q-toolbar inv-toolbar">'
      + '<span class="inv-flat-label">감사</span>'
      + '<span style="flex:1"></span>'
      + _asBtn('엑셀 올리기','asPick()','primary')
      + ' ' + _asBtn('저장된 명세표','asOpenList()')
      + (adm ? (' ' + _asBtn('인쇄 보정','asCalib()')) : '')
      + '<input type="file" id="asFile" accept=".xls,.xlsx,.htm,.html" style="display:none" onchange="asOnFile(event)">'
      + '</div><div style="padding:14px 16px 40px">';""",
    """    var h = '<div class="q-toolbar inv-toolbar">'
      + '<span class="as-subtab'+(_asTab==='new'?' on':'')+'" onclick="asTab(\\'new\\')">명세표 만들기</span>'
      + '<span class="as-subtab'+(_asTab==='list'?' on':'')+'" onclick="asTab(\\'list\\')">저장된 명세표</span>'
      + '<span style="flex:1"></span>'
      + (adm ? _asBtn('인쇄 보정','asCalib()') : '')
      + '<input type="file" id="asFile" accept=".xls,.xlsx,.htm,.html" style="display:none" onchange="asOnFile(event)">'
      + '</div>';
    if(_asTab==='list'){ el.innerHTML = h + _asListHtml(); return; }
    h += '<div style="padding:14px 16px 40px">';""",
    1, '①②③ 툴바 — 소카테고리·감사 글자 삭제')

rep("""      h += '<div id="asDrop" style="border:2px dashed #c8d2de;background:#fafbfc;padding:40px 22px;text-align:center;line-height:1.9">'
        + '<div style="font-size:14.5px;font-weight:700;color:#1B3A6B">엑셀을 여기에 끌어다 놓으세요</div>'
        + '<div style="font-size:12.5px;color:#6b7280;margin-top:4px">SMC 유저특가 조회에서 받은 파일 · 위 [엑셀 올리기] 와 같습니다</div>'
        + '<div style="font-size:12px;color:#8a94a6;margin-top:10px">물류출하일마다 한 장 · 발행일은 출하일 + 2영업일</div>'
        + '</div>';""",
    """      h += '<div id="asDrop" style="border:2px dashed #c8d2de;background:#fafbfc;padding:38px 22px;text-align:center;line-height:1.9">'
        + '<div style="font-size:14.5px;font-weight:700;color:#1B3A6B">엑셀을 여기에 끌어다 놓으세요</div>'
        + '<div style="font-size:12.5px;color:#6b7280;margin-top:4px">SMC 유저특가 조회에서 받은 파일</div>'
        + '<div style="margin-top:14px">' + _asBtn('엑셀 올리기','asPick()','primary') + '</div>'
        + '<div style="font-size:12px;color:#8a94a6;margin-top:14px">물류출하일마다 한 장 · 발행일은 출하일 + 2영업일</div>'
        + '</div>';""",
    1, '③ 엑셀 올리기 단추를 끌어다 놓는 칸 안으로')

# ── ⑤ 미리보기에 양식 그리기 ────────────────────────────────
# grid 값: false = 인쇄(글자만) · true = [인쇄 보정] 시험 인쇄(칸 점선) · 'form' = 미리보기(양식까지)
rep("""    return '<div class="as-slip'+(grid?' as-grid':'')+'">'+o.join('')+'</div>';""",
    """    return '<div class="as-slip'+(grid===true?' as-grid':'')+'">'+(grid==='form'?_asFormSvg(p):'')+o.join('')+'</div>';""",
    1, '⑤ 미리보기에 양식 넣기')

rep("""      +'.as-grid{outline:1px dashed #9bb7dd}'
      +'.as-grid .as-f{outline:1px dotted #d9e2ef}';""",
    """      +'.as-grid{outline:1px dashed #9bb7dd}'
      +'.as-grid .as-f{outline:1px dotted #d9e2ef}'
      +'.as-form{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:1}'
      +'.as-slip .as-f{z-index:2}';""",
    1, '⑤ 미리보기 CSS')

rep("""    w.document.write(_asDocHtml(dr, dr.docs, true)); w.document.close();""",
    """    w.document.write(_asDocHtml(dr, dr.docs, 'form')); w.document.close();""",
    1, "⑤ 미리보기는 'form' 으로")

# 양식 그리기 함수 — 샘플 스캔 실측 좌표(mm). 인감·로고는 그리지 않는다.
rep("""  function _asPrintHtml(html){""",
    """  // r282: 미리보기용 양식(선·칸 이름). 실제 인쇄는 글자만 나가고 이 그림은 쓰지 않는다.
  //        종이 양식에 이미 있는 인감은 그리지 않는다(공개 저장소에 넣지 않는다).
  function _asFormSvg(p){
    var W=p.slipW, H=p.slipH, C='#4a6fb5';
    var o=[];
    function L(x1,y1,x2,y2,w){ o.push('<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="'+C+'" stroke-width="'+(w||0.22)+'"/>'); }
    function T(x,y,t,sz,anchor,bold){ o.push('<text x="'+x+'" y="'+y+'" font-size="'+(sz||2.4)+'" fill="'+C+'" text-anchor="'+(anchor||'start')+'"'+(bold?' font-weight="700"':'')+'>'+esc(t)+'</text>'); }
    // 바깥 테두리 + 가로 칸
    o.push('<rect x="0.2" y="0.3" width="'+(W-0.5)+'" height="117.9" fill="none" stroke="'+C+'" stroke-width="0.45"/>');
    [19.5,35.3,43.8,52.2,60.8,109.9].forEach(function(y){ L(0.2,y,W-0.3,y); });
    // 제목
    T(W/2,8.4,'거 래 명 세 서',6,'middle',1);
    L(W*0.27,9.6,W*0.73,9.6,0.35);
    T(W/2,13.6,'(공급받는자 보관용)',2.6,'middle');
    T(1.6,18.0,'거래명세서 번호:',2.5);
    T(W-26.5,18.0,'년',2.5); T(W-16.5,18.0,'월',2.5); T(W-6.5,18.0,'일',2.5);
    // 공급자(종이에 미리 찍혀 있다) / 공급받는자(타자)
    //   줄: 등록번호 19.5~27.2 · 상호·성명 27.2~35.3 · 주소 35.3~43.8 (타자 자리에서 역산)
    [6.7,16.2,100.0,103.0].forEach(function(x){ L(x,19.5,x,43.8); });
    L(0.2,27.2,100.0,27.2); L(103.0,27.2,W-0.3,27.2);
    L(81.0,27.2,81.0,35.3); L(88.0,27.2,88.0,35.3);            // 공급자 성명
    L(133.5,27.2,133.5,35.3); L(141.5,27.2,141.5,35.3);        // 공급받는자 성명
    T(3.4,23.2,'공',2.4,'middle'); T(3.4,31.0,'급',2.4,'middle'); T(3.4,39.6,'자',2.4,'middle');
    T(101.6,23.2,'공',2.0,'middle'); T(101.6,27.4,'급',2.0,'middle'); T(101.6,31.6,'받',2.0,'middle'); T(101.6,35.8,'는',2.0,'middle'); T(101.6,40.0,'자',2.0,'middle');
    T(8.1,22.8,'등록',2.1); T(8.1,25.4,'번호',2.1);
    T(8.6,31.9,'상 호',2.1); T(8.6,40.0,'주 소',2.1);
    T(82.4,30.5,'성',2.0); T(82.4,33.3,'명',2.0);
    T(134.9,30.5,'성',2.0); T(134.9,33.3,'명',2.0);
    // 총금액 — 한글 금액과 같은 칸 왼쪽
    T(1.6,48.6,'총금액',3.0,'start',1); T(14.5,48.6,'(공급가액+세액):',2.4);
    // 품목표 머리
    [7.7,96.5,107.0,128.1,150.3].forEach(function(x){ L(x,52.2,x,109.9); });
    T(4.0,57.5,'번호',2.4,'middle'); T(52.0,57.5,'품 명 및 규 격',2.6,'middle');
    T(101.7,57.5,'수 량',2.4,'middle'); T(117.5,57.5,'단   가',2.4,'middle');
    T(139.2,57.5,'공급가액',2.4,'middle'); T(160.4,57.5,'세   액',2.4,'middle');
    // 인수자·계
    L(15.5,109.9,15.5,118.2); L(62.0,109.9,62.0,118.2); L(82.0,109.9,82.0,118.2);
    L(128.1,109.9,128.1,118.2); L(150.3,109.9,150.3,118.2);   // 공급가액 계 · 세액 계
    T(2.0,115.5,'인 수 자',2.5); T(64.5,115.5,'계',2.5);
    T(58.5,115.5,'㊞',2.5);
    // 꼬리말
    T(W/2,123.0,'신한은행 : 100-001-944331  충해전기(주)      TEL : 02-2671-4474/5   FAX : 02-2672-3157',2.2,'middle');
    T(W-1.0,126.3,'E-MAIL : chjk@chjk.co.kr',2.2,'end');
    return '<svg class="as-form" viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg">'+o.join('')+'</svg>';
  }
  function _asPrintHtml(html){""",
    1, '⑤ 양식 그리기 함수')

# ── ④ 저장된 명세표 — 현재 화면에서 ─────────────────────────
rep("""  window.asOpenList = async function(){""",
    """  // ───────── r282 저장된 명세표 (현재 화면) ─────────
  var _asLRows = null, _asListBusy = false;
  var _asLF = { vname:'', from:'', to:'', q:'' };
  var _asLPage = 0, _asLOpen = {};
  var _AS_PER = 20;
  window.asTab = function(t){ _asTab = (t==='list')?'list':'new'; _asRender(); if(_asTab==='list' && !_asLRows) asLLoad(); };
  window.asLLoad = async function(force){
    if(_asListBusy) return;
    if(_asLRows && !force){ _asRender(); return; }
    _asListBusy = true; _asRender();
    try{
      var r = await _fbFetch(_asDocUrl(null));
      var d = r && r.ok ? (await r.json()) : null;
      _asLRows = d ? Object.keys(d).map(function(k){ var v=d[k]||{}; if(!v.id) v.id=k; return v; }).filter(function(v){ return v && v.date; }) : [];
      // 과거 → 현재 순
      _asLRows.sort(function(a,b){ return String(a.date||'').localeCompare(String(b.date||'')) || ((a.no||0)-(b.no||0)) || ((a.at||0)-(b.at||0)); });
    }catch(e){ _asLRows = []; showInfoModal('저장된 명세표', '불러오지 못했습니다: '+String(e && e.message || e)); }
    _asListBusy = false; _asRender();
  };
  function _asLReady(){ return !!(_asLF.vname && _asLF.from && _asLF.to); }   // 품목 검색은 업체+기간을 정해야 열린다
  function _asLFiltered(){
    var arr = (_asLRows||[]).slice();
    if(_asLF.vname) arr = arr.filter(function(v){ return _qNorm(v.vname).indexOf(_qNorm(_asLF.vname))>=0; });
    if(_asLF.from)  arr = arr.filter(function(v){ return String(v.date||'') >= _asLF.from; });
    if(_asLF.to)    arr = arr.filter(function(v){ return String(v.date||'') <= _asLF.to; });
    if(_asLF.q && _asLReady()){
      var q=_qNorm(_asLF.q);
      arr = arr.filter(function(v){ return (v.rows||[]).some(function(r){
        return _qNorm(r.spec).indexOf(q)>=0 || _qNorm(r.name).indexOf(q)>=0; }); });
    }
    return arr;
  }
  function _asListHtml(){
    var ready=_asLReady();
    var h = '<div style="padding:14px 16px 40px">';
    // 검색줄
    h += '<div style="border:1px solid #c8d2de;background:#fafbfc;padding:10px 12px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12.5px">'
      + '<span style="font-weight:700;color:#14305c">업체</span>'
      + '<div style="position:relative;width:250px">'
      +   '<input id="asLV" class="q-flat" type="text" placeholder="업체 검색…" autocomplete="off" value="'+esc(_asLF.vname)+'"'
      +     ' oninput="asLVdd()" onfocus="asLVdd()" onkeydown="asLVkey(event)">'
      +   '<div id="asLVdd" style="display:none;position:absolute;top:calc(100% + 2px);left:0;right:0;background:#fff;border:1px solid #d6e4f5;border-radius:8px;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:240px;overflow:auto;z-index:50"></div>'
      + '</div>'
      + '<span style="font-weight:700;color:#14305c;margin-left:4px">기간</span>'
      + '<input type="date" id="asLFrom" value="'+esc(_asLF.from)+'" onchange="asLSet(\\'from\\',this.value)" style="height:28px;padding:0 6px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit">'
      + '<span style="color:#8a94a6">~</span>'
      + '<input type="date" id="asLTo" value="'+esc(_asLF.to)+'" onchange="asLSet(\\'to\\',this.value)" style="height:28px;padding:0 6px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit">'
      + '<span style="font-weight:700;color:'+(ready?'#14305c':'#c3cad5')+';margin-left:4px">품목·규격</span>'
      + '<input id="asLQ" type="text" value="'+esc(_asLF.q)+'" oninput="asLSet(\\'q\\',this.value)" placeholder="'+(ready?'품목명 또는 품번':'업체와 기간을 먼저 정하세요')+'"'
      +   (ready?'':' disabled')+' style="width:200px;height:28px;padding:0 8px;border:1px solid '+(ready?'#c8d2de':'#e5e7eb')+';border-radius:0;font-size:12.5px;font-family:inherit;background:'+(ready?'#fff':'#f3f4f6')+'">'
      + '<span style="flex:1"></span>'
      + _asBtn('지우기','asLClear()') + ' ' + _asBtn('새로고침','asLLoad(1)')
      + '</div>';
    if(_asListBusy){ return h + '<div style="padding:30px;color:#9ca3af">불러오는 중…</div></div>'; }
    if(_asLRows===null){ return h + '<div style="padding:30px;color:#9ca3af">불러오는 중…</div></div>'; }
    var arr=_asLFiltered(), total=arr.length;
    var pages=Math.max(1, Math.ceil(total/_AS_PER));
    if(_asLPage>=pages) _asLPage=pages-1;
    var part=arr.slice(_asLPage*_AS_PER, _asLPage*_AS_PER+_AS_PER);
    h += '<div style="margin:12px 0 8px;font-size:12.5px;color:#6b7280">모두 <b>'+total+'</b>건'
      + (total?(' · '+(_asLPage*_AS_PER+1)+'~'+(_asLPage*_AS_PER+part.length)+'번째 · 과거 → 현재 순'):'')
      + '</div>';
    if(!total){ return h + '<div style="padding:30px;color:#9ca3af;border:1px solid #eef2f7">조건에 맞는 거래명세표가 없습니다.</div></div>'; }
    h += '<table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'
      + '<th style="padding:6px 8px;text-align:left;width:100px">발행일</th>'
      + '<th style="padding:6px 8px;text-align:center;width:54px">번호</th>'
      + '<th style="padding:6px 8px;text-align:left">업체</th>'
      + '<th style="padding:6px 8px;text-align:center;width:64px">품목</th>'
      + '<th style="padding:6px 8px;text-align:right;width:110px">공급가액</th>'
      + '<th style="padding:6px 8px;text-align:right;width:100px">세액</th>'
      + '<th style="padding:6px 8px;text-align:right;width:110px">합계</th>'
      + '<th style="padding:6px 8px;text-align:left;width:70px">작성</th>'
      + '<th style="padding:6px 8px;width:170px"></th></tr></thead><tbody>';
    part.forEach(function(v){
      var op=!!_asLOpen[v.id];
      h += '<tr class="as-lrow" style="border-bottom:1px solid #f1f4f8">'
        + '<td style="padding:5px 8px">'+esc(v.date||'')+'</td>'
        + '<td style="padding:5px 8px;text-align:center">'+esc(String(v.no||''))+'</td>'
        + '<td style="padding:5px 8px">'+esc(v.vname||'')+'</td>'
        + '<td style="padding:5px 8px;text-align:center">'+((v.rows||[]).length)+'</td>'
        + '<td style="padding:5px 8px;text-align:right">'+_asNum(v.supply)+'</td>'
        + '<td style="padding:5px 8px;text-align:right">'+_asNum(v.tax)+'</td>'
        + '<td style="padding:5px 8px;text-align:right"><b>'+_asNum(v.total)+'</b></td>'
        + '<td style="padding:5px 8px;color:#8a94a6">'+esc(v.by||'')+'</td>'
        + '<td style="padding:5px 8px;text-align:right;white-space:nowrap">'
        +   '<button type="button" onclick="asLToggle(\\''+esc(v.id)+'\\')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer;color:#1B3A6B">'+(op?'\\u25be 내역':'\\u25b8 내역')+'</button> '
        +   '<button type="button" onclick="asLPrint(\\''+esc(v.id)+'\\')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer">인쇄</button> '
        +   '<button type="button" onclick="asLDel(\\''+esc(v.id)+'\\')" title="삭제" style="border:1px solid #fecaca;background:#fff5f5;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer;color:#dc2626">삭제</button>'
        + '</td></tr>';
      if(op){
        h += '<tr><td colspan="9" style="padding:0 8px 10px;background:#fcfdff">'
          + (v.memo?('<div style="font-size:12px;color:#6b7280;margin:6px 0">비고: '+esc(v.memo)+'</div>'):'')
          + '<table style="width:100%;border-collapse:collapse;font-size:12px"><thead><tr style="background:#f3f6fa;color:#5b7ba6">'
          + '<th style="padding:3px 6px;text-align:right;width:36px">번호</th><th style="padding:3px 6px;text-align:left">품명 및 규격</th>'
          + '<th style="padding:3px 6px;text-align:center;width:60px">수량</th><th style="padding:3px 6px;text-align:right;width:90px">단가</th>'
          + '<th style="padding:3px 6px;text-align:right;width:100px">공급가액</th><th style="padding:3px 6px;text-align:right;width:90px">세액</th></tr></thead><tbody>'
          + (v.rows||[]).slice(0,200).map(function(r,i){ return '<tr style="border-bottom:1px solid #f1f4f8">'
              + '<td style="padding:2px 6px;text-align:right;color:#8a94a6">'+(i+1)+'</td>'
              + '<td style="padding:2px 6px">'+(r.name?('<b>'+esc(r.name)+'</b>  '):'')+esc(r.spec)+'</td>'
              + '<td style="padding:2px 6px;text-align:center">'+_asNum(r.qty)+'</td>'
              + '<td style="padding:2px 6px;text-align:right">'+_asNum(r.price)+'</td>'
              + '<td style="padding:2px 6px;text-align:right">'+_asNum(r.supply)+'</td>'
              + '<td style="padding:2px 6px;text-align:right">'+_asNum(r.tax)+'</td></tr>'; }).join('')
          + '</tbody></table>'
          + (((v.rows||[]).length>200)?('<div style="padding:5px 2px;font-size:12px;color:#8a94a6">앞 200줄만 보여 줍니다 · 모두 '+(v.rows||[]).length+'줄</div>'):'')
          + '</td></tr>';
      }
    });
    h += '</tbody></table>';
    if(pages>1){
      h += '<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-top:14px;font-size:12.5px">'
        + _asBtn('◀ 이전','asLGo('+(_asLPage-1)+')')
        + '<span style="color:#6b7280">'+(_asLPage+1)+' / '+pages+'</span>'
        + _asBtn('다음 ▶','asLGo('+(_asLPage+1)+')')
        + '</div>';
    }
    return h + '</div>';
  }
  window.asLGo = function(n){ var arr=_asLFiltered(); var pages=Math.max(1,Math.ceil(arr.length/_AS_PER));
    _asLPage = Math.max(0, Math.min(pages-1, n)); _asRender(); };
  window.asLSet = function(k, v){
    _asLF[k] = String(v||'').trim();
    if(k!=='q' && !_asLReady()) _asLF.q='';
    _asLPage=0; _asRender();
    if(k==='q'){ var e=document.getElementById('asLQ'); if(e){ e.focus(); e.setSelectionRange(e.value.length,e.value.length); } }
  };
  window.asLClear = function(){ _asLF={vname:'',from:'',to:'',q:''}; _asLPage=0; _asLOpen={}; _asRender(); };
  window.asLToggle = function(id){ _asLOpen[id] = !_asLOpen[id]; _asRender(); };
  window.asLVdd = function(){
    var inp=document.getElementById('asLV'), dd=document.getElementById('asLVdd'); if(!inp||!dd) return;
    var rows=_asVendorRows(inp.value).slice(0,60);
    window._asLVNav = rows.map(function(r){ return r.name; }); window._asLVActive=-1;
    if(!rows.length){ dd.innerHTML='<div style="padding:9px 12px;color:#bbb;font-size:13px">일치하는 업체 없음</div>'; }
    else dd.innerHTML = rows.map(function(r,i){
      var nm=String(r.name).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\\\'");
      return '<div data-aslvi="'+i+'" class="asvd-item" onclick="asLPickV(\\''+nm+'\\')" style="padding:8px 13px;border-bottom:1px solid #edf1f5;display:flex;align-items:center;justify-content:space-between;gap:10px;cursor:pointer">'
        + '<span style="flex:1;min-width:0;display:flex;align-items:baseline;gap:6px"><span style="font-size:13px;color:#1a1a1a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(r.name)+'</span>'
        + (r.bz?('<span style="font-size:11px;color:#9ca3af;white-space:nowrap">'+esc(r.bz)+'</span>'):'')+'</span>'
        + '<span style="font-size:11px;color:#9ca3af;white-space:nowrap">'+esc(r.right)+'</span></div>';
    }).join('');
    dd.style.display='block';
  };
  window.asLVkey = function(ev){
    var dd=document.getElementById('asLVdd'); if(!dd) return;
    var n=(window._asLVNav||[]).length;
    if(ev.key==='Escape'){ dd.style.display='none'; return; }
    if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){
      if(!n) return; ev.preventDefault();
      window._asLVActive=(ev.key==='ArrowDown')?Math.min(n-1,(window._asLVActive|0)+1):Math.max(0,(window._asLVActive|0)-1);
      Array.prototype.forEach.call(dd.querySelectorAll('.asvd-item'), function(el){
        var on=(+el.getAttribute('data-aslvi'))===window._asLVActive;
        el.style.background = on?'#eaf1fb':'#fff'; if(on && el.scrollIntoView) el.scrollIntoView({block:'nearest'});
      });
      return;
    }
    if(ev.key==='Enter'){ ev.preventDefault();
      var idx=(window._asLVActive>=0)?window._asLVActive:(n===1?0:-1);
      if(idx>=0) asLPickV(window._asLVNav[idx]);
      else asLSet('vname', (document.getElementById('asLV')||{}).value||'');
    }
  };
  window.asLPickV = function(nm){ var dd=document.getElementById('asLVdd'); if(dd) dd.style.display='none'; asLSet('vname', nm); };
  window.asLPrint = function(id){
    var v=(_asLRows||[]).filter(function(x){ return x.id===id; })[0]; if(!v) return;
    var dr={ vid:v.vid, vname:v.vname, biz:v.biz, ceo:v.ceo, addr:v.addr };
    _asPrintHtml(_asDocHtml(dr, [{ ship:v.ship, date:v.date, no:v.no, rows:v.rows||[], memo:v.memo||'' }], false));
  };
  window.asLDel = function(id){
    var v=(_asLRows||[]).filter(function(x){ return x.id===id; })[0]; if(!v) return;
    if(_isViewer()){ showInfoModal('삭제','보기 전용 계정입니다.'); return; }
    showConfirmModal('거래명세표 삭제',
      esc(v.date||'')+' · 번호 '+esc(String(v.no||''))+' · '+esc(v.vname||'')+'\\n품목 '+((v.rows||[]).length)+'건 · 합계 '+_asNum(v.total)+'\\n\\n이 거래명세표를 지웁니다. 되돌릴 수 없습니다.',
      async function(){
        try{
          var r = await _fbFetch(_asDocUrl(id), {method:'DELETE'});
          if(!r || !r.ok) throw new Error('HTTP '+(r?r.status:'네트워크'));
          _asLRows = (_asLRows||[]).filter(function(x){ return x.id!==id; });
          delete _asLOpen[id];
          _asRender();
          showInfoModal('삭제','지웠습니다.');
        }catch(e){ showInfoModal('삭제 실패', String(e && e.message || e)); }
      }, '삭제', '#dc2626');
  };
  window.asOpenList = async function(){""",
    1, '④ 저장된 명세표 화면')

# 옛 팝업 진입점은 소카테고리로 넘긴다
rep("""  window.asOpenList = async function(){
    var ov=_asOverlay('asListOv');""",
    """  window.asOpenList = function(){ asTab('list'); };   // r282: 팝업 대신 소카테고리
  window.asOpenListOld = async function(){
    var ov=_asOverlay('asListOv');""",
    1, '④ 옛 팝업 진입점 정리')

# 탭 상태 변수
rep("""  var _asDrafts = [], _asRaw = [], _asFileName = '', _asShowInput = false;""",
    """  var _asDrafts = [], _asRaw = [], _asFileName = '', _asShowInput = false;
  var _asTab = 'new';   // r282: 감사 안 소카테고리 — 'new' 명세표 만들기 / 'list' 저장된 명세표""",
    1, '④ 탭 상태 변수')

# 저장 뒤 목록 캐시를 비운다
rep("""          showInfoModal('저장 완료', '거래명세표 '+n+'건을 저장했습니다.' + (added?('\\n원장에 품목 '+added+'건을 등록했습니다.'):''));""",
    """          _asLRows = null;   // r282: 저장된 명세표 목록을 다시 읽는다
          showInfoModal('저장 완료', '거래명세표 '+n+'건을 저장했습니다.' + (added?('\\n원장에 품목 '+added+'건을 등록했습니다.'):''));""",
    1, '④ 저장 뒤 목록 갱신')

# 발견한 버그: 금액이 길면 한글 금액이 '(₩…)' 와 겹쳐 찍혔다 (예 1,237,537 → 15자).
rep("""      F(p.totKoX, p.totY, _asKoAmt(head.total)+'整');""",
    """      var _ko=_asKoAmt(head.total)+'整';
      var _koW=_ko.length*p.fs*0.3528, _koX=p.totKoX;                 // 한글 1자 = 글자 크기 그대로
      if(_koX+_koW > p.totNumX-1.5) _koX=Math.max(1.0, p.totNumX-1.5-_koW);   // 겹치면 왼쪽으로 민다
      F(_koX, p.totY, _ko);""",
    1, '⑥ 긴 한글 금액 겹침 막기')

# ⑦ 재고를 업무 아래 소카테고리로 — 매입처와 감사 사이 (사용자 지시 11-26)
rep("""  <button class="page-tab" data-page="inventory">재고</button>\n""", "", 1, '⑦ 상단 [재고] 탭 제거')
rep("""  <button class="sub-tab" data-page="audit">감사</button><!-- r278 -->""",
    """  <button class="sub-tab" data-page="inventory">재고</button><!-- r282: 상단 탭에서 옮겨 옴 -->
  <button class="sub-tab" data-page="audit">감사</button><!-- r278 -->""",
    1, '⑦ 업무 소카테고리에 [재고] 추가')
rep("""    var _ETC=['links','purchase','audit'];   // r278 · r279: 매입처를 업무 아래로""",
    """    var _ETC=['links','purchase','inventory','audit'];   // r278 · r279 매입처 · r282 재고를 업무 아래로""",
    1, '⑦ _ETC 에 재고')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r282 2026-11-26 -->')
    print('  ok  test marker %s -> r282' % m.group(0))

for k in ['window.asTab', '_asListHtml', 'window.asLDel', 'window.asLPrint', 'window.asLToggle',
          'window.asLVdd', 'window.asLGo', '_asFormSvg', 'as-subtab', '거 래 명 세 서',
          '업체와 기간을 먼저 정하세요', '과거 → 현재 순',
          "grid==='form'?_asFormSvg(p)", "_asDocHtml(dr, dr.docs, 'form')",
          'if(_koX+_koW > p.totNumX-1.5)',
          "_ETC=['links','purchase','inventory','audit']",
          '<button class="sub-tab" data-page="inventory">재고</button>']:
    assert k in s, 'NEED missing: ' + k
for k in ['renderAuditPage', '_asBindDrop', 'id="asDrop"', 'window.asSavePrint', 'as-doc-row']:
    assert k in s, 'KEEP missing: ' + k
assert '<span class="inv-flat-label">감사</span>' not in s, 'FORBIDDEN: 툴바 감사 글자가 남아 있다'
assert '<button class="page-tab" data-page="inventory">' not in s, 'FORBIDDEN: 상단 재고 탭이 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r282 적용 완료: %d -> %d' % (orig, len(s)))
