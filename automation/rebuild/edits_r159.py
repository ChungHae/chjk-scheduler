# -*- coding: utf-8 -*-
# r159: [업체 지점·종사업장번호 — 2단계: 화면 입력·표시]
#
#  r158 에서 자료 구조([이름,번호,지점,종사업장번호])만 넓혔고 화면은 그대로였다.
#  이번에 사람이 보고 넣을 수 있게 만든다.
#
#  1) 업체 상세 폼: 업체명/사업자번호/대표자 줄 바로 아래에 "지점"(서울·화성 선택)과
#     "종사업장번호" 한 줄을 새로 넣는다. 기존 줄들은 자리를 그대로 둔다.
#     종사업장번호는 선택 입력 — 비워도 저장되고 아무 검증도 걸지 않는다(사용자 지시).
#     넣을 때만 숫자 4자리로 정규화된다(_cliSbNorm).
#  2) clxSave: 폼의 지점·종사업장번호를 읽어 저장. 폼에 그 칸이 없는 경우(예전 화면이
#     떠 있는 상태)에는 기존 값을 그대로 유지해 지점이 지워지지 않게 방어한다.
#  3) 업체 목록: 사업자번호 옆에 "지점" 열 추가(서울/화성 배지). 표 열이 6 -> 7 로 늘어나
#     colgroup·thead·펼침행 colspan 을 함께 맞춘다.
#  4) 툴바에 지점 필터(전체/서울/화성). 검색과 함께 걸리며, 필터를 바꾸면 1페이지로 간다.
#     개수 표시도 필터 결과 기준으로 바뀐다.
#
#  아직 안 하는 것(3단계 이후): 같은 이름+다른 지점 2줄 등록 허용, clientInfo 키 이관,
#  견적 쪽 연결, 홈택스 종사업장번호 읽기.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R159 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r159(s, path):
    # ── 1. select 용 헬퍼 (_clxFld 옆) ──
    s = rep(s,
        """  function _clxFld(k, label, val, span, extra){""",
        r"""  // r159: 선택 입력칸 (_clxFld 와 같은 결). clxSave 는 .clx-f[data-k] 로 읽으므로 클래스를 맞춘다.
  function _clxSelFld(k, label, val, opts){
    var o=opts.map(function(v){ return '<option value="'+esc(v)+'"'+(String(val)===v?' selected':'')+'>'+esc(v)+'</option>'; }).join('');
    return '<div style="grid-column:span 1;display:flex;flex-direction:column;gap:3px;min-width:0">'
      + '<span style="font-size:11px;font-weight:700;color:#5b7ba6">'+label+'</span>'
      + '<select class="clx-f" data-k="'+k+'" style="width:100%;height:30px;box-sizing:border-box;padding:0 6px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\'#1B3A6B\'" onblur="this.style.borderColor=\'#c8d2de\'">'+o+'</select>'
      + '</div>';
  }
  function _clxFld(k, label, val, span, extra){""", 1, 'SELHELPER')

    # ── 2. 폼에 지점·종사업장번호 줄 추가 ──
    s = rep(s,
        "      +   _clxFld('name','업체명 *',orig,1) + _clxFld('bizNo','사업자번호',bz,1,'oninput=\"clxBizInput(this)\" onchange=\"clxBizBlur(this)\"') + _clxFld('ceo','대표자',inf.ceo,1)",
        "      +   _clxFld('name','업체명 *',orig,1) + _clxFld('bizNo','사업자번호',bz,1,'oninput=\"clxBizInput(this)\" onchange=\"clxBizBlur(this)\"') + _clxFld('ceo','대표자',inf.ceo,1)\n"
        "      +   _clxSelFld('branch','지점', _cliBr(pair||[]), CLI_BR)\n"
        "      +   _clxFld('subBiz','종사업장번호 (선택)', _cliSb(pair||[]), 1, 'placeholder=\"필요할 때만 · 예 0001\" inputmode=\"numeric\"')\n"
        "      +   '<div></div>'",
        1, 'FORMROW')

    # ── 3. clxSave 가 지점·종사업장을 읽어 저장 ──
    s = rep(s,
        """    if(!orig){
      clientList.push(_cliMake(nm,bz));
    } else {
      var found=false;
      for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===orig){ clientList[i]=_cliKeep(clientList[i], nm, bz); found=true; break; } }
      if(!found) clientList.push(_cliMake(nm,bz));
      for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===orig){ customClients[j]=_cliKeep(customClients[j], nm, bz); } }""",
        r"""    // r159: 폼의 지점·종사업장번호. 칸이 없는 화면이면 기존 값을 그대로 유지(지점 유실 방지)
    var _hasFld=function(k){ return !!box.querySelector('.clx-f[data-k="'+k+'"]'); };
    var _prev = orig ? (clientList.filter(function(c){ return c[0]===orig; })[0] || null) : null;
    var _br = _hasFld('branch') ? _cliBrNorm(get('branch')) : (_prev ? _cliBr(_prev) : '서울');
    var _sb = _hasFld('subBiz') ? _cliSbNorm(get('subBiz')) : (_prev ? _cliSb(_prev) : '');
    if(!orig){
      clientList.push(_cliMake(nm,bz,_br,_sb));
    } else {
      var found=false;
      for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===orig){ clientList[i]=_cliMake(nm,bz,_br,_sb); found=true; break; } }
      if(!found) clientList.push(_cliMake(nm,bz,_br,_sb));
      for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===orig){ customClients[j]=_cliMake(nm,bz,_br,_sb); } }""",
        1, 'CLXSAVEBR')

    # ── 4. 지점 필터 상태 + 툴바 버튼 ──
    s = rep(s,
        "  var _clxPage = 1;   // r148: 페이지네이션(1페이지 20개)",
        "  var _clxBr = 'all';   // r159: 지점 필터 (all|서울|화성)\n"
        "  var _clxPage = 1;   // r148: 페이지네이션(1페이지 20개)",
        1, 'BRSTATE')
    s = rep(s,
        '      <span id="clxCount" style="font-size:11px;color:#9ca3af;white-space:nowrap;margin-left:6px"></span>',
        '      <span class="inv-flat-div"></span>\n'
        '      <div id="clxBrBtns" style="display:flex;gap:4px"></div>\n'
        '      <span id="clxCount" style="font-size:11px;color:#9ca3af;white-space:nowrap;margin-left:6px"></span>',
        1, 'TOOLBAR')
    s = rep(s,
        "  window.clxCancel = function(){ _clxExp=null; _clxRender(); };",
        r"""  window.clxCancel = function(){ _clxExp=null; _clxRender(); };
  window.clxSetBr = function(b){ _clxBr=b; _clxExp=null; _clxPage=1; _clxRender(); };
  function _clxBrBtnsHtml(){
    return [['all','전체'],['서울','서울'],['화성','화성']].map(function(b){
      return '<button type="button" class="btn pf-btn'+(_clxBr===b[0]?' active':'')+'" onclick="clxSetBr(\''+b[0]+'\')" style="font-size:11.5px;padding:3px 11px">'+b[1]+'</button>';
    }).join('');
  }""", 1, 'BRBTNS')

    # ── 5. 목록: 지점 필터 적용 + 개수 표시 + 버튼 렌더 ──
    s = rep(s,
        """    var all=allClients().slice().sort(function(a,b){ return String(a[0]).localeCompare(String(b[0])); });
    var cnt=document.getElementById('clxCount'); if(cnt) cnt.textContent = all.length + '개 업체';
    var q=_clxQ, qd=q.replace(/\\D/g,'');
    var list=all.filter(function(c){
      if(_clxExp!==null && _clxExp!=='' && c[0]===_clxExp) return true;   // 펼친 업체는 항상 표시
      if(!q) return true;""",
        r"""    var _allRaw=allClients().slice().sort(function(a,b){ return String(a[0]).localeCompare(String(b[0])); });
    // r159: 지점 필터 (펼쳐 놓은 업체는 필터와 무관하게 남긴다)
    var all=_allRaw.filter(function(c){
      if(_clxBr==='all') return true;
      if(_clxExp!==null && _clxExp!=='' && c[0]===_clxExp) return true;
      return _cliBr(c)===_clxBr;
    });
    var _brb=document.getElementById('clxBrBtns'); if(_brb) _brb.innerHTML=_clxBrBtnsHtml();
    var cnt=document.getElementById('clxCount');
    if(cnt) cnt.textContent = (_clxBr==='all') ? (all.length + '개 업체')
                                               : (all.length + '개 업체 (' + _clxBr + ' · 전체 ' + _allRaw.length + ')');
    var q=_clxQ, qd=q.replace(/\D/g,'');
    var list=all.filter(function(c){
      if(_clxExp!==null && _clxExp!=='' && c[0]===_clxExp) return true;   // 펼친 업체는 항상 표시
      if(!q) return true;""", 1, 'BRFILTER')

    # ── 6. 표에 지점 열 추가 (6 -> 7열) ──
    s = rep(s,
        "      + '<colgroup><col style=\"width:220px\"><col style=\"width:120px\"><col style=\"width:180px\"><col><col style=\"width:130px\"><col style=\"width:130px\"></colgroup>'\n"
        "      + '<thead><tr>'\n"
        "      +   '<th style=\"'+TH+'\">업체명</th><th style=\"'+TH+'\">사업자번호</th><th style=\"'+TH+'\">대표자</th><th style=\"'+TH+'\">주소</th><th style=\"'+TH+'\">대표전화</th><th style=\"'+TH+'\">FAX</th>'",
        "      + '<colgroup><col style=\"width:220px\"><col style=\"width:120px\"><col style=\"width:104px\"><col style=\"width:150px\"><col><col style=\"width:130px\"><col style=\"width:130px\"></colgroup>'\n"
        "      + '<thead><tr>'\n"
        "      +   '<th style=\"'+TH+'\">업체명</th><th style=\"'+TH+'\">사업자번호</th><th style=\"'+TH+'\">지점</th><th style=\"'+TH+'\">대표자</th><th style=\"'+TH+'\">주소</th><th style=\"'+TH+'\">대표전화</th><th style=\"'+TH+'\">FAX</th>'",
        1, 'THEAD')
    s = rep(s,
        "            + '<td style=\"'+TD+';color:#6b7280;text-align:center\">'+esc(bz)+'</td>'\n"
        "            + '<td style=\"'+TD+';text-align:center\">'+esc(inf.ceo||'')+'</td>'",
        "            + '<td style=\"'+TD+';color:#6b7280;text-align:center\">'+esc(bz)+'</td>'\n"
        "            + '<td style=\"'+TD+';text-align:center\">'+_clxBrBadge(c)+'</td>'\n"
        "            + '<td style=\"'+TD+';text-align:center\">'+esc(inf.ceo||'')+'</td>'",
        1, 'TDBR')
    s = rep(s,
        "            tr += '<tr><td colspan=\"6\" style=\"padding:0;border-bottom:2px solid #1B3A6B;background:#fff\">'+_clxFormHtml(nm, c)+'</td></tr>';",
        "            tr += '<tr><td colspan=\"7\" style=\"padding:0;border-bottom:2px solid #1B3A6B;background:#fff\">'+_clxFormHtml(nm, c)+'</td></tr>';",
        1, 'COLSPAN')

    # 지점 배지 (종사업장번호가 있으면 함께 표시)
    s = rep(s,
        "  function _clxRender(){",
        r"""  // r159: 지점 배지 — 화성만 색을 달리해 눈에 띄게. 종사업장번호가 있으면 함께 보여준다.
  function _clxBrBadge(c){
    var b=_cliBr(c), sb=_cliSb(c);
    var col = (b==='화성') ? '#b45309' : '#5b7ba6';
    var bg  = (b==='화성') ? '#fff8ef' : '#f4f8fe';
    return '<span style="font-size:10.5px;font-weight:700;color:'+col+';border:1px solid '+col+';background:'+bg+';padding:0 5px;white-space:nowrap">'+b+'</span>'
      + (sb ? '<span style="font-size:10.5px;color:#9ca3af;margin-left:4px">'+esc(sb)+'</span>' : '');
  }
  function _clxRender(){""", 1, 'BRBADGE')

    # ── 7. 페이지 진입 시 필터 초기화 ──
    s = rep(s,
        "if (page === 'clients'){ _clxExp=null; _clxQ=''; _clxPage=1;",
        "if (page === 'clients'){ _clxExp=null; _clxQ=''; _clxPage=1; _clxBr='all';",
        1, 'PAGEINIT')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r159(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r158 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r158 2026-08-26 -->', '<!-- test build r159 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
