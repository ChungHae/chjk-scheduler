# -*- coding: utf-8 -*-
# r107: (1) 업체 관리 탭 이름 → "업체"
#       (2) 마스터(chjk 등 관리자) 계정이 연차 현황에서 모든 직원(김재성 포함)의
#           연차·반차·반반차를 대신 등록할 수 있게 — 직원별 [등록] 버튼 추가.
#           (openVacationModal 은 이미 targetId 대상 등록을 지원 → 진입 경로만 추가)

# (old, new, expected_count)
R107_EDITS = [

# (1) 탭 이름
("""<button class="sub-tab" data-page="clients">업체 관리</button>""",
 """<button class="sub-tab" data-page="clients">업체</button>""", 1),

# (2a) 관리자 연차 현황 목록에 김재성 포함 (전 직원)
("""    var list = _admin ? members.filter(function(m){ return m.name!=='김재성'; })
                      : members.filter(function(m){ return m.id===myMemberId; });""",
 """    var list = _admin ? members.slice()
                      : members.filter(function(m){ return m.id===myMemberId; });""", 1),

# (2b) 직원별 [등록] 버튼 + 무제한 직원 표기
("""      var rc = remain<=3 ? '#ef4444' : '#2f5288';
      return '<tr style="border-bottom:1px solid #eef2f7">'
        + '<td style="padding:8px 6px;font-weight:700;color:#14305c;white-space:nowrap">'+esc(m.name)+'</td>'
        + '<td style="padding:8px 6px;text-align:center">'+alloc+'</td>'
        + '<td style="padding:8px 6px;text-align:center;color:#6b7280">'+used+'</td>'
        + '<td style="padding:8px 6px;text-align:center;font-weight:700;color:'+rc+'">'+remain+'</td>'""",
 """      var rc = remain<=3 ? '#ef4444' : '#2f5288';
      var _unlM = _vacUnlimited(m.id);
      return '<tr style="border-bottom:1px solid #eef2f7">'
        + '<td style="padding:8px 6px;font-weight:700;color:#14305c;white-space:nowrap">'+esc(m.name)
        +   (_admin?('<button data-mid="'+m.id+'" onclick="vacAdminApply(this.dataset.mid)" title="이 직원의 연차·반차·반반차 등록" style="margin-left:7px;padding:2px 8px;border:1px solid #1B3A6B;background:#fff;color:#1B3A6B;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;font-family:inherit" onmouseover="this.style.background=\\'#1B3A6B\\';this.style.color=\\'#fff\\'" onmouseout="this.style.background=\\'#fff\\';this.style.color=\\'#1B3A6B\\'">등록</button>'):'')
        + '</td>'
        + '<td style="padding:8px 6px;text-align:center">'+(_unlM?'무제한':alloc)+'</td>'
        + '<td style="padding:8px 6px;text-align:center;color:#6b7280">'+used+'</td>'
        + '<td style="padding:8px 6px;text-align:center;font-weight:700;color:'+rc+'">'+(_unlM?'&mdash;':remain)+'</td>'""", 1),

# (2c) 등록 진입 함수 (연차 현황 닫고 등록 모달 열기)
("""  window.openVacAdmin = function(){""",
 """  window.vacAdminApply = function(mid){
    var ov=document.getElementById('vacAdminOverlay'); if(ov) ov.style.display='none';
    openVacationModal(mid);
  };
  window.openVacAdmin = function(){""", 1),
]

def apply_r107(s, path):
    for i,(old,new,exp) in enumerate(R107_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R107 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r107(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r106 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r106 2026-08-20 -->', '<!-- test build r107 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
