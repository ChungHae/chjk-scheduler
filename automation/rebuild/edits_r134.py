# -*- coding: utf-8 -*-
# r134: [규칙 동기화 버그 수정 + 별칭 전체 삭제]
#  버그: 매입매출 규칙 5종(sched_fx_alias/openings/adjusts/terms/excluded)이
#  Firebase 로는 저장되지만(doFbSave), 연결·폴링 시 Firebase → 로컬 반영 목록(KEYS)에
#  빠져 있어 페이지가 항상 자기 로컬 복사본만 읽음.
#  → 정식→테스트 복사로 서버를 비워도 별칭표가 그대로(80건) 남는 원인.
#  → 다른 기기와 규칙이 동기화되지 않는 잠재 버그이기도 함.
#  1) fbConnect·폴링 KEYS 에 규칙 5종 추가
#  2) 정식→테스트 복사 적용부: 규칙 5종은 정식에 없으면 빈 값으로 로컬 리셋
#  3) 별칭표 관리에 "전체 삭제" 버튼 (관리자, 확인창 경유)

import io

FXKEYS = "'sched_fx_alias','sched_fx_openings','sched_fx_adjusts','sched_fx_terms','sched_fx_excluded'"

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R134 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r134(s, path):
    BASE = "['sched_members','sched_entries','sched_team_goal','sched_team_tasks','sched_config','sched_assignments','sched_assign_comments','sched_bank_txns','sched_tax_invoices','sched_ar_items','sched_purchase_vendors','sched_links','sched_inventory_add','sched_inventory_qty','sched_inventory_log','sched_inventory_hidden','sched_inv_reset','sched_personal','sched_comments','sched_categories','sched_files','sched_quote_index','sched_quote_saved','sched_price_makers','sched_price_note','sched_issues','sched_leave2026','sched_clients_added','sched_client_list','sched_projects','sched_client_info','sched_proj_memos']"
    # (1) 연결·폴링 KEYS (const ×2) — 규칙 5종 추가
    s = rep(s, "const KEYS = " + BASE + ";",
            "const KEYS = " + BASE[:-1] + "," + FXKEYS + "];", 2, 'KEYS')
    # (2) 정식→테스트 복사 적용부: 규칙 5종은 없으면 빈 값으로 리셋
    # 정식→테스트 복사 기능은 test 파일에만 존재
    if 'testpage' in path:
        s = rep(s, "          var KEYS = " + BASE + ";\n          KEYS.forEach(function(k){ if(prod[k]!==undefined) save(k, prod[k]); });",
                "          var KEYS = " + BASE + ";\n          KEYS.forEach(function(k){ if(prod[k]!==undefined) save(k, prod[k]); });\n"
                "          // r134: 매입매출 규칙은 정식에 없으면 빈 값으로 리셋 (스테이지 로컬 잔재 제거)\n"
                "          [" + FXKEYS + "].forEach(function(k){\n"
                "            var v = prod[k]!==undefined ? prod[k] : ((k===\'sched_fx_adjusts\'||k===\'sched_fx_excluded\') ? [] : {});\n"
                "            save(k, v);\n"
                "          });", 1, 'COPY')
    # (3) 별칭 전체 삭제 버튼 + 핸들러
    s = rep(s, """            + ' <button type="button" class="btn" onclick="fxUnassignAll()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#dc2626;background:#fff">업로드 배정 전체 취소</button>'""",
            """            + ' <button type="button" class="btn" onclick="fxUnassignAll()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#dc2626;background:#fff">업로드 배정 전체 취소</button>'
            + (akeys.length ? ' <button type="button" class="btn" onclick="fxAliasClearAll()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#fff;background:#dc2626">별칭 전체 삭제</button>' : '')""", 1, 'BTN')
    s = rep(s, "  window.fxUnassignAll = function(){",
            """  window.fxAliasClearAll = function(){
    if(!_isAdmin()) return;
    var n=Object.keys(fxAlias).length;
    if(!n){ showInfoModal('별칭표','삭제할 별칭이 없습니다.'); return; }
    showConfirmModal('별칭 전체 삭제', '별칭표 '+n+'건을 모두 삭제합니다.\\n(이미 배정된 입금은 그대로 둡니다 — 배정까지 되돌리려면 "업로드 배정 전체 취소"를 이어서 눌러주세요)\\n\\n계속할까요?', function(){
      fxAlias={};
      _fxSave();
      _fxRenderUnasg();
    }, '전체 삭제', '#dc2626');
  };
  window.fxUnassignAll = function(){""", 1, 'CLEAR')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r134(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r133 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r133 2026-08-24 -->', '<!-- test build r134 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
