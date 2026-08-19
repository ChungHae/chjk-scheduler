# -*- coding: utf-8 -*-
# r95: 메모 신규 등록도 인라인 방식으로 통일. (재작성본 v2)

R95_EDITS = [
("""_pmVendors=[], _pmVendEditFor=null;""",
 """_pmVendors=[], _pmVendEditFor=null, _pmDraftId=null;"""),

("""  window.pmToggleForm = function(on){
    var next = (on===undefined) ? !_pmForm : !!on;
    if(!next) _pmEditId=null;
    if(next && !_pmEditId) _pmVendors=[];
    _pmForm = next;
    _pmRender(true);
    if(_pmForm) setTimeout(function(){ var i=document.getElementById('projMemoVendor'); if(i) try{ i.focus(); }catch(_e){} },40);
  };""",
 """  window.pmToggleForm = function(on){
    if(_pmDraftId){   // 작성 중이던 초안: 비었으면 취소(제거), 내용 있으면 편집만 종료
      var _dm=projMemos.find(function(x){ return x.id===_pmDraftId; });
      if(_dm && !(_dm.vendors&&_dm.vendors.length) && !(_dm.items&&_dm.items.length)){
        projMemos=projMemos.filter(function(x){ return x.id!==_pmDraftId; });
      }
      _pmDraftId=null; _pmVendEditFor=null;
      _pmRender(true); return;
    }
    if(on===false) return;
    if(!myMemberId){ showInfoModal('메모','프로필(내 이름)을 먼저 설정해주세요.'); return; }
    var me=members.find(function(x){ return x.id===myMemberId; });
    var id='pm'+Date.now().toString(36)+Math.random().toString(36).slice(2,6);
    projMemos.unshift({ id:id, memberId:myMemberId||'', authorName:(me?me.name:''), vendors:[], items:[], hidden:false, createdAt:Date.now() });
    _pmDraftId=id; _pmVendEditFor=id; _pmShowAll=false;
    _pmRender(true);
    setTimeout(function(){ pmVendAddStart(id); },60);
  };"""),

("""  function _pmSave(){
    save('sched_proj_memos', projMemos);""",
 """  function _pmSave(){
    if(_pmDraftId){
      var _dft=projMemos.find(function(x){ return x.id===_pmDraftId; });
      if(_dft && ((_dft.vendors&&_dft.vendors.length)||(_dft.items&&_dft.items.length))) _pmDraftId=null;   // 내용 생김 → 확정
    }
    save('sched_proj_memos', projMemos);"""),

("""    if(!force){
      if(_pmForm && document.getElementById('pmItemRows')) return;   // 작성 중 외부 재렌더 금지
      var _ae=document.activeElement;
      if(_ae && _ae.closest && _ae.closest('#projMemoBoard')) return;   // 인라인 수정 중 보호
    }""",
 """    if(!force){
      if(_pmForm && document.getElementById('pmItemRows')) return;   // 작성 중 외부 재렌더 금지
      var _ae=document.activeElement;
      if(_ae && _ae.closest && _ae.closest('#projMemoBoard')) return;   // 인라인 수정 중 보호
    }
    if(_pmDraftId && _pmVendEditFor!==_pmDraftId){
      var _ae0=document.activeElement;
      if(!(_ae0 && _ae0.closest && _ae0.closest('#projMemoBoard'))){
        var _dm0=projMemos.find(function(x){ return x.id===_pmDraftId; });
        if(_dm0 && !(_dm0.vendors&&_dm0.vendors.length) && !(_dm0.items&&_dm0.items.length)){
          projMemos=projMemos.filter(function(x){ return x.id!==_pmDraftId; });
        }
        _pmDraftId=null;
      }
    }"""),
]

def apply_r95(s, path):
    for i,(old,new) in enumerate(R95_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R95 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r95(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r94 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r94 2026-08-19 -->', '<!-- test build r95 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
