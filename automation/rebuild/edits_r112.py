# -*- coding: utf-8 -*-
# r112: 연차 대리 등록을 마스터 계정(chjk)만 가능하게 제한.
#       (일반 관리자: 연차 현황 열람만 가능 — 등록 버튼/김재성 행 비표시, r107 이전과 동일)

R112_EDITS = [

# (1) 마스터 여부 판별 추가
("""  window.vacAdminApply = function(mid){
    var ov=document.getElementById('vacAdminOverlay'); if(ov) ov.style.display='none';
    openVacationModal(mid);
  };""",
 """  function _vacIsMaster(){ return !!(_authUser && (String(_authUser.id||'').trim()==='chjk' || String(_authUser.name||'').trim()==='chjk')); }
  window.vacAdminApply = function(mid){
    if(!_vacIsMaster()) return;   // r112 대리 등록은 마스터(chjk)만
    var ov=document.getElementById('vacAdminOverlay'); if(ov) ov.style.display='none';
    openVacationModal(mid);
  };""", 1),

# (2) 김재성 행: 마스터만 표시 (일반 관리자는 r107 이전처럼 제외)
("""    var list = _admin ? members.slice()
                      : members.filter(function(m){ return m.id===myMemberId; });""",
 """    var _master = _vacIsMaster();
    var list = _admin ? (_master ? members.slice() : members.filter(function(m){ return m.name!=='김재성'; }))
                      : members.filter(function(m){ return m.id===myMemberId; });""", 1),

# (3) [등록] 버튼: 마스터만
("""        +   (_admin?('<button data-mid="'+m.id+'" onclick="vacAdminApply(this.dataset.mid)" title="이 직원의 연차·반차·반반차 등록\"""",
 """        +   (_master?('<button data-mid="'+m.id+'" onclick="vacAdminApply(this.dataset.mid)" title="이 직원의 연차·반차·반반차 등록\"""", 1),
]

def apply_r112(s, path):
    for i,(old,new,exp) in enumerate(R112_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R112 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r112(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r111 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r111 2026-08-20 -->', '<!-- test build r112 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
