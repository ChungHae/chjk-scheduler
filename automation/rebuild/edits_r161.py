# -*- coding: utf-8 -*-
# r161: [업체 지점 — 3단계-A: 업체 상세(clientInfo) 키를 "업체명|지점" 으로 이관]
#
#  목표: 같은 업체명을 서울·화성 두 줄로 등록할 수 있으려면, 업체 상세가 업체명만으로
#  묶여 있으면 안 된다(두 지점이 한 상세를 공유해 서로 덮어씀).
#  이번 모듈은 "키를 바꾸는 것" 까지만 한다. 같은 이름 2줄 허용은 다음 모듈(r162).
#
#  전수 조사로 확인한 clientInfo 접근 지점(26곳)을 모두 처리한다.
#
#  핵심 설계
#   - _cliKey(c)      : clientList 행 -> '업체명|지점'
#   - _ciKey(nm, br)  : 이름+지점 -> 키
#   - _cliFind(nm,br) : 이름(+지점)으로 clientList 행 찾기
#   - _clxInfo(nmOrRow, br) : 복합키로 읽되, 옛 이름키도 함께 조회(하위호환).
#     -> 마이그레이션이 아직 안 돈 자료나, 구버전 브라우저가 올린 자료가 들어와도 화면이 비지 않는다.
#   - _ciMigrate(m)   : 옛 이름키 상세를 clientList 의 지점을 참고해 '이름|지점' 으로 옮김.
#     clientInfo 가 메모리에 올라오는 곳은 딱 두 곳(선언 L4606, reloadState L4563)이라
#     그 두 곳만 감싸면 최초 로드·주기 동기화·정식→테스트 복사·백업 복원이 모두 커버된다.
#     이미 복합키인 항목은 건드리지 않고, 충돌하면 원본을 남겨 자료가 사라지지 않게 한다.
#
#  데이터 유실을 막기 위해 특히 신경 쓴 곳
#   (1) clxSave: 지점만 바꿔도 키가 바뀐다. 기존 'nm!==orig' 조건으로는 이동이 안 돼
#       상세가 고아가 된다 -> 복합키끼리 비교하도록 교체.
#   (2) clxMigApply(메모 기준 정리): 지점을 화성으로 바꾸면서 상세를 전혀 옮기지 않았다.
#       -> 이 모듈에서 상세 이동을 추가. (조사에서 찾은 최대 위험 지점)
#   (3) _clxImportXlsx: 엑셀의 지점 열로 지점이 바뀌는데 상세는 이름키로 읽고 썼다.
#       -> 변경 전 키를 잡아 두었다가 바뀌면 옮긴다.
#   (4) 삭제 3곳(deleteClient/qVendorDel/clxDelete)은 이름만 받는다 -> 지점을 찾아 복합키로 삭제.
#       옛 이름키 잔재도 함께 지운다.
#   (5) _fxCeoMap: ci[nm] 으로 상세를 읽어 대표자 색인을 만든다 -> 복합키로 변경.
#       단, 색인의 "값" 은 업체명 그대로 둔다. 값을 복합키로 바꾸면 같은 업체가 두 지점에
#       있을 때 length 가 2가 되어 _fxResolveVendor 의 "단독 일치" 조건이 깨지고
#       멀쩡한 입금이 전부 미배정으로 떨어진다.
#       덤으로 메모 스탬프가 항목 수만 보고 있어 대표자만 고치면 캐시가 안 풀리던 문제도
#       _ciVer(상세 저장 카운터)를 넣어 함께 고친다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R161 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r161(s, path):
    # ── 1. 키 헬퍼 + 마이그레이션 (clientInfo 선언 직전) ──
    s = rep(s,
        "  let clientInfo = _cliDecMap(load('sched_client_info') ?? {});",
        r"""  // ── r161: 업체 상세 키를 '업체명|지점' 으로 ─────────────
  var _ciVer = 0;   // 상세가 저장될 때마다 +1 (대표자 색인 캐시 무효화용)
  function _cliKey(c){ return String((c&&c[0])!=null?c[0]:'') + '|' + _cliBr(c); }
  function _ciKey(nm, br){ return String(nm==null?'':nm) + '|' + _cliBrNorm(br); }
  //  이름(+지점)으로 clientList 행 찾기. 지점을 안 주면 첫 일치 행.
  function _cliFind(nm, br){
    var all=(typeof allClients==='function' && allClients())||[];
    var want=(br==null)?null:_cliBrNorm(br);
    for(var i=0;i<all.length;i++){
      if(String(all[i][0])!==String(nm)) continue;
      if(want===null || _cliBr(all[i])===want) return all[i];
    }
    return null;
  }
  //  옛 이름키 상세를 '이름|지점' 으로 옮긴다. 이미 복합키면 그대로.
  //  (clientList 는 이 시점에 이미 올라와 있다 — 선언 순서상 clientList 가 먼저)
  function _ciMigrate(m){
    if(!m || typeof m!=='object') return {};
    var byName={};
    try{
      var src=(clientList && clientList.length) ? clientList : [];
      for(var i=0;i<src.length;i++){
        var c=src[i]; if(!c || c[0]==null) continue;
        var k=String(c[0]); if(byName[k]===undefined) byName[k]=_cliBr(c);
      }
    }catch(_e){}
    var out={};
    Object.keys(m).forEach(function(k){
      if(/\|(서울|화성)$/.test(k)){ out[k]=m[k]; return; }   // 이미 복합키
      var nk = k + '|' + (byName[k] || '서울');
      if(out[nk]===undefined) out[nk]=m[k];
      else out[k]=m[k];                                      // 충돌 시 원본 유지(유실 방지)
    });
    return out;
  }
  let clientInfo = _ciMigrate(_cliDecMap(load('sched_client_info') ?? {}));""", 1, 'KEYHELPERS')

    # reloadState 쪽도 동일하게
    s = rep(s,
        "    clientInfo       = _cliDecMap(load('sched_client_info') ?? {});",
        "    clientInfo       = _ciMigrate(_cliDecMap(load('sched_client_info') ?? {}));   // r161\n"
        "    _ciVer++;",
        1, 'RELOADMIG')

    # ── 2. _clxInfo 를 지점 인식으로 (옛 이름키 하위호환) ──
    s = rep(s,
        "  function _clxInfo(nm){ return (clientInfo && clientInfo[nm]) || {}; }",
        r"""  // r161: 업체명 또는 clientList 행으로 상세 조회. 복합키 우선, 옛 이름키는 하위호환으로 함께 조회.
  function _clxInfo(nmOrRow, br){
    if(!clientInfo) return {};
    var nm, key;
    if(nmOrRow && typeof nmOrRow==='object' && nmOrRow.length!==undefined){
      nm=String(nmOrRow[0]==null?'':nmOrRow[0]); key=_cliKey(nmOrRow);
    } else {
      nm=String(nmOrRow==null?'':nmOrRow);
      if(br==null){ var row=_cliFind(nm); key = row ? _cliKey(row) : _ciKey(nm,'서울'); }
      else key=_ciKey(nm, br);
    }
    return clientInfo[key] || clientInfo[nm] || {};
  }
  //  이름(+지점)에 해당하는 상세 키. 저장·삭제 때 사용.
  function _clxInfoKey(nm, br){
    if(br!=null) return _ciKey(nm, br);
    var row=_cliFind(nm);
    return row ? _cliKey(row) : _ciKey(nm,'서울');
  }""", 1, 'CLXINFO')

    # ── 3. _clxPersist 에서 버전 올리기 ──
    s = rep(s,
        "  function _clxPersist(){\n    save('sched_client_list', clientList);\n    save('sched_client_info', clientInfo);",
        "  function _clxPersist(){\n    _ciVer++;   // r161: 대표자 색인 캐시 무효화\n    save('sched_client_list', clientList);\n    save('sched_client_info', clientInfo);",
        1, 'PERSISTVER')

    # ── 4. 삭제 3곳: 복합키 + 옛 이름키 함께 정리 ──
    s = rep(s,
        "      ensureClientList();\n"
        "      clientList = clientList.filter(function(x){ return x[0]!==name; });",
        "      ensureClientList();\n"
        "      var _dk=_clxInfoKey(name);   // r161: 목록에서 지우기 전에 지점 확정\n"
        "      clientList = clientList.filter(function(x){ return x[0]!==name; });",
        1, 'DELCLIKEY')
    s = rep(s,
        "      if(clientInfo[name]){ delete clientInfo[name]; save('sched_client_info', clientInfo); }",
        "      // r161: 상세는 '이름|지점' 키. 옛 이름키 잔재도 함께 정리\n"
        "      if(clientInfo[_dk]!==undefined || clientInfo[name]!==undefined){\n"
        "        delete clientInfo[_dk]; delete clientInfo[name]; _ciVer++;\n"
        "        save('sched_client_info', clientInfo);\n"
        "      }",
        1, 'DELCLI')
    s = rep(s,
        "      clientList=clientList.filter(function(c){ return c[0]!==v.name; });",
        "      var _vk=_clxInfoKey(v.name);   // r161: 목록에서 지우기 전에 지점 확정\n"
        "      clientList=clientList.filter(function(c){ return c[0]!==v.name; });",
        1, 'QVDELKEY')
    s = rep(s,
        "      if(clientInfo[v.name]){ delete clientInfo[v.name]; save('sched_client_info', clientInfo); }",
        "      // r161: 상세는 '이름|지점' 키\n"
        "      if(clientInfo[_vk]!==undefined || clientInfo[v.name]!==undefined){\n"
        "        delete clientInfo[_vk]; delete clientInfo[v.name]; _ciVer++;\n"
        "        save('sched_client_info', clientInfo);\n"
        "      }",
        1, 'QVDEL')

    # ── 5. openAddClient 이름 변경 (지점은 기존 행에서 가져옴) ──
    s = rep(s,
        "        if(nm!==editOrig && clientInfo[editOrig]){ clientInfo[nm]=clientInfo[editOrig]; delete clientInfo[editOrig]; save('sched_client_info', clientInfo); }",
        "        // r161: 이 모달에는 지점 칸이 없다 — 지점은 기존 행 값을 그대로 쓴다\n"
        "        var _obr=_cliBr(_cliFind(nm) || _cliFind(editOrig) || []);\n"
        "        var _ok2=_ciKey(editOrig,_obr), _nk2=_ciKey(nm,_obr);\n"
        "        if(_ok2!==_nk2){\n"
        "          var _src2 = (clientInfo[_ok2]!==undefined) ? _ok2 : ((clientInfo[editOrig]!==undefined) ? editOrig : null);\n"
        "          if(_src2!==null){ clientInfo[_nk2]=clientInfo[_src2]; delete clientInfo[_src2]; _ciVer++; save('sched_client_info', clientInfo); }\n"
        "        }",
        1, 'ADDCLIRENAME')

    # ── 6. clxSave: 지점만 바뀌어도 상세를 옮긴다 + 복합키로 저장 ──
    s = rep(s,
        "      if(nm!==orig && clientInfo[orig]){ clientInfo[nm]=clientInfo[orig]; delete clientInfo[orig]; }",
        "      // r161: 지점만 바뀌어도 키가 달라진다 -> 복합키끼리 비교해 이동\n"
        "      var _oldKey=_ciKey(orig, (_prev?_cliBr(_prev):'서울'));\n"
        "      var _newKey=_ciKey(nm, _br);\n"
        "      if(_oldKey!==_newKey){\n"
        "        var _srcK = (clientInfo[_oldKey]!==undefined) ? _oldKey : ((clientInfo[orig]!==undefined) ? orig : null);\n"
        "        if(_srcK!==null){ clientInfo[_newKey]=clientInfo[_srcK]; delete clientInfo[_srcK]; }\n"
        "      } else if(clientInfo[orig]!==undefined && orig!==_newKey){\n"
        "        clientInfo[_newKey]=clientInfo[orig]; delete clientInfo[orig];   // 옛 이름키 잔재 정리\n"
        "      }",
        1, 'CLXRENAME')
    s = rep(s,
        "    clientInfo[nm] = { zip:get('zip'),",
        "    clientInfo[_ciKey(nm,_br)] = { zip:get('zip'),",
        1, 'CLXWRITE')
    # clxDelete
    s = rep(s,
        "      try{ ensureClientList(); }catch(_e){}\n"
        "      clientList = clientList.filter(function(c){ return c[0]!==nm; });\n"
        "      customClients = customClients.filter(function(c){ return c[0]!==nm; });\n"
        "      save('sched_clients_added', customClients);\n"
        "      delete clientInfo[nm];",
        "      try{ ensureClientList(); }catch(_e){}\n"
        "      var _ck3=_clxInfoKey(nm);   // r161: 목록에서 지우기 \"전\" 에 지점을 확정해야 키를 찾을 수 있다\n"
        "      clientList = clientList.filter(function(c){ return c[0]!==nm; });\n"
        "      customClients = customClients.filter(function(c){ return c[0]!==nm; });\n"
        "      save('sched_clients_added', customClients);\n"
        "      delete clientInfo[_ck3]; delete clientInfo[nm];   // 복합키 + 옛 이름키",
        1, 'CLXDEL')

    # ── 7. clxMigApply: 지점을 바꾸면 상세도 함께 옮긴다 (조사에서 찾은 최대 위험 지점) ──
    s = rep(s,
        """        for(var i=0;i<clientList.length;i++){
          if(!set[clientList[i][0]]) continue;
          clientList[i]=_cliMake(clientList[i][0], clientList[i][1], '화성', _cliSb(clientList[i]));
          n++;
        }""",
        r"""        for(var i=0;i<clientList.length;i++){
          if(!set[clientList[i][0]]) continue;
          var _mo=_cliKey(clientList[i]);                                                   // r161: 변경 전 키
          clientList[i]=_cliMake(clientList[i][0], clientList[i][1], '화성', _cliSb(clientList[i]));
          var _mn=_cliKey(clientList[i]);                                                   // 변경 후 키
          if(_mo!==_mn){
            var _ms = (clientInfo[_mo]!==undefined) ? _mo : ((clientInfo[clientList[i][0]]!==undefined) ? clientList[i][0] : null);
            if(_ms!==null){ clientInfo[_mn]=clientInfo[_ms]; delete clientInfo[_ms]; }      // 상세도 함께 이동
          }
          n++;
        }""", 1, 'MIGMOVE')

    # ── 8. 엑셀 가져오기: 지점 변경 시 상세 이동 + 복합키 읽기/쓰기 ──
    s = rep(s,
        """            var isNew=false;
            var brv=val(r,'branch'), sbv=val(r,'subBiz');""",
        """            var isNew=false;
            var brv=val(r,'branch'), sbv=val(r,'subBiz');
            // r161: 지점이 바뀌면 상세 키도 바뀐다 -> 변경 전 키를 잡아 둔다
            var _preRow = target ? _cliFind(target) : null;
            var _preKey = _preRow ? _cliKey(_preRow) : '';""",
        1, 'XLSPREKEY')
    s = rep(s,
        """            bizMap[bd]=target;
            var inf=clientInfo[target]||{};""",
        """            bizMap[bd]=target;
            // r161: 상세는 '이름|지점' 키로 읽고 쓴다. 지점이 바뀌었으면 먼저 옮긴다.
            var _row2=_cliFind(target);
            var _tkey=_row2 ? _cliKey(_row2) : _ciKey(target,'서울');
            if(_preKey && _preKey!==_tkey && clientInfo[_preKey]!==undefined){
              clientInfo[_tkey]=clientInfo[_preKey]; delete clientInfo[_preKey];
            }
            var inf=clientInfo[_tkey] || clientInfo[target] || {};
            if(clientInfo[target]!==undefined && _tkey!==target) delete clientInfo[target];   // 옛 이름키 잔재""",
        1, 'XLSREAD')
    s = rep(s,
        "            clientInfo[target]=inf;\n            if(isNew) createdSet[target]=true; else updatedSet[target]=true;",
        "            clientInfo[_tkey]=inf;\n            if(isNew) createdSet[target]=true; else updatedSet[target]=true;",
        1, 'XLSWRITE')

    # ── 9. 목록·폼·엑셀내보내기·정리도구: clientList 행을 그대로 넘겨 지점까지 반영 ──
    s = rep(s, "          var nm=c[0], bz=c[1]||'', inf=_clxInfo(nm);\n          var exp=_clxExp===nm;",
               "          var nm=c[0], bz=c[1]||'', inf=_clxInfo(c);\n          var exp=_clxExp===nm;", 1, 'RENDERINFO')
    s = rep(s, "        var nm=c[0], bz=c[1]||'', inf=_clxInfo(nm);\n        var _br=_cliBr(c), _sb=_cliSb(c);",
               "        var nm=c[0], bz=c[1]||'', inf=_clxInfo(c);\n        var _br=_cliBr(c), _sb=_cliSb(c);", 1, 'XLSEXPORT')
    s = rep(s, "      return String(_clxInfo(c[0]).memo||'').indexOf('화성')>=0;",
               "      return String(_clxInfo(c).memo||'').indexOf('화성')>=0;", 1, 'MIGCAND')
    s = rep(s, "      var nm=c[0], inf=_clxInfo(nm);\n      return '<tr>'",
               "      var nm=c[0], inf=_clxInfo(c);\n      return '<tr>'", 1, 'MIGPANEL')
    s = rep(s, "    var inf=orig?_clxInfo(orig):{};",
               "    var inf=orig?_clxInfo(pair && pair.length ? pair : orig):{};   // r161: 지점까지 반영", 1, 'FORMINFO')

    # ── 10. 대표자 색인: 복합키로 읽되 값(업체명)은 그대로 + 캐시 스탬프 보강 ──
    s = rep(s,
        "    var stamp=cl.length+':'+Object.keys(ci).length;",
        "    var stamp=cl.length+':'+Object.keys(ci).length+':'+_ciVer;   // r161: 대표자만 고쳐도 캐시가 풀리도록",
        1, 'CEOSTAMP')
    s = rep(s,
        "      var inf=ci[nm]||{};",
        "      // r161: 상세는 '이름|지점' 키. 색인의 값은 업체명 그대로 둔다\n"
        "      //  (복합키를 넣으면 같은 업체가 두 지점에 있을 때 '단독 일치' 조건이 깨져 미배정이 쏟아진다)\n"
        "      var inf=ci[_cliKey(c)] || ci[nm] || {};",
        1, 'CEOKEY')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r161(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r160 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r160 2026-08-26 -->', '<!-- test build r161 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
