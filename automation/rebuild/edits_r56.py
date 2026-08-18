# -*- coding: utf-8 -*-
# r56: 이메일 형식 검증 — 세금계산서 메일주소·담당자 이메일 (입력 중 빨간 표시 + 저장 차단)
R56_EDITS = [
# E1: 세금계산서 메일 필드에 실시간 검사
("""_clxFld('taxEmail','세금계산서 메일주소',inf.taxEmail,1)""",
 """_clxFld('taxEmail','세금계산서 메일주소',inf.taxEmail,1,'oninput="clxEmailCheck(this)" onblur="clxEmailCheck(this)"')"""),

# E2: 담당자 이메일 칸에도 실시간 검사
("""+ f('email','이메일',c.email)""",
 """+ f('email','이메일',c.email,'oninput="clxEmailCheck(this)" onblur="clxEmailCheck(this)"')"""),

# E3: 검증 헬퍼
("""  window.clxSave = function(orig){""",
 """  // 이메일 형식 검증 — 비어 있으면 통과, 값이 있으면 name@domain.tld 형태만 허용
  function _clxValidEmail(v){ v=String(v||'').trim(); if(!v) return true; return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(v); }
  window.clxEmailCheck = function(el){
    var ok=_clxValidEmail(el.value);
    el.style.borderColor = ok ? '#c8d2de' : '#dc2626';
    el.style.background = ok ? '' : '#fff5f5';
    el.title = ok ? '' : '이메일 형식이 올바르지 않습니다 (예: name@company.co.kr)';
  };
  window.clxSave = function(orig){"""),

# E4: 저장 시 차단 (목록 변경 전에 검사)
("""    var dupName=_findClientByBiz(bz, orig||null);
    if(bz && dupName && dupName!==nm){ showInfoModal('업체 관리','사업자번호 '+esc(bz)+' 은(는) 이미 "'+esc(dupName)+'" 으로 등록되어 있습니다.'); return; }""",
 """    var dupName=_findClientByBiz(bz, orig||null);
    if(bz && dupName && dupName!==nm){ showInfoModal('업체 관리','사업자번호 '+esc(bz)+' 은(는) 이미 "'+esc(dupName)+'" 으로 등록되어 있습니다.'); return; }
    var _badEm=null;
    if(!_clxValidEmail(get('taxEmail'))) _badEm=get('taxEmail');
    Array.prototype.forEach.call(box.querySelectorAll('.clx-crow .clx-cf[data-k="email"]'), function(el){
      if(_badEm===null && !_clxValidEmail(el.value)) _badEm=(el.value||'').trim();
    });
    if(_badEm!==null){ showInfoModal('업체 관리','이메일 형식이 올바르지 않습니다: '+esc(_badEm)+'\\n예: name@company.co.kr'); return; }"""),
]
def apply_r56(s, path):
    for i,(old,new) in enumerate(R56_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R56 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r56(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r55 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r55 2026-08-13 -->', '<!-- test build r56 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
