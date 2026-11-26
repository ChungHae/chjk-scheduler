# -*- coding: utf-8 -*-
# r283 — 감사 화면 손보기 (사용자 지시 2026-11-26)
#   ① 저장된 명세표: [내역] 단추를 없애고 **줄 아무 곳이나 눌러** 접힘/펼침
#   ② 내역 표의 품목·규격을 따로 왼쪽 정렬하고, 규격이 위 표의 '업체' 와 같은 자리에서 시작
#   ③ 기간 검색칸: 20260101 이라고 치면 2026-01-01 로 바뀌고 커서가 끝 날짜로 넘어감
#   ④ 명세표 만들기: 올린 파일 [비우기] · [다른 파일 올리기]
#   ⑤ 명세표 만들기: 접기 단추를 없애고 **전표 줄 아무 곳이나 눌러** 접힘/펼침 ('N품목 · M장' 표시 삭제)
#   ⑥ 내역 표 번호 칸 가운데 정렬 · 칸 높이 조금 높임 (양쪽 화면)
#   ⑦ 명세표 만들기: 비고 칸 가로 2배 · 번호 칸 높이 조금 낮춤
#  ※ 미리보기 양식 재현(사용자가 올린 거래명세표.pdf)은 파일을 다시 받아 별도 리비전에서 한다.
#  사용:  python3 edits_r283.py <index.html> [--test]
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


def repblock(start, end, new, label):
    global s
    i = s.find(start); assert i >= 0, 'BLOCK start not found: ' + label
    j = s.find(end, i); assert j > i, 'BLOCK end not found: ' + label
    s = s[:i] + new + s[j:]
    print('  ok  %s' % label)

assert 'asLDateIn' not in s, 'FORBIDDEN(이미 r283 적용됨)'

# ── CSS ──────────────────────────────────────────────────────
rep("""    #pageAudit .as-lrow:hover { background:#f7f9fc; }""",
    """    #pageAudit .as-lrow:hover { background:#f7f9fc; }
    /* r283: 줄 아무 곳이나 눌러 접힘/펼침 */
    #pageAudit .as-lrow { cursor:pointer; }
    #pageAudit .as-doc-row { cursor:pointer; }
    #pageAudit .as-doc-row input { cursor:text; }
    #pageAudit .as-doc-head:hover { background:#f7f9fc; }
    #pageAudit .as-cap { font-size:11.5px; color:#8a94a6; }""",
    1, '① 줄 클릭 CSS')

# ── ⑤⑦ 명세표 만들기 전표 줄 ────────────────────────────────
rep("""          + '<div class="as-doc-row">'
          + '<button type="button" onclick="asToggleDoc('+di+','+ci+')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:12px;padding:3px 9px;cursor:pointer;font-family:inherit;color:#1B3A6B;text-align:left">'
          +   (d.open?'\\u25be':'\\u25b8')+' '+d.rows.length+'품목 · '+pages+'장'
          + '</button>'
          + '<span style="color:#8a94a6">물류출하일 '+esc(_asDot(d.ship))+'</span>'
          + '<span>발행일 <b>'+esc(d.date)+'</b></span>'
          + '<span>번호 <input value="'+(d.no==null?'':d.no)+'" oninput="asSetNo('+di+','+ci+',this.value)" style="width:48px;height:26px;text-align:center;padding:0 4px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></span>'
          + '<span>공급가액 <b>'+_asNum(supply)+'</b> · 세액 <b>'+_asNum(tax)+'</b> · 합계 <b>'+_asNum(supply+tax)+'</b></span>'
          + '<span style="justify-self:end;white-space:nowrap">비고 <input value="'+esc(d.memo||'')+'" oninput="asSetMemo('+di+','+ci+',this.value)" placeholder="(선택)" style="width:150px;height:26px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit"></span>'
          + '</div>'""",
    """          // r283: 접기 단추를 없애고 줄 아무 곳이나 누르면 접히고 펼쳐진다(칸 안 글자는 그대로 고친다).
          + '<div class="as-doc-row as-doc-head" onclick="asToggleDoc('+di+','+ci+')" title="누르면 품목이 펼쳐집니다">'
          + '<span style="color:#1B3A6B;font-size:12px">'+(d.open?'\\u25be':'\\u25b8')+'</span>'
          + '<span style="color:#8a94a6">물류출하일 '+esc(_asDot(d.ship))+'</span>'
          + '<span>발행일 <b>'+esc(d.date)+'</b></span>'
          + '<span>번호 <input value="'+(d.no==null?'':d.no)+'" onclick="event.stopPropagation()" oninput="asSetNo('+di+','+ci+',this.value)" style="width:48px;height:22px;text-align:center;padding:0 4px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></span>'
          + '<span>공급가액 <b>'+_asNum(supply)+'</b> · 세액 <b>'+_asNum(tax)+'</b> · 합계 <b>'+_asNum(supply+tax)+'</b></span>'
          + '<span style="justify-self:end;white-space:nowrap">비고 <input value="'+esc(d.memo||'')+'" onclick="event.stopPropagation()" oninput="asSetMemo('+di+','+ci+',this.value)" placeholder="(선택)" style="width:300px;height:26px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit"></span>'
          + '</div>'""",
    1, '⑤⑦ 전표 줄 — 줄 클릭 · 비고 2배 · 번호칸 낮춤')

rep("""    #pageAudit .as-doc-row { display:grid; grid-template-columns:128px 152px 132px 92px minmax(260px,1fr) auto; align-items:center; column-gap:14px; row-gap:6px; font-size:12.5px; }""",
    """    #pageAudit .as-doc-row { display:grid; grid-template-columns:18px 152px 132px 92px minmax(260px,1fr) auto; align-items:center; column-gap:14px; row-gap:6px; font-size:12.5px; }""",
    1, '⑤ 전표 줄 격자 폭 (단추 자리를 화살표로)')

rep("""    @media (max-width:980px){ #pageAudit .as-doc-row { grid-template-columns:128px 152px 132px 92px; }""",
    """    @media (max-width:980px){ #pageAudit .as-doc-row { grid-template-columns:18px 152px 132px 92px; }""",
    1, '⑤ 좁은 화면 격자 폭')

# ── ⑥ 명세표 만들기 내역 표 — 번호 가운데 · 품목/규격 분리 · 칸 높이 ──
rep("""          + '<th style="padding:4px 6px;text-align:right;width:36px">번호</th><th style="padding:4px 6px;text-align:left">품명 및 규격</th>'
          + '<th style="padding:4px 6px;text-align:center;width:60px">수량</th><th style="padding:4px 6px;text-align:right;width:90px">단가</th>'
          + '<th style="padding:4px 6px;text-align:right;width:100px">공급가액</th><th style="padding:4px 6px;text-align:right;width:90px">세액</th></tr></thead><tbody>';""",
    """          + '<th style="padding:6px;text-align:center;width:44px">번호</th>'
          + '<th style="padding:6px 8px;text-align:left;width:150px">품목</th>'
          + '<th style="padding:6px 8px;text-align:left">규격</th>'
          + '<th style="padding:6px;text-align:center;width:60px">수량</th><th style="padding:6px;text-align:right;width:90px">단가</th>'
          + '<th style="padding:6px;text-align:right;width:100px">공급가액</th><th style="padding:6px;text-align:right;width:90px">세액</th></tr></thead><tbody>';""",
    1, '⑥ 만들기 내역 머리')

rep("""            + '<td style="padding:3px 6px;text-align:right;color:#8a94a6">'+(i+1)+'</td>'
            + '<td style="padding:3px 6px">'+(r.name?('<b>'+esc(r.name)+'</b>  '):'<span style="color:#dc2626">(품목 없음) </span>')+esc(r.spec)+'</td>'
            + '<td style="padding:3px 6px;text-align:center">'+_asNum(r.qty)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.price)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.supply)+'</td>'
            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.tax)+'</td></tr>';""",
    """            + '<td style="padding:6px;text-align:center;color:#8a94a6">'+(i+1)+'</td>'
            + '<td style="padding:6px 8px;text-align:left">'+(r.name?('<b>'+esc(r.name)+'</b>'):'<span style="color:#dc2626">(품목 없음)</span>')+'</td>'
            + '<td style="padding:6px 8px;text-align:left">'+esc(r.spec)+'</td>'
            + '<td style="padding:6px;text-align:center">'+_asNum(r.qty)+'</td>'
            + '<td style="padding:6px;text-align:right">'+_asNum(r.price)+'</td>'
            + '<td style="padding:6px;text-align:right">'+_asNum(r.supply)+'</td>'
            + '<td style="padding:6px;text-align:right">'+_asNum(r.tax)+'</td></tr>';""",
    1, '⑥ 만들기 내역 칸')

# ── ④ 파일 비우기 · 다른 파일 올리기 ────────────────────────
rep("""    h += '<div style="font-size:12px;color:#6b7280;margin-bottom:10px">파일: <b>'+esc(_asFileName)+'</b> · 품번 '+_asRaw.length+'줄</div>';""",
    """    // r283: 잘못 올렸을 때 다시 올리거나 비울 수 있게
    h += '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12px;color:#6b7280;margin-bottom:10px">'
      + '<span>파일: <b>'+esc(_asFileName)+'</b> · 품번 '+_asRaw.length+'줄</span>'
      + _asBtn('다른 파일 올리기','asPick()')
      + _asBtn('비우기','asClearFile()','warn')
      + '<span class="as-cap">끌어다 놓아도 바뀝니다</span>'
      + '</div>';""",
    1, '④ 파일 비우기·다시 올리기 단추')

rep("""  window.asPick = function(){ var i=document.getElementById('asFile'); if(i) i.click(); };""",
    """  window.asPick = function(){ var i=document.getElementById('asFile'); if(i){ i.value=''; i.click(); } };
  // r283: 올린 파일과 작성 중인 거래명세표를 비운다 (저장한 것은 그대로)
  window.asClearFile = function(){
    showConfirmModal('비우기',
      '올린 파일과 작성 중인 거래명세표를 모두 비웁니다.\\n저장해 둔 명세표는 지워지지 않습니다.',
      function(){
        _asDrafts=[]; _asRaw=[]; _asFileName=''; _asShowInput=false;
        var f=document.getElementById('asFile'); if(f) f.value='';
        _asRender();
      }, '비우기', '#dc2626');
  };""",
    1, '④ asClearFile')

# ── ③ 기간 검색칸 ───────────────────────────────────────────
rep("""      + '<input type="date" id="asLFrom" value="'+esc(_asLF.from)+'" onchange="asLSet(\\'from\\',this.value)" style="height:28px;padding:0 6px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit">'
      + '<span style="color:#8a94a6">~</span>'
      + '<input type="date" id="asLTo" value="'+esc(_asLF.to)+'" onchange="asLSet(\\'to\\',this.value)" style="height:28px;padding:0 6px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit">'""",
    """      + '<input type="text" id="asLFrom" inputmode="numeric" maxlength="10" placeholder="20260101" value="'+esc(_asLF.from)+'" oninput="asLDateIn(this,\\'from\\')" onkeydown="asLDateKey(event,this,\\'from\\')" onblur="asLDateIn(this,\\'from\\',1)" style="width:104px;height:28px;padding:0 8px;text-align:center;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit">'
      + '<span style="color:#8a94a6">~</span>'
      + '<input type="text" id="asLTo" inputmode="numeric" maxlength="10" placeholder="20261231" value="'+esc(_asLF.to)+'" oninput="asLDateIn(this,\\'to\\')" onkeydown="asLDateKey(event,this,\\'to\\')" onblur="asLDateIn(this,\\'to\\',1)" style="width:104px;height:28px;padding:0 8px;text-align:center;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit">'""",
    1, '③ 기간 입력칸을 숫자 8자리로')

rep("""  window.asLSet = function(k, v){""",
    """  // r283: 20260101 → 2026-01-01 로 바꿔 넣고, 시작 날짜를 다 적으면 끝 날짜 칸으로 넘어간다
  function _asYmdOk(y,m,d){
    if(y<1900 || y>2999 || m<1 || m>12 || d<1 || d>31) return false;
    var dt=new Date(y, m-1, d);
    return dt.getFullYear()===y && dt.getMonth()===m-1 && dt.getDate()===d;
  }
  window.asLDateIn = function(el, which, isBlur){
    var g = String(el.value||'').replace(/[^0-9]/g,'').slice(0,8);
    var t = g;
    if(g.length>6) t = g.slice(0,4)+'-'+g.slice(4,6)+'-'+g.slice(6);
    else if(g.length>4) t = g.slice(0,4)+'-'+g.slice(4);
    el.value = t;
    if(g.length<8){
      el.style.borderColor = '#c8d2de';
      if(isBlur && !g && _asLF[which]){ _asLF[which]=''; if(!_asLReady()) _asLF.q=''; _asLPage=0; _asRender(); }
      return;
    }
    var y=+g.slice(0,4), m=+g.slice(4,6), d=+g.slice(6,8);
    if(!_asYmdOk(y,m,d)){ el.style.borderColor='#dc2626'; return; }
    el.style.borderColor = '#c8d2de';
    if(_asLF[which] === t) return;        // 값이 그대로면 다시 그리지 않는다(블러 때 커서가 날아간다)
    _asLF[which] = t;
    if(!_asLReady()) _asLF.q = '';
    _asLPage = 0;
    _asLFocus = (which==='from' && !isBlur) ? 'asLTo' : null;
    _asRender();
  };
  window.asLDateKey = function(ev, el, which){
    if(ev.key==='Enter'){ ev.preventDefault(); asLDateIn(el, which, 1);
      if(which==='from'){ var t=document.getElementById('asLTo'); if(t) t.focus(); } }
  };
  window.asLSet = function(k, v){""",
    1, '③ asLDateIn · asLDateKey')

# 다시 그린 뒤 커서를 되돌려 준다
rep("""    if(_asTab==='list'){ el.innerHTML = h + _asListHtml(); return; }""",
    """    if(_asTab==='list'){ el.innerHTML = h + _asListHtml(); _asLRestore(); return; }""",
    1, '③ 목록 화면에서 커서 복원')

rep("""  var _asLPage = 0, _asLOpen = {};""",
    """  var _asLPage = 0, _asLOpen = {};
  var _asLFocus = null;                       // r283: 다시 그린 뒤 커서를 둘 칸
  function _asLRestore(){
    var id=_asLFocus; _asLFocus=null; if(!id) return;
    var e=document.getElementById(id); if(!e) return;
    try{ e.focus(); e.setSelectionRange(e.value.length, e.value.length); }catch(_e){}
  }""",
    1, '③ _asLFocus · _asLRestore')

rep("""    if(k==='q'){ var e=document.getElementById('asLQ'); if(e){ e.focus(); e.setSelectionRange(e.value.length,e.value.length); } }""",
    """    if(k==='q'){ var e=document.getElementById('asLQ'); if(e){ e.focus(); e.setSelectionRange(e.value.length,e.value.length); } }   // r283: 즉시 복원(아래 _asLRestore 와 중복돼도 해롭지 않다)""",
    1, '③ q 칸 커서 주석')

# ── ①⑥ 저장된 명세표 줄·내역 ───────────────────────────────
rep("""      + '<th style="padding:6px 8px;text-align:left;width:70px">작성</th>'
      + '<th style="padding:6px 8px;width:170px"></th></tr></thead><tbody>';""",
    """      + '<th style="padding:6px 8px;text-align:left;width:70px">작성</th>'
      + '<th style="padding:6px 8px;width:116px"></th></tr></thead><tbody>';""",
    1, '① 작업 칸 폭 줄임')

rep("""      h += '<tr class="as-lrow" style="border-bottom:1px solid #f1f4f8">'
        + '<td style="padding:5px 8px">'+esc(v.date||'')+'</td>'""",
    """      h += '<tr class="as-lrow" onclick="asLToggle(\\''+esc(v.id)+'\\')" title="누르면 내역이 펼쳐집니다" style="border-bottom:1px solid #f1f4f8">'
        + '<td style="padding:5px 8px"><span style="color:#5b7ba6;margin-right:4px">'+(op?'\\u25be':'\\u25b8')+'</span>'+esc(v.date||'')+'</td>'""",
    1, '① 줄 클릭으로 펼침')

rep("""        +   '<button type="button" onclick="asLToggle(\\''+esc(v.id)+'\\')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer;color:#1B3A6B">'+(op?'\\u25be 내역':'\\u25b8 내역')+'</button> '
        +   '<button type="button" onclick="asLPrint(\\''+esc(v.id)+'\\')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer">인쇄</button> '
        +   '<button type="button" onclick="asLDel(\\''+esc(v.id)+'\\')" title="삭제" style="border:1px solid #fecaca;background:#fff5f5;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer;color:#dc2626">삭제</button>'""",
    """        +   '<button type="button" onclick="event.stopPropagation();asLPrint(\\''+esc(v.id)+'\\')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer">인쇄</button> '
        +   '<button type="button" onclick="event.stopPropagation();asLDel(\\''+esc(v.id)+'\\')" title="삭제" style="border:1px solid #fecaca;background:#fff5f5;border-radius:0;font-size:11.5px;padding:2px 8px;cursor:pointer;color:#dc2626">삭제</button>'""",
    1, '① [내역] 단추 삭제 · 나머지 단추는 줄 클릭과 분리')

rep("""        h += '<tr><td colspan="9" style="padding:0 8px 10px;background:#fcfdff">'
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
              + '<td style="padding:2px 6px;text-align:right">'+_asNum(r.tax)+'</td></tr>'; }).join('')""",
    """        // r283: 번호 44 + 품목 110 = 위 표의 발행일 100 + 번호 54 → 규격이 '업체' 와 같은 자리에서 시작한다
        h += '<tr><td colspan="9" style="padding:0 0 10px;background:#fcfdff">'
          + (v.memo?('<div style="font-size:12px;color:#6b7280;margin:6px 0 6px 8px">비고: '+esc(v.memo)+'</div>'):'')
          + '<table style="width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed"><thead><tr style="background:#f3f6fa;color:#5b7ba6">'
          + '<th style="padding:6px 8px;text-align:center;width:44px">번호</th>'
          + '<th style="padding:6px 8px;text-align:left;width:110px">품목</th>'
          + '<th style="padding:6px 8px;text-align:left">규격</th>'
          + '<th style="padding:6px 8px;text-align:center;width:60px">수량</th><th style="padding:6px 8px;text-align:right;width:90px">단가</th>'
          + '<th style="padding:6px 8px;text-align:right;width:110px">공급가액</th><th style="padding:6px 8px;text-align:right;width:100px">세액</th></tr></thead><tbody>'
          + (v.rows||[]).slice(0,200).map(function(r,i){ return '<tr style="border-bottom:1px solid #f1f4f8">'
              + '<td style="padding:6px 8px;text-align:center;color:#8a94a6">'+(i+1)+'</td>'
              + '<td style="padding:6px 8px;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+esc(r.name||'')+'">'+(r.name?('<b>'+esc(r.name)+'</b>'):'')+'</td>'
              + '<td style="padding:6px 8px;text-align:left">'+esc(r.spec)+'</td>'
              + '<td style="padding:6px 8px;text-align:center">'+_asNum(r.qty)+'</td>'
              + '<td style="padding:6px 8px;text-align:right">'+_asNum(r.price)+'</td>'
              + '<td style="padding:6px 8px;text-align:right">'+_asNum(r.supply)+'</td>'
              + '<td style="padding:6px 8px;text-align:right">'+_asNum(r.tax)+'</td></tr>'; }).join('')""",
    1, '①⑥ 저장된 명세표 내역 표')

rep("""          + (((v.rows||[]).length>200)?('<div style="padding:5px 2px;font-size:12px;color:#8a94a6">앞 200줄만 보여 줍니다 · 모두 '+(v.rows||[]).length+'줄</div>'):'')""",
    """          + (((v.rows||[]).length>200)?('<div style="padding:5px 8px;font-size:12px;color:#8a94a6">앞 200줄만 보여 줍니다 · 모두 '+(v.rows||[]).length+'줄</div>'):'')""",
    1, '① 안내 줄 들여쓰기')

# ── ⑧ 업체 검색 드롭다운: 바깥을 누르면 닫힌다 (사용자 지적) ──
rep("""  function _asBindDrop(){""",
    """  // r283: 드롭다운 밖을 누르면 닫는다 (한 번만 건다)
  function _asBindDD(){
    if(window.__asDDBound) return; window.__asDDBound = true;
    document.addEventListener('mousedown', function(ev){
      var t = ev.target;
      Array.prototype.forEach.call(document.querySelectorAll('#pageAudit [id^="asVdd"], #pageAudit #asLVdd'), function(dd){
        if(dd.style.display==='none') return;
        var inp = document.getElementById(dd.id.replace('dd','').replace('asV','asV').replace('asL','asL'));
        if(dd.contains(t)) return;
        if(inp && inp===t) return;
        // 짝이 되는 입력칸(asV0 ↔ asVdd0 · asLV ↔ asLVdd)
        var pair = document.getElementById(dd.id==='asLVdd' ? 'asLV' : ('asV'+dd.id.slice(5)));
        if(pair && (pair===t || pair.contains(t))) return;
        dd.style.display='none';
      });
    }, true);
  }
  function _asBindDrop(){""",
    1, '⑧ 드롭다운 바깥 클릭 닫기')

rep("""  function _asBindDrop(){
    var el=document.getElementById('pageAudit');""",
    """  function _asBindDrop(){
    _asBindDD();                       // r283: 드롭다운 닫기도 같이 건다
    var el=document.getElementById('pageAudit');""",
    1, '⑧ _asBindDrop 에서 함께 연결')

# ── ⑨ 인쇄 위치 보정 (사용자 시험 인쇄 실측 2026-11-26) ──
#    빈 양식 PDF 300dpi 와 시험 인쇄 스캔을 겹쳐 재어 보니
#    가로는 x 가 커질수록 벌어졌고(약 +0.77%, 기준 +0.7mm) 세로는 약 +0.5% 였다.
#    '계' 합계는 칸(110.07~118.40) 바닥에 걸쳐 찍혀 있었다 → 칸 가운데로.
rep("""    offX:0, offY:0,                            // 프린터 보정(전체 이동)""",
    """    offX:-0.7, offY:0,                         // 프린터 보정(전체 이동) · r283 실측
    sclX:0.9924, sclY:0.9950,                  // r283: 프린터 배율 보정 (1 = 그대로)""",
    1, '⑨ 배율·이동 기본값')

rep("""    sumY:114.9,""", """    sumY:112.5,                                // r283: '계' 합계가 칸 바닥에 걸쳐 찍혀 가운데로""", 1, '⑨ 계 합계 자리')

rep("""      var st='position:absolute;white-space:pre;top:'+(y+p.offY)+'mm;font-size:'+(opt.fs||p.fs)+'pt;line-height:'+(opt.fs||p.fs)+'pt;';
      if(opt.right) st+='right:'+((p.slipW-x)-p.offX)+'mm;text-align:right;';
      else st+='left:'+(x+p.offX)+'mm;';
      if(opt.w) st+='width:'+opt.w+'mm;overflow:hidden;';""",
    """      var _sx=(p.sclX||1), _sy=(p.sclY||1);                     // r283: 프린터 배율 보정
      var _px=x*_sx + p.offX, _py=y*_sy + p.offY;
      var st='position:absolute;white-space:pre;top:'+_py+'mm;font-size:'+(opt.fs||p.fs)+'pt;line-height:'+(opt.fs||p.fs)+'pt;';
      if(opt.right) st+='right:'+(p.slipW-_px)+'mm;text-align:right;';
      else st+='left:'+_px+'mm;';
      if(opt.w) st+='width:'+(opt.w*_sx)+'mm;overflow:hidden;';""",
    1, '⑨ F() 에 배율 적용')

# 저장된 보정값은 '손잡이' 키만 받아들인다 — 양식 실측값(칸 좌표)은 늘 코드 쪽이 이긴다
rep("""      if(r.ok){ var d = await r.json(); if(d && typeof d==='object') Object.keys(d).forEach(function(k){ if(k in _AS_POS0 && typeof d[k]==='number') _asPos[k]=d[k]; }); }""",
    """      if(r.ok){ var d = await r.json(); if(d && typeof d==='object') Object.keys(d).forEach(function(k){ if(_AS_KNOBS.indexOf(k)>=0 && typeof d[k]==='number') _asPos[k]=d[k]; }); }""",
    1, '⑨ 저장값은 손잡이 키만')

rep("""    var out={}; Object.keys(_AS_POS0).forEach(function(k){ out[k]=P()[k]; });""",
    """    var out={}; _AS_KNOBS.forEach(function(k){ out[k]=P()[k]; });   // r283: 손잡이 값만 저장""",
    1, '⑨ 손잡이 값만 저장')

rep("""  var _asPos = null, _asCfgLoaded = false;""",
    """  // r283: 사람이 [인쇄 보정]에서 만지는 값. 나머지(칸 좌표)는 양식 실측값이라 저장하지 않는다.
  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowY','fs'];
  var _asPos = null, _asCfgLoaded = false;""",
    1, '⑨ _AS_KNOBS')

rep("""      + fld('offX','가로 이동') + fld('offY','세로 이동')
      + '<div style="height:1px;background:#eef2f7;margin:4px 0"></div>'""",
    """      + fld('offX','가로 이동') + fld('offY','세로 이동')
      + fld('sclX','가로 배율',0.001) + fld('sclY','세로 배율',0.001)
      + '<div style="height:1px;background:#eef2f7;margin:4px 0"></div>'""",
    1, '⑨ 보정 창에 배율 칸')

rep("""    ['offX','offY','slipX','slipY1','slipY2','rowY','fs'].forEach(function(k){""",
    """    _AS_KNOBS.forEach(function(k){""",
    1, '⑨ 보정 창 읽기')

# ── ⑩ 미리보기 양식을 실제 거래명세표 용지대로 다시 그린다 ──
#    근거: 사용자가 올린 빈 양식 PDF 를 300dpi 로 펴고(기울기 보정) 파랑 선만 골라 실측.
#    가로선 18.46 / 26.93 / 35.39 / 43.95 / 52.41 / 60.88 / 110.07 / 118.40
#    세로선 0.45 / 6.89 / 7.99 / 16.40 / 50.24 / 56.67 / 91.81 / 96.93 / 100.53 /
#           107.56 / 128.72 / 135.50 / 141.93 / 150.95 / 171.40  (전표 좌상단 기준 mm)
repblock('  // r282: 미리보기용 양식', '  function _asPrintHtml(html){',
'  // r283: 빈 양식 PDF(300dpi)를 실측해 그대로 그린다. 미리보기 전용 — 인쇄에는 쓰지 않는다.\n  //        종이에 이미 찍혀 있는 인감은 그리지 않는다(공개 저장소 원칙).\n  function _asFormSvg(p){\n    var W=p.slipW, H=p.slipH, C=\'#4a6fb5\', o=[];\n    function L(x1,y1,x2,y2,w){ o.push(\'<line x1="\'+x1+\'" y1="\'+y1+\'" x2="\'+x2+\'" y2="\'+y2+\'" stroke="\'+C+\'" stroke-width="\'+(w||0.25)+\'"/>\'); }\n    function T(x,y,t,sz,anchor,bold,ls){\n      o.push(\'<text x="\'+x+\'" y="\'+y+\'" font-size="\'+sz+\'" fill="\'+C+\'" text-anchor="\'+(anchor||\'start\')+\'"\'\n        + (bold?\' font-weight="700"\':\'\') + (ls?(\' letter-spacing="\'+ls+\'"\'):\'\') + \'>\' + esc(t) + \'</text>\');\n    }\n    // ── 테두리와 칸 ──\n    o.push(\'<rect x="0.45" y="0.30" width="170.95" height="118.10" fill="none" stroke="\'+C+\'" stroke-width="0.5"/>\');\n    [18.46,43.95,52.41,60.88,110.07].forEach(function(y){ L(0.45,y,171.40,y); });\n    [26.93,35.39].forEach(function(y){ L(6.89,y,171.40,y); });\n    [6.89,16.40,91.81,100.53].forEach(function(x){ L(x,18.46,x,43.95); });\n    [50.24,56.67,135.50,141.93].forEach(function(x){ L(x,26.93,x,35.39); });\n    [96.93,107.56,128.72,150.95].forEach(function(x){ L(x,52.41,x,118.40); });\n    L(7.99,52.41,7.99,110.07);\n    [19.67,83.13].forEach(function(x){ L(x,110.07,x,118.40); });\n    // ── 제목 ──\n    T(83.8,8.9,\'거 래 명 세 서\',6.6,\'middle\',1);\n    L(52.3,9.74,116.2,9.74,0.3); L(52.3,10.42,116.2,10.42,0.3);\n    T(84.4,14.4,\'(공급받는자 보관용)\',2.4,\'middle\');\n    T(1.7,17.2,\'거래명세서 번호:\',2.6);\n    T(148.5,17.2,\'년\',2.6); T(156.5,17.2,\'월\',2.6); T(164.7,17.2,\'일\',2.6);\n    // ── 공급자 (종이에 미리 찍혀 있는 내용) ──\n    T(4.0,23.3,\'공\',2.8,\'middle\'); T(4.0,31.2,\'급\',2.8,\'middle\'); T(4.0,39.8,\'자\',2.8,\'middle\');\n    T(8.1,22.6,\'등록\',2.9); T(8.1,25.7,\'번호\',2.9);\n    T(8.1,32.3,\'상 호\',2.9); T(8.1,40.5,\'주 소\',2.9);\n    T(53.4,30.6,\'성\',2.3,\'middle\'); T(53.4,33.9,\'명\',2.3,\'middle\');\n    T(26.2,24.9,\'113-81-14978\',3.5,\'start\',0,0.85);\n    T(20.6,33.2,\'충해전기(주)\',3.6,\'start\',1);\n    T(59.6,33.2,\'김 해 식\',3.0);\n    T(21.0,39.6,\'서울특별시 구로구 구로중앙로\',2.9);\n    T(22.0,43.1,\'구로기계공구상가 B블럭 13동 103호\',2.9);\n    // ── 공급받는자 (타자로 채우는 칸) ──\n    [\'공\',\'급\',\'받\',\'는\',\'자\'].forEach(function(ch,i){ T(93.9, 22.4+i*4.2, ch, 2.2, \'middle\'); });\n    T(96.6,22.6,\'등록\',2.1); T(96.6,25.7,\'번호\',2.1);\n    T(96.6,32.3,\'상 호\',2.1); T(96.6,40.5,\'주 소\',2.1);\n    T(138.6,30.6,\'성\',2.1,\'middle\'); T(138.6,33.9,\'명\',2.1,\'middle\');\n    // ── 총금액 ──\n    T(2.1,49.4,\'총금액\',3.5,\'start\',1); T(16.2,49.4,\'(공급가액+세액):\',2.6);\n    // ── 품목표 머리 ──\n    T(4.2,58.3,\'번호\',2.8,\'middle\');\n    T(52.4,58.3,\'품 명 및 규 격\',2.9,\'middle\');\n    T(102.3,58.3,\'수 량\',2.8,\'middle\');\n    T(118.1,58.3,\'단   가\',2.8,\'middle\');\n    T(139.8,58.3,\'공급가액\',2.8,\'middle\');\n    T(161.2,58.3,\'세   액\',2.8,\'middle\');\n    // ── 인수자 · 계 ──\n    T(2.8,115.9,\'인 수 자\',2.9);\n    T(80.0,115.9,\'㈞\',2.6,\'middle\');\n    T(89.0,115.9,\'계\',2.9);\n    // ── 꼬리말 ──\n    T(47.0,122.3,\'신한은행 : 100-001-944331 충해전기(주)    TEL : 02-2671-4474/5   FAX : 02-2672-3157\',2.35);\n    T(170.7,126.6,\'E-MAIL : chjk@chjk.co.kr\',2.35,\'end\');\n    return \'<svg class="as-form" viewBox="0 0 \'+W+\' \'+H+\'" xmlns="http://www.w3.org/2000/svg"\'\n      + \' font-family="BatangChe, Batang, serif">\'+o.join(\'\')+\'</svg>\';\n  }\n',
    '⑩ 미리보기 양식 재현')

# ⑨-2 긴 한글 금액 겹침 막기(r282)도 배율을 감안한다 — 인쇄된 뒤 1.5mm 가 남도록
rep("""      if(_koX+_koW > p.totNumX-1.5) _koX=Math.max(1.0, p.totNumX-1.5-_koW);   // 겹치면 왼쪽으로 민다""",
    """      var _koS=(p.sclX||1), _koNeed=(1.5 + _koW*(1-_koS))/_koS;              // r283: 배율을 감안한 여백
      if(_koX+_koW > p.totNumX-_koNeed) _koX=Math.max(1.0, p.totNumX-_koNeed-_koW);   // 겹치면 왼쪽으로 민다""",
    1, '⑨ 한글 금액 여백에 배율 반영')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r283 2026-11-26 -->')
    print('  ok  test marker %s -> r283' % m.group(0))

for k in ['window.asLDateIn', 'window.asLDateKey', 'window.asClearFile', '_asLRestore',
          'as-doc-head', 'event.stopPropagation();asLPrint', 'table-layout:fixed',
          'grid-template-columns:18px 152px 132px 92px minmax(260px,1fr) auto',
          '다른 파일 올리기', 'width:300px;height:26px',
          '_AS_KNOBS', 'sclX:0.9924', 'sumY:112.5', '_asBindDD', 'x*_sx + p.offX',
          '113-81-14978', '거래명세서 번호:', 'L(7.99,52.41,7.99,110.07)']:
    assert k in s, 'NEED missing: ' + k
for k in ['window.asToggleDoc', 'window.asLToggle', 'window.asLPrint', 'window.asLDel',
          'renderAuditPage', '_asBindDrop', 'id="asDrop"', 'as-subtab']:
    assert k in s, 'KEEP missing: ' + k
assert "+' '+d.rows.length+'품목 · '+pages+'장'" not in s, 'FORBIDDEN: 전표 줄에 품목·장 표시가 남아 있다'
assert '\\u25b8 내역' not in s, 'FORBIDDEN: [내역] 단추가 남아 있다'
assert 'type="date" id="asLFrom"' not in s, 'FORBIDDEN: 옛 날짜 입력칸이 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r283 적용 완료: %d -> %d' % (orig, len(s)))
