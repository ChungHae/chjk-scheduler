# -*- coding: utf-8 -*-
# r125: [매입매출 4단계] 매입·매출 집계 화면.
#  - 사업장 토글(미수 현황과 공유) + 연도 선택 + 보기(월별/거래처별) + 거래처 검색
#  - 월별: 매출/매입 각각 건수·공급가액·세액·합계 + 연간 합계행 + 월 차액(합계 기준)
#  - 거래처별: 거래처 | 매출(건·합계) | 매입(건·합계), 매출 합계순 정렬
#  - 세금계산서(계산서 발행) 기준. 매입 자료는 r126 홈택스 업로드 후 채워짐.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R125 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

HANDLERS = r"""  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxRenderArBody(); };
  var _fxSumMode='month', _fxSumYear=null, _fxSumQ='';
  window.fxSumMode = function(m){ _fxSumMode=m; _fxRenderSumBody(); };
  window.fxSumYear = function(y){ _fxSumYear=y; _fxRenderSumBody(); };
  window.fxSumSearch = function(v){ _fxSumQ=String(v||'').trim().toLowerCase(); _fxRenderSumBody(); };
  function _fxYears(){
    var ys={};
    fxSalesInv.concat(fxPurchInv).forEach(function(e){ if(e.biz===_fxRegion && e.date) ys[e.date.slice(0,4)]=1; });
    var arr=Object.keys(ys).sort().reverse();
    return arr.length?arr:[String(new Date().getFullYear())];
  }
  function _fxRenderSumBody(){
    var host=document.getElementById('fxSumBody'); if(!host) return;
    var years=_fxYears();
    if(!_fxSumYear || years.indexOf(_fxSumYear)<0) _fxSumYear=years[0];
    var ysel=document.getElementById('fxSumYearSel');
    if(ysel && ysel.dataset.opt!==years.join('|')){
      ysel.innerHTML = years.map(function(y){ return '<option value="'+y+'"'+(y===_fxSumYear?' selected':'')+'>'+y+'년</option>'; }).join('');
      ysel.dataset.opt=years.join('|');
    }
    if(ysel) ysel.value=_fxSumYear;
    document.querySelectorAll('#fxSumModeBtns .pf-btn').forEach(function(b){ b.classList.toggle('active', b.dataset.m===_fxSumMode); });
    var q=document.getElementById('fxSumQ'); if(q) q.style.display = _fxSumMode==='vendor'?'':'none';
    var sv=fxSalesInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===_fxSumYear; });
    var pv=fxPurchInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===_fxSumYear; });
    var TH='padding:9px 10px;background:#fafafa;color:#888;font-weight:500;font-size:12px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var TD='padding:9px 10px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;white-space:nowrap;font-size:12.5px;text-align:right';
    if(_fxSumMode==='month'){
      var M={};
      for(var m=1;m<=12;m++) M[m]={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
      sv.forEach(function(e){ var m=Number(e.date.slice(5,7)); if(M[m]){ M[m].sc++; M[m].ss+=e.supply||0; M[m].st+=e.tax||0; M[m].stt+=e.total||0; } });
      pv.forEach(function(e){ var m=Number(e.date.slice(5,7)); if(M[m]){ M[m].pc++; M[m].ps+=e.supply||0; M[m].pt+=e.tax||0; M[m].ptt+=e.total||0; } });
      var T={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
      var rows='';
      for(var m2=1;m2<=12;m2++){
        var x=M[m2];
        ['sc','ss','st','stt','pc','ps','pt','ptt'].forEach(function(k){ T[k]+=x[k]; });
        var dim = !x.sc && !x.pc;
        rows += '<tr'+(dim?' style="opacity:.45"':'')+'>'
          + '<td style="'+TD+';text-align:center;font-weight:700;color:#14305c">'+m2+'월</td>'
          + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.sc||'-')+'</td>'
          + '<td style="'+TD+'">'+_fxFmt(x.ss)+'</td>'
          + '<td style="'+TD+';color:#6b7280">'+_fxFmt(x.st)+'</td>'
          + '<td style="'+TD+';font-weight:700">'+_fxFmt(x.stt)+'</td>'
          + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.pc||'-')+'</td>'
          + '<td style="'+TD+'">'+_fxFmt(x.ps)+'</td>'
          + '<td style="'+TD+';color:#6b7280">'+_fxFmt(x.pt)+'</td>'
          + '<td style="'+TD+';font-weight:700">'+_fxFmt(x.ptt)+'</td>'
          + '<td style="'+TD+';font-weight:700;color:'+((x.stt-x.ptt)>=0?'#14305c':'#dc2626')+'">'+_fxFmt(x.stt-x.ptt)+'</td>'
          + '</tr>';
      }
      rows += '<tr style="background:#f4f8fe">'
        + '<td style="'+TD+';text-align:center;font-weight:700;color:#1B3A6B">합계</td>'
        + '<td style="'+TD+';text-align:center;font-weight:700">'+T.sc+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T.ss)+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T.st)+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T.stt)+'</td>'
        + '<td style="'+TD+';text-align:center;font-weight:700">'+T.pc+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T.ps)+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T.pt)+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T.ptt)+'</td>'
        + '<td style="'+TD+';font-weight:700;color:'+((T.stt-T.ptt)>=0?'#1B3A6B':'#dc2626')+'">'+_fxFmt(T.stt-T.ptt)+'</td>'
        + '</tr>';
      host.innerHTML =
        '<div style="background:#fff;border:1px solid #d6deea;overflow:auto"><table style="width:100%;border-collapse:separate;border-spacing:0;font-size:12.5px;min-width:900px">'
        + '<thead><tr>'
        +   '<th style="'+TH+'" rowspan="2">월</th>'
        +   '<th style="'+TH+'" colspan="4">매출 (계산서 발행)</th>'
        +   '<th style="'+TH+'" colspan="4">매입 (계산서 수취)</th>'
        +   '<th style="'+TH+'" rowspan="2">차액(합계)</th>'
        + '</tr><tr>'
        +   '<th style="'+TH+'">건수</th><th style="'+TH+'">공급가액</th><th style="'+TH+'">세액</th><th style="'+TH+'">합계</th>'
        +   '<th style="'+TH+'">건수</th><th style="'+TH+'">공급가액</th><th style="'+TH+'">세액</th><th style="'+TH+'">합계</th>'
        + '</tr></thead><tbody>'+rows+'</tbody></table></div>'
        + (pv.length?'':'<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">매입 계산서 자료는 자료 업로드(홈택스 매입) 연결 후 채워집니다.</div>');
      return;
    }
    // 거래처별
    var V={};
    function vslot(e){ var k=(e.vbiz&&/\d{3}-\d{2}-\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', sc:0, stt:0, pc:0, ptt:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }
    sv.forEach(function(e){ var s2=vslot(e); s2.sc++; s2.stt+=e.total||0; });
    pv.forEach(function(e){ var s3=vslot(e); s3.pc++; s3.ptt+=e.total||0; });
    var list=Object.keys(V).map(function(k){ return V[k]; });
    if(_fxSumQ) list=list.filter(function(x){ return x.name.toLowerCase().indexOf(_fxSumQ)>=0 || x.vbiz.indexOf(_fxSumQ)>=0; });
    list.sort(function(a,b){ return (b.stt+b.ptt)-(a.stt+a.ptt); });
    if(!list.length){ host.innerHTML='<div style="text-align:center;padding:48px;color:#b6bec9;font-size:13px">해당 연도 자료가 없습니다.</div>'; return; }
    var tS=list.reduce(function(a,x){return a+x.stt;},0), tP=list.reduce(function(a,x){return a+x.ptt;},0);
    var rows2=list.map(function(x){
      return '<tr>'
        + '<td style="'+TD+';text-align:left;font-weight:700;color:#14305c;overflow:hidden;text-overflow:ellipsis">'+esc(x.name)+(x.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+x.vbiz+'</span>':'')+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.sc||'-')+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(x.stt)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.pc||'-')+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(x.ptt)+'</td>'
        + '</tr>';
    }).join('');
    rows2 += '<tr style="background:#f4f8fe"><td style="'+TD+';text-align:left;font-weight:700;color:#1B3A6B">합계 ('+list.length+'곳)</td>'
      + '<td style="'+TD+'"></td><td style="'+TD+';font-weight:700">'+_fxFmt(tS)+'</td>'
      + '<td style="'+TD+'"></td><td style="'+TD+';font-weight:700">'+_fxFmt(tP)+'</td></tr>';
    host.innerHTML =
      '<div style="background:#fff;border:1px solid #d6deea"><table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px">'
      + '<colgroup><col><col style="width:70px"><col style="width:140px"><col style="width:70px"><col style="width:140px"></colgroup>'
      + '<thead><tr><th style="'+TH+'">거래처</th><th style="'+TH+'">매출 건</th><th style="'+TH+'">매출 합계</th><th style="'+TH+'">매입 건</th><th style="'+TH+'">매입 합계</th></tr></thead>'
      + '<tbody>'+rows2+'</tbody></table></div>';
  }"""

SUM_BRANCH_OLD = """    if(_fxTab==='sum'){
      body.innerHTML = '<div style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">자료 불러오는 중…</div>';
      _fxEnsureData().then(function(){
        if(_fxTab!=='sum') return;
        body.innerHTML = _empty('세금계산서 기준 월별·거래처별 매입·매출 집계 — 다음 단계(r125)에서 제공됩니다.');
      });
      return;
    }"""

SUM_BRANCH_NEW = """    if(_fxTab==='sum'){
      body.innerHTML = '<div style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">자료 불러오는 중…</div>';
      _fxEnsureData().then(function(){
        if(_fxTab!=='sum') return;
        if(meta) meta.textContent = '매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';
        if(!fxSalesInv.length && !fxPurchInv.length){
          body.innerHTML = _empty('자료가 아직 없습니다.<br><b style="color:#5b7ba6">자료 업로드</b> 탭에서 계산서 자료를 올려주세요.');
          return;
        }
        body.innerHTML =
          '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px">'
          + '<div style="display:flex;gap:4px">'
          +   ['서울','화성'].map(function(b){ return '<button type="button" class="btn pf-btn'+(_fxRegion===b?' active':'')+'" onclick="fxSetRegion(\\''+b+'\\')" style="font-size:11.5px;padding:3px 12px">'+b+'</button>'; }).join('')
          + '</div>'
          + '<select id="fxSumYearSel" class="q-flat" onchange="fxSumYear(this.value)" style="width:96px;background:#fff;color:#1a1a1a;cursor:pointer"></select>'
          + '<div id="fxSumModeBtns" style="display:flex;gap:4px">'
          +   '<button type="button" class="btn pf-btn" data-m="month" onclick="fxSumMode(\\'month\\')" style="font-size:11.5px;padding:3px 12px">월별</button>'
          +   '<button type="button" class="btn pf-btn" data-m="vendor" onclick="fxSumMode(\\'vendor\\')" style="font-size:11.5px;padding:3px 12px">거래처별</button>'
          + '</div>'
          + '<input type="text" id="fxSumQ" class="q-flat" placeholder="거래처 검색…" value="'+esc(_fxSumQ)+'" oninput="fxSumSearch(this.value)" style="width:200px;display:none">'
          + '</div>'
          + '<div id="fxSumBody"></div>';
        _fxRenderSumBody();
      });
      return;
    }"""

def apply_r125(s, path):
    s = rep(s, "  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxRenderArBody(); };", HANDLERS, 1, 'H')
    s = rep(s, SUM_BRANCH_OLD, SUM_BRANCH_NEW, 1, 'SUM')
    # 사업장 토글이 집계 탭도 갱신하도록
    s = rep(s, "  window.fxSetRegion = function(b){ _fxRegion=b; _fxExp=null; renderFxPage(); };",
            "  window.fxSetRegion = function(b){ _fxRegion=b; _fxExp=null; _fxSumYear=null; renderFxPage(); };", 1, 'RG')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r125(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r124 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r124 2026-08-21 -->', '<!-- test build r125 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
