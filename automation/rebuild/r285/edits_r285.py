# -*- coding: utf-8 -*-
# r285 — 감사 (사용자 지시 2026-11-26)
#   ① 물류출하일이 올바른 날짜가 아닌 줄은 자동으로 빼고 화면에 내보내지 않는다
#   ② 저장된 명세표에서 '작성' 칸 삭제
#   ③ 저장된 명세표에 체크칸 + 전체 선택 · 선택 인쇄 · 선택 삭제
#   ④ 중복이면 화면을 그리기 전에 먼저 물어보고, 취소하면 올린 것을 버린다
#   ⑤ 고른 줄 · 펼친 줄에 배경색
#   ⑥ 미리보기 양식을 Firebase 에 올려 둔 실제 양식 그림으로 (없으면 지금 SVG)
#  사용:  python3 edits_r285.py <index.html> [--test]
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

assert '_asLSel' not in s, 'FORBIDDEN(이미 r285 적용됨)'

# ── ① 물류출하일이 올바르지 않으면 뺀다 ─────────────────────
rep("""      out.push({ ucode:c[ix.user]||'', uname:c[ix.uname]||'', spec:spec, qty:qty, price:price, ship:String(c[ix.ship]||'').replace(/[^0-9]/g,'') });
    }
    if(!out.length) throw new Error('읽을 품번이 없습니다.');
    return out;""",
    """      var sh = String(c[ix.ship]||'').replace(/[^0-9]/g,'');
      if(!_asShipOk(sh)){ _asDropped++; continue; }   // r285: 물류출하일이 날짜가 아니면 뺀다
      out.push({ ucode:c[ix.user]||'', uname:c[ix.uname]||'', spec:spec, qty:qty, price:price, ship:sh });
    }
    if(!out.length) throw new Error('물류출하일이 올바른 줄이 없습니다. 엑셀을 확인해 주세요.');
    return out;""",
    1, '① 비정상 물류출하일 제외')

rep("""  function _asParseFile(buf){""",
    """  // r285: 8자리 실제 날짜인지 본다 (1900~2999년)
  var _asDropped = 0;
  function _asShipOk(s){
    s = String(s||'');
    if(!/^[0-9]{8}$/.test(s)) return false;
    var y=+s.slice(0,4), m=+s.slice(4,6), d=+s.slice(6,8);
    if(y<1900 || y>2999 || m<1 || m>12 || d<1 || d>31) return false;
    var dt=new Date(y, m-1, d);
    return dt.getFullYear()===y && dt.getMonth()===m-1 && dt.getDate()===d;
  }
  function _asParseFile(buf){
    _asDropped = 0;""",
    1, '① _asShipOk')

rep("""      + '<span>파일: <b>'+esc(_asFileName)+'</b> · 품번 '+_asRaw.length+'줄</span>'""",
    """      + '<span>파일: <b>'+esc(_asFileName)+'</b> · 품번 '+_asRaw.length+'줄'
      +   (_asDropped?('<span style="color:#b45309"> · 물류출하일이 올바르지 않은 '+_asDropped+'줄은 뺐습니다</span>'):'')+'</span>'""",
    1, '① 뺀 줄 수 표시')

# ── ⑤ 배경색 CSS ────────────────────────────────────────────
rep("""    #pageAudit .as-lrow:hover { background:#f7f9fc; }""",
    """    #pageAudit .as-lrow:hover { background:#f7f9fc; }
    /* r285: 고른 줄 · 펼친 줄을 눈에 띄게 */
    #pageAudit .as-lrow.as-open { background:#f1f6fd; }
    #pageAudit .as-lrow.as-sel, #pageAudit .as-lrow.as-sel:hover { background:#dbe8fb; }
    #pageAudit tr.as-detail > td { background:#f8fbff; }
    #pageAudit .as-doc-head.as-open { background:#f1f6fd; }""",
    1, '⑤ 배경색 CSS')

rep("""          + '<div class="as-doc-row as-doc-head" onclick="asToggleDoc('+di+','+ci+')" title="누르면 품목이 펼쳐집니다">'""",
    """          + '<div class="as-doc-row as-doc-head'+(d.open?' as-open':'')+'" onclick="asToggleDoc('+di+','+ci+')" title="누르면 품목이 펼쳐집니다">'""",
    1, '⑤ 명세표 만들기 펼친 줄')

# ── ②③⑤ 저장된 명세표 표 ───────────────────────────────────
rep("""    h += '<table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'
      + '<th style="padding:6px 8px;text-align:left;width:100px">발행일</th>'
      + '<th style="padding:6px 8px;text-align:center;width:54px">번호</th>'
      + '<th style="padding:6px 8px;text-align:left">업체</th>'
      + '<th style="padding:6px 8px;text-align:center;width:64px">품목</th>'
      + '<th style="padding:6px 8px;text-align:right;width:110px">공급가액</th>'
      + '<th style="padding:6px 8px;text-align:right;width:100px">세액</th>'
      + '<th style="padding:6px 8px;text-align:right;width:110px">합계</th>'
      + '<th style="padding:6px 8px;text-align:left;width:70px">작성</th>'
      + '<th style="padding:6px 8px;width:116px"></th></tr></thead><tbody>';""",
    """    // r285: 고른 것 묶음 처리 줄
    var _selIds = part.filter(function(v){ return _asLSel[v.id]; }).map(function(v){ return v.id; });
    var _selAll = part.length>0 && _selIds.length===part.length;
    var _selN = Object.keys(_asLSel).filter(function(k){ return _asLSel[k]; }).length;
    h += '<div style="display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:12.5px;min-height:30px">'
      + (_selN ? ('<b style="color:#1B3A6B">'+_selN+'건 골랐습니다</b>'
                 + _asBtn('고른 것 인쇄','asLPrintSel()','primary')
                 + _asBtn('고른 것 삭제','asLDelSel()','warn')
                 + _asBtn('선택 해제','asLSelNone()'))
                : '<span style="color:#9ca3af">줄 왼쪽 네모를 눌러 여러 건을 한 번에 인쇄하거나 지울 수 있습니다.</span>')
      + '</div>';
    h += '<table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'
      + '<th style="padding:6px 4px;width:34px;text-align:center"><input type="checkbox" id="asLAll"'+(_selAll?' checked':'')+' onclick="asLSelAll(this.checked)" title="이 쪽 전체 선택" style="width:15px;height:15px;cursor:pointer"></th>'
      + '<th style="padding:6px 8px;text-align:left;width:100px">발행일</th>'
      + '<th style="padding:6px 8px;text-align:center;width:54px">번호</th>'
      + '<th style="padding:6px 8px;text-align:left">업체</th>'
      + '<th style="padding:6px 8px;text-align:center;width:64px">품목</th>'
      + '<th style="padding:6px 8px;text-align:right;width:110px">공급가액</th>'
      + '<th style="padding:6px 8px;text-align:right;width:100px">세액</th>'
      + '<th style="padding:6px 8px;text-align:right;width:110px">합계</th>'
      + '<th style="padding:6px 8px;width:116px"></th></tr></thead><tbody>';""",
    1, '②③ 표 머리 — 체크칸 추가 · 작성 칸 삭제')

rep("""      h += '<tr class="as-lrow" onclick="asLToggle(\\''+esc(v.id)+'\\')" title="누르면 내역이 펼쳐집니다" style="border-bottom:1px solid #f1f4f8">'
        + '<td style="padding:5px 8px"><span style="color:#5b7ba6;margin-right:4px">'+(op?'\\u25be':'\\u25b8')+'</span>'+esc(v.date||'')+'</td>'""",
    """      var sel=!!_asLSel[v.id];
      h += '<tr class="as-lrow'+(sel?' as-sel':'')+(op?' as-open':'')+'" onclick="asLToggle(\\''+esc(v.id)+'\\')" title="누르면 내역이 펼쳐집니다" style="border-bottom:1px solid #f1f4f8">'
        + '<td style="padding:5px 4px;text-align:center"><input type="checkbox"'+(sel?' checked':'')+' onclick="event.stopPropagation();asLSelOne(\\''+esc(v.id)+'\\',this.checked)" style="width:15px;height:15px;cursor:pointer"></td>'
        + '<td style="padding:5px 8px"><span style="color:#5b7ba6;margin-right:4px">'+(op?'\\u25be':'\\u25b8')+'</span>'+esc(v.date||'')+'</td>'""",
    1, '③⑤ 줄 — 체크칸·배경색')

rep("""        + '<td style="padding:5px 8px;text-align:right"><b>'+_asNum(v.total)+'</b></td>'
        + '<td style="padding:5px 8px;color:#8a94a6">'+esc(v.by||'')+'</td>'
        + '<td style="padding:5px 8px;text-align:right;white-space:nowrap">'""",
    """        + '<td style="padding:5px 8px;text-align:right"><b>'+_asNum(v.total)+'</b></td>'
        + '<td style="padding:5px 8px;text-align:right;white-space:nowrap">'""",
    1, '② 작성 칸 삭제')

rep("""        h += '<tr><td colspan="9" style="padding:0 0 10px;background:#fcfdff">'""",
    """        h += '<tr class="as-detail"><td colspan="9" style="padding:0 0 10px">'""",
    1, '⑤ 내역 줄 배경')

# 체크칸(34px)이 생겨 '업체' 가 밀렸다 — 규격이 다시 '업체' 와 같은 자리에서 시작하도록 품목 폭을 넓힌다
rep("""          + '<th style="padding:6px 8px;text-align:left;width:110px">품목</th>'
          + '<th style="padding:6px 8px;text-align:left">규격</th>'
          + '<th style="padding:6px 8px;text-align:center;width:60px">수량</th><th style="padding:6px 8px;text-align:right;width:90px">단가</th>'""",
    """          + '<th style="padding:6px 8px;text-align:left;width:144px">품목</th>'
          + '<th style="padding:6px 8px;text-align:left">규격</th>'
          + '<th style="padding:6px 8px;text-align:center;width:60px">수량</th><th style="padding:6px 8px;text-align:right;width:90px">단가</th>'""",
    1, '⑤ 규격 자리 맞추기')

# ── ③ 고른 것 처리 ──────────────────────────────────────────
rep("""  window.asLToggle = function(id){ _asLOpen[id] = !_asLOpen[id]; _asRender(); };""",
    """  window.asLToggle = function(id){ _asLOpen[id] = !_asLOpen[id]; _asRender(); };
  // r285: 체크해서 여러 건을 한 번에 인쇄·삭제
  window.asLSelOne = function(id, on){ if(on) _asLSel[id]=1; else delete _asLSel[id]; _asRender(); };
  window.asLSelAll = function(on){
    var arr=_asLFiltered().slice(_asLPage*_AS_PER, _asLPage*_AS_PER+_AS_PER);
    arr.forEach(function(v){ if(on) _asLSel[v.id]=1; else delete _asLSel[v.id]; });
    _asRender();
  };
  window.asLSelNone = function(){ _asLSel={}; _asRender(); };
  function _asSelRecs(){
    var byId={}; (_asLRows||[]).forEach(function(v){ byId[v.id]=v; });
    return Object.keys(_asLSel).filter(function(k){ return _asLSel[k] && byId[k]; })
      .map(function(k){ return byId[k]; })
      .sort(function(a,b){ return String(a.date||'').localeCompare(String(b.date||'')) || ((a.no||0)-(b.no||0)); });
  }
  window.asLPrintSel = function(){
    var recs=_asSelRecs();
    if(!recs.length){ showInfoModal('인쇄','고른 거래명세표가 없습니다.'); return; }
    _asPrintHtml(_asDocHtmlMany(recs, false));
  };
  window.asLDelSel = function(){
    var recs=_asSelRecs();
    if(!recs.length){ showInfoModal('삭제','고른 거래명세표가 없습니다.'); return; }
    if(_isViewer()){ showInfoModal('삭제','보기 전용 계정입니다.'); return; }
    var head=recs.slice(0,6).map(function(v){ return '  · '+(v.date||'')+' 번호 '+(v.no||'')+' · '+(v.vname||''); }).join('\\n');
    showConfirmModal('거래명세표 '+recs.length+'건 삭제',
      head + (recs.length>6?('\\n  … 모두 '+recs.length+'건'):'') + '\\n\\n고른 거래명세표를 모두 지웁니다. 되돌릴 수 없습니다.',
      async function(){
        var okN=0, bad=[];
        for(var i=0;i<recs.length;i++){
          try{
            var r = await _fbFetch(_asDocUrl(recs[i].id), {method:'DELETE'});
            if(!r || !r.ok) throw new Error('HTTP '+(r?r.status:'네트워크'));
            _asLRows = (_asLRows||[]).filter(function(x){ return x.id!==recs[i].id; });
            delete _asLSel[recs[i].id]; delete _asLOpen[recs[i].id];
            okN++;
          }catch(e){ bad.push((recs[i].date||'')+' 번호 '+(recs[i].no||'')); }
        }
        _asRender();
        showInfoModal('삭제', okN+'건을 지웠습니다.' + (bad.length?('\\n지우지 못한 것: '+bad.join(', ')):''));
      }, '모두 삭제', '#dc2626');
  };""",
    1, '③ 선택 인쇄·삭제')

rep("""  var _asLPage = 0, _asLOpen = {};""",
    """  var _asLPage = 0, _asLOpen = {};
  var _asLSel = {};                           // r285: 체크한 거래명세표""",
    1, '③ _asLSel')

rep("""  window.asLClear = function(){ _asLF={vname:'',from:'',to:'',q:''}; _asLPage=0; _asLOpen={}; _asRender(); };""",
    """  window.asLClear = function(){ _asLF={vname:'',from:'',to:'',q:''}; _asLPage=0; _asLOpen={}; _asLSel={}; _asRender(); };""",
    1, '③ [지우기] 에 선택 해제 포함')

# ── ③ 여러 건 인쇄본 ────────────────────────────────────────
rep("""    var css='@page{size:A4;margin:0}'""",
    """    return _asWrapDoc(pagesHtml, p);
  }
  // r285: 거래처가 달라도 고른 것을 한 번에 인쇄한다
  function _asDocHtmlMany(recs, grid){
    var p=P(), pagesHtml=[];
    (recs||[]).forEach(function(v){
      var rows=v.rows||[];
      var supply=rows.reduce(function(a,r){ return a+(+r.supply||0); },0);
      var tax=rows.reduce(function(a,r){ return a+(+r.tax||0); },0);
      var head={ biz:v.biz, vname:v.vname, ceo:v.ceo, addr:v.addr, supply:supply, tax:tax, total:supply+tax };
      var d={ ship:v.ship, date:v.date, no:v.no, rows:rows, memo:v.memo||'' };
      var pages=Math.max(1, Math.ceil(rows.length/_AS_ROWS));
      for(var pg=0; pg<pages; pg++){
        pagesHtml.push('<div class="as-page">'
          + '<div class="as-pos" style="top:'+p.slipY1+'mm">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'
          + '<div class="as-pos" style="top:'+p.slipY2+'mm">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'
          + '</div>');
      }
    });
    return _asWrapDoc(pagesHtml, p);
  }
  function _asWrapDoc(pagesHtml, p){
    var css='@page{size:A4;margin:0}'""",
    1, '③ _asDocHtmlMany · _asWrapDoc')

# ── ④ 중복이면 화면을 그리기 전에 먼저 묻는다 ──────────────
rep("""      var buf = await f.arrayBuffer();
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
      _asMarkDupAll();   // r284: 이미 저장된 것과 같은 내용인지 표시
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }""",
    """      var buf = await f.arrayBuffer();
      var raw = _asParseFile(buf), dropped = _asDropped;
      await _asLoadMap();
      var byU={}; raw.forEach(function(r){ var k=_asMapKey(r.ucode,r.uname); (byU[k]=byU[k]||[]).push(r); });
      var drafts=[];
      var keys=Object.keys(byU);
      for(var i=0;i<keys.length;i++){
        var k=keys[i], list=byU[k], m=_asMap[k];
        var dr;
        if(m && m.vname){ dr = await _asBuildDraft(list, m.vid, m.vname); }
        else dr = { vid:'', vname:'', biz:'', ceo:'', addr:'', docs:[] };
        dr.key=k; dr.ucode=list[0].ucode; dr.uname=list[0].uname; dr.list=list;
        drafts.push(dr);
      }
      // r285: 중복이면 화면을 그리기 전에 먼저 묻는다
      await _asEnsureList();
      var dups=[];
      drafts.forEach(function(dr){ (dr.docs||[]).forEach(function(d){
        d.dup = dr.vname ? _asDupOf(dr, d) : null;
        if(d.dup) dups.push({ dr:dr, d:d });
      }); });
      function _commit(){
        _asRaw = raw; _asDropped = dropped; _asFileName = f.name; _asShowInput = false;
        _asDrafts = drafts; _asRender();
      }
      if(dups.length){
        showConfirmModal('중복 확인 — 그대로 올릴까요?',
          '올린 자료 가운데 이미 저장된 거래명세표와 같은 내용이 ' + dups.length + '건 있습니다.\\n'
          + dups.slice(0,6).map(function(x){ return '  · '+(x.d.date||'')+' 번호 '+(x.d.dup.no||'')+' · '+(x.dr.vname||'')+' ('+(x.d.rows.length)+'품목)'; }).join('\\n')
          + (dups.length>6?('\\n  … 모두 '+dups.length+'건'):'')
          + '\\n\\n[그대로 올리기] 를 고르면 화면에 그대로 띄웁니다. [취소] 하면 이 파일을 버립니다.',
          function(){ _commit(); }, '그대로 올리기', '#b45309');
        return;
      }
      _commit();
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }""",
    1, '④ 올리기 전 중복 확인')

# ── ⑥ 미리보기 양식 그림 ────────────────────────────────────
rep("""  function _asFormSvg(p){""",
    """  // r285: Firebase 에 올려 둔 실제 양식 그림이 있으면 그것을 깔고, 없으면 아래 SVG 를 쓴다.
  //        (공개 저장소에는 그림을 넣지 않는다 — 명판·인감과 같은 방식)
  var _asFormImg = null, _asFormTried = false;
  async function _asLoadForm(){
    if(_asFormTried) return _asFormImg;
    _asFormTried = true;
    if(!_fbDbUrl) return null;
    try{
      var r = await _fbFetch(_asKeyUrl('sched_audit_form'));
      if(r && r.ok){ var d = await r.json(); if(typeof d==='string' && d.indexOf('data:image')===0) _asFormImg = d; }
    }catch(e){}
    return _asFormImg;
  }
  window.asFormPick = function(){ var i=document.getElementById('asFormFile'); if(i){ i.value=''; i.click(); } };
  window.asFormOnFile = function(ev){
    var f = ev.target.files && ev.target.files[0]; ev.target.value='';
    if(!f) return;
    if(!/^image\\//.test(f.type||'')){ showInfoModal('양식 그림','이미지 파일(PNG·JPG)을 골라 주세요.'); return; }
    var rd = new FileReader();
    rd.onload = async function(){
      try{
        if(_isViewer()) throw new Error('보기 전용 계정입니다.');
        var ok = await _fbPutOk(_asKeyUrl('sched_audit_form'), String(rd.result), '감사 양식 그림');
        if(!ok) throw new Error('저장하지 못했습니다.');
        _asFormImg = String(rd.result); _asFormTried = true;
        showInfoModal('양식 그림','등록했습니다. 미리보기에 이 그림이 깔립니다.');
      }catch(e){ showInfoModal('양식 그림', String(e && e.message || e)); }
    };
    rd.readAsDataURL(f);
  };
  window.asFormClear = function(){
    showConfirmModal('양식 그림 지우기','등록한 양식 그림을 지웁니다. 미리보기는 선으로 그린 양식으로 돌아갑니다.',
      async function(){
        try{
          var r = await _fbFetch(_asKeyUrl('sched_audit_form'), {method:'DELETE'});
          if(!r || !r.ok) throw new Error('HTTP '+(r?r.status:'네트워크'));
          _asFormImg = null; showInfoModal('양식 그림','지웠습니다.');
        }catch(e){ showInfoModal('양식 그림', String(e && e.message || e)); }
      }, '지우기', '#dc2626');
  };
  function _asFormSvg(p){
    if(_asFormImg) return '<img class="as-form" src="'+esc(_asFormImg)+'" alt="">';""",
    1, '⑥ 양식 그림 불러오기·등록')

rep("""      +'.as-form{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:1}'""",
    """      +'.as-form{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:1}'
      +'img.as-form{object-fit:fill}'""",
    1, '⑥ 양식 그림 CSS')

rep("""      + fld('sclX','가로 배율',0.001) + fld('sclY','세로 배율',0.001)
      + '<div style="height:1px;background:#eef2f7;margin:4px 0"></div>'""",
    """      + fld('sclX','가로 배율',0.001) + fld('sclY','세로 배율',0.001)
      + '<div style="height:1px;background:#eef2f7;margin:4px 0"></div>'
      + '<div style="display:flex;align-items:center;gap:8px;font-size:12.5px"><span style="width:118px;color:#5b7ba6">미리보기 양식</span>'
      +   _asBtn(_asFormImg?'양식 그림 바꾸기':'양식 그림 등록','asFormPick()')
      +   (_asFormImg?(' '+_asBtn('지우기','asFormClear()','warn')):'')
      +   '<input type="file" id="asFormFile" accept="image/*" style="display:none" onchange="asFormOnFile(event)">'
      + '</div>'
      + '<div style="font-size:11.5px;color:#8a94a6;line-height:1.7">양식 그림은 미리보기에만 깔립니다 — 인쇄에는 들어가지 않습니다. 그림은 사내전산 자료(Firebase)에 보관하고 공개 저장소에는 넣지 않습니다.</div>'
      + '<div style="height:1px;background:#eef2f7;margin:4px 0"></div>'""",
    1, '⑥ [인쇄 보정] 창에 양식 그림 등록')

rep("""    if(!_asCfgLoaded){ el.innerHTML='<div style="padding:28px;color:#9ca3af">불러오는 중…</div>'; await _asLoadCfg(); await _asLoadMap(); }""",
    """    if(!_asCfgLoaded){ el.innerHTML='<div style="padding:28px;color:#9ca3af">불러오는 중…</div>'; await _asLoadCfg(); await _asLoadMap(); }
    if(!_asFormTried) await _asLoadForm();      // r285: 미리보기 양식 그림 (있으면)""",
    1, '⑥ 화면 열 때 불러오기')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r285 2026-11-26 -->')
    print('  ok  test marker %s -> r285' % m.group(0))

for k in ['_asShipOk', '_asDropped', 'window.asLSelOne', 'window.asLSelAll', 'window.asLSelNone',
          'window.asLPrintSel', 'window.asLDelSel', '_asDocHtmlMany', '_asWrapDoc',
          'as-sel', 'as-open', 'as-detail', '_asLoadForm', 'window.asFormOnFile',
          '그대로 올리기', '고른 것 인쇄', '고른 것 삭제']:
    assert k in s, 'NEED missing: ' + k
for k in ['_asDupOf', '_asEnsureList', 'renderAuditPage', 'asLDateIn', '_asFormSvg']:
    assert k in s, 'KEEP missing: ' + k
assert '>작성</th>' not in s.split('_asListHtml')[1][:6000], 'FORBIDDEN: 저장된 명세표에 작성 칸이 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r285 적용 완료: %d -> %d' % (orig, len(s)))
