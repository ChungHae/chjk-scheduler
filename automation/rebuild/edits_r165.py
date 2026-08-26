# -*- coding: utf-8 -*-
# r165: [배포 전 전수 점검에서 발견 — 업체 엑셀 가져오기가 같은 이름 2줄을 구분하지 못함]
#
#  증상(재현됨): 한국전기가 서울(0000)·화성(0007) 두 줄로 등록된 상태에서
#  업체 엑셀을 내려받아 그대로 다시 올리면 두 줄이 모두 "화성/0007" 이 된다.
#  즉 서울 줄이 화성 줄 값으로 덮어써지고 자료가 사라진다.
#
#  원인: r162 에서 같은 이름 2줄 등록을 열었는데, 엑셀 가져오기의 대상 행 찾기는
#  그대로 "이름" 기준이었다.
#    var target = bizMap[bd] || (nameSet[exName] ? exName : '');   // 이름 하나로 좁혀짐
#    for(...){ if(clientList[li][0]!==target) continue; ... break; }  // 항상 첫 줄에 걸림
#  엑셀 2행(서울 줄 / 화성 줄)이 모두 같은 첫 줄을 대상으로 잡아 뒤 행이 앞 행을 덮었다.
#
#  수정: 대상 행을 (사업자번호|이름) + 지점 으로 찾는다.
#   - 엑셀에 지점 값이 있으면 그 지점의 줄만 찾는다. 없으면 신규로 만든다.
#   - 지점 칸이 비어 있으면(구버전 엑셀·담당자 연속행) 후보가 딱 하나일 때만 그 줄을 쓴다.
#     후보가 여러 줄이면 어느 줄인지 확정할 수 없으므로 건너뛰고 그 수를 알린다(덮어쓰기 사고 방지).
#   - 담당자 연속행(이름·번호만 있고 나머지는 빈 칸)은 바로 앞 행에서 확정한 줄을 이어 쓴다.
#     (내보내기가 연속행의 지점 칸을 비워 두기 때문 — 이게 없으면 담당자 2명 이상인
#      같은 이름 2줄 업체의 연속행이 전부 "모호" 로 걸린다)
#   - 갱신은 찾은 줄의 복합키로 직접 수행한다(이름 기준 루프 제거).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R165 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r165(s, path):
    s = rep(s,
        """            var target=bizMap[bd] || (exName && nameSet[exName] ? exName : '');
            var isNew=false;
            var brv=val(r,'branch'), sbv=val(r,'subBiz');
            // r161: 지점이 바뀌면 상세 키도 바뀐다 -> 변경 전 키를 잡아 둔다
            var _preRow = target ? _cliFind(target) : null;
            var _preKey = _preRow ? _cliKey(_preRow) : '';
            if(!target){
              if(!exName){ skipNoName++; continue; }
              target=exName; isNew=true;
              clientList.push(_cliMake(target, bz, brv, sbv));
              nameSet[target]=true;
            } else {
              // r158: 지점·종사업장은 값이 있을 때만 덮어쓴다(빈 칸 = 그대로 두기).
              //  사업자번호는 기존대로 "비어 있을 때만" 채운다.
              for(var li=0;li<clientList.length;li++){
                if(clientList[li][0]!==target) continue;
                var _cur=clientList[li];
                var _hadBz=!!String(_cur[1]||'').replace(/\\D/g,'');
                clientList[li]=_cliMake(target, (_hadBz?_cur[1]:bz), (brv||_cliBr(_cur)), (sbv||_cliSb(_cur)));
                break;
              }
            }
            bizMap[bd]=target;
            // r161: 상세는 '이름|지점' 키로 읽고 쓴다. 지점이 바뀌었으면 먼저 옮긴다.
            var _row2=_cliFind(target);
            var _tkey=_row2 ? _cliKey(_row2) : _ciKey(target,'서울');
            if(_preKey && _preKey!==_tkey && clientInfo[_preKey]!==undefined){
              clientInfo[_tkey]=clientInfo[_preKey]; delete clientInfo[_preKey];
            }
            var inf=clientInfo[_tkey] || clientInfo[target] || {};
            if(clientInfo[target]!==undefined && _tkey!==target) delete clientInfo[target];   // 옛 이름키 잔재""",
        r"""            var brv=val(r,'branch'), sbv=val(r,'subBiz');
            var _wantBr = brv ? _cliBrNorm(brv) : null;
            var isNew=false;
            // ── r165: 대상 행을 (사업자번호|이름) + 지점 으로 찾는다 ──
            //   같은 이름이 서울·화성 두 줄일 수 있으므로 이름만으로 찾으면 엉뚱한 줄을 덮어쓴다.
            var _byBiz=[], _byName=[];
            (allClients()||[]).forEach(function(c){
              if(bd && String(c[1]||'').replace(/\D/g,'')===bd) _byBiz.push(c);
              else if(exName && c[0]===exName) _byName.push(c);
            });
            var _pool=_byBiz.length ? _byBiz : _byName;
            var _row=null, _ambig=false;
            if(_wantBr){
              _row = _pool.filter(function(c){ return _cliBr(c)===_wantBr; })[0] || null;   // 없으면 신규
            } else if(_pool.length===1){
              _row = _pool[0];
            } else if(_pool.length>1){
              // 지점 칸이 비어 있고 후보가 여러 줄 — 담당자 연속행이면 앞 행에서 확정한 줄을 이어 쓴다
              if(_lastKey && exName===_lastNm && bd===_lastBd){
                _row = _pool.filter(function(c){ return _cliKey(c)===_lastKey; })[0] || null;
              }
              if(!_row){ _ambig=true; }
            }
            if(_ambig){ skipAmbig++; continue; }
            var _preKey = _row ? _cliKey(_row) : '';
            var target;
            if(!_row){
              if(!exName){ skipNoName++; continue; }
              target=exName; isNew=true;
              var _newRow=_cliMake(target, bz, brv, sbv);
              clientList.push(_newRow);
              nameSet[target]=true;
              _row=_newRow;
            } else {
              // 지점·종사업장은 값이 있을 때만 덮어쓴다(빈 칸 = 그대로 두기).
              // 사업자번호는 기존대로 "비어 있을 때만" 채운다.
              target=_row[0];
              for(var li=0;li<clientList.length;li++){
                if(_cliKey(clientList[li])!==_preKey) continue;
                var _cur=clientList[li];
                var _hadBz=!!String(_cur[1]||'').replace(/\D/g,'');
                clientList[li]=_cliMake(_cur[0], (_hadBz?_cur[1]:bz), (brv||_cliBr(_cur)), (sbv||_cliSb(_cur)));
                _row=clientList[li];
                break;
              }
            }
            bizMap[bd]=target;
            // r161: 상세는 '이름|지점' 키로 읽고 쓴다. 지점이 바뀌었으면 먼저 옮긴다.
            var _tkey=_cliKey(_row);
            _lastNm=exName; _lastBd=bd; _lastKey=_tkey;   // r165: 담당자 연속행이 이어받을 기준
            if(_preKey && _preKey!==_tkey && clientInfo[_preKey]!==undefined){
              clientInfo[_tkey]=clientInfo[_preKey]; delete clientInfo[_preKey];
            }
            var inf=clientInfo[_tkey] || clientInfo[target] || {};
            if(clientInfo[target]!==undefined && _tkey!==target) delete clientInfo[target];   // 옛 이름키 잔재""",
        1, 'XLSTARGET')

    # 상태 변수 + 모호 건수
    s = rep(s,
        "          var createdSet={}, updatedSet={}, skipNoBiz=0, skipNoName=0;",
        "          var createdSet={}, updatedSet={}, skipNoBiz=0, skipNoName=0, skipAmbig=0;\n"
        "          var _lastNm='', _lastBd='', _lastKey='';   // r165: 담당자 연속행 연결용",
        1, 'XLSVARS')

    # 결과 안내에 모호 건수 표시
    s = rep(s,
        "          if(!nc && !nu && !skipNoBiz && !skipNoName){ showInfoModal('업로드 결과','가져올 데이터가 없습니다. 헤더와 내용을 확인해주세요.'); return; }",
        "          if(!nc && !nu && !skipNoBiz && !skipNoName && !skipAmbig){ showInfoModal('업로드 결과','가져올 데이터가 없습니다. 헤더와 내용을 확인해주세요.'); return; }",
        1, 'XLSMSG0')
    s = rep(s,
        "          if(skipNoName) msg+='\\n건너뜀(신규인데 업체명 없음): '+skipNoName+'행';",
        "          if(skipNoName) msg+='\\n건너뜀(신규인데 업체명 없음): '+skipNoName+'행';\n"
        "          // r165: 지점 칸이 비어 있는데 같은 이름·번호가 여러 지점에 있어 어느 줄인지 확정 못한 행\n"
        "          if(skipAmbig) msg+='\\n건너뜀(지점 확정 불가): '+skipAmbig+'행\\n  같은 업체가 서울·화성 양쪽에 있습니다. 엑셀의 \\'지점\\' 열을 채워서 다시 올려주세요.';",
        1, 'XLSMSGAMBIG')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r165(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r164 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r164 2026-08-26 -->', '<!-- test build r165 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
