# -*- coding: utf-8 -*-
# r164: [종사업장이 여러 곳인 업체 처리 — r163 채우기 도구 보완 + 확인 수단]
#
#  사용자 확인: 플라즈맵처럼 사업자번호 하나에 본점+종사업장 4곳(총 5곳)을 운영하는
#  실제 거래처가 있다. 결제는 본사가 한 번에 하므로 미수 원장은 지금처럼 합치는 게 맞다
#  (원장 구조는 건드리지 않는다). 다만 계산서는 종사업장별로 다르게 발행해야 한다.
#
#  r163 의 결함: "계산서에서 종사업장번호 채우기" 도구가 _fxVsbOf 로 "가장 최근 값" 하나를
#  골라 채우자고 제안한다. 종사업장이 5곳인 업체에는 그중 아무거나(마지막 것) 채우는 셈이라
#  틀린 값이 들어간다. 실제로 플라즈맵 사례에서 0004 를 제안하는 것을 확인했다.
#
#  수정
#   (1) _fxVsbList(biz,name,vbiz): 계산서에 나타난 종사업장번호를 전부(중복 제거·정렬) 반환.
#   (2) 채우기 도구 후보 = 종사업장번호가 "딱 하나로 확정되는" 업체만.
#       여러 곳인 업체는 자동으로 채우지 않고, 패널 아래에 별도 안내 목록으로 보여준다
#       (값 목록을 함께 표시해 사람이 업체 화면에서 직접 고르도록).
#   (3) 업체 상세 폼: 종사업장번호 칸 아래에 "계산서 기준: 0000 0001 …" 을 표시하고
#       각 값을 누르면 그 값이 입력칸에 들어간다. 여러 곳인 업체를 사람이 쉽게 고르게.
#   (4) 미수현황 원장 상세: 계산서 줄에 종사업장번호를 표기해 어느 사업장 건인지 보이게.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R164 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r164(s, path):
    # ── 1. 종사업장번호 목록 조회 ──
    s = rep(s,
        "  // r163: 계산서에 적힌 그 거래처의 종사업장번호 (사업장 기준, 최근 것 우선)",
        r"""  // r164: 계산서에 나타난 그 거래처의 종사업장번호 전부 (중복 제거·오름차순)
  function _fxVsbList(biz, name, vbiz){
    var bd=String(vbiz||'').replace(/\D/g,'');
    var seen={}, out=[];
    function scan(arr){
      for(var i=0;i<arr.length;i++){
        var e=arr[i];
        if(e.biz!==biz || !e.vsb) continue;
        if(bd){ if(String(e.vbiz||'').replace(/\D/g,'')!==bd) continue; }
        else if(e.vendor!==name) continue;
        var v=_cliSbNorm(e.vsb);
        if(v && !seen[v]){ seen[v]=1; out.push(v); }
      }
    }
    scan(fxSalesInv); scan(fxPurchInv);
    return out.sort();
  }
  // r163: 계산서에 적힌 그 거래처의 종사업장번호 (사업장 기준, 최근 것 우선)""", 1, 'VSBLIST')

    # ── 2. 채우기 후보를 "하나로 확정되는 업체" 로 제한 + 여러 곳 목록 분리 ──
    s = rep(s,
        """  function _clxSbCands(){
    var out=[];
    (allClients()||[]).forEach(function(c){
      if(_cliSb(c)) return;
      var v=_fxVsbOf(_cliBr(c), c[0], c[1]);
      if(!v || v==='0000') return;
      out.push({ c:c, sb:v });
    });
    return out.sort(function(a,b){ return String(a.c[0]).localeCompare(String(b.c[0]),'ko'); });
  }""",
        r"""  //  r164: 후보 = 계산서상 종사업장번호가 "하나로 확정되는" 업체만.
  //   여러 곳인 업체(본점+종사업장 여러 개)는 아무거나 채우면 틀린 값이 되므로 자동 대상에서 뺀다.
  function _clxSbScan(){
    var one=[], many=[];
    (allClients()||[]).forEach(function(c){
      if(_cliSb(c)) return;
      var list=_fxVsbList(_cliBr(c), c[0], c[1]);
      var real=list.filter(function(v){ return v!=='0000'; });
      if(!real.length) return;                      // 값이 없거나 0000(본점)뿐 -> 대상 아님
      if(real.length===1 && list.length===1) one.push({ c:c, sb:real[0] });
      else many.push({ c:c, list:list });           // 여러 곳 -> 사람이 직접 고르도록 안내만
    });
    var byName=function(a,b){ return String(a.c[0]).localeCompare(String(b.c[0]),'ko'); };
    return { one:one.sort(byName), many:many.sort(byName) };
  }
  function _clxSbCands(){ return _clxSbScan().one; }""", 1, 'SBSCAN')
    s = rep(s,
        "  function _clxSbShow(){ return _isAdmin() && !_clxSbOff() && _clxSbCands().length>0; }",
        "  function _clxSbShow(){\n"
        "    if(!_isAdmin() || _clxSbOff()) return false;\n"
        "    var sc=_clxSbScan();\n"
        "    return (sc.one.length + sc.many.length) > 0;   // r164: 여러 곳 안내만 있어도 연다\n"
        "  }",
        1, 'SBSHOW')

    # 버튼 숫자도 합계로
    s = rep(s,
        "'\">종사업장번호 채우기 '+_clxSbCands().length+'</button>')",
        "'\">종사업장번호 '+(function(){ var sc=_clxSbScan(); return sc.one.length + (sc.many.length?('+'+sc.many.length):''); })()+'</button>')",
        1, 'SBBTNNUM')

    # ── 3. 패널: 여러 곳 업체 안내 구역 추가 ──
    s = rep(s,
        """  function _clxSbPanelHtml(){
    var cands=_clxSbCands();
    if(!cands.length) return '';""",
        """  function _clxSbPanelHtml(){
    var _sc=_clxSbScan();
    var cands=_sc.one;
    if(!cands.length && !_sc.many.length) return '';""", 1, 'SBPANELHEAD')
    s = rep(s,
        "      +   '<span style=\"font-size:13.5px;font-weight:700;color:#14305c\">계산서에서 종사업장번호 채우기 — 후보 '+cands.length+'곳</span>'\n"
        "      +   '<span style=\"flex:1\"></span>'\n"
        "      +   '<button type=\"button\" class=\"btn\" onclick=\"clxSbApply()\" style=\"font-size:12px;padding:4px 14px;border:1px solid #1B3A6B;background:#1B3A6B;color:#fff\">선택한 업체에 채우기</button>'",
        "      +   '<span style=\"font-size:13.5px;font-weight:700;color:#14305c\">계산서에서 종사업장번호 채우기 — 자동 후보 '+cands.length+'곳'+(_sc.many.length?(' · 직접 선택 '+_sc.many.length+'곳'):'')+'</span>'\n"
        "      +   '<span style=\"flex:1\"></span>'\n"
        "      +   (cands.length ? '<button type=\"button\" class=\"btn\" onclick=\"clxSbApply()\" style=\"font-size:12px;padding:4px 14px;border:1px solid #1B3A6B;background:#1B3A6B;color:#fff\">선택한 업체에 채우기</button>' : '')",
        1, 'SBPANELHEAD2')
    s = rep(s,
        "      + '<div style=\"max-height:420px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse;table-layout:fixed\">'\n"
        "      + '<colgroup><col style=\"width:46px\"><col><col style=\"width:80px\"><col style=\"width:130px\"><col style=\"width:110px\"></colgroup>'\n"
        "      + '<thead><tr><th style=\"'+TH+'\">적용</th><th style=\"'+TH+';text-align:left\">업체명</th><th style=\"'+TH+'\">지점</th><th style=\"'+TH+'\">사업자번호</th><th style=\"'+TH+'\">계산서 종사업장</th></tr></thead>'\n"
        "      + '<tbody>'+rows+'</tbody></table></div>'",
        r"""      + (cands.length ? ('<div style="max-height:360px;overflow:auto"><table style="width:100%;border-collapse:collapse;table-layout:fixed">'
      + '<colgroup><col style="width:46px"><col><col style="width:80px"><col style="width:130px"><col style="width:110px"></colgroup>'
      + '<thead><tr><th style="'+TH+'">적용</th><th style="'+TH+';text-align:left">업체명</th><th style="'+TH+'">지점</th><th style="'+TH+'">사업자번호</th><th style="'+TH+'">계산서 종사업장</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>') : '')
      + (_sc.many.length ? ('<div style="padding:9px 16px;background:#fff8ef;border-top:1px solid #f0d9b8;font-size:11.5px;color:#b45309;line-height:1.7">'
          + '<b>종사업장이 여러 곳인 업체 '+_sc.many.length+'곳 — 자동으로 채우지 않습니다.</b><br>'
          + '하나를 임의로 넣으면 틀린 값이 됩니다. 업체를 열어 종사업장번호 칸 아래의 값 중에서 직접 골라 주세요.'
          + '</div>'
          + '<div style="max-height:240px;overflow:auto"><table style="width:100%;border-collapse:collapse;table-layout:fixed">'
          + '<colgroup><col><col style="width:80px"><col style="width:130px"><col style="width:200px"></colgroup>'
          + '<thead><tr><th style="'+TH+';text-align:left">업체명</th><th style="'+TH+'">지점</th><th style="'+TH+'">사업자번호</th><th style="'+TH+';text-align:left">계산서에 나타난 종사업장</th></tr></thead>'
          + '<tbody>'+_sc.many.map(function(x){
              return '<tr>'
                + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(x.c[0])+'</td>'
                + '<td style="'+TD+';text-align:center">'+_clxBrBadge(x.c)+'</td>'
                + '<td style="'+TD+';text-align:center;color:#6b7280;white-space:nowrap">'+esc(x.c[1]||'')+'</td>'
                + '<td style="'+TD+';color:#374151">'+x.list.map(function(v){ return '<span style="display:inline-block;border:1px solid #cdd8e6;background:#f4f8fe;padding:0 6px;margin:1px 3px 1px 0;font-size:11.5px">'+esc(v)+'</span>'; }).join('')+'</td>'
                + '</tr>';
            }).join('')+'</tbody></table></div>') : '')""", 1, 'SBPANELMANY')

    # ── 4. 업체 상세 폼: 계산서 기준 종사업장번호 목록(클릭하면 입력) ──
    s = rep(s,
        "      +   _clxFld('subBiz','종사업장번호 (선택)', _cliSb(pair||[]), 1, 'placeholder=\"필요할 때만 · 예 0001\" inputmode=\"numeric\"')",
        "      +   _clxSbFldHtml(pair)",
        1, 'FORMSB')
    s = rep(s,
        "  function _clxSelFld(k, label, val, opts){",
        r"""  // r164: 종사업장번호 칸 + 계산서에서 확인된 값 목록(누르면 입력칸에 들어감)
  function _clxSbFldHtml(pair){
    var base=_clxFld('subBiz','종사업장번호 (선택)', _cliSb(pair||[]), 1, 'placeholder="필요할 때만 · 예 0001" inputmode="numeric"');
    var list=[];
    try{ if(pair && pair.length) list=_fxVsbList(_cliBr(pair), pair[0], pair[1]); }catch(_e){}
    if(!list.length) return base;
    var chips=list.map(function(v){
      return '<button type="button" onclick="clxSbPick(this,\'' + esc(v) + '\')" title="누르면 종사업장번호 칸에 입력됩니다" '
        + 'style="border:1px solid #cdd8e6;background:#f4f8fe;color:#14305c;font-size:11px;padding:1px 6px;margin:2px 3px 0 0;cursor:pointer;font-family:inherit;border-radius:0">'+esc(v)+'</button>';
    }).join('');
    return base.replace('</div>',
      '<div style="font-size:10.5px;color:#9ca3af;margin-top:2px">계산서 기준 '+chips+'</div></div>');
  }
  window.clxSbPick = function(btn, v){
    var f=btn.closest('#clxForm'); if(!f) return;
    var el=f.querySelector('.clx-f[data-k="subBiz"]'); if(!el) return;
    el.value=v; try{ el.focus(); }catch(_e){}
  };
  function _clxSelFld(k, label, val, opts){""", 1, 'SBFLD')

    # ── 5. 미수현황 원장 상세: 계산서 줄에 종사업장 표기 ──
    s = rep(s,
        "    L.invs.forEach(function(e){ rows.push({date:e.date, type:'계산서', desc:'세금계산서 (공급가 '+_fxFmt(e.supply)+' + 세액 '+_fxFmt(e.tax)+')'+(e.note?' · '+e.note:''), chg:e.total}); });",
        "    // r164: 종사업장번호가 있으면 어느 사업장 건인지 보이게 (사업자번호 하나에 사업장이 여러 곳인 거래처 대응)\n"
        "    L.invs.forEach(function(e){ rows.push({date:e.date, type:'계산서', desc:'세금계산서 (공급가 '+_fxFmt(e.supply)+' + 세액 '+_fxFmt(e.tax)+')'+(e.vsb?' · 종사업장 '+e.vsb:'')+(e.note?' · '+e.note:''), chg:e.total}); });",
        1, 'LEDGERVSB')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r164(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r163 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r163 2026-08-26 -->', '<!-- test build r164 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
