# -*- coding: utf-8 -*-
# 라이브 r49(배포본) -> r54 재구성:
#  큰 블록(CLX JS·섹션 HTML·CSS)은 두 파일에 동일하게 적용됐으므로 test r54 파일에서 그대로 추출해 이식하고,
#  배선(동기화·훅·버튼 숨김 등) 소규모 edit는 r50 기록대로 재적용한다.
import io, sys

LIVE = '/mnt/user-data/outputs/index.html'
TEST = '/mnt/user-data/outputs/testpage/index.html'

live = io.open(LIVE, encoding='utf-8').read()
test = io.open(TEST, encoding='utf-8').read()

def cut(s, a, b, include_a=True, include_b=False):
    i = s.index(a); j = s.index(b, i)
    start = i if include_a else i+len(a)
    end = j+len(b) if include_b else j
    return s[start:end]

# ── 1. CLX JS 블록 (r50~r54 누적 상태) ──
CLX = cut(test, "  // ─── 업체 관리 카테고리 (목록 + 펼침 편집) ──────────────────", "  function _vacUnlimited(id){")
assert 'clxAddrSearch' in CLX and '_clxFmtPhone' in CLX and "/^0(30|50)\\d/" in CLX and 'grid-column:1/-1;height:1px' not in CLX
anchor = "  function _vacUnlimited(id){"
assert live.count(anchor) == 1 and live.count("업체 관리 카테고리") == 0
live = live.replace(anchor, CLX + anchor)

# ── 2. 섹션 HTML ──
SEC = cut(test, "  <!-- ─── 업체 관리 페이지 ─────────────────────────────── -->", '  <div id="pageBiz" class="page-section">')
assert 'id="pageClients"' in SEC and 'clxList' in SEC
a2 = '  <div id="pageBiz" class="page-section">'
assert live.count(a2) == 1
live = live.replace(a2, SEC + a2)

# ── 3. CSS 블록 ──
CSS = cut(test, "    /* ── 업체 관리: 각진 + 매입처식 툴바 ── */", "    @media (max-width: 768px){ #pageClients .clx-grid { grid-template-columns:1fr; } }", include_b=True)
a3 = "    #pageProject .inv-toolbar .qic svg { width:15px; height:15px; }"
assert live.count(a3) == 1
live = live.replace(a3, a3 + "\n" + CSS)

# ── 4. 서브탭 ──
a4 = '  <button class="sub-tab" data-page="project">프로젝트</button>'
assert live.count(a4) == 1
live = live.replace(a4, a4 + '\n  <button class="sub-tab" data-page="clients">업체 관리</button>')

# ── 5. 배선 소규모 edit (r50 기록 재적용) ──
PAIRS = [
("    var _SCHED=['personal','weekly','biz','project'];",
 "    var _SCHED=['personal','weekly','biz','project','clients'];"),
("const pageMap = { weekly:'pageWeekly', biz:'pageBiz', project:'pageProject',",
 "const pageMap = { weekly:'pageWeekly', biz:'pageBiz', project:'pageProject', clients:'pageClients',"),
("""    if (page === 'project'){ _projMode={view:'list',id:null}; _projExpId=null; _projLogEditId=null; _projTitleEdit=false; _projDraft=null; _projDirty=false; _projSearchQ=''; var _ps8=document.getElementById('projSearch'); if(_ps8) _ps8.value=''; _projFilterMember = myMemberId || 'all'; var _pm8=document.getElementById('projMemberFilter'); if(_pm8){ try{ _pm8.blur(); }catch(_e8){} } renderProjectPage(); }""",
 """    if (page === 'project'){ _projMode={view:'list',id:null}; _projExpId=null; _projLogEditId=null; _projTitleEdit=false; _projDraft=null; _projDirty=false; _projSearchQ=''; var _ps8=document.getElementById('projSearch'); if(_ps8) _ps8.value=''; _projFilterMember = myMemberId || 'all'; var _pm8=document.getElementById('projMemberFilter'); if(_pm8){ try{ _pm8.blur(); }catch(_e8){} } renderProjectPage(); }
    if (page === 'clients'){ _clxExp=null; _clxQ=''; var _cx8=document.getElementById('clxSearch'); if(_cx8) _cx8.value=''; renderClientsPage(); }"""),
("""  let clientList = load('sched_client_list') ?? [];""",
 """  let clientList = load('sched_client_list') ?? [];
  let clientInfo = load('sched_client_info') ?? {};
  // 업체 상세 { 업체명: {addr,ceo,uptae,jongmok,taxEmail,tel,fax,bank,account,holder,memo,contacts:[{dept,rank,name,phone}]} }"""),
("""        sched_clients_added: customClients,
        sched_client_list: clientList,""",
 """        sched_clients_added: customClients,
        sched_client_list: clientList,
        sched_client_info: clientInfo,"""),
("""    projectsList     = load('sched_projects') ?? [];""",
 """    projectsList     = load('sched_projects') ?? [];
    clientInfo       = load('sched_client_info') ?? {};"""),
("""    save('sched_assign_comments', assignComments);
    save('sched_projects', projectsList);""",
 """    save('sched_assign_comments', assignComments);
    save('sched_projects', projectsList);
    save('sched_client_info', clientInfo);"""),
("""      sched_leave2026: _leaveVer, sched_clients_added: customClients, sched_client_list: clientList,
      sched_projects: projectsList""",
 """      sched_leave2026: _leaveVer, sched_clients_added: customClients, sched_client_list: clientList,
      sched_projects: projectsList, sched_client_info: clientInfo"""),
("""      else if(_id==='pageProject' && typeof renderProjectPage==='function') renderProjectPage();""",
 """      else if(_id==='pageProject' && typeof renderProjectPage==='function') renderProjectPage();
      else if(_id==='pageClients' && typeof renderClientsPage==='function') renderClientsPage();"""),
("""        for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===editOrig){ customClients[j]=[nm,bz]; } }
        save('sched_clients_added', customClients);
      } else {""",
 """        for(var j=0;j<customClients.length;j++){ if(customClients[j][0]===editOrig){ customClients[j]=[nm,bz]; } }
        save('sched_clients_added', customClients);
        if(nm!==editOrig && clientInfo[editOrig]){ clientInfo[nm]=clientInfo[editOrig]; delete clientInfo[editOrig]; save('sched_client_info', clientInfo); }
      } else {"""),
("""      clientList = clientList.filter(function(x){ return x[0]!==name; });
      customClients = customClients.filter(function(x){ return x[0]!==name; });
      save('sched_clients_added', customClients);
      _saveClients();""",
 """      clientList = clientList.filter(function(x){ return x[0]!==name; });
      customClients = customClients.filter(function(x){ return x[0]!==name; });
      save('sched_clients_added', customClients);
      if(clientInfo[name]){ delete clientInfo[name]; save('sched_client_info', clientInfo); }
      _saveClients();"""),
("""      clientList=clientList.filter(function(c){ return c[0]!==v.name; });
      customClients=customClients.filter(function(c){ return c[0]!==v.name; });
      try{ ensureClientList(); }catch(e){}
      save('sched_client_list', clientList); save('sched_clients_added', customClients);""",
 """      clientList=clientList.filter(function(c){ return c[0]!==v.name; });
      customClients=customClients.filter(function(c){ return c[0]!==v.name; });
      try{ ensureClientList(); }catch(e){}
      save('sched_client_list', clientList); save('sched_clients_added', customClients);
      if(clientInfo[v.name]){ delete clientInfo[v.name]; save('sched_client_info', clientInfo); }"""),
("""    const cmBtn = document.getElementById('btnClientMgr');
    if (cmBtn) cmBtn.style.display = (hasProfile || _isAdmin()) ? '' : 'none';""",
 """    const cmBtn = document.getElementById('btnClientMgr');
    if (cmBtn) cmBtn.style.display = 'none';   // 2026-08-13 업체 관리는 일정 > 업체 관리 탭으로 이동"""),
]
for i,(old,new) in enumerate(PAIRS):
    n = live.count(old)
    if n != 1: raise SystemExit('PAIR %d count %d' % (i, n))
    live = live.replace(old, new)

# KEYS (live 2곳)
KO = ",'sched_client_list','sched_projects']"
KN = ",'sched_client_list','sched_projects','sched_client_info']"
assert live.count(KO) == 2, live.count(KO)
live = live.replace(KO, KN)

io.open(LIVE, 'w', encoding='utf-8').write(live)
print('LIVE rebuilt to r54')
