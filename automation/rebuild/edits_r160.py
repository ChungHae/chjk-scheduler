# -*- coding: utf-8 -*-
# r160: [메모에 "화성" 이 적힌 업체를 화성지점으로 — 일회성 정리 도구]
#
#  배경(사용자 설명): 화성지점이 본페이지에 자기 거래처를 이미 등록해 버렸고,
#  구분하려고 메모에 "화성" 이라고 적어 두었다. r159 부터는 등록할 때 지점을 고를 수 있으니
#  이 메모 규칙은 이번 한 번만 지점으로 옮기고 그 뒤에는 기능 자체가 사라져야 한다.
#
#  설계 — "다 쓰면 스스로 사라진다":
#   후보 = 메모에 '화성' 이 있으면서 아직 지점이 '서울' 인 업체.
#   지정하고 나면 그 업체는 지점이 '화성' 이 되어 후보에서 빠진다.
#   -> 후보가 0곳이 되면 버튼과 패널이 화면에서 사라진다. 별도 플래그가 없어도
#      자연스럽게 일회성이 된다(플래그를 안 쓰므로 PC/브라우저마다 어긋날 일도 없음).
#   메모에 화성이 있지만 실제로는 서울인 업체가 남아 후보가 계속 뜨는 경우를 위해
#   패널 안에 "이 정리 도구 더 이상 보지 않기" 를 둔다(이 브라우저에만 적용).
#
#  안전장치:
#   - 관리자만 보이고, 조회 전용 계정은 실행 불가(_guardW).
#   - 자동으로 바꾸지 않는다. 후보를 메모 원문과 함께 보여주고 체크한 것만 바꾼다.
#     (메모의 '화성' 이 지점 뜻이 아닌 경우 — 주소·납품 메모 등 — 를 사람이 걸러내도록)
#   - 확인창에 몇 곳을 바꾸는지 명시. 되돌리려면 업체별로 지점을 다시 고르면 된다.
#   - 메모는 건드리지 않는다(기록으로 남김).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R160 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r160(s, path):
    # ── 1. 후보 계산 + 패널 (clxSetBr 옆에 배치) ──
    s = rep(s,
        "  window.clxSetBr = function(b){ _clxBr=b; _clxExp=null; _clxPage=1; _clxRender(); };",
        r"""  window.clxSetBr = function(b){ _clxBr=b; _clxExp=null; _clxPage=1; _clxRender(); };
  // ── r160: 메모 기준 지점 정리 (일회성) ──────────────────
  var _clxMigOpen=false;
  function _clxMigOff(){ try{ return localStorage.getItem('sched_clx_br_mig_off')==='1'; }catch(_e){ return false; } }
  //  후보 = 메모에 '화성' 이 있고 아직 지점이 서울인 업체. 지정하면 후보에서 빠진다.
  function _clxMigCands(){
    return allClients().filter(function(c){
      if(_cliBr(c)!=='서울') return false;
      return String(_clxInfo(c[0]).memo||'').indexOf('화성')>=0;
    }).sort(function(a,b){ return String(a[0]).localeCompare(String(b[0]),'ko'); });
  }
  function _clxMigShow(){ return _isAdmin() && !_clxMigOff() && _clxMigCands().length>0; }
  window.clxMigToggle = function(){ _clxMigOpen=!_clxMigOpen; _clxRender(); };
  window.clxMigDismiss = function(){
    showConfirmModal('정리 도구 숨기기',
      '남은 후보를 그대로 두고 이 정리 도구를 더 이상 표시하지 않습니다.\n(이 브라우저에서만 적용됩니다)\n\n계속할까요?',
      function(){
        try{ localStorage.setItem('sched_clx_br_mig_off','1'); }catch(_e){}
        _clxMigOpen=false; _clxRender();
      }, '숨기기', '#5b7ba6');
  };
  window.clxMigApply = function(){
    if(!_guardW()) return;
    if(!_isAdmin()) return;
    var box=document.getElementById('clxMigPanel'); if(!box) return;
    var names=[].filter.call(box.querySelectorAll('input[type="checkbox"][data-nm]'), function(x){ return x.checked; })
                .map(function(x){ return x.getAttribute('data-nm'); });
    if(!names.length){ showInfoModal('지점 지정','선택된 업체가 없습니다.'); return; }
    showConfirmModal('메모 기준 지점 지정',
      '선택한 '+names.length+'곳을 화성지점으로 지정합니다.\n'
      + '(메모는 그대로 둡니다. 잘못되면 업체별로 지점을 다시 고르면 됩니다)\n\n계속할까요?',
      function(){
        var set={}; names.forEach(function(n){ set[n]=1; });
        var n=0;
        for(var i=0;i<clientList.length;i++){
          if(!set[clientList[i][0]]) continue;
          clientList[i]=_cliMake(clientList[i][0], clientList[i][1], '화성', _cliSb(clientList[i]));
          n++;
        }
        for(var j=0;j<customClients.length;j++){
          if(!set[customClients[j][0]]) continue;
          customClients[j]=_cliMake(customClients[j][0], customClients[j][1], '화성', _cliSb(customClients[j]));
        }
        save('sched_clients_added', customClients);
        _clxPersist();
        _clxMigOpen=false;
        _clxRender();
        var left=_clxMigCands().length;
        showInfoModal('지점 지정 완료',
          n+'곳을 화성지점으로 지정했습니다.'
          + (left ? ('\n\n메모에 "화성" 이 남아 있는 업체가 '+left+'곳 더 있습니다. 지점 뜻이 아니라면 그대로 두세요.')
                  : '\n\n남은 후보가 없어 이 정리 도구는 사라집니다.'));
      }, '지정', '#b45309');
  };
  function _clxMemoHi(memo){
    var full=String(memo||'');
    var m=full;
    if(m.length>120){
      var idx=m.indexOf('화성');
      var st=Math.max(0, idx-40);
      m=(st>0?'…':'')+m.slice(st, st+120)+((st+120)<full.length?'…':'');
    }
    return esc(m).replace(/화성/g,'<b style="color:#b45309;background:#fff3e0;padding:0 2px">화성</b>');
  }
  function _clxMigPanelHtml(){
    var cands=_clxMigCands();
    if(!cands.length) return '';
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;vertical-align:middle';
    var rows=cands.map(function(c){
      var nm=c[0], inf=_clxInfo(nm);
      return '<tr>'
        + '<td style="'+TD+';text-align:center"><input type="checkbox" data-nm="'+esc(nm)+'" checked style="width:15px;height:15px;cursor:pointer"></td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(nm)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280;white-space:nowrap">'+esc(c[1]||'')+'</td>'
        + '<td style="'+TD+';color:#6b7280;line-height:1.6;white-space:normal">'+_clxMemoHi(inf.memo)+'</td>'
        + '</tr>';
    }).join('');
    return '<div id="clxMigPanel" style="background:#fff;border:1px solid #f0d9b8;border-left:3px solid #b45309;margin-bottom:8px">'
      + '<div style="padding:11px 16px;background:#fff8ef;display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
      +   '<span style="font-size:13.5px;font-weight:700;color:#b45309">메모 기준 지점 정리 — 후보 '+cands.length+'곳</span>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" class="btn" onclick="clxMigApply()" style="font-size:12px;padding:4px 14px;border:1px solid #b45309;background:#b45309;color:#fff">선택한 업체를 화성으로 지정</button>'
      +   '<button type="button" class="btn" onclick="clxMigToggle()" style="font-size:12px;padding:4px 14px;border:1px solid #c8d2de;background:#fff;color:#444">닫기</button>'
      + '</div>'
      + '<div style="padding:8px 16px;font-size:11.5px;color:#8a94a6;line-height:1.7;border-bottom:1px solid #f0d9b8">'
      +   '화성지점이 등록한 거래처를 구분하려고 메모에 적어둔 "화성" 을 지점 값으로 옮기는 <b>일회성 정리</b>입니다. '
      +   '지정한 업체는 후보에서 빠지고, 후보가 모두 없어지면 이 도구는 화면에서 사라집니다.<br>'
      +   '메모의 "화성" 이 지점 뜻이 아닌 경우(주소·납품 메모 등)는 <b>체크를 풀어 두세요.</b> 메모 자체는 지우지 않습니다.'
      + '</div>'
      + '<div style="max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse;table-layout:fixed">'
      + '<colgroup><col style="width:46px"><col style="width:220px"><col style="width:130px"><col></colgroup>'
      + '<thead><tr><th style="'+TH+'">지정</th><th style="'+TH+';text-align:left">업체명</th><th style="'+TH+'">사업자번호</th><th style="'+TH+';text-align:left">메모</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>'
      + '<div style="padding:8px 16px;border-top:1px solid #f0d9b8;text-align:right">'
      +   '<button type="button" class="btn" onclick="clxMigDismiss()" style="font-size:11px;padding:2px 10px;border:1px solid #d6deea;background:#fff;color:#9ca3af;font-weight:400">이 정리 도구 더 이상 보지 않기</button>'
      + '</div></div>';
  }""", 1, 'MIGCORE')

    # ── 2. 툴바 버튼 자리 ──
    s = rep(s,
        '      <div id="clxBrBtns" style="display:flex;gap:4px"></div>',
        '      <div id="clxBrBtns" style="display:flex;gap:4px"></div>\n'
        '      <span id="clxMigWrap"></span>',
        1, 'TOOLBARSLOT')

    # ── 3. 렌더: 버튼 + 패널 ──
    s = rep(s,
        "    var _brb=document.getElementById('clxBrBtns'); if(_brb) _brb.innerHTML=_clxBrBtnsHtml();",
        "    var _brb=document.getElementById('clxBrBtns'); if(_brb) _brb.innerHTML=_clxBrBtnsHtml();\n"
        "    // r160: 메모 기준 지점 정리 버튼 (후보가 없으면 사라진다)\n"
        "    var _mw=document.getElementById('clxMigWrap');\n"
        "    if(_mw) _mw.innerHTML = _clxMigShow()\n"
        "      ? ('<button type=\"button\" class=\"btn\" onclick=\"clxMigToggle()\" style=\"font-size:11.5px;padding:3px 11px;margin-left:6px;border:1px solid #b45309;background:'+(_clxMigOpen?'#b45309':'#fff')+';color:'+(_clxMigOpen?'#fff':'#b45309')+'\">메모 기준 지점 정리 '+_clxMigCands().length+'</button>')\n"
        "      : '';",
        1, 'MIGBTN')
    s = rep(s,
        """    var html='';
    if(_clxExp===''){""",
        """    var html='';
    if(_clxMigOpen && _clxMigShow()) html += _clxMigPanelHtml();   // r160
    if(_clxExp===''){""",
        1, 'MIGMOUNT')

    # ── 4. 페이지 진입 시 패널 접힘 ──
    s = rep(s,
        "if (page === 'clients'){ _clxExp=null; _clxQ=''; _clxPage=1; _clxBr='all';",
        "if (page === 'clients'){ _clxExp=null; _clxQ=''; _clxPage=1; _clxBr='all'; _clxMigOpen=false;",
        1, 'PAGEINIT')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r160(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r159 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r159 2026-08-26 -->', '<!-- test build r160 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
