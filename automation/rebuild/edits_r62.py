# -*- coding: utf-8 -*-
# r62: 업체 목록을 엑셀식 표(업체명·사업자번호·대표자·주소·대표전화·FAX)로,
#      헤더 틀고정(sticky), 행 클릭 시 아래로 상세 폼 펼침(기존 방식 유지)

CLX_RENDER2 = '''  function _clxRender(){
    var box=document.getElementById('clxList'); if(!box) return;
    try{ ensureClientList(); }catch(_e){}
    var all=allClients().slice().sort(function(a,b){ return String(a[0]).localeCompare(String(b[0])); });
    var cnt=document.getElementById('clxCount'); if(cnt) cnt.textContent = all.length + '개 업체';
    var q=_clxQ, qd=q.replace(/\\D/g,'');
    var list=all.filter(function(c){
      if(_clxExp!==null && _clxExp!=='' && c[0]===_clxExp) return true;   // 펼친 업체는 항상 표시
      if(!q) return true;
      if(String(c[0]).toLowerCase().indexOf(q)>=0) return true;
      if(qd && String(c[1]||'').replace(/\\D/g,'').indexOf(qd)>=0) return true;
      return false;
    });
    var _capNote='';
    if(list.length>300){
      _capNote='<div style="text-align:center;padding:8px;color:#9ca3af;font-size:11.5px">상위 300개만 표시 중 (전체 '+list.length+'개) · 검색으로 찾아주세요</div>';
      list=list.slice(0,300);
      if(_clxExp && _clxExp!=='' && !list.some(function(c){ return c[0]===_clxExp; })){
        var _exRow=all.filter(function(c){ return c[0]===_clxExp; });
        list=_exRow.concat(list);   // 펼친 업체는 표시 제한과 무관하게 맨 위에 노출
      }
    }
    var html='';
    if(_clxExp===''){
      html += '<div style="background:#fff;border:1px solid #d8e1ec;border-left:3px solid #1B3A6B;margin-bottom:8px">'
        + '<div style="padding:11px 16px;display:flex;align-items:center;gap:8px;background:#f4f8fe"><span style="font-size:14px;font-weight:700;color:#14305c">신규 업체 등록</span></div>'
        + _clxFormHtml('', ['','']) + '</div>';
    }
    if(!list.length){
      html += '<div style="text-align:center;padding:40px 16px;color:#b6bec9;font-size:13px">'+(all.length?'조건에 맞는 업체가 없습니다.':'등록된 업체가 없습니다. 우측 상단의 &#65291; 버튼으로 등록해보세요.')+'</div>';
      box.innerHTML=html; return;
    }
    var TH='padding:9px 10px;background:#fafafa;color:#888;font-weight:500;font-size:12px;text-align:center;position:sticky;top:var(--tfh, 140px);z-index:2;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var TD='padding:8px 10px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle';
    html += '<div style="background:#fff;border:1px solid #d6deea;border-left:none;border-right:none;margin:0 calc(var(--mpx, 24px)*-1)">'
      + '<table style="width:100%;border-collapse:separate;border-spacing:0;min-width:980px;table-layout:fixed;font-size:12.5px">'
      + '<colgroup><col style="width:220px"><col style="width:120px"><col style="width:90px"><col><col style="width:130px"><col style="width:130px"></colgroup>'
      + '<thead><tr>'
      +   '<th style="'+TH+'">업체명</th><th style="'+TH+'">사업자번호</th><th style="'+TH+'">대표자</th><th style="'+TH+'">주소</th><th style="'+TH+'">대표전화</th><th style="'+TH+'">FAX</th>'
      + '</tr></thead><tbody>'
      + list.map(function(c){
          var nm=c[0], bz=c[1]||'', inf=_clxInfo(nm);
          var exp=_clxExp===nm;
          var dim=_clxExp!==null && !exp;   // 다른 업체가 펼쳐져 있으면 나머지는 흐리게
          var addr=[inf.addr||'', inf.addr2||''].filter(Boolean).join(' ');
          var tr='<tr data-nm="'+esc(nm)+'" onclick="clxToggle(this.dataset.nm)" style="cursor:pointer;'+(exp?'background:#f4f8fe;':'')+(dim?'opacity:.18;transition:opacity .12s;':'')+'"'
            + (dim?' onmouseover="this.style.opacity=\\'.85\\'" onmouseout="this.style.opacity=\\'.18\\'"':(exp?'':' onmouseover="this.style.background=\\'#f7fafd\\'" onmouseout="this.style.background=\\'\\'"'))+'>'
            + '<td style="'+TD+';font-weight:700;color:#14305c" title="'+esc(nm)+'">'+esc(nm)+'</td>'
            + '<td style="'+TD+';color:#6b7280;text-align:center">'+esc(bz)+'</td>'
            + '<td style="'+TD+';text-align:center">'+esc(inf.ceo||'')+'</td>'
            + '<td style="'+TD+'" title="'+esc(addr)+'">'+esc(addr)+'</td>'
            + '<td style="'+TD+'">'+esc(inf.tel||'')+'</td>'
            + '<td style="'+TD+'">'+esc(inf.fax||'')+'</td>'
            + '</tr>';
          if(exp){
            tr += '<tr><td colspan="6" style="padding:0;border-bottom:2px solid #1B3A6B;background:#fff">'+_clxFormHtml(nm, c)+'</td></tr>';
          }
          return tr;
        }).join('')
      + '</tbody></table></div>' + _capNote;
    box.innerHTML=html;
  }
'''

START = "  function _clxRender(){"
END = "  // 전화번호 하이픈 자동 삽입"

def apply_r62(s, path):
    a = s.index(START)
    b = s.index(END, a)
    return s[:a] + CLX_RENDER2 + s[b:]

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r62(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r61 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r61 2026-08-13 -->', '<!-- test build r62 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
