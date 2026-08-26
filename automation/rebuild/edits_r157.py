# -*- coding: utf-8 -*-
# r157: [전체 백업/복원에 매입매출(fx) 자료 포함]
#
#  발견: 설정의 "전체 백업" 이 매입매출 모듈 자료를 하나도 담지 않는다.
#    - _fullBackupMain() 에 sched_fx_alias / sched_fx_openings / sched_fx_adjusts /
#      sched_fx_terms / sched_fx_excluded 가 없음 (구 입출금 모듈 키만 들어 있음)
#    - blobs 에 quote/price/qsaved 만 있고 _fx 블롭(계산서·입금) 6개가 없음
#    => 백업 파일로 복원해도 계산서·입금 자료와 미배정 매칭 작업(별칭·결제조건·
#       기초이월·조정·제외)이 전부 사라진다.
#
#  지점 구분 작업(업체 식별자 변경) 전에 반드시 고쳐야 하는 항목이라 먼저 처리.
#
#  수정:
#   1) _fullBackupMain() 에 fx 설정 5종 추가. 복원은 기존 경로 그대로
#      (Object.keys(data.main).forEach(save) -> reloadState() 가 이미 이 5개를 다시 읽는다).
#   2) 백업 시 _fx 블롭 6개(sales/purch/dep x 서울/화성)를 동시 요청해 blobs.fx 에 담는다.
#   3) 복원 시 blobs.fx 를 _fxBlobPut 으로 되돌리고, 메모리에 남은 옛 자료가 덮어쓰지
#      않도록 _fxLoaded=false / 블롭캐시 비움 / 원장캐시 무효화.
#   4) 백업 완료 안내에 포함된 매입매출 건수를 표시해 빠졌는지 눈으로 확인 가능하게.
#
#  version 은 3 그대로 둔다. 새 백업 파일을 구버전(배포본 r121 등)에서 복원해도
#  형식 오류 없이 기존 항목은 복원되도록 하기 위함(비상시 복원 경로를 막지 않는다).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R157 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r157(s, path):
    # 1) 설정 5종 포함
    s = rep(s,
        "      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos\n    };",
        "      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos,\n"
        "      // r157: 매입매출 설정 5종 — 빠져 있어서 복원 시 미배정 매칭 작업이 통째로 사라졌다\n"
        "      sched_fx_alias: fxAlias, sched_fx_openings: fxOpenings, sched_fx_adjusts: fxAdjusts,\n"
        "      sched_fx_terms: fxTerms, sched_fx_excluded: fxExcluded\n    };",
        1, 'MAINKEYS')

    # 2) 백업: fx 블롭 6개 포함
    s = rep(s,
        "      var blobs = { quote:{}, price:{}, qsaved:{} };",
        "      var blobs = { quote:{}, price:{}, qsaved:{}, fx:{} };",
        1, 'BLOBSDECL')
    s = rep(s,
        "      for(var qs of (quoteSaved||[])){ try{ var b4=await _qsBlobGet(qs.id); if(b4!=null) blobs.qsaved[qs.id]=b4; }catch(e){} }\n"
        "      var data = { version:3, full:true, exportedAt:new Date().toISOString(), main:main, blobs:blobs };",
        r"""      for(var qs of (quoteSaved||[])){ try{ var b4=await _qsBlobGet(qs.id); if(b4!=null) blobs.qsaved[qs.id]=b4; }catch(e){} }
      // r157: 매입매출 대용량 블롭(계산서·입금) 6개 — 동시 요청
      var _fxK=['sales_서울','sales_화성','purch_서울','purch_화성','dep_서울','dep_화성'];
      var _fxCnt=0;
      try{
        var _fxG=await Promise.all(_fxK.map(function(k){ try{ return _fxBlobGet(k); }catch(_e){ return null; } }));
        _fxK.forEach(function(k,ix){
          var v=_fxG[ix];
          if(v!=null){ blobs.fx[k]=v; _fxCnt += (v&&v.length)||0; }
        });
      }catch(_e){}
      var data = { version:3, full:true, exportedAt:new Date().toISOString(), main:main, blobs:blobs };""",
        1, 'FXEXPORT')

    # 백업 완료 안내에 건수 표시
    s = rep(s,
        "        showInfoModal('전체 백업 완료', '재고·견적 원장·가격표·SMC·매입처·미수금·거래처·일정 등\\n전체 데이터를 파일로 저장했습니다.\\n\\n※ 자료실 파일 원본과 계정 정보는 제외됩니다.');",
        "        showInfoModal('전체 백업 완료', '재고·견적 원장·가격표·SMC·매입처·미수금·거래처·일정 등\\n전체 데이터를 파일로 저장했습니다.\\n\\n'"
        "\n          + '매입매출(계산서·입금) '+_fxCnt.toLocaleString()+'건 포함 — 별칭·결제조건·기초이월·조정·제외 설정도 함께 저장됩니다.\\n\\n'"
        "\n          + '※ 자료실 파일 원본과 계정 정보는 제외됩니다.');",
        1, 'BACKUPMSG')

    # 3) 복원: fx 블롭 되돌리기
    s = rep(s,
        "            for(var id4 in (bl.qsaved||{})){ await _try(function(){ return _qsBlobPut(id4, bl.qsaved[id4]); }, '저장견적/'+id4); }",
        r"""            for(var id4 in (bl.qsaved||{})){ await _try(function(){ return _qsBlobPut(id4, bl.qsaved[id4]); }, '저장견적/'+id4); }
            // r157: 매입매출 블롭 복원 + 메모리에 남은 옛 자료가 덮어쓰지 않도록 초기화
            for(var id5 in (bl.fx||{})){ await _try(function(){ return _fxBlobPut(id5, bl.fx[id5]); }, '매입매출/'+id5); }
            if(bl.fx && Object.keys(bl.fx).length){
              try{ _fxLoaded=false; _fxLoading=null; _fxBlobCache={}; _fxCacheBump++; }catch(_e){}
            }""",
        1, 'FXRESTORE')

    # 복원 안내 문구에도 매입매출 명시
    s = rep(s,
        "        showConfirmModal('전체 복원', '백업 파일의 데이터로 현재 데이터를 덮어씁니다.\\n(재고·견적·가격표·SMC·매입처·미수금·거래처·일정 전체)\\n\\n계속할까요?', async function(){",
        "        showConfirmModal('전체 복원', '백업 파일의 데이터로 현재 데이터를 덮어씁니다.\\n(재고·견적·가격표·SMC·매입처·미수금·거래처·일정 전체)\\n'"
        "\n          + ((data.blobs && data.blobs.fx && Object.keys(data.blobs.fx).length) ? '매입매출(계산서·입금)과 별칭·결제조건·기초이월·조정·제외도 함께 복원됩니다.\\n' : '이 파일에는 매입매출 자료가 없습니다 — 매입매출은 현재 상태가 유지됩니다.\\n')"
        "\n          + '\\n계속할까요?', async function(){",
        1, 'RESTOREMSG')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r157(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r156 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r156 2026-08-26 -->', '<!-- test build r157 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
