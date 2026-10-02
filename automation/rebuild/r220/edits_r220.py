# -*- coding: utf-8 -*-
# r220 (2026-10-02): 회계 > 집계에 '연도별' 모드 추가 + 매출총이익·마진율.
#   입출금 탭(구 Streamlit 요약 대시보드)을 없애기 전에, 거기서만 보이던
#   ① 연도별 매출·매입 추이 ② 매출총이익·마진율 을 집계 탭으로 옮긴다.
#   매출총이익 = 매출 공급가액 − 매입 공급가액 (구 Streamlit 수치와 동일함을 2026년 값으로 대조 확인)
import io, sys

YEAR_BRANCH = r"""    if(_fxSumMode==='year'){   // r220: 연도별 (여러 해 한 표 + 추이)
      var yl=_fxYears().slice().sort(), Y={};
      yl.forEach(function(y){ Y[y]={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 }; });
      fxSalesInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date){ var y1=e.date.slice(0,4); if(Y[y1]){ Y[y1].sc++; Y[y1].ss+=e.supply||0; Y[y1].st+=e.tax||0; Y[y1].stt+=e.total||0; } } });
      fxPurchInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date){ var y2=e.date.slice(0,4); if(Y[y2]){ Y[y2].pc++; Y[y2].ps+=e.supply||0; Y[y2].pt+=e.tax||0; Y[y2].ptt+=e.total||0; } } });
      var mxv=0; yl.forEach(function(y){ mxv=Math.max(mxv, Y[y].ss, Y[y].ps); });
      var bars=yl.map(function(y){
        var x=Y[y];
        var hs=mxv?Math.max(2,Math.round(x.ss/mxv*118)):2, hp=mxv?Math.max(2,Math.round(x.ps/mxv*118)):2;
        return '<div style="flex:1;min-width:44px;display:flex;flex-direction:column;align-items:center;gap:5px">'
          + '<div style="display:flex;align-items:flex-end;gap:3px;height:122px">'
          +   '<div title="매출 '+_fxFmt(x.ss)+'원" style="width:16px;height:'+hs+'px;background:#1B3A6B"></div>'
          +   '<div title="매입 '+_fxFmt(x.ps)+'원" style="width:16px;height:'+hp+'px;background:#9aa6b8"></div>'
          + '</div>'
          + '<div style="font-size:11px;color:'+(y===_fxSumYear?'#1B3A6B':'#8a94a6')+';font-weight:'+(y===_fxSumYear?'700':'400')+'">'+y+'</div>'
          + '</div>';
      }).join('');
      var T2={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
      var rowsY=yl.slice().reverse().map(function(y){
        var x=Y[y];
        ['sc','ss','st','stt','pc','ps','pt','ptt'].forEach(function(k){ T2[k]+=x[k]; });
        var pf=x.ss-x.ps, mr=x.ss?pf/x.ss*100:0;
        return '<tr'+((!x.sc&&!x.pc)?' style="opacity:.45"':'')+'>'
          + '<td style="'+TD+';text-align:center;font-weight:700;color:#14305c">'+y+'년</td>'
          + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.sc||'-')+'</td>'
          + '<td style="'+TD+'">'+_fxFmt(x.ss)+'</td>'
          + '<td style="'+TD+';font-weight:700">'+_fxFmt(x.stt)+'</td>'
          + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.pc||'-')+'</td>'
          + '<td style="'+TD+'">'+_fxFmt(x.ps)+'</td>'
          + '<td style="'+TD+';font-weight:700">'+_fxFmt(x.ptt)+'</td>'
          + '<td style="'+TD+';font-weight:700;color:'+(pf>=0?'#14305c':'#dc2626')+'">'+_fxFmt(pf)+'</td>'
          + '<td style="'+TD+';color:'+(pf>=0?'#14305c':'#dc2626')+'">'+(x.ss?mr.toFixed(1)+'%':'-')+'</td>'
          + '</tr>';
      }).join('');
      var pfT=T2.ss-T2.ps, mrT=T2.ss?pfT/T2.ss*100:0;
      rowsY += '<tr style="background:#f4f8fe">'
        + '<td style="'+TD+';text-align:center;font-weight:700;color:#1B3A6B">합계</td>'
        + '<td style="'+TD+';text-align:center;font-weight:700">'+T2.sc+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T2.ss)+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T2.stt)+'</td>'
        + '<td style="'+TD+';text-align:center;font-weight:700">'+T2.pc+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T2.ps)+'</td>'
        + '<td style="'+TD+';font-weight:700">'+_fxFmt(T2.ptt)+'</td>'
        + '<td style="'+TD+';font-weight:700;color:'+(pfT>=0?'#1B3A6B':'#dc2626')+'">'+_fxFmt(pfT)+'</td>'
        + '<td style="'+TD+';font-weight:700;color:'+(pfT>=0?'#1B3A6B':'#dc2626')+'">'+(T2.ss?mrT.toFixed(1)+'%':'-')+'</td>'
        + '</tr>';
      host.innerHTML =
        '<div style="background:#fff;border:1px solid #d6deea;padding:14px 16px 10px;margin-bottom:12px">'
        + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap">'
        +   '<span style="font-size:12.5px;font-weight:700;color:#14305c">연도별 매출·매입 추이</span>'
        +   '<span style="font-size:11px;color:#9ca3af">공급가액 기준 · 부가세 별도</span><span style="flex:1"></span>'
        +   '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#6b7280"><i style="width:9px;height:9px;background:#1B3A6B;display:inline-block"></i>매출</span>'
        +   '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#6b7280"><i style="width:9px;height:9px;background:#9aa6b8;display:inline-block"></i>매입</span>'
        + '</div>'
        + '<div style="display:flex;align-items:flex-end;gap:4px">'+bars+'</div>'
        + '</div>'
        + '<div style="background:#fff;border:1px solid #d6deea;overflow:auto"><table style="width:100%;border-collapse:separate;border-spacing:0;font-size:12.5px;min-width:860px">'
        + '<thead><tr>'
        +   '<th style="'+TH+'" rowspan="2">연도</th>'
        +   '<th style="'+TH+'" colspan="3">매출 (계산서 발행)</th>'
        +   '<th style="'+TH+'" colspan="3">매입 (계산서 수취)</th>'
        +   '<th style="'+TH+'" rowspan="2">매출총이익</th>'
        +   '<th style="'+TH+'" rowspan="2">마진율</th>'
        + '</tr><tr>'
        +   '<th style="'+TH+'">건수</th><th style="'+TH+'">공급가액</th><th style="'+TH+'">합계</th>'
        +   '<th style="'+TH+'">건수</th><th style="'+TH+'">공급가액</th><th style="'+TH+'">합계</th>'
        + '</tr></thead><tbody>'+rowsY+'</tbody></table></div>'
        + '<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">매출총이익 = 매출 공급가액 − 매입 공급가액 · 마진율 = 매출총이익 ÷ 매출 공급가액 (부가세 별도)</div>';
      return;
    }
"""

MONTH_NEW = r"""    if(_fxSumMode==='month'){
      var M={};
      for(var m=1;m<=12;m++) M[m]={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
      sv.forEach(function(e){ var m=Number(e.date.slice(5,7)); if(M[m]){ M[m].sc++; M[m].ss+=e.supply||0; M[m].st+=e.tax||0; M[m].stt+=e.total||0; } });
      pv.forEach(function(e){ var m=Number(e.date.slice(5,7)); if(M[m]){ M[m].pc++; M[m].ps+=e.supply||0; M[m].pt+=e.tax||0; M[m].ptt+=e.total||0; } });
      var T={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
      var _mg=function(x){ return x.ss ? ((x.ss-x.ps)/x.ss*100) : null; };   // r220: 마진율 (공급가액 기준)
      var rows='';
      for(var m2=1;m2<=12;m2++){
        var x=M[m2];
        ['sc','ss','st','stt','pc','ps','pt','ptt'].forEach(function(k){ T[k]+=x[k]; });
        var dim = !x.sc && !x.pc;
        var _r=_mg(x);
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
          + '<td style="'+TD+';color:'+((_r!=null&&_r>=0)?'#14305c':'#dc2626')+'">'+(_r!=null?_r.toFixed(1)+'%':'-')+'</td>'
          + '</tr>';
      }
      var _rT=_mg(T);
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
        + '<td style="'+TD+';font-weight:700;color:'+((_rT!=null&&_rT>=0)?'#1B3A6B':'#dc2626')+'">'+(_rT!=null?_rT.toFixed(1)+'%':'-')+'</td>'
        + '</tr>';
      host.innerHTML =
        '<div style="background:#fff;border:1px solid #d6deea;overflow:auto"><table style="width:100%;border-collapse:separate;border-spacing:0;font-size:12.5px;min-width:980px">'
        + '<thead><tr>'
        +   '<th style="'+TH+'" rowspan="2">월</th>'
        +   '<th style="'+TH+'" colspan="4">매출 (계산서 발행)</th>'
        +   '<th style="'+TH+'" colspan="4">매입 (계산서 수취)</th>'
        +   '<th style="'+TH+'" rowspan="2">차액(합계)</th>'
        +   '<th style="'+TH+'" rowspan="2">마진율</th>'
        + '</tr><tr>'
        +   '<th style="'+TH+'">건수</th><th style="'+TH+'">공급가액</th><th style="'+TH+'">세액</th><th style="'+TH+'">합계</th>'
        +   '<th style="'+TH+'">건수</th><th style="'+TH+'">공급가액</th><th style="'+TH+'">세액</th><th style="'+TH+'">합계</th>'
        + '</tr></thead><tbody>'+rows+'</tbody></table></div>'
        + '<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">마진율 = (매출 공급가액 − 매입 공급가액) ÷ 매출 공급가액 (부가세 별도)</div>'
        + (pv.length?'':'<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">매입 계산서 자료는 자료 업로드(홈택스 매입) 연결 후 채워집니다.</div>');
      return;
    }
"""

XLS_NEW = r"""      if(_fxSumMode==='year'){   // r220: 연도별 시트
        var yl2=_fxYears().slice().sort(), Y2={};
        yl2.forEach(function(y){ Y2[y]={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 }; });
        fxSalesInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date){ var a1=e.date.slice(0,4); if(Y2[a1]){ Y2[a1].sc++; Y2[a1].ss+=e.supply||0; Y2[a1].st+=e.tax||0; Y2[a1].stt+=e.total||0; } } });
        fxPurchInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date){ var a2=e.date.slice(0,4); if(Y2[a2]){ Y2[a2].pc++; Y2[a2].ps+=e.supply||0; Y2[a2].pt+=e.tax||0; Y2[a2].ptt+=e.total||0; } } });
        var TY={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
        var aoaY=[['연도','매출 건수','매출 공급가액','매출 합계','매입 건수','매입 공급가액','매입 합계','매출총이익','마진율(%)']];
        yl2.slice().reverse().forEach(function(y){
          var x=Y2[y];
          ['sc','ss','st','stt','pc','ps','pt','ptt'].forEach(function(k){ TY[k]+=x[k]; });
          aoaY.push([y+'년', x.sc, x.ss, x.stt, x.pc, x.ps, x.ptt, x.ss-x.ps, x.ss?Math.round((x.ss-x.ps)/x.ss*1000)/10:0]);
        });
        aoaY.push(['합계', TY.sc, TY.ss, TY.stt, TY.pc, TY.ps, TY.ptt, TY.ss-TY.ps, TY.ss?Math.round((TY.ss-TY.ps)/TY.ss*1000)/10:0]);
        var wsY=XLSX.utils.aoa_to_sheet(aoaY);
        wsY['!cols']=[{wch:8},{wch:9},{wch:16},{wch:16},{wch:9},{wch:16},{wch:16},{wch:16},{wch:10}];
        _fxXlsStyle(wsY, 0, [2,3,5,6,7], null);
        var wbY=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wbY, wsY, '연도별');
        XLSX.writeFile(wbY, '매입매출집계_연도별_'+_fxRegionLabel()+'_'+_fxDs()+'.xlsx');
        return;
      }
      if(_fxSumMode==='month'){
        var M={}, m;
        for(m=1;m<=12;m++) M[m]={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
        sv.forEach(function(e){ var k=Number(e.date.slice(5,7)); if(M[k]){ M[k].sc++; M[k].ss+=e.supply||0; M[k].st+=e.tax||0; M[k].stt+=e.total||0; } });
        pv.forEach(function(e){ var k=Number(e.date.slice(5,7)); if(M[k]){ M[k].pc++; M[k].ps+=e.supply||0; M[k].pt+=e.tax||0; M[k].ptt+=e.total||0; } });
        var T={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
        aoa=[['월','매출 건수','매출 공급가액','매출 세액','매출 합계','매입 건수','매입 공급가액','매입 세액','매입 합계','차액(합계)','마진율(%)']];
        for(m=1;m<=12;m++){
          var x=M[m];
          ['sc','ss','st','stt','pc','ps','pt','ptt'].forEach(function(k){ T[k]+=x[k]; });
          aoa.push([m+'월', x.sc, x.ss, x.st, x.stt, x.pc, x.ps, x.pt, x.ptt, x.stt-x.ptt, x.ss?Math.round((x.ss-x.ps)/x.ss*1000)/10:0]);
        }
        aoa.push(['합계', T.sc, T.ss, T.st, T.stt, T.pc, T.ps, T.pt, T.ptt, T.stt-T.ptt, T.ss?Math.round((T.ss-T.ps)/T.ss*1000)/10:0]);
        fn='매입매출집계_월별_'+_fxRegionLabel()+'_'+yr+'_'+_fxDs()+'.xlsx';
        money=[2,3,4,6,7,8,9]; left=null;
        var ws1=XLSX.utils.aoa_to_sheet(aoa);
        ws1['!cols']=[{wch:6},{wch:9},{wch:14},{wch:12},{wch:14},{wch:9},{wch:14},{wch:12},{wch:14},{wch:14},{wch:10}];
        _fxXlsStyle(ws1, 0, money, left);
        var wb1=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb1, ws1, yr+'년 월별');
        XLSX.writeFile(wb1, fn);
        return;
      }
"""

OPS = [
 # 툴바에 '연도별' 버튼
 ["""+   '<button type="button" class="btn pf-btn" data-m="month" onclick="fxSumMode(\\'month\\')" style="font-size:11.5px;padding:3px 11px">월별</button>'""",
  """+   '<button type="button" class="btn pf-btn" data-m="month" onclick="fxSumMode(\\'month\\')" style="font-size:11.5px;padding:3px 11px">월별</button>'\n"""
  """        +   '<button type="button" class="btn pf-btn" data-m="year" onclick="fxSumMode(\\'year\\')" style="font-size:11.5px;padding:3px 11px">연도별</button>'""",
  1, "BTN"],
 # 연도 선택은 연도별 모드에서 숨긴다
 ["    var q=document.getElementById('fxSumQ'); if(q) q.style.display = _fxSumMode==='vendor'?'':'none';",
  "    var q=document.getElementById('fxSumQ'); if(q) q.style.display = _fxSumMode==='vendor'?'':'none';\n"
  "    if(ysel) ysel.style.display = (_fxSumMode==='year') ? 'none' : '';   // r220: 연도별은 연도 선택이 필요 없다",
  1, "YSEL"],
]

SPLICES = [
 ["    if(_fxSumMode==='month'){\n      var M={};",
  "        + (pv.length?'':'<div style=\"margin-top:8px;font-size:11.5px;color:#9ca3af\">매입 계산서 자료는 자료 업로드(홈택스 매입) 연결 후 채워집니다.</div>');\n      return;\n    }\n",
  YEAR_BRANCH + MONTH_NEW, "RENDER"],
 ["      if(_fxSumMode==='month'){\n        var M={}, m;",
  "        XLSX.writeFile(wb1, fn);\n        return;\n      }\n",
  XLS_NEW, "XLS"],
]

MARKER = ["<!-- test build r219 2026-10-02 -->", "<!-- test build r220 2026-10-02 -->"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R220 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def splice(s, a, b, new, label):
    if s.count(a) != 1: raise SystemExit('R220 FAIL %s startAnchor %d' % (label, s.count(a)))
    if s.count(b) != 1: raise SystemExit('R220 FAIL %s endAnchor %d' % (label, s.count(b)))
    i = s.index(a); j = s.index(b, i)
    if j < i: raise SystemExit('R220 FAIL %s order' % label)
    return s[:i] + new + s[j + len(b):]


def apply_r220(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    for a, b, new, label in SPLICES:
        s = splice(s, a, b, new, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r220(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r220 applied:', path)
