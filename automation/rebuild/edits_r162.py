# -*- coding: utf-8 -*-
# r162: [업체 지점 — 3단계-B: 같은 업체명을 서울·화성 두 줄로 등록 허용]
#
#  r161 에서 업체 상세를 '업체명|지점' 으로 옮겼으니, 이제 실제로 같은 이름 2줄을 열어준다.
#
#  바꾸는 것
#   (1) 식별자를 화면까지 관철: _clxExp(펼친 업체)와 폼의 data-orig 가 업체명 대신
#       복합키('이름|지점')를 담는다. 안 그러면 같은 이름 두 줄이 동시에 펼쳐지고,
#       저장·삭제가 엉뚱한 줄을 건드린다.
#   (2) 중복 검사 완화:
#       - 업체명 중복 -> 같은 "지점 안에서만" 막는다.
#       - 사업자번호 중복 -> 같은 "지점 안에서만" 막는다(_findClientByBiz 에 지점 인자 추가).
#         다른 지점이면 같은 번호로 등록 가능 — 이게 이번 작업의 목적.
#   (3) 행 찾기: clxSave 의 수정 대상 행을 이름이 아니라 복합키로 찾는다.
#   (4) ensureClientList 의 중복 제거를 이름 -> 이름+지점 기준으로.
#   (5) 지점 칸이 없는 옛 경로 보호:
#       - openAddClient(자동완성 연필/견적 거래처 수정) 는 지점 칸이 없다 -> 서울 기준으로만
#         중복을 보고, 수정 시에는 기존 행의 지점을 그대로 쓴다.
#       - deleteClient(자동완성 삭제) 와 qVendorDel(견적 거래처 삭제) 은 이름만 받는다 ->
#         같은 이름이 2곳 이상이면 어느 쪽인지 확정할 수 없으므로 업체 목록을 건드리지 않고
#         안내한다(잘못된 줄을 지우는 사고 방지).
#
#  건드리지 않는 것(의도적)
#   - 매입매출 쪽 _findClientByBiz(vbiz, null) 3곳은 지점 없이 그대로 둔다.
#     여기에 지점을 넘기면 "서울 계좌 입금인데 업체는 화성에만 등록" 같은 경우에
#     기존처럼 그 업체로 안내하지 않고 서울 줄을 새로 만들어 버려서, 지금 흐름이 크게 바뀐다.
#     매입매출 연결은 별도로 다룬다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R162 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r162(s, path):
    # ── 1. 키 분해 헬퍼 (_cliFind 옆) ──
    s = rep(s,
        "  //  옛 이름키 상세를 '이름|지점' 으로 옮긴다. 이미 복합키면 그대로.",
        r"""  //  r162: 복합키를 이름/지점으로 분해. 옛 형식(이름만)도 받아준다(지점 null).
  function _ciSplit(key){
    var s2=String(key==null?'':key);
    var m=s2.match(/^([\s\S]*)\|(서울|화성)$/);
    return m ? { name:m[1], br:m[2] } : { name:s2, br:null };
  }
  //  옛 이름키 상세를 '이름|지점' 으로 옮긴다. 이미 복합키면 그대로.""", 1, 'CISPLIT')

    # ── 2. _findClientByBiz 에 지점 인자 ──
    s = rep(s,
        """  function _findClientByBiz(biz, exceptName){
    var bd=(biz||'').replace(/[^0-9]/g,'');
    if(!bd) return null;
    var all=allClients();
    for(var i=0;i<all.length;i++){ if(all[i][1] && all[i][1].replace(/[^0-9]/g,'')===bd && all[i][0]!==exceptName) return all[i][0]; }
    return null;
  }""",
        r"""  //  r162: branch 를 주면 그 지점 안에서만 중복을 본다(다른 지점이면 같은 번호 허용).
  //   except 는 업체명 또는 복합키 둘 다 받는다(하위호환).
  function _findClientByBiz(biz, except, branch){
    var bd=(biz||'').replace(/[^0-9]/g,'');
    if(!bd) return null;
    var want=(branch==null)?null:_cliBrNorm(branch);
    var all=allClients();
    for(var i=0;i<all.length;i++){
      var c=all[i];
      if(!c[1] || c[1].replace(/[^0-9]/g,'')!==bd) continue;
      if(want!==null && _cliBr(c)!==want) continue;
      if(except && (c[0]===except || _cliKey(c)===except)) continue;
      return c[0];
    }
    return null;
  }""", 1, 'FINDBYBIZ')

    # ── 3. ensureClientList 중복 제거를 이름+지점으로 ──
    s = rep(s,
        "      CLIENT_DATA.concat(customClients).forEach(function(x){ if(!seen[x[0]]){ seen[x[0]]=1; arr.push(_cliMake(x[0], x[1]||'', x[2], x[3])); } });",
        "      // r162: 같은 이름이라도 지점이 다르면 별개 업체\n"
        "      CLIENT_DATA.concat(customClients).forEach(function(x){\n"
        "        var k=String(x[0])+'|'+_cliBrNorm(x[2]);\n"
        "        if(!seen[k]){ seen[k]=1; arr.push(_cliMake(x[0], x[1]||'', x[2], x[3])); }\n"
        "      });",
        1, 'ENSURE')

    # ── 4. openAddClient (지점 칸 없음 → 서울 기준) ──
    s = rep(s,
        "      var dupName=_findClientByBiz(bz, isEdit?editOrig:null);\n"
        "      if(bz && dupName){ showInfoModal('알림', '사업자번호 '+bz+' 은(는) 이미 \"'+dupName+'\" 으로 등록되어 있습니다.'); return; }",
        "      // r162: 이 모달에는 지점 칸이 없다 — 수정은 기존 행의 지점, 신규는 서울 기준으로 중복을 본다\n"
        "      var _mRow = isEdit ? _cliFind(editOrig) : null;\n"
        "      var _mBr = _mRow ? _cliBr(_mRow) : '서울';\n"
        "      var dupName=_findClientByBiz(bz, isEdit?(_mRow?_cliKey(_mRow):editOrig):null, _mBr);\n"
        "      if(bz && dupName){ showInfoModal('알림', _mBr+'지점에 사업자번호 '+bz+' 이(가) 이미 \"'+dupName+'\" 으로 등록되어 있습니다.'); return; }",
        1, 'ADDCLIBIZ')
    s = rep(s,
        "        var existsName=allClients().some(function(it){ return it[0]===nm; });",
        "        var existsName=allClients().some(function(it){ return _cliKey(it)===_ciKey(nm,'서울'); });   // r162: 서울지점 기준",
        1, 'ADDCLINAME')
    s = rep(s,
        "        for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===editOrig){ clientList[i]=_cliKeep(clientList[i], nm, bz); found=true; break; } }",
        "        var _eKey = _mRow ? _cliKey(_mRow) : _ciKey(editOrig,'서울');   // r162: 이름이 겹쳐도 그 줄만\n"
        "        for(var i=0;i<clientList.length;i++){ if(_cliKey(clientList[i])===_eKey){ clientList[i]=_cliKeep(clientList[i], nm, bz); found=true; break; } }",
        1, 'ADDCLIROW')

    # ── 5. deleteClient: 같은 이름이 여러 지점이면 삭제하지 않는다 ──
    s = rep(s,
        "  function deleteClient(name, input){\n    if(typeof showConfirmModal!=='function'){ return; }",
        "  function deleteClient(name, input){\n"
        "    if(typeof showConfirmModal!=='function'){ return; }\n"
        "    // r162: 같은 이름이 지점별로 여러 곳이면 어느 줄인지 확정할 수 없다 -> 여기서는 지우지 않는다\n"
        "    var _dRows=(allClients()||[]).filter(function(c){ return c[0]===name; });\n"
        "    if(_dRows.length>1){\n"
        "      showInfoModal('거래처 삭제', '\"'+esc(name)+'\" 은(는) 지점별로 '+_dRows.length+'곳 등록되어 있습니다.\\n"
        "어느 지점을 지울지 확정할 수 없어 여기서는 삭제하지 않습니다.\\n\\n일정 > 업체 화면에서 해당 지점의 업체를 열어 삭제해 주세요.');\n"
        "      return;\n"
        "    }",
        1, 'DELGUARD')

    # ── 6. qVendorDel: 중복이면 업체 목록은 건드리지 않는다 ──
    s = rep(s,
        "      var _vk=_clxInfoKey(v.name);   // r161: 목록에서 지우기 전에 지점 확정\n"
        "      clientList=clientList.filter(function(c){ return c[0]!==v.name; });\n"
        "      customClients=customClients.filter(function(c){ return c[0]!==v.name; });",
        "      // r162: 같은 이름이 지점별로 여러 곳이면 어느 줄인지 확정할 수 없다 -> 업체 목록은 그대로 둔다\n"
        "      var _vRows=(allClients()||[]).filter(function(c){ return c[0]===v.name; });\n"
        "      var _vk=_clxInfoKey(v.name);   // r161: 목록에서 지우기 전에 지점 확정\n"
        "      var _vMulti=_vRows.length>1;\n"
        "      if(!_vMulti){\n"
        "        clientList=clientList.filter(function(c){ return c[0]!==v.name; });\n"
        "        customClients=customClients.filter(function(c){ return c[0]!==v.name; });\n"
        "      }",
        1, 'QVGUARD')
    s = rep(s,
        "      // r161: 상세는 '이름|지점' 키\n"
        "      if(clientInfo[_vk]!==undefined || clientInfo[v.name]!==undefined){",
        "      // r161: 상세는 '이름|지점' 키\n"
        "      if(!_vMulti && (clientInfo[_vk]!==undefined || clientInfo[v.name]!==undefined)){",
        1, 'QVINFO')
    s = rep(s,
        "      saveAll(); if(typeof doFbSave==='function') doFbSave(); renderEstimatePage();",
        "      saveAll(); if(typeof doFbSave==='function') doFbSave(); renderEstimatePage();\n"
        "      if(_vMulti) showInfoModal('거래처 삭제', '견적 원장은 삭제했습니다.\\n다만 \"'+esc(v.name)+'\" 은(는) 지점별로 '+_vRows.length+'곳 등록되어 있어\\n업체 목록에서는 지우지 않았습니다. 필요하면 일정 > 업체에서 해당 지점을 지워 주세요.');",
        1, 'QVMSG')

    # ── 7. 목록·펼침: 복합키로 ──
    s = rep(s, "  var _clxExp = null;   // 펼친 업체명 ('' = 신규 등록 폼, null = 모두 접힘)",
               "  var _clxExp = null;   // r162: 펼친 업체의 복합키 '이름|지점' ('' = 신규 등록 폼, null = 모두 접힘)", 1, 'EXPCOMMENT')
    s = rep(s, "  window.clxToggle = function(nm){\n    _clxExp = (_clxExp===nm) ? null : nm;",
               "  window.clxToggle = function(key){\n    _clxExp = (_clxExp===key) ? null : key;", 1, 'TOGGLE')
    s = rep(s, "      if(_clxExp!==null && _clxExp!=='' && c[0]===_clxExp) return true;\n      return _cliBr(c)===_clxBr;",
               "      if(_clxExp!==null && _clxExp!=='' && _cliKey(c)===_clxExp) return true;\n      return _cliBr(c)===_clxBr;", 1, 'EXPFILT1')
    s = rep(s, "      if(_clxExp!==null && _clxExp!=='' && c[0]===_clxExp) return true;   // 펼친 업체는 항상 표시",
               "      if(_clxExp!==null && _clxExp!=='' && _cliKey(c)===_clxExp) return true;   // 펼친 업체는 항상 표시", 1, 'EXPFILT2')
    s = rep(s, "    if(_clxExp && _clxExp!=='' && !list.some(function(c){ return c[0]===_clxExp; })){\n"
               "      var _exRow=all.filter(function(c){ return c[0]===_clxExp; });",
               "    if(_clxExp && _clxExp!=='' && !list.some(function(c){ return _cliKey(c)===_clxExp; })){\n"
               "      var _exRow=all.filter(function(c){ return _cliKey(c)===_clxExp; });", 1, 'EXPPAGE')
    s = rep(s,
        "          var nm=c[0], bz=c[1]||'', inf=_clxInfo(c);\n"
        "          var exp=_clxExp===nm;",
        "          var nm=c[0], bz=c[1]||'', inf=_clxInfo(c);\n"
        "          var _key=_cliKey(c);            // r162: 같은 이름이라도 지점이 다르면 다른 줄\n"
        "          var exp=_clxExp===_key;",
        1, 'ROWKEY')
    s = rep(s,
        "          var tr='<tr data-nm=\"'+esc(nm)+'\" onclick=\"clxToggle(this.dataset.nm)\"",
        "          var tr='<tr data-nm=\"'+esc(nm)+'\" data-key=\"'+esc(_key)+'\" onclick=\"clxToggle(this.dataset.key)\"",
        1, 'ROWCLICK')
    s = rep(s,
        "            tr += '<tr><td colspan=\"7\" style=\"padding:0;border-bottom:2px solid #1B3A6B;background:#fff\">'+_clxFormHtml(nm, c)+'</td></tr>';",
        "            tr += '<tr><td colspan=\"7\" style=\"padding:0;border-bottom:2px solid #1B3A6B;background:#fff\">'+_clxFormHtml(_key, c)+'</td></tr>';",
        1, 'ROWFORM')

    # ── 8. 폼: orig 가 복합키 ──
    s = rep(s,
        "  function _clxFormHtml(orig, pair){\n    var bz=(pair&&pair[1])||'';\n    var inf=orig?_clxInfo(pair && pair.length ? pair : orig):{};   // r161: 지점까지 반영",
        "  function _clxFormHtml(orig, pair){\n    var bz=(pair&&pair[1])||'';\n"
        "    var _onm=orig?_ciSplit(orig).name:'';   // r162: orig 는 복합키 — 화면에는 업체명만\n"
        "    var inf=orig?_clxInfo(pair && pair.length ? pair : _onm):{};",
        1, 'FORMORIG')
    s = rep(s,
        "      +   _clxFld('name','업체명 *',orig,1)",
        "      +   _clxFld('name','업체명 *',_onm,1)",
        1, 'FORMNAME')

    # ── 9. clxSave 머리 재구성: 복합키 기준 중복 검사 + 행 찾기 ──
    s = rep(s,
        """    if((!orig || nm!==orig) && allClients().some(function(c){ return c[0]===nm; })){ showInfoModal('업체 관리','이미 등록된 업체명입니다: '+esc(nm)); return; }
    var bz=_clxFmtBiz(get('bizNo'));
    var dupName=_findClientByBiz(bz, orig||null);
    if(bz && dupName && dupName!==nm){ showInfoModal('업체 관리','사업자번호 '+esc(bz)+' 은(는) 이미 \"'+esc(dupName)+'\" 으로 등록되어 있습니다.'); return; }""",
        r"""    var bz=_clxFmtBiz(get('bizNo'));
    // r162: 식별자는 업체명+지점. 지점 값이 필요하므로 중복 검사보다 먼저 확정한다.
    try{ ensureClientList(); }catch(_e0){}
    var _hasFld=function(k){ return !!box.querySelector('.clx-f[data-k="'+k+'"]'); };
    var _op=_ciSplit(orig||'');
    var _prev = orig ? _cliFind(_op.name, _op.br) : null;
    var _br = _hasFld('branch') ? _cliBrNorm(get('branch')) : (_prev ? _cliBr(_prev) : '서울');
    var _sb = _hasFld('subBiz') ? _cliSbNorm(get('subBiz')) : (_prev ? _cliSb(_prev) : '');
    var _oldKey = orig ? (_prev ? _cliKey(_prev) : _ciKey(_op.name, _op.br||'서울')) : '';
    var _newKey = _ciKey(nm, _br);
    if(_oldKey!==_newKey && allClients().some(function(c){ return _cliKey(c)===_newKey; })){
      showInfoModal('업체 관리', _br+'지점에 이미 등록된 업체명입니다: '+esc(nm)+'\n(다른 지점이라면 지점을 바꿔 주세요)'); return;
    }
    // 사업자번호 중복은 같은 지점 안에서만 막는다 — 다른 지점이면 같은 번호로 등록 가능
    var dupName=_findClientByBiz(bz, _oldKey||null, _br);
    if(bz && dupName){ showInfoModal('업체 관리', _br+'지점에 사업자번호 '+esc(bz)+' 이(가) 이미 "'+esc(dupName)+'" 으로 등록되어 있습니다.'); return; }""",
        1, 'SAVEHEAD')
    # 기존 _prev/_br/_sb 선언 블록 제거 (위로 옮겼으므로)
    s = rep(s,
        """    try{ ensureClientList(); }catch(_e){}
    // r159: 폼의 지점·종사업장번호. 칸이 없는 화면이면 기존 값을 그대로 유지(지점 유실 방지)
    var _hasFld=function(k){ return !!box.querySelector('.clx-f[data-k="'+k+'"]'); };
    var _prev = orig ? (clientList.filter(function(c){ return c[0]===orig; })[0] || null) : null;
    var _br = _hasFld('branch') ? _cliBrNorm(get('branch')) : (_prev ? _cliBr(_prev) : '서울');
    var _sb = _hasFld('subBiz') ? _cliSbNorm(get('subBiz')) : (_prev ? _cliSb(_prev) : '');
    if(!orig){""",
        """    if(!orig){""", 1, 'SAVEHEADDEDUP')
    # 수정 대상 행을 복합키로 찾기
    s = rep(s,
        "      for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===orig){ clientList[i]=_cliMake(nm,bz,_br,_sb); found=true; break; } }\n"
        "      if(!found) clientList.push(_cliMake(nm,bz,_br,_sb));\n"
        "      for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===orig){ customClients[j]=_cliMake(nm,bz,_br,_sb); } }",
        "      // r162: 이름이 겹쳐도 그 지점의 줄만 바꾼다\n"
        "      for(var i=0;i<clientList.length;i++){ if(_cliKey(clientList[i])===_oldKey){ clientList[i]=_cliMake(nm,bz,_br,_sb); found=true; break; } }\n"
        "      if(!found) clientList.push(_cliMake(nm,bz,_br,_sb));\n"
        "      for(var j=0;j<customClients.length;j++){ if(_cliKey(customClients[j])===_oldKey){ customClients[j]=_cliMake(nm,bz,_br,_sb); } }",
        1, 'SAVEROW')
    # 상세 이동은 이미 계산한 _oldKey/_newKey 사용
    s = rep(s,
        "      // r161: 지점만 바뀌어도 키가 달라진다 -> 복합키끼리 비교해 이동\n"
        "      var _oldKey=_ciKey(orig, (_prev?_cliBr(_prev):'서울'));\n"
        "      var _newKey=_ciKey(nm, _br);\n"
        "      if(_oldKey!==_newKey){\n"
        "        var _srcK = (clientInfo[_oldKey]!==undefined) ? _oldKey : ((clientInfo[orig]!==undefined) ? orig : null);\n"
        "        if(_srcK!==null){ clientInfo[_newKey]=clientInfo[_srcK]; delete clientInfo[_srcK]; }\n"
        "      } else if(clientInfo[orig]!==undefined && orig!==_newKey){\n"
        "        clientInfo[_newKey]=clientInfo[orig]; delete clientInfo[orig];   // 옛 이름키 잔재 정리\n"
        "      }",
        "      // r161/r162: 이름이든 지점이든 바뀌면 상세도 함께 옮긴다 (키는 위에서 확정)\n"
        "      if(_oldKey!==_newKey){\n"
        "        var _srcK = (clientInfo[_oldKey]!==undefined) ? _oldKey\n"
        "                  : ((clientInfo[_op.name]!==undefined) ? _op.name : null);\n"
        "        if(_srcK!==null){ clientInfo[_newKey]=clientInfo[_srcK]; delete clientInfo[_srcK]; }\n"
        "      } else if(clientInfo[_op.name]!==undefined && _op.name!==_newKey){\n"
        "        clientInfo[_newKey]=clientInfo[_op.name]; delete clientInfo[_op.name];   // 옛 이름키 잔재 정리\n"
        "      }",
        1, 'SAVEMOVE')
    s = rep(s, "    _clxExp=nm;\n    _clxRender();", "    _clxExp=_newKey;   // r162\n    _clxRender();", 1, 'SAVEEXP')

    # ── 10. clxDelete: 복합키로 그 줄만 ──
    s = rep(s,
        """  window.clxDelete = function(nm){
    if(!nm) return;
    showConfirmModal('업체 삭제', esc(nm)+' 업체를 목록에서 삭제할까요?\\n상세정보도 함께 삭제되며, 일정·견적의 거래처 목록에서도 빠집니다.', function(){
      try{ ensureClientList(); }catch(_e){}
      var _ck3=_clxInfoKey(nm);   // r161: 목록에서 지우기 "전" 에 지점을 확정해야 키를 찾을 수 있다
      clientList = clientList.filter(function(c){ return c[0]!==nm; });
      customClients = customClients.filter(function(c){ return c[0]!==nm; });""",
        r"""  window.clxDelete = function(key){
    if(!key) return;
    // r162: key 는 복합키('이름|지점'). 같은 이름이 있어도 그 지점의 줄만 지운다.
    var _dp=_ciSplit(key);
    var _dRow=_cliFind(_dp.name, _dp.br);
    var _ck3=_dRow ? _cliKey(_dRow) : _ciKey(_dp.name, _dp.br||'서울');
    var nm=_dp.name;
    showConfirmModal('업체 삭제', esc(nm)+' ('+_ciSplit(_ck3).br+'지점) 업체를 목록에서 삭제할까요?\n상세정보도 함께 삭제되며, 일정·견적의 거래처 목록에서도 빠집니다.', function(){
      try{ ensureClientList(); }catch(_e){}
      clientList = clientList.filter(function(c){ return _cliKey(c)!==_ck3; });
      customClients = customClients.filter(function(c){ return _cliKey(c)!==_ck3; });""",
        1, 'CLXDELKEY')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r162(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r161 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r161 2026-08-26 -->', '<!-- test build r162 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
