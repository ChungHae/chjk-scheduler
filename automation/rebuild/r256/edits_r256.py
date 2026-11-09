# -*- coding: utf-8 -*-
# r256 — ① 원장 엑셀 '합치기' 가 메이커·구매처·구매링크·비고를 지우던 문제
#        ② 규격추가 '덮어쓰기' 도 같은 문제
#        ③ 일정>업체에서 업체명을 고쳐도 견적 쪽(거래처 목록·원장·담당 업체·기준가·등록 대기·저장 견적)은 옛 이름 그대로이던 문제
#  사용:  python3 edits_r256.py <index.html> [--test]
import io, sys

path = sys.argv[1]
IS_TEST = ('--test' in sys.argv)
s = io.open(path, encoding='utf-8').read()
orig_len = len(s)

def rep(old, new, cnt, label):
    global s
    n = s.count(old)
    assert n == cnt, 'ANCHOR %s: expected %d, found %d' % (label, cnt, n)
    s = s.replace(old, new)
    print('  ok  %s' % label)

# ── 가드: 이미 적용돼 있지 않아야 한다 ──
for forb in ['_qMergeLedgerRow', '_qRenameClientEverywhere', '_qRenamePending']:
    assert forb not in s, 'FORBIDDEN(이미 r256 적용됨): ' + forb

# ═══════════════════════════════════════════════════════════════
# ① 원장 엑셀 업로드 '합치기' — 올라온 값만 덮고 나머지는 지킨다
# ═══════════════════════════════════════════════════════════════
rep(
"""  function _qRowDiffers(a,b){ var f=['e','buy','sell','disc','eta','name']; for(var i=0;i<f.length;i++){ var x=a[f[i]], y=b[f[i]]; if((x==null?'':String(x))!==(y==null?'':String(y))) return true; } return false; }""",
"""  function _qRowDiffers(a,b){ var f=['e','buy','sell','disc','eta','name']; for(var i=0;i<f.length;i++){ var x=a[f[i]], y=b[f[i]]; if((x==null?'':String(x))!==(y==null?'':String(y))) return true; } return _qInfoDiffers(a&&a.info, b&&b.info); }
  // r256: 추가 정보(메이커·구매처·구매링크·비고)도 '달라짐' 판정에 넣는다.
  //  예전에는 이 값만 바뀐 행이 업로드 리포트에 '동일' 로 잡혀, 지워진 것조차 알 수 없었다.
  function _qInfoDiffers(a,b){
    var A=a||{}, B=b||{}, ks=['maker','src','link','remark'];
    for(var i=0;i<ks.length;i++){
      var x=A[ks[i]], y=B[ks[i]];
      if(String(x==null?'':x).trim()!==String(y==null?'':y).trim()) return true;
    }
    return false;
  }
  // r256: 원장 엑셀 '합치기' 는 값을 덮는 것이지 지우는 것이 아니다.
  //  예전에는 같은 규격이면 업로드 행으로 **통째로 갈아 끼워서**, 엑셀에 메이커·구매처·
  //  구매링크·비고 열이 없거나 칸이 비어 있으면 규격추가로 적어 둔 추가 정보가 소리 없이
  //  사라졌다(가격표 확판/소물 표시 pl·small 도 함께). 이제 올라온 값만 덮고,
  //  비어 있는 항목은 원래 값을 지킨다.
  function _qMergeLedgerRow(old, up){
    var o = Object.assign({}, old || {});
    Object.keys(up || {}).forEach(function(k){ if(k!=='info') o[k]=up[k]; });
    // 단종/변경은 올라온 값이 비면 해제한다 (판매가가 숫자로 돌아온 경우)
    if(!(up && up.disc!=null && String(up.disc).trim()!=='')) delete o.disc;
    var oi=(old&&old.info)?old.info:null, ui=(up&&up.info)?up.info:null;
    if(oi || ui){
      var m=Object.assign({}, oi||{});
      if(ui) Object.keys(ui).forEach(function(k){ var v=ui[k]; if(v!=null && String(v).trim()!=='') m[k]=v; });
      if(Object.keys(m).length) o.info=m; else delete o.info;
    }
    return o;
  }""", 1, '① _qRowDiffers 확장 + _qMergeLedgerRow 추가')

rep(
"""        if(up){ used[k]=1; if(_qRowDiffers(old,up)){ changed.push(up); } else { same++; } return up; }""",
"""        if(up){ used[k]=1; var _mg=_qMergeLedgerRow(old, up); if(_qRowDiffers(old,_mg)){ changed.push(_mg); } else { same++; } return _mg; }   // r256: 통째 교체 → 값만 덮기""",
1, '① 업로드 병합이 기존 추가정보를 지키게')

# ═══════════════════════════════════════════════════════════════
# ② 규격추가 '덮어쓰기' — 빈칸으로 둔 항목은 기존 값을 지킨다
# ═══════════════════════════════════════════════════════════════
rep(
"""showConfirmModal('이미 등록된 규격', '"'+esc(spec)+'" 규격이 이미 등록되어 있습니다.\\n현재 정보로 덮어쓸까요?', function(){ _qRows[exIdx]=row; _commit(null); }, '덮어쓰기', '#dc2626');""",
"""showConfirmModal('이미 등록된 규격', '"'+esc(spec)+'" 규격이 이미 등록되어 있습니다.\\n현재 정보로 덮어쓸까요?\\n(메이커·구매처·구매링크·비고를 비워 두면 기존 값이 그대로 남습니다)', function(){ _qRows[exIdx]=_qMergeLedgerRow(_qRows[exIdx], row); _commit(null); }, '덮어쓰기', '#dc2626');""",
1, '② 규격추가 덮어쓰기가 기존 추가정보를 지키게')

# ═══════════════════════════════════════════════════════════════
# ③ 업체명 변경 → 견적 쪽도 함께
# ═══════════════════════════════════════════════════════════════
rep(
"""  function _fxRenameVendorAfter(oldName, newName){""",
"""  // r256: 일정>업체에서 업체명을 고치면 매입매출(회계) 자료만 따라 바뀌고
  //  견적 쪽 — 견적관리 거래처 목록과 원장(quoteVendors) · 담당 업체 · 업체 기준가 ·
  //  업체 등록 대기 · 저장 견적 목록 — 은 옛 이름 그대로 남아 '연동이 안 된다' 고 보였다.
  //  원장 자료(_quote/<id>)는 거래처 id 로 묶여 있어 이름만 바꾸면 그대로 따라온다.
  function _qRenameClientEverywhere(oldName, newName){
    var o=String(oldName==null?'':oldName).trim(), n=String(newName==null?'':newName).trim();
    var out={vendor:0, cart:0, saved:0, owner:0, pbase:0, pend:0};
    if(!o || !n || o===n) return out;
    try{
      if(typeof quoteVendors!=='undefined' && quoteVendors)
        quoteVendors.forEach(function(v){ if(v && String(v.name||'').trim()===o){ v.name=n; out.vendor++; } });
      if(typeof _qCart!=='undefined' && _qCart)
        _qCart.forEach(function(c){ if(c && String(c.vname||'').trim()===o){ c.vname=n; out.cart++; } });
      if(typeof quoteSaved!=='undefined' && quoteSaved)
        quoteSaved.forEach(function(q){ if(q && String(q.vname||'').trim()===o){ q.vname=n; out.saved++; } });
      if(typeof clientOwner!=='undefined' && clientOwner && typeof clientOwner==='object' && !Array.isArray(clientOwner))
        ['m','a'].forEach(function(sk){
          var t=clientOwner[sk]; if(!t || typeof t!=='object') return;
          if(t[o]!==undefined){ if(t[n]===undefined) t[n]=t[o]; delete t[o]; out.owner++; }
        });
      if(typeof clientPBase!=='undefined' && clientPBase && typeof clientPBase==='object' && !Array.isArray(clientPBase) && clientPBase[o]!==undefined){
        if(clientPBase[n]===undefined) clientPBase[n]=clientPBase[o];
        delete clientPBase[o]; out.pbase++;
      }
      if(typeof clientPend!=='undefined' && clientPend)
        clientPend.forEach(function(p){ if(p && String(p.name||'').trim()===o){ p.name=n; out.pend++; } });
      if(out.cart){ try{ _qCartSave(); }catch(_e){} }
      if(out.vendor||out.saved||out.owner||out.pbase||out.pend){
        try{ saveAll(); }catch(_e){}
        try{ if(typeof doFbSave==='function') doFbSave(); }catch(_e){}
        try{ if(typeof renderEstimatePage==='function') renderEstimatePage(); }catch(_e){}
      }
    }catch(_e){}
    return out;
  }
  // 견적 쪽 변경 내용을 한 줄로 적어 두었다가, 회계 쪽 안내창에 같이 붙여 보여 준다.
  //  (안내창이 두 번 겹쳐 뜨면 앞의 것을 못 보고 지나치기 때문)
  var _qRenamePending='';
  function _qRenameNote(o, n, r){
    if(!r) return;
    var p=[];
    if(r.vendor) p.push('견적 거래처·원장');
    if(r.saved)  p.push('저장 견적 '+r.saved+'건');
    if(r.owner)  p.push('담당 업체');
    if(r.pbase)  p.push('업체 기준가');
    if(r.pend)   p.push('업체 등록 대기');
    _qRenamePending = p.length ? ('견적 자료의 업체명도 함께 바꿨습니다: ' + p.join(' · ')) : '';
  }
  function _qRenameTake(){ var t=_qRenamePending; _qRenamePending=''; return t ? ('\\n\\n' + t) : ''; }
  function _qRenameFlush(){ var t=_qRenameTake(); if(t) showInfoModal('견적 자료 거래처명 변경', t.replace(/^\\n+/,'')); }

  function _fxRenameVendorAfter(oldName, newName){""", 1, '③ _qRenameClientEverywhere 추가')

rep(
"""      if(!cnt) return;
      if(cnt.ambiguous){
        showInfoModal('매입매출 거래처명',
          '"'+o+'" 이(가) 업체 목록에 아직 남아 있어(다른 지점 등) 매입매출 자료의 이름은 바꾸지 않았습니다.\\n'
          + '어느 쪽 자료인지 확정할 수 없기 때문입니다.');
        return;
      }""",
"""      if(!cnt){ _qRenameFlush(); return; }
      if(cnt.ambiguous){
        showInfoModal('매입매출 거래처명',
          '"'+o+'" 이(가) 업체 목록에 아직 남아 있어(다른 지점 등) 매입매출 자료의 이름은 바꾸지 않았습니다.\\n'
          + '어느 쪽 자료인지 확정할 수 없기 때문입니다.' + _qRenameTake());
        return;
      }""", 1, '③ 안내 합치기 (없음·모호)')

rep(
"""      var total=cnt.inv+cnt.dep+cnt.adj+cnt.alias+cnt.term+cnt.open+cnt.excl;
      if(!total) return;""",
"""      var total=cnt.inv+cnt.dep+cnt.adj+cnt.alias+cnt.term+cnt.open+cnt.excl;
      if(!total){ _qRenameFlush(); return; }""", 1, '③ 안내 합치기 (회계 0건)')

rep(
"""        + '사업자번호로 묶는 방식은 그대로라 미수 잔액과 배정은 바뀌지 않았습니다.');""",
"""        + '사업자번호로 묶는 방식은 그대로라 미수 잔액과 배정은 바뀌지 않았습니다.' + _qRenameTake());""",
1, '③ 안내 합치기 (회계 변경됨)')

rep(
"""      showInfoModal('매입매출 거래처명', '매입매출 자료의 거래처명을 바꾸지 못했습니다.\\n'+(e&&e.message||e)
        + '\\n\\n업체 목록의 이름은 정상적으로 바뀌었습니다.');""",
"""      showInfoModal('매입매출 거래처명', '매입매출 자료의 거래처명을 바꾸지 못했습니다.\\n'+(e&&e.message||e)
        + '\\n\\n업체 목록의 이름은 정상적으로 바뀌었습니다.' + _qRenameTake());""",
1, '③ 안내 합치기 (회계 실패)')

# 호출 지점 2곳
rep(
"""    if(orig && _op.name && _op.name!==nm){ try{ _fxRenameVendorAfter(_op.name, nm); }catch(_e){} }""",
"""    if(orig && _op.name && _op.name!==nm){
      try{ _qRenameNote(_op.name, nm, _qRenameClientEverywhere(_op.name, nm)); }catch(_e){}   // r256: 견적 쪽도 같이
      try{ _fxRenameVendorAfter(_op.name, nm); }catch(_e){}
    }""", 1, '③ 호출 — 업체 관리(clxSave)')

rep(
"""      if(isEdit && editOrig && editOrig!==nm){ try{ _fxRenameVendorAfter(editOrig, nm); }catch(_e){} }""",
"""      if(isEdit && editOrig && editOrig!==nm){
        try{ _qRenameNote(editOrig, nm, _qRenameClientEverywhere(editOrig, nm)); }catch(_e){}   // r256: 견적 쪽도 같이
        try{ _fxRenameVendorAfter(editOrig, nm); }catch(_e){}
      }""", 1, '③ 호출 — 간단 업체 수정(openAddClient)')

# ── 테스트 빌드 마커 ──
if IS_TEST:
    import re
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r256 2026-11-09 -->')
    print('  ok  test marker %s -> r256' % m.group(0))

# ── 확인 ──
NEED = ['_qMergeLedgerRow', '_qInfoDiffers', '_qRenameClientEverywhere', '_qRenameTake', '_qRenameFlush']
for k in NEED:
    assert k in s, 'NEED missing: ' + k
KEEP = ['_fxRenameVendorAfter', 'qxDoUpload', 'qsSave', 'qLedgerOpenVendor']
for k in KEEP:
    assert k in s, 'KEEP missing: ' + k

io.open(path, 'w', encoding='utf-8').write(s)
print('r256 적용 완료: %d -> %d' % (orig_len, len(s)))
