# -*- coding: utf-8 -*-
# r140: [배정된 입금 수기 수정(재배정)]
#  같은 입금자명이 두 회사에 걸치거나 잘못 매칭된 경우를 위해, 원장의 입금·어음
#  행에 수정(연필 #5b7ba6 — 디자인 규칙) 버튼 추가.
#  클릭 → 확인창 → 그 입금만 미배정으로 복귀 (별칭표는 건드리지 않음)
#  → 자료 업로드 탭의 미배정 목록에서 다시 지정 (거기서 지정하면 별칭도 새로 학습됨).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R140 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r140(s, path):
    # (1) 원장 행에 입금 id 부여
    s = rep(s, "    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:(e.bank||'')+(e.bank?' · ':'')+(e.payer||''), chg:-e.amount}); });",
            "    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:(e.bank||'')+(e.bank?' · ':'')+(e.payer||''), chg:-e.amount, did:e.id}); });", 1, 'DID')

    # (2) 입금 행에 연필(재배정) 버튼
    s = rep(s, r"""      var del = (r.aid && _isAdmin()) ? ' <button type="button" onclick="event.stopPropagation();fxDelAdjust(\''+String(r.aid).replace(/'/g,'\\\'')+'\')" data-tip="조정 삭제" aria-label="조정 삭제" style="border:none;background:transparent;cursor:pointer;padding:0 2px;vertical-align:-1px">'+TRASH+'</button>' : '';""",
            r"""      var del = (r.aid && _isAdmin()) ? ' <button type="button" onclick="event.stopPropagation();fxDelAdjust(\''+String(r.aid).replace(/'/g,'\\\'')+'\')" data-tip="조정 삭제" aria-label="조정 삭제" style="border:none;background:transparent;cursor:pointer;padding:0 2px;vertical-align:-1px">'+TRASH+'</button>' : '';
      var PEN='<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#5b7ba6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>';
      if(r.did && _isAdmin()){
        del += ' <button type="button" onclick="event.stopPropagation();fxDepUnassign(\''+String(r.did).replace(/'/g,'\\\'')+'\')" data-tip="재배정 (미배정으로 되돌리기)" aria-label="재배정" style="border:none;background:transparent;cursor:pointer;padding:0 2px;vertical-align:-1px">'+PEN+'</button>';
      }""", 1, 'PEN')

    # (3) 핸들러
    s = rep(s, "  window.fxDelAdjust = function(id){",
            r"""  window.fxDepUnassign = function(id){
    if(!_isAdmin()) return;
    var d=fxDeposits.find(function(e){ return e.id===id; }); if(!d) return;
    showConfirmModal('입금 재배정',
      d.date+' · '+_fxFmt(d.amount)+'원 · 입금자 "'+(d.payer||'')+'"\n현재 배정: '+(d.vendor||'-')+'\n\n이 입금을 미배정으로 되돌립니다.\n자료 업로드 탭의 미배정 목록에서 올바른 거래처로 다시 지정하세요.\n(별칭표는 바뀌지 않으며, 다시 지정할 때 새로 학습됩니다)',
      function(){
        d.vendor=''; d.vbiz='';
        _fxSaveBig().catch(function(_e){});
        _fxRenderArBody();
        showInfoModal('입금 재배정', '미배정으로 되돌렸습니다.\n자료 업로드 탭 > 미배정 입금 목록에서 다시 지정해 주세요.');
      }, '되돌리기', '#5b7ba6');
  };
  window.fxDelAdjust = function(id){""", 1, 'HANDLER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r140(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r139 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r139 2026-08-24 -->', '<!-- test build r140 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
