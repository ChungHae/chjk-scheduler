# -*- coding: utf-8 -*-
# r219 (사용자 요청 2026-10-02): 회계 > 집계 > [거래처별] 을 '건수·합계 나열' 이 아니라
#   매출 순위표 / 매입 순위표 두 개로 좌우 나란히 보여준다.
#   - 순위 · 거래처 · 건 · 합계 · 비중(%) + 비중 막대 · 전년 대비 증감
#   - 기본 TOP 20, [전체 N곳 보기] 로 펼침 (매출/매입 각각 따로)
#   - 엑셀도 '매출 순위' / '매입 순위' 두 시트로 바뀐다
import io, sys, json

RK_RENDER = r"""    // 거래처별 → 매출·매입 순위표 (r219)
    var V={};
    function _vk(e){ return (_fxRegion==='all'?(e.biz+'|'):'')+((e.vbiz&&/\d{3}-\d{2}-\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor)); }
    function vslot(e){ var k=_vk(e); if(!V[k]) V[k]={k:k, name:e.vendor, vbiz:e.vbiz||'', b:e.biz, sc:0, stt:0, pc:0, ptt:0, ys:0, yp:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }
    sv.forEach(function(e){ var s2=vslot(e); s2.sc++; s2.stt+=e.total||0; });
    pv.forEach(function(e){ var s3=vslot(e); s3.pc++; s3.ptt+=e.total||0; });
    var _py=String(Number(_fxSumYear)-1), _hasPy=false;
    fxSalesInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===_py){ _hasPy=true; vslot(e).ys+=e.total||0; } });
    fxPurchInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===_py){ _hasPy=true; vslot(e).yp+=e.total||0; } });
    var _all=Object.keys(V).map(function(k){ return V[k]; });
    if(_fxSumQ) _all=_all.filter(function(x){ return x.name.toLowerCase().indexOf(_fxSumQ)>=0 || x.vbiz.indexOf(_fxSumQ)>=0; });
    if(!_all.length){ host.innerHTML='<div style="text-align:center;padding:48px;color:#b6bec9;font-size:13px">해당 연도 자료가 없습니다.</div>'; return; }
    var RTH='padding:8px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var RTD='padding:7px 8px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;white-space:nowrap;font-size:12px;text-align:right';
    function _rkDelta(cur, prev){
      if(!_hasPy) return '<span style="color:#cfd6e0">-</span>';
      if(!prev) return cur?'<span style="color:#5b7ba6;font-size:11px">신규</span>':'<span style="color:#cfd6e0">-</span>';
      var r=(cur-prev)/prev*100, up=(r>=0);
      return '<span style="color:'+(up?'#14305c':'#dc2626')+';font-size:11px">'+(up?'▲':'▼')+Math.abs(r).toFixed(1)+'%</span>';
    }
    function _rkCard(title, inner){
      return '<div style="background:#fff;border:1px solid #d6deea">'+title+inner+'</div>';
    }
    function _rkTable(label, amtK, cntK, pyK, side, barCol){
      var rows=_all.filter(function(x){ return (x[amtK]||0)>0; }).sort(function(a,b){ return b[amtK]-a[amtK]; });
      var tot=rows.reduce(function(a,x){ return a+x[amtK]; },0);
      var head='<div style="padding:10px 12px;font-size:12.5px;font-weight:700;color:#14305c;border-bottom:1px solid #e3e9f0">'+label
        + ' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+_fxSumYear+'년 · '+rows.length+'곳 · '+_fxFmt(tot)+'원</span></div>';
      if(!rows.length) return _rkCard(head, '<div style="text-align:center;padding:32px;color:#b6bec9;font-size:12.5px">자료가 없습니다.</div>');
      var mx=rows[0][amtK];
      var lim=(side==='p')?_fxRkTopP:_fxRkTopS;
      var shown=(lim>0 && rows.length>lim)?rows.slice(0,lim):rows;
      var acc=0;
      var body=shown.map(function(x,i){
        acc+=x[amtK];
        var pct=tot?x[amtK]/tot*100:0;
        var bw=mx?Math.max(1,Math.round(x[amtK]/mx*100)):0;
        return '<tr>'
          + '<td style="'+RTD+';text-align:center;color:'+(i<3?'#1B3A6B':'#9ca3af')+';font-weight:'+(i<3?'700':'400')+'">'+(i+1)+'</td>'
          + '<td style="'+RTD+';text-align:left;overflow:hidden">'
          +   '<div style="font-weight:700;color:#14305c;overflow:hidden;text-overflow:ellipsis">'+((_fxRegion==='all'&&x.b)?_fxBizBadge(x.b):'')+esc(x.name)+(x.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:10.5px">'+x.vbiz+'</span>':'')+'</div>'
          +   '<div style="margin-top:3px;height:3px;background:#edf1f7"><div style="height:3px;width:'+bw+'%;background:'+barCol+'"></div></div>'
          + '</td>'
          + '<td style="'+RTD+';text-align:center;color:#6b7280">'+(x[cntK]||'-')+'</td>'
          + '<td style="'+RTD+';font-weight:700">'+_fxFmt(x[amtK])+'</td>'
          + '<td style="'+RTD+';color:#6b7280">'+pct.toFixed(1)+'%</td>'
          + '<td style="'+RTD+';text-align:center">'+_rkDelta(x[amtK], x[pyK]||0)+'</td>'
          + '</tr>';
      }).join('');
      body += '<tr style="background:#f4f8fe">'
        + '<td style="'+RTD+'"></td>'
        + '<td style="'+RTD+';text-align:left;font-weight:700;color:#1B3A6B">합계 ('+rows.length+'곳)</td>'
        + '<td style="'+RTD+';text-align:center;font-weight:700">'+rows.reduce(function(a,x){ return a+(x[cntK]||0); },0)+'</td>'
        + '<td style="'+RTD+';font-weight:700">'+_fxFmt(tot)+'</td>'
        + '<td style="'+RTD+';color:#6b7280">100%</td>'
        + '<td style="'+RTD+'"></td></tr>';
      var FT='padding:9px 10px;border-bottom:1px solid #eef2f7;text-align:center;font-size:11.5px;color:#8a94a6';
      var BT='font-size:11px;padding:2px 10px;border:1px solid #5b7ba6;color:#5b7ba6;background:#fff;cursor:pointer';
      if(lim>0 && rows.length>lim){
        body += '<tr><td colspan="6" style="'+FT+'">상위 '+lim+'곳 = 전체의 <b style="color:#5b7ba6">'+(tot?(acc/tot*100).toFixed(1):'0.0')+'%</b> · '
          + '<button type="button" onclick="fxSumRankMore(\''+side+'\')" style="'+BT+'">전체 '+rows.length+'곳 보기</button></td></tr>';
      } else if(lim===0 && rows.length>20){
        body += '<tr><td colspan="6" style="'+FT+'"><button type="button" onclick="fxSumRankMore(\''+side+'\')" style="'+BT+'">TOP 20만 보기</button></td></tr>';
      }
      return _rkCard(head,
        '<table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed">'
        + '<colgroup><col style="width:34px"><col><col style="width:42px"><col style="width:104px"><col style="width:52px"><col style="width:62px"></colgroup>'
        + '<thead><tr><th style="'+RTH+'">순위</th><th style="'+RTH+'">거래처</th><th style="'+RTH+'">건</th><th style="'+RTH+'">합계</th><th style="'+RTH+'">비중</th><th style="'+RTH+'">전년</th></tr></thead>'
        + '<tbody>'+body+'</tbody></table>');
    }
    host.innerHTML =
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:12px;align-items:start">'
      + _rkTable('매출 순위', 'stt', 'sc', 'ys', 's', '#5b7ba6')
      + _rkTable('매입 순위', 'ptt', 'pc', 'yp', 'p', '#8a94a6')
      + '</div>'
      + (_hasPy?'':'<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">전년('+_py+'년) 자료가 없어 전년 대비 증감은 표시되지 않습니다.</div>');
"""

RK_XLS = r"""      var V={};
      function _vk(e){ return (_fxRegion==='all'?(e.biz+'|'):'')+((e.vbiz&&/\d{3}-\d{2}-\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor)); }
      function vslot(e){ var k=_vk(e); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', b:e.biz, sc:0, stt:0, pc:0, ptt:0, ys:0, yp:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }
      sv.forEach(function(e){ var s2=vslot(e); s2.sc++; s2.stt+=e.total||0; });
      pv.forEach(function(e){ var s3=vslot(e); s3.pc++; s3.ptt+=e.total||0; });
      var py=String(Number(yr)-1);
      fxSalesInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===py) vslot(e).ys+=e.total||0; });
      fxPurchInv.forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===py) vslot(e).yp+=e.total||0; });
      var all=Object.keys(V).map(function(k){ return V[k]; });
      if(_fxSumQ) all=all.filter(function(x){ return x.name.toLowerCase().indexOf(_fxSumQ)>=0 || x.vbiz.indexOf(_fxSumQ)>=0; });
      if(!all.length){ showInfoModal('집계','조건에 맞는 거래처가 없습니다.'); return; }
      var allMode=(_fxRegion==='all');
      var wb2=XLSX.utils.book_new(), made=0;
      [['매출 순위','stt','sc','ys'],['매입 순위','ptt','pc','yp']].forEach(function(cf){
        var label=cf[0], amtK=cf[1], cntK=cf[2], pyK=cf[3];
        var rows=all.filter(function(x){ return (x[amtK]||0)>0; }).sort(function(a,b){ return b[amtK]-a[amtK]; });
        if(!rows.length) return;
        var tot=rows.reduce(function(a,x){ return a+x[amtK]; },0);
        var head=(allMode?['사업장']:[]).concat(['순위','거래처','사업자번호','건수','합계','비중(%)',py+'년 합계','증감(%)']);
        var aoa2=[head];
        rows.forEach(function(x,i){
          var prev=x[pyK]||0;
          var dv = prev ? Math.round((x[amtK]-prev)/prev*1000)/10 : (x[amtK]?'신규':'');
          aoa2.push((allMode?[x.b||'']:[]).concat([i+1, x.name, x.vbiz||'', x[cntK]||0, x[amtK], tot?Math.round(x[amtK]/tot*1000)/10:0, prev||'', dv]));
        });
        aoa2.push((allMode?['']:[]).concat(['','합계 ('+rows.length+'곳)','', rows.reduce(function(a,x){ return a+(x[cntK]||0); },0), tot, 100, '', '']));
        var ws=XLSX.utils.aoa_to_sheet(aoa2);
        ws['!cols']=(allMode?[{wch:8}]:[]).concat([{wch:6},{wch:26},{wch:14},{wch:8},{wch:15},{wch:9},{wch:15},{wch:9}]);
        _fxXlsStyle(ws, 0, (allMode?[5,7]:[4,6]), (allMode?[2]:[1]));
        XLSX.utils.book_append_sheet(wb2, ws, label);
        made++;
      });
      if(!made){ showInfoModal('집계','해당 연도 자료가 없습니다.'); return; }
      XLSX.writeFile(wb2, '매입매출집계_거래처순위_'+_fxRegionLabel()+'_'+yr+'_'+_fxDs()+'.xlsx');
"""

OPS = [
 [
  "  var _fxSumMode='month', _fxSumYear=null, _fxSumQ='';",
  "  var _fxSumMode='month', _fxSumYear=null, _fxSumQ='';\n"
  "  var _fxRkTopS=20, _fxRkTopP=20;   // r219: 거래처 순위표 표시 개수 (0 = 전체)\n"
  "  window.fxSumRankMore = function(side){ if(side==='p') _fxRkTopP = _fxRkTopP?0:20; else _fxRkTopS = _fxRkTopS?0:20; _fxRenderSumBody(); };",
  1, "STATE"
 ],
]

SPLICES = [
 ["    // 거래처별\n    var V={};", "      + '<tbody>'+rows2+'</tbody></table></div>';\n", RK_RENDER, "RENDER"],
 ["      var V={};\n      function vslot(e){", "      XLSX.writeFile(wb2, '매입매출집계_거래처별_'+_fxRegionLabel()+'_'+yr+'_'+_fxDs()+'.xlsx');\n", RK_XLS, "XLS"],
]

MARKER = ["<!-- test build r218 2026-10-02 -->", "<!-- test build r219 2026-10-02 -->"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R219 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def splice(s, a, b, new, label):
    if s.count(a) != 1: raise SystemExit('R219 FAIL %s startAnchor %d' % (label, s.count(a)))
    if s.count(b) != 1: raise SystemExit('R219 FAIL %s endAnchor %d' % (label, s.count(b)))
    i = s.index(a); j = s.index(b, i)
    if j < i: raise SystemExit('R219 FAIL %s order' % label)
    j += len(b)
    return s[:i] + new + s[j:]


def apply_r219(s, path):
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
        s = apply_r219(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r219 applied:', path)
