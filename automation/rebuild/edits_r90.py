# -*- coding: utf-8 -*-
# r90: 메모에 거래처(업체명) 여러 개 등록. (재작성본 v2)
#      - 검색 선택/엔터로 칩(chip) 추가, ×로 제거, 미등록 업체도 엔터로 추가
#      - 카드 제목에 " · " 로 이어서 표시 (전체 목록은 마우스오버 툴팁)
#      - 데이터: vendor(문자열) → vendors(배열). 기존 데이터 자동 마이그레이션.

R90_EDITS = [
("""  var _pmForm=false, _pmEditId=null, _pmShowHidden=false, _pmShowAll=false;""",
 """  var _pmForm=false, _pmEditId=null, _pmShowHidden=false, _pmShowAll=false, _pmVendors=[];"""),

("""        m.items=[{ id:'pi'+(m.id||'m')+'0', text:String(m.text||''), done:!!m.done, date:ds }];
        delete m.text; delete m.done;
      }
      return m;""",
 """        m.items=[{ id:'pi'+(m.id||'m')+'0', text:String(m.text||''), done:!!m.done, date:ds }];
        delete m.text; delete m.done;
      }
      if(m && !Array.isArray(m.vendors)){
        m.vendors = m.vendor ? [String(m.vendor)] : [];
        delete m.vendor;
      }
      return m;"""),

("""    var next = (on===undefined) ? !_pmForm : !!on;
    if(!next) _pmEditId=null;
    _pmForm = next;""",
 """    var next = (on===undefined) ? !_pmForm : !!on;
    if(!next) _pmEditId=null;
    if(next && !_pmEditId) _pmVendors=[];
    _pmForm = next;"""),

("""    _pmEditId=id; _pmForm=true;
    _pmRender(true);
    setTimeout(function(){ var rs=document.querySelectorAll('#pmItemRows .pm-item-text');""",
 """    _pmEditId=id; _pmForm=true;
    _pmVendors=(m.vendors||[]).slice();
    _pmRender(true);
    setTimeout(function(){ var rs=document.querySelectorAll('#pmItemRows .pm-item-text');"""),

("""  window.pmVendorPick = function(nm){
    var i=document.getElementById('projMemoVendor'); if(i) i.value=nm||'';
    var box=document.getElementById('pmVendorSug'); if(box){ box.style.display='none'; box.innerHTML=''; }
    var t=document.querySelector('#pmItemRows .pm-item-text'); if(t) setTimeout(function(){ try{ t.focus(); }catch(_e){} },20);
  };
  window.pmVendorKey = function(ev){
    if(ev.key!=='Enter') return;
    ev.preventDefault();
    var box=document.getElementById('pmVendorSug');
    if(box && box.style.display==='block'){
      var first=box.querySelector('div[data-nm]');
      if(first){ pmVendorPick(first.dataset.nm); return; }
    }
    var t=document.querySelector('#pmItemRows .pm-item-text'); if(t) try{ t.focus(); }catch(_e){}
  };""",
 """  function _pmVendorChipsSync(){
    var box=document.getElementById('pmVendorChips'); if(!box) return;
    box.style.display=_pmVendors.length?'flex':'none';
    box.innerHTML=_pmVendors.map(function(nm){
      return '<span style="display:inline-flex;align-items:center;gap:6px;padding:3px 8px;background:#fff;border:1px solid #aac4e6;font-size:12px;color:#14305c;font-weight:600">'+esc(nm)
        + '<span data-nm="'+esc(nm)+'" onclick="pmVendorDelChip(this.dataset.nm)" title="선택 해제" style="cursor:pointer;color:#8b97a5;font-weight:700;line-height:1" onmouseover="this.style.color=\\'#dc2626\\'" onmouseout="this.style.color=\\'#8b97a5\\'">&#10005;</span></span>';
    }).join('');
  }
  window.pmVendorDelChip = function(nm){
    _pmVendors=_pmVendors.filter(function(x){ return x!==nm; });
    _pmVendorChipsSync();
  };
  window.pmVendorPick = function(nm){
    nm=String(nm||'').trim();
    if(nm && _pmVendors.indexOf(nm)<0){ _pmVendors.push(nm); _pmVendorChipsSync(); }
    var i=document.getElementById('projMemoVendor'); if(i){ i.value=''; setTimeout(function(){ try{ i.focus(); }catch(_e){} },20); }
    var box=document.getElementById('pmVendorSug'); if(box){ box.style.display='none'; box.innerHTML=''; }
  };
  window.pmVendorKey = function(ev){
    if(ev.key!=='Enter') return;
    ev.preventDefault();
    var box=document.getElementById('pmVendorSug');
    if(box && box.style.display==='block'){
      var first=box.querySelector('div[data-nm]');
      if(first){ pmVendorPick(first.dataset.nm); return; }
    }
    var i=document.getElementById('projMemoVendor');
    var raw=i?String(i.value||'').trim():'';
    if(raw){ pmVendorPick(raw); return; }   // 미등록 업체도 엔터로 칩 추가
    var t=document.querySelector('#pmItemRows .pm-item-text'); if(t) try{ t.focus(); }catch(_e){}
  };"""),

("""    var v=(document.getElementById('projMemoVendor')||{value:''}).value.trim();
    var rows=document.querySelectorAll('#pmItemRows .pm-item-row');""",
 """    var _vLeft=(document.getElementById('projMemoVendor')||{value:''}).value.trim();
    if(_vLeft && _pmVendors.indexOf(_vLeft)<0) _pmVendors.push(_vLeft);   // 입력만 하고 엔터 안 친 업체도 포함
    var vlist=_pmVendors.slice();
    var rows=document.querySelectorAll('#pmItemRows .pm-item-row');"""),
("""      if(m && myMemberId && m.memberId===myMemberId){ m.vendor=v; m.items=items; }""",
 """      if(m && myMemberId && m.memberId===myMemberId){ m.vendors=vlist; m.items=items; }"""),
("""      projMemos.unshift({ id:'pm'+Date.now().toString(36)+Math.random().toString(36).slice(2,6), memberId:myMemberId||'', authorName:(me?me.name:''), vendor:v, items:items, hidden:false, createdAt:Date.now() });""",
 """      projMemos.unshift({ id:'pm'+Date.now().toString(36)+Math.random().toString(36).slice(2,6), memberId:myMemberId||'', authorName:(me?me.name:''), vendors:vlist, items:items, hidden:false, createdAt:Date.now() });"""),

("""    showConfirmModal('메모 삭제', (m.vendor?esc(m.vendor)+' ':'')+'메모를 삭제할까요?""",
 """    showConfirmModal('메모 삭제', ((m.vendors&&m.vendors.length)?esc(m.vendors.join(', '))+' ':'')+'메모를 삭제할까요?"""),

("""        +   '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;">'+(m.vendor?esc(m.vendor):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'""",
 """        +   '<span title="'+esc((m.vendors||[]).join(', '))+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;">'+((m.vendors&&m.vendors.length)?esc(m.vendors.join(' &middot; ')):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'"""),

("""        + '<input id="projMemoVendor" type="text" value="'+esc(em?em.vendor||'':'')+'" placeholder="업체명 (선택) &mdash; 입력하면 업체 목록에서 선택할 수 있습니다" autocomplete="off" oninput="pmVendorSearch(this)" onkeydown="pmVendorKey(event)" """,
 """        + '<input id="projMemoVendor" type="text" placeholder="업체명 (선택) &mdash; 검색/입력 후 엔터로 여러 업체 추가" autocomplete="off" oninput="pmVendorSearch(this)" onkeydown="pmVendorKey(event)" """),
("""        + '<div id="pmVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:200px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.14)"></div>'
        + '</div>'
        + '<div id="pmItemRows" style="display:flex;flex-direction:column;gap:6px">'+rowsHtml+'</div>'""",
 """        + '<div id="pmVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:200px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.14)"></div>'
        + '</div>'
        + '<div id="pmVendorChips" style="display:none;flex-wrap:wrap;gap:6px"></div>'
        + '<div id="pmItemRows" style="display:flex;flex-direction:column;gap:6px">'+rowsHtml+'</div>'"""),

("""    box.innerHTML = (cards||formCard)
      ? ('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px">'+formCard+cards+'</div>')
      : '';
  }""",
 """    box.innerHTML = (cards||formCard)
      ? ('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px">'+formCard+cards+'</div>')
      : '';
    if(_pmForm) _pmVendorChipsSync();
  }"""),
]

def apply_r90(s, path):
    for i,(old,new) in enumerate(R90_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R90 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r90(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r89 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r89 2026-08-19 -->', '<!-- test build r90 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
