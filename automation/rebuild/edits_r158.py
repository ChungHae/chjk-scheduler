# -*- coding: utf-8 -*-
# r158: [업체 지점(서울/화성)·종사업장번호 — 1단계: 자료 구조 기반]
#
#  목표(사용자 승인 ③안): 업체 식별자를 "업체명"에서 "업체명+지점"으로 바꿔
#  같은 사업자번호를 서울·화성 두 줄로 등록할 수 있게 한다. 향후 ERP 확장 대비.
#
#  이 모듈(1단계)은 화면 동작을 바꾸지 않는다. 자료 구조만 넓히고,
#  "업체 항목을 건드리는 모든 코드"가 새 칸을 지우지 않도록 막는 게 전부다.
#  (등록 규칙 완화·목록 표시·일괄 분류는 r159 이후)
#
#  구조: clientList 항목을 [업체명, 사업자번호] -> [업체명, 사업자번호, 지점, 종사업장번호] 로 확장.
#    - c[2] 지점: '서울' | '화성'. 값이 없으면 '서울' 로 읽는다(기존 자료 전부 서울 취급).
#    - c[3] 종사업장번호: 숫자 4자리 문자열('0001'). 엑셀이 앞의 0을 지우는 문제 때문에
#      1~4자리 숫자는 0을 채워 4자리로 정규화한다.
#    - c[2]/c[3] 슬롯은 기존 코드에서 전혀 쓰이지 않는 것을 확인했다(c[2]·c[3] 사용처 0건).
#      모든 코드가 c[0](이름)·c[1](번호)만 읽으므로 항목이 길어져도 영향이 없다.
#
#  손봐야 할 지점 — clientList 를 바꾸는 코드는 아래 12곳이 전부다(전수 확인):
#    4618  ensureClientList     : CLIENT_DATA 로 초기 구성
#    4713  openAddClient(수정)  : 항목 통째 교체 -> 지점·종사업장 소실됨
#    4714  openAddClient(수정/없으면 추가)
#    4721  openAddClient(신규)
#    4811  matchExistingBizIfNeeded : 개인일정 업체명에서 자동 생성
#    4812  matchExistingBizIfNeeded : 주간일정 프로젝트명에서 자동 생성
#    9895  qxDoUpload           : 원장 엑셀 업로드 시 자동 등록
#    14719 clxSave(신규)
#    14722 clxSave(수정)        : 항목 통째 교체 -> 소실됨
#    14723 clxSave(수정/없으면 추가)
#    14877 _clxImportXlsx(신규)
#    14881 _clxImportXlsx(기존)  : 항목 통째 교체 -> 소실됨
#    16971 fxPickNewVend        : 미배정 입금에서 신규 업체 등록 -> 그 입금의 사업장을 지점으로
#    17073 fxPickCrossVend      : 사업장 이동 배정 -> 이동 대상 사업장을 지점으로
#
#  엑셀도 함께 처리한다. 내보내기에 지점·종사업장번호 열을 넣지 않으면
#  "내려받아 고쳐서 올리기" 한 번에 지점이 통째로 날아간다.
#    - 내보내기: 사업자번호 뒤에 2열 삽입(스타일/열너비 인덱스도 전부 재계산)
#    - 가져오기: 헤더 이름으로 읽으므로 열 순서와 무관. 값이 비어 있으면 기존 값 유지.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R158 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r158(s, path):
    # ── 1. 접근자 (allClients 바로 뒤) ──
    s = rep(s,
        """  function ensureClientList(){
    if(!clientList || !clientList.length){
      var seen={}, arr=[];
      CLIENT_DATA.concat(customClients).forEach(function(x){ if(!seen[x[0]]){ seen[x[0]]=1; arr.push([x[0], x[1]||'']); } });
      clientList=arr;
    }
  }""",
        r"""  // ── r158: 업체 지점(서울/화성) · 종사업장번호 ──────────────
  //  clientList 항목 = [업체명, 사업자번호, 지점, 종사업장번호]
  //  지점이 없는 기존 자료는 전부 '서울' 로 읽는다(값을 쓰지는 않는다).
  var CLI_BR = ['서울','화성'];
  function _cliBr(c){ return (c && String(c[2]||'').indexOf('화성')>=0) ? '화성' : '서울'; }
  function _cliBrNorm(v){ return (String(v==null?'':v).indexOf('화성')>=0) ? '화성' : '서울'; }
  //  종사업장번호: 숫자만 남기고 1~4자리는 0을 채워 4자리로 (엑셀이 앞의 0을 지우는 문제 대응)
  function _cliSbNorm(v){
    var d=String(v==null?'':v).replace(/\D/g,'');
    if(!d) return '';
    return d.length<=4 ? d.padStart(4,'0') : d;
  }
  function _cliSb(c){ return c ? _cliSbNorm(c[3]) : ''; }
  //  새 항목 만들기 — 지점·종사업장을 생략하면 서울/공란
  function _cliMake(name, biz, br, sb){
    return [String(name==null?'':name), String(biz==null?'':biz), _cliBrNorm(br), _cliSbNorm(sb)];
  }
  //  기존 항목의 지점·종사업장을 지키면서 이름/번호만 교체 (항목 통째 교체 지점에서 사용)
  function _cliKeep(old, name, biz){
    return _cliMake(name, biz, (old?_cliBr(old):'서울'), (old?_cliSb(old):''));
  }
  function ensureClientList(){
    if(!clientList || !clientList.length){
      var seen={}, arr=[];
      CLIENT_DATA.concat(customClients).forEach(function(x){ if(!seen[x[0]]){ seen[x[0]]=1; arr.push(_cliMake(x[0], x[1]||'', x[2], x[3])); } });
      clientList=arr;
    }
  }""", 1, 'ACCESSORS')

    # ── 2. openAddClient ──
    s = rep(s,
        """        for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===editOrig){ clientList[i]=[nm,bz]; found=true; break; } }
        if(!found) clientList.push([nm,bz]);
        for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===editOrig){ customClients[j]=[nm,bz]; } }""",
        """        for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===editOrig){ clientList[i]=_cliKeep(clientList[i], nm, bz); found=true; break; } }
        if(!found) clientList.push(_cliMake(nm,bz));
        for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===editOrig){ customClients[j]=_cliKeep(customClients[j], nm, bz); } }""",
        1, 'ADDCLI_EDIT')
    s = rep(s,
        """        if(existsName){ showInfoModal('알림', '이미 등록된 업체명입니다.'); return; }
        clientList.push([nm,bz]);""",
        """        if(existsName){ showInfoModal('알림', '이미 등록된 업체명입니다.'); return; }
        clientList.push(_cliMake(nm,bz));""",
        1, 'ADDCLI_NEW')

    # ── 3. 일정/프로젝트 이름에서 자동 생성 ──
    s = rep(s,
        "      (personalSchedules||[]).forEach(function(s){ var b=(s.bizName||'').trim(); if(b && !_exist[b]){ _exist[b]=1; clientList.push([b,'']); _newCount++; changed++; } });",
        "      (personalSchedules||[]).forEach(function(s){ var b=(s.bizName||'').trim(); if(b && !_exist[b]){ _exist[b]=1; clientList.push(_cliMake(b,'')); _newCount++; changed++; } });",
        1, 'AUTOGEN1')
    s = rep(s,
        "var pn=(''+p.name).trim(); if(pn && !_exist[pn]){ _exist[pn]=1; clientList.push([pn,'']); _newCount++; changed++; } }); } });",
        "var pn=(''+p.name).trim(); if(pn && !_exist[pn]){ _exist[pn]=1; clientList.push(_cliMake(pn,'')); _newCount++; changed++; } }); } });",
        1, 'AUTOGEN2')

    # ── 4. 원장 엑셀 업로드 자동 등록 ──
    s = rep(s,
        "      if(!allClients().some(function(c){ return c[0]===nm; })){ clientList.push([nm,'']); customClients.push([nm,'']); }",
        "      if(!allClients().some(function(c){ return c[0]===nm; })){ clientList.push(_cliMake(nm,'')); customClients.push(_cliMake(nm,'')); }",
        1, 'QXUPLOAD')

    # ── 5. clxSave ──
    s = rep(s,
        """    if(!orig){
      clientList.push([nm,bz]);
    } else {
      var found=false;
      for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===orig){ clientList[i]=[nm,bz]; found=true; break; } }
      if(!found) clientList.push([nm,bz]);
      for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===orig){ customClients[j]=[nm,bz]; } }""",
        """    if(!orig){
      clientList.push(_cliMake(nm,bz));
    } else {
      var found=false;
      for(var i=0;i<clientList.length;i++){ if(clientList[i][0]===orig){ clientList[i]=_cliKeep(clientList[i], nm, bz); found=true; break; } }
      if(!found) clientList.push(_cliMake(nm,bz));
      for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===orig){ customClients[j]=_cliKeep(customClients[j], nm, bz); } }""",
        1, 'CLXSAVE')

    # ── 6. 업체 엑셀 가져오기 ──
    s = rep(s,
        """            if(!target){
              if(!exName){ skipNoName++; continue; }
              target=exName; isNew=true;
              clientList.push([target,bz]);
              nameSet[target]=true;
            } else {
              for(var li=0;li<clientList.length;li++){ if(clientList[li][0]===target && !String(clientList[li][1]||'').replace(/\\D/g,'')){ clientList[li]=[target,bz]; break; } }
            }""",
        r"""            var brv=val(r,'branch'), sbv=val(r,'subBiz');
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
                var _hadBz=!!String(_cur[1]||'').replace(/\D/g,'');
                clientList[li]=_cliMake(target, (_hadBz?_cur[1]:bz), (brv||_cliBr(_cur)), (sbv||_cliSb(_cur)));
                break;
              }
            }""", 1, 'XLSIMPORT')

    # 헤더 인식표에 지점·종사업장번호 추가
    s = rep(s,
        "    '사업자번호':'bizNo','사업자등록번호':'bizNo',",
        "    '사업자번호':'bizNo','사업자등록번호':'bizNo',\n"
        "    '지점':'branch','사업장':'branch','담당지점':'branch','관리지점':'branch',\n"
        "    '종사업장번호':'subBiz','종사업장':'subBiz','종사업장코드':'subBiz',",
        1, 'HMAP')

    # ── 7. 업체 엑셀 내보내기 (사업자번호 뒤에 2열 삽입 + 인덱스 재계산) ──
    s = rep(s,
        "      var aoa=[['업체명','사업자번호','대표자','우편번호','주소','상세주소','업태','종목','대표전화','FAX','세금계산서 메일주소','거래은행','계좌번호','예금주','메모','부서','직급','담당자명','연락처1','연락처2','이메일']];",
        "      // r158: 지점·종사업장번호 2열 추가 (없으면 내려받아 다시 올릴 때 지점이 날아간다)\n"
        "      var aoa=[['업체명','사업자번호','지점','종사업장번호','대표자','우편번호','주소','상세주소','업태','종목','대표전화','FAX','세금계산서 메일주소','거래은행','계좌번호','예금주','메모','부서','직급','담당자명','연락처1','연락처2','이메일']];",
        1, 'XLSHEAD')
    s = rep(s,
        """        var nm=c[0], bz=c[1]||'', inf=_clxInfo(nm);
        var cts=(inf.contacts&&inf.contacts.length)?inf.contacts:[{}];
        cts.forEach(function(ct,i){
          if(i===0){
            aoa.push([nm,bz,inf.ceo||'',inf.zip||'',inf.addr||'',inf.addr2||'',inf.uptae||'',inf.jongmok||'',inf.tel||'',inf.fax||'',inf.taxEmail||'',inf.bank||'',inf.account||'',inf.holder||'',inf.memo||'',ct.dept||'',ct.rank||'',ct.name||'',ct.phone||'',ct.phone2||'',ct.email||'']);
          }else{
            aoa.push([nm,bz,'','','','','','','','','','','','','',ct.dept||'',ct.rank||'',ct.name||'',ct.phone||'',ct.phone2||'',ct.email||'']);
          }
        });""",
        """        var nm=c[0], bz=c[1]||'', inf=_clxInfo(nm);
        var _br=_cliBr(c), _sb=_cliSb(c);
        var cts=(inf.contacts&&inf.contacts.length)?inf.contacts:[{}];
        cts.forEach(function(ct,i){
          if(i===0){
            aoa.push([nm,bz,_br,_sb,inf.ceo||'',inf.zip||'',inf.addr||'',inf.addr2||'',inf.uptae||'',inf.jongmok||'',inf.tel||'',inf.fax||'',inf.taxEmail||'',inf.bank||'',inf.account||'',inf.holder||'',inf.memo||'',ct.dept||'',ct.rank||'',ct.name||'',ct.phone||'',ct.phone2||'',ct.email||'']);
          }else{
            aoa.push([nm,bz,'','','','','','','','','','','','','','','',ct.dept||'',ct.rank||'',ct.name||'',ct.phone||'',ct.phone2||'',ct.email||'']);
          }
        });""", 1, 'XLSROWS')
    s = rep(s,
        "      ws['!cols']=[{wch:22},{wch:14},{wch:9},{wch:8},{wch:32},{wch:14},{wch:10},{wch:12},{wch:14},{wch:14},{wch:24},{wch:10},{wch:16},{wch:9},{wch:24},{wch:9},{wch:9},{wch:10},{wch:14},{wch:14},{wch:24}];",
        "      ws['!cols']=[{wch:22},{wch:14},{wch:7},{wch:12},{wch:9},{wch:8},{wch:32},{wch:14},{wch:10},{wch:12},{wch:14},{wch:14},{wch:24},{wch:10},{wch:16},{wch:9},{wch:24},{wch:9},{wch:9},{wch:10},{wch:14},{wch:14},{wch:24}];",
        1, 'XLSCOLS')
    s = rep(s,
        "      var R=aoa.length, NC=21;\n"
        "      for(var r=0;r<R;r++){ for(var c=0;c<NC;c++){\n"
        "        var ref=XLSX.utils.encode_cell({r:r,c:c}); var cl=ws[ref]; if(!cl) continue;\n"
        "        var leftCol=(c===0||c===4||c===5||c===10||c===14||c===20);",
        "      // r158: 2열 늘어나 스타일 인덱스 재계산 (좌측정렬: 업체명0·주소6·상세주소7·계산서메일12·메모16·이메일22)\n"
        "      var R=aoa.length, NC=23;\n"
        "      for(var r=0;r<R;r++){ for(var c=0;c<NC;c++){\n"
        "        var ref=XLSX.utils.encode_cell({r:r,c:c}); var cl=ws[ref]; if(!cl) continue;\n"
        "        var leftCol=(c===0||c===6||c===7||c===12||c===16||c===22);",
        1, 'XLSSTYLE')

    # ── 7-2. 빈 양식 다운로드에도 같은 2열 (없으면 양식으로 올릴 때 지점을 못 넣는다) ──
    s = rep(s,
        "      var ws=XLSX.utils.aoa_to_sheet([['업체명','사업자번호','대표자','우편번호','주소','상세주소','업태','종목','대표전화','FAX','세금계산서 메일주소','거래은행','계좌번호','예금주','메모','부서','직급','담당자명','연락처1','연락처2','이메일']]);",
        "      var ws=XLSX.utils.aoa_to_sheet([['업체명','사업자번호','지점','종사업장번호','대표자','우편번호','주소','상세주소','업태','종목','대표전화','FAX','세금계산서 메일주소','거래은행','계좌번호','예금주','메모','부서','직급','담당자명','연락처1','연락처2','이메일']]);",
        1, 'TPLHEAD')
    s = rep(s,
        "      ws['!cols']=[{wch:20},{wch:14},{wch:9},{wch:9},{wch:30},{wch:14},{wch:10},{wch:12},{wch:14},{wch:14},{wch:22},{wch:10},{wch:16},{wch:9},{wch:16},{wch:9},{wch:9},{wch:10},{wch:14},{wch:14},{wch:22}];",
        "      ws['!cols']=[{wch:20},{wch:14},{wch:7},{wch:12},{wch:9},{wch:9},{wch:30},{wch:14},{wch:10},{wch:12},{wch:14},{wch:14},{wch:22},{wch:10},{wch:16},{wch:9},{wch:16},{wch:9},{wch:9},{wch:10},{wch:14},{wch:14},{wch:22}];",
        1, 'TPLCOLS')

    # ── 8. 미배정 입금에서 업체를 새로 등록할 때: 그 입금의 사업장을 지점으로 ──
    s = rep(s,
        """        try{ ensureClientList(); }catch(_e){}
        clientList.push([name, vbiz||'']);
        _saveClients();
        fxPickVend(i, name);""",
        """        try{ ensureClientList(); }catch(_e){}
        // r158: 이 입금이 들어온 사업장을 업체의 지점으로 기록
        var _d0=_fxUnList[i];
        clientList.push(_cliMake(name, vbiz||'', (_d0&&_d0.biz)||'서울'));
        _saveClients();
        fxPickVend(i, name);""", 1, 'FXNEWVEND')
    s = rep(s,
        """        if(!dup && !nameReg){
          try{ ensureClientList(); }catch(_e){}
          clientList.push([name, vbiz||'']);
          _saveClients();
        }""",
        """        if(!dup && !nameReg){
          try{ ensureClientList(); }catch(_e){}
          clientList.push(_cliMake(name, vbiz||'', other));   // r158: 이동 대상 사업장을 지점으로
          _saveClients();
        }""", 1, 'FXCROSSVEND')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r158(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r157 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r157 2026-08-26 -->', '<!-- test build r158 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
