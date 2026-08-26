# -*- coding: utf-8 -*-
# r163: [업체 지점 — 4단계: 홈택스 계산서에서 종사업장번호 읽기 + 업체에 채우기]
#
#  왜 지금 하나: 계산서 재적재를 앞두고 있다. 지금 상태로 홈택스 파일을 올리면
#  파일 안에 이미 들어 있는 종사업장번호를 읽지 않고 버린다. 나중에 넣으려면
#  업체마다 손으로 쳐야 한다. 재적재 전에 넣어 두면 자동으로 채워진다.
#
#  홈택스 목록의 열 위치(현재 파서가 쓰는 '작성일자' 기준 오프셋):
#    매출: 공급받는자 사업자등록번호 off+9  -> 종사업장번호 off+10  (거래처가 공급받는자)
#    매입: 공급자   사업자등록번호 off+4  -> 종사업장번호 off+5   (거래처가 공급자)
#  즉 두 경우 모두 "거래처 사업자번호 칸 바로 다음" 이다 -> iVb+1 하나로 처리.
#
#  하는 일
#   (1) 계산서 자료에 vsb(거래처 종사업장번호)를 함께 저장. _cliSbNorm 으로 4자리 정규화.
#       기존 자료에 vsb 가 없어도 아무 데도 영향 없음(없으면 빈 값으로 읽힘).
#   (2) 미배정 입금에서 계산서에만 있는 거래처를 새로 등록할 때(fxPickNewVend) 종사업장번호도 함께 등록.
#   (3) 업체 페이지에 "계산서에서 종사업장번호 채우기 N" 도구(관리자 전용).
#       계산서에는 종사업장번호가 있는데 업체에는 비어 있는 곳을 찾아, 목록을 보여주고
#       체크한 것만 채운다(r160 과 같은 검토 후 적용 방식). 채우면 후보에서 빠지고,
#       후보가 0곳이면 버튼이 사라진다.
#       ※ '0000' 은 본점을 뜻해 사실상 전 업체에 붙는 값이라 후보에서 제외한다.
#         (계산서 자료에는 그대로 저장되므로 필요하면 업체 화면에서 직접 입력하면 된다)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R163 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r163(s, path):
    # ── 1. 홈택스 파서: 종사업장번호 열 읽기 ──
    s = rep(s,
        "          var iVb = off + (kind==='sales' ? 9 : 4), iVn = off + (kind==='sales' ? 11 : 6);",
        "          var iVb = off + (kind==='sales' ? 9 : 4), iVn = off + (kind==='sales' ? 11 : 6);\n"
        "          // r163: 종사업장번호는 거래처 사업자번호 바로 다음 칸 (매출 off+10 / 매입 off+5)\n"
        "          var iSb = iVb + 1;",
        1, 'HTCOL')
    s = rep(s,
        "            var vbz=_fxCell(row[iVb]), vnm=_fxCell(row[iVn]);",
        "            var vbz=_fxCell(row[iVb]), vnm=_fxCell(row[iVn]);\n"
        "            var vsb=_cliSbNorm(_fxCell(row[iSb]));   // r163",
        1, 'HTREAD')
    s = rep(s,
        "            A.push({ id:'H|'+biz+'|'+no, biz:biz, date:d, vendor:vnm, vbiz:vbz,\n"
        "                     supply:sup, tax:tax, total:tot, no:no, src:'hometax', note:'' });",
        "            A.push({ id:'H|'+biz+'|'+no, biz:biz, date:d, vendor:vnm, vbiz:vbz, vsb:vsb,\n"
        "                     supply:sup, tax:tax, total:tot, no:no, src:'hometax', note:'' });",
        1, 'HTPUSH')

    # ── 2. 계산서 기준 종사업장번호 조회 + 미배정에서 신규 등록 시 함께 반영 ──
    s = rep(s,
        "  function _fxVbizOf(biz, name){",
        r"""  // r163: 계산서에 적힌 그 거래처의 종사업장번호 (사업장 기준, 최근 것 우선)
  function _fxVsbOf(biz, name, vbiz){
    var bd=String(vbiz||'').replace(/\D/g,'');
    var best='', bestDate='';
    function scan(arr){
      for(var i=0;i<arr.length;i++){
        var e=arr[i];
        if(e.biz!==biz || !e.vsb) continue;
        if(bd){ if(String(e.vbiz||'').replace(/\D/g,'')!==bd) continue; }
        else if(e.vendor!==name) continue;
        if((e.date||'') >= bestDate){ bestDate=e.date||''; best=_cliSbNorm(e.vsb); }
      }
    }
    scan(fxSalesInv); scan(fxPurchInv);
    return best;
  }
  function _fxVbizOf(biz, name){""", 1, 'VSBOF')
    s = rep(s,
        "        // r158: 이 입금이 들어온 사업장을 업체의 지점으로 기록\n"
        "        var _d0=_fxUnList[i];\n"
        "        clientList.push(_cliMake(name, vbiz||'', (_d0&&_d0.biz)||'서울'));",
        "        // r158: 이 입금이 들어온 사업장을 업체의 지점으로 기록\n"
        "        var _d0=_fxUnList[i];\n"
        "        var _d0b=(_d0&&_d0.biz)||'서울';\n"
        "        // r163: 계산서에 종사업장번호가 있으면 함께 등록\n"
        "        clientList.push(_cliMake(name, vbiz||'', _d0b, _fxVsbOf(_d0b, name, vbiz)));",
        1, 'PICKNEWSB')

    # ── 3. 업체 페이지: 계산서에서 종사업장번호 채우기 (관리자 전용) ──
    s = rep(s,
        "  function _clxMigPanelHtml(){",
        r"""  // ── r163: 계산서에서 종사업장번호 채우기 ────────────────
  var _clxSbOpen=false;
  function _clxSbOff(){ try{ return localStorage.getItem('sched_clx_sb_fill_off')==='1'; }catch(_e){ return false; } }
  //  후보 = 업체에 종사업장번호가 비어 있고, 그 지점의 계산서에 '0000' 이 아닌 값이 있는 곳
  function _clxSbCands(){
    var out=[];
    (allClients()||[]).forEach(function(c){
      if(_cliSb(c)) return;
      var v=_fxVsbOf(_cliBr(c), c[0], c[1]);
      if(!v || v==='0000') return;
      out.push({ c:c, sb:v });
    });
    return out.sort(function(a,b){ return String(a.c[0]).localeCompare(String(b.c[0]),'ko'); });
  }
  function _clxSbShow(){ return _isAdmin() && !_clxSbOff() && _clxSbCands().length>0; }
  window.clxSbToggle = function(){ _clxSbOpen=!_clxSbOpen; _clxRender(); };
  window.clxSbDismiss = function(){
    showConfirmModal('종사업장번호 채우기 숨기기',
      '남은 후보를 그대로 두고 이 도구를 더 이상 표시하지 않습니다.\n(이 브라우저에서만 적용됩니다)\n\n계속할까요?',
      function(){
        try{ localStorage.setItem('sched_clx_sb_fill_off','1'); }catch(_e){}
        _clxSbOpen=false; _clxRender();
      }, '숨기기', '#5b7ba6');
  };
  window.clxSbApply = function(){
    if(!_guardW()) return;
    if(!_isAdmin()) return;
    var box=document.getElementById('clxSbPanel'); if(!box) return;
    var picks={};
    [].forEach.call(box.querySelectorAll('input[type="checkbox"][data-key]'), function(x){
      if(x.checked) picks[x.getAttribute('data-key')]=x.getAttribute('data-sb');
    });
    var keys=Object.keys(picks);
    if(!keys.length){ showInfoModal('종사업장번호','선택된 업체가 없습니다.'); return; }
    showConfirmModal('종사업장번호 채우기',
      '선택한 '+keys.length+'곳의 종사업장번호를 계산서 값으로 채웁니다.\n(업체명·사업자번호·지점은 바뀌지 않습니다)\n\n계속할까요?',
      function(){
        var n=0;
        for(var i=0;i<clientList.length;i++){
          var k=_cliKey(clientList[i]);
          if(picks[k]===undefined) continue;
          clientList[i]=_cliMake(clientList[i][0], clientList[i][1], _cliBr(clientList[i]), picks[k]);
          n++;
        }
        _clxPersist();
        _clxSbOpen=false;
        _clxRender();
        var left=_clxSbCands().length;
        showInfoModal('종사업장번호 채우기',
          n+'곳의 종사업장번호를 채웠습니다.'
          + (left ? ('\n\n남은 후보가 '+left+'곳 있습니다.') : '\n\n남은 후보가 없어 이 도구는 사라집니다.'));
      }, '채우기', '#1B3A6B');
  };
  function _clxSbPanelHtml(){
    var cands=_clxSbCands();
    if(!cands.length) return '';
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;vertical-align:middle';
    var rows=cands.map(function(x){
      var c=x.c;
      return '<tr>'
        + '<td style="'+TD+';text-align:center"><input type="checkbox" data-key="'+esc(_cliKey(c))+'" data-sb="'+esc(x.sb)+'" checked style="width:15px;height:15px;cursor:pointer"></td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(c[0])+'</td>'
        + '<td style="'+TD+';text-align:center">'+_clxBrBadge(c)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280;white-space:nowrap">'+esc(c[1]||'')+'</td>'
        + '<td style="'+TD+';text-align:center;font-weight:700;color:#1B3A6B">'+esc(x.sb)+'</td>'
        + '</tr>';
    }).join('');
    return '<div id="clxSbPanel" style="background:#fff;border:1px solid #cdd8e6;border-left:3px solid #1B3A6B;margin-bottom:8px">'
      + '<div style="padding:11px 16px;background:#f4f8fe;display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
      +   '<span style="font-size:13.5px;font-weight:700;color:#14305c">계산서에서 종사업장번호 채우기 — 후보 '+cands.length+'곳</span>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" class="btn" onclick="clxSbApply()" style="font-size:12px;padding:4px 14px;border:1px solid #1B3A6B;background:#1B3A6B;color:#fff">선택한 업체에 채우기</button>'
      +   '<button type="button" class="btn" onclick="clxSbToggle()" style="font-size:12px;padding:4px 14px;border:1px solid #c8d2de;background:#fff;color:#444">닫기</button>'
      + '</div>'
      + '<div style="padding:8px 16px;font-size:11.5px;color:#8a94a6;line-height:1.7;border-bottom:1px solid #dbe6f3">'
      +   '홈택스 계산서에 적힌 그 거래처의 종사업장번호를 업체 정보에 옮깁니다. 같은 사업장(지점)의 계산서 중 <b>가장 최근 값</b>을 씁니다.<br>'
      +   '<b>0000(본점)</b>은 사실상 모든 업체에 붙는 값이라 후보에서 제외했습니다 — 필요하면 업체를 열어 직접 입력하세요.'
      + '</div>'
      + '<div style="max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse;table-layout:fixed">'
      + '<colgroup><col style="width:46px"><col><col style="width:80px"><col style="width:130px"><col style="width:110px"></colgroup>'
      + '<thead><tr><th style="'+TH+'">적용</th><th style="'+TH+';text-align:left">업체명</th><th style="'+TH+'">지점</th><th style="'+TH+'">사업자번호</th><th style="'+TH+'">계산서 종사업장</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>'
      + '<div style="padding:8px 16px;border-top:1px solid #dbe6f3;text-align:right">'
      +   '<button type="button" class="btn" onclick="clxSbDismiss()" style="font-size:11px;padding:2px 10px;border:1px solid #d6deea;background:#fff;color:#9ca3af;font-weight:400">이 도구 더 이상 보지 않기</button>'
      + '</div></div>';
  }
  function _clxMigPanelHtml(){""", 1, 'SBTOOL')

    # 툴바 버튼 + 패널 배치
    s = rep(s,
        '      <span id="clxMigWrap"></span>',
        '      <span id="clxMigWrap"></span>\n      <span id="clxSbWrap"></span>',
        1, 'SBSLOT')
    s = rep(s,
        "    if(_mw) _mw.innerHTML = _clxMigShow()",
        "    var _sw=document.getElementById('clxSbWrap');\n"
        "    if(_sw) _sw.innerHTML = _clxSbShow()\n"
        "      ? ('<button type=\"button\" class=\"btn\" onclick=\"clxSbToggle()\" style=\"font-size:11.5px;padding:3px 11px;margin-left:6px;border:1px solid #1B3A6B;background:'+(_clxSbOpen?'#1B3A6B':'#fff')+';color:'+(_clxSbOpen?'#fff':'#1B3A6B')+'\">종사업장번호 채우기 '+_clxSbCands().length+'</button>')\n"
        "      : '';\n"
        "    if(_mw) _mw.innerHTML = _clxMigShow()",
        1, 'SBBTN')
    s = rep(s,
        "    if(_clxMigOpen && _clxMigShow()) html += _clxMigPanelHtml();   // r160",
        "    if(_clxMigOpen && _clxMigShow()) html += _clxMigPanelHtml();   // r160\n"
        "    if(_clxSbOpen && _clxSbShow()) html += _clxSbPanelHtml();     // r163",
        1, 'SBMOUNT')
    s = rep(s,
        "_clxBr='all'; _clxMigOpen=false;",
        "_clxBr='all'; _clxMigOpen=false; _clxSbOpen=false;",
        1, 'SBPAGEINIT')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r163(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r162 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r162 2026-08-26 -->', '<!-- test build r163 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
