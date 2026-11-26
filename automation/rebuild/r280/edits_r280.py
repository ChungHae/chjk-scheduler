# -*- coding: utf-8 -*-
# r280 — 감사 화면 다듬기 (사용자 지시 2026-11-26)
#   ① 업체 연결 칸을 견적관리 거래처 검색과 같은 디자인으로(입력칸 + 드롭다운 목록, 키보드 이동)
#   ② 각 거래명세표의 품목 표는 기본 접힘 — 품목이 1,000개가 넘어도 화면이 길어지지 않게
#   ③ 품목을 못 찾은 품번 칸이 20~30개여도 넘치지 않게 격자 + 안쪽 스크롤, 입력 진행 표시
#  사용:  python3 edits_r280.py <index.html> [--test]
import io, sys, re

path = sys.argv[1]
IS_TEST = ('--test' in sys.argv)
s = io.open(path, encoding='utf-8').read()
orig = len(s)

def rep(old, new, cnt, label):
    global s
    n = s.count(old)
    assert n == cnt, 'ANCHOR %s: expected %d, found %d' % (label, cnt, n)
    s = s.replace(old, new)
    print('  ok  %s' % label)

assert 'window.asVdd' not in s, 'FORBIDDEN(이미 r280 적용됨)'

# ① 감사 화면에도 q-flat 입력칸 스타일 (견적·링크 툴바와 동일)
rep("""    #pageAudit .inv-flat-label { font-size:12.5px; font-weight:700; color:#14305c; white-space:nowrap; flex-shrink:0; margin-right:6px; }""",
    """    #pageAudit .inv-flat-label { font-size:12.5px; font-weight:700; color:#14305c; white-space:nowrap; flex-shrink:0; margin-right:6px; }
    /* r280: 업체 검색칸 — 견적관리 거래처 검색과 동일 */
    #pageAudit .q-flat { box-sizing:border-box; width:100%; height:28px; padding:4px 8px; margin:0; border:1px solid #c8d2de; border-radius:0; background:#fff; outline:none; font-size:13px; font-family:inherit; color:#14305c; }
    #pageAudit .q-flat:focus { border-color:#1B3A6B; }
    #pageAudit .asvd-item:hover { background:#f4f6f9; }""",
    1, '① 감사 q-flat 스타일')

# ① 업체 연결 칸 — 견적관리와 같은 검색 + 드롭다운
rep("""        h += '<span style="font-size:12.5px;color:#b45309">업체를 이어 주세요</span>'
           + ' <input list="asClients" id="asV'+di+'" placeholder="업체명" style="height:28px;padding:0 8px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit;min-width:220px">'
           + ' ' + _asBtn('연결','asLink('+di+')','primary');""",
    """        h += '<span style="font-size:12.5px;color:#b45309">업체를 이어 주세요</span>'
           + '<div style="position:relative;width:360px;max-width:100%">'
           +   '<input id="asV'+di+'" class="q-flat" type="text" placeholder="업체 검색…" autocomplete="off"'
           +     ' oninput="asVdd('+di+')" onfocus="asVdd('+di+')" onkeydown="asVkey(event,'+di+')">'
           +   '<div id="asVdd'+di+'" style="display:none;position:absolute;top:calc(100% + 2px);left:0;right:0;background:#fff;border:1px solid #d6e4f5;border-radius:8px;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:260px;overflow:auto;z-index:50"></div>'
           + '</div>';""",
    1, '① 업체 검색칸 교체')

# ③ 품목 못 찾은 품번 — 격자 + 안쪽 스크롤 + 진행 표시
rep("""        h += '<div style="padding:10px 12px;background:#fff8ef;border-bottom:1px solid #f0d9b5;font-size:12.5px;color:#b45309">'
          + '원장에서 <b>품목을 찾지 못한 품번 '+miss.length+'종</b> 입니다. '""",
    """        var _done = miss.filter(function(sp){ return (dr._newNames||{})[sp]; }).length;
        h += '<div style="padding:10px 12px;background:#fff8ef;border-bottom:1px solid #f0d9b5;font-size:12.5px;color:#b45309">'
          + '원장에서 <b>품목을 찾지 못한 품번 '+miss.length+'종</b>'+(_done?(' <span style="color:#1B3A6B">· '+_done+'종 입력함</span>'):'')+' 입니다. '""",
    1, '③ 못 찾은 품번 머리 — 진행 표시')

rep("""          h += '<div style="padding:10px 12px;border-bottom:1px solid #eef2f7;display:flex;flex-wrap:wrap;gap:8px">';
          miss.forEach(function(sp){
            h += '<span style="display:inline-flex;align-items:center;gap:6px;border:1px solid #c8d2de;padding:4px 8px">'
              + '<span style="font-size:12px;color:#1a1a1a">'+esc(sp)+'</span>'
              + '<input value="" placeholder="품목" oninput="asSetName('+di+',this.value,this.dataset.sp)" data-sp="'+esc(sp)+'" style="height:26px;width:150px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit">'
              + '</span>';
          });
          h += '</div>';""",
    """          h += '<div style="padding:10px 12px;border-bottom:1px solid #eef2f7">'
            + '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:6px;max-height:252px;overflow:auto;padding-right:2px">';
          miss.forEach(function(sp){
            var _v=(dr._newNames||{})[sp]||'';
            h += '<span style="display:flex;align-items:center;gap:6px;border:1px solid '+(_v?'#1B3A6B':'#c8d2de')+';padding:4px 8px;background:#fff;min-width:0">'
              + '<span style="font-size:12px;color:#1a1a1a;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+esc(sp)+'">'+esc(sp)+'</span>'
              + '<input value="'+esc(_v)+'" placeholder="품목" oninput="asSetName('+di+',this.value,this.dataset.sp)" data-sp="'+esc(sp)+'" style="height:26px;width:144px;flex-shrink:0;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit">'
              + '</span>';
          });
          h += '</div></div>';""",
    1, '③ 못 찾은 품번 — 격자·스크롤')

# ③ 못 찾은 품번 목록을 고정 — 품목을 적어 넣어도 입력칸이 사라지지 않게
rep("""  function _asMissing(dr){
    var seen={}, out=[];
    dr.docs.forEach(function(d){ d.rows.forEach(function(r){ if(!r.name){ var k=_qNorm(r.spec); if(!seen[k]){ seen[k]=1; out.push(r.spec); } } }); });
    return out;
  }""",
    """  // r280: 처음 한 번만 추려 기억한다. 품목을 적어 넣으면 그 줄은 더 이상 '없음' 이 아니지만,
  //       입력칸이 눈앞에서 사라지면 안 되므로 목록은 그대로 둔다.
  function _asMissing(dr){
    if(dr._missList) return dr._missList;
    var seen={}, out=[];
    dr.docs.forEach(function(d){ d.rows.forEach(function(r){ if(!r.name){ var k=_qNorm(r.spec); if(!seen[k]){ seen[k]=1; out.push(r.spec); } } }); });
    dr._missList = out;
    return out;
  }
  // 아직 품목이 비어 있는 줄 수 (저장 안내에 쓴다)
  function _asEmptyRows(dr){
    var n=0;
    dr.docs.forEach(function(d){ d.rows.forEach(function(r){ if(!r.name) n++; }); });
    return n;
  }""",
    1, '③ 못 찾은 품번 목록 고정')

rep("""    var n=dr.docs.length, miss=_asMissing(dr).length;""",
    """    var n=dr.docs.length, miss=_asEmptyRows(dr);""",
    1, '③ 저장 안내는 아직 빈 줄 수로')

rep("""      '거래명세표 '+n+'건을 저장하고 인쇄합니다.' + (miss?('\\n품목을 찾지 못한 품번 '+miss+'종은 품번만 찍힙니다.'):'')""",
    """      '거래명세표 '+n+'건을 저장하고 인쇄합니다.' + (miss?('\\n품목이 비어 있는 줄 '+miss+'개는 품번만 찍힙니다.'):'')""",
    1, '③ 저장 안내 문구')

# ② 품목 표 기본 접힘
rep("""          + '<span style="color:#8a94a6">'+d.rows.length+'품목 · '+pages+'장</span>'""",
    """          + '<button type="button" onclick="asToggleDoc('+di+','+ci+')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:12px;padding:2px 9px;cursor:pointer;font-family:inherit;color:#1B3A6B">'
          +   (d.open?'\\u25be':'\\u25b8')+' '+d.rows.length+'품목 · '+pages+'장'
          + '</button>'""",
    1, '② 품목 접기 단추')

rep("""          + '<table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:12px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'""",
    """          ;
        if(d.open){
        var _SHOW=200, _part=d.rows.slice(0,_SHOW);
        h += '<table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:12px"><thead><tr style="background:#f7f9fc;color:#5b7ba6">'""",
    1, '② 표는 펼쳤을 때만 (머리)')

rep("""        d.rows.forEach(function(r,i){
          h += '<tr style="border-bottom:1px solid #f1f4f8">'""",
    """        _part.forEach(function(r,i){
          h += '<tr style="border-bottom:1px solid #f1f4f8">'""",
    1, '② 표 줄 — 앞 200줄만')

rep("""        h += '</tbody></table></div>';
      });""",
    """        h += '</tbody></table>';
        if(d.rows.length>_SHOW) h += '<div style="padding:6px 2px;font-size:12px;color:#8a94a6">앞 '+_SHOW+'줄만 보여 줍니다 · 나머지 '+(d.rows.length-_SHOW)+'줄도 저장·인쇄에는 그대로 들어갑니다.</div>';
        }
        h += '</div>';
      });""",
    1, '② 표는 펼쳤을 때만 (꼬리)')

# ② 토글 + ① 드롭다운 함수
rep("""  window.asToggleInput = function(on){ _asShowInput = !!on; _asRender(); };""",
    """  window.asToggleInput = function(on){ _asShowInput = !!on; _asRender(); };
  window.asToggleDoc = function(di,ci){   // r280: 품목 표는 기본 접힘 (1,000줄짜리도 있을 수 있다)
    var d=_asDrafts[di] && _asDrafts[di].docs[ci]; if(!d) return;
    d.open = !d.open; _asRender();
  };
  // r280: 업체 검색 — 견적관리 거래처 검색과 같은 틀
  function _asVendorRows(q){
    var nq=_qNorm(q||''), out=[];
    var vs=[]; try{ vs=(quoteVendors||[]).slice(); }catch(e){ vs=[]; }
    vs.sort(function(a,b){ return String(a.name||'').localeCompare(String(b.name||''),undefined,{numeric:true,sensitivity:'base'}); });
    var have={};
    vs.forEach(function(v){ have[_qNorm(v.name)]=1; });
    var bz={}; try{ (allClients()||[]).forEach(function(c){ if(c&&c[0]) bz[_qNorm(c[0])]=c[1]||''; }); }catch(e){}
    vs.forEach(function(v){ if(nq && _qNorm(v.name).indexOf(nq)<0) return;
      if(out.length<80) out.push({ name:v.name, bz:bz[_qNorm(v.name)]||'', right:'규격 '+(v.count||0) }); });
    var ex=[]; try{ ex=(allClients()||[]).filter(function(c){ return c&&c[0]&&!have[_qNorm(c[0])]; }); }catch(e){}
    ex.sort(function(a,b){ return String(a[0]).localeCompare(String(b[0]),undefined,{numeric:true,sensitivity:'base'}); });
    ex.forEach(function(c){ if(nq && _qNorm(c[0]).indexOf(nq)<0) return;
      if(out.length<160) out.push({ name:c[0], bz:c[1]||'', right:'원장 없음', dim:1 }); });
    return out;
  }
  window.asVdd = function(di){
    var inp=document.getElementById('asV'+di), dd=document.getElementById('asVdd'+di);
    if(!inp||!dd) return;
    var rows=_asVendorRows(inp.value);
    window._asVNav = rows.map(function(r){ return r.name; });
    window._asVActive = -1;
    if(!rows.length){
      dd.innerHTML='<div style="padding:9px 12px;color:#bbb;font-size:13px">일치하는 업체 없음 — 일정 &gt; 업체에서 먼저 등록하세요</div>';
    } else {
      dd.innerHTML = rows.map(function(r,i){
        var nm=String(r.name).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\\\'");
        return '<div data-asvi="'+i+'" class="asvd-item" onclick="asPickVendor('+di+',\\''+nm+'\\')" style="padding:9px 14px;border-bottom:1px solid #edf1f5;display:flex;align-items:center;justify-content:space-between;gap:10px;cursor:pointer">'
          + '<span style="flex:1;min-width:0;display:flex;align-items:baseline;gap:6px"><span style="font-size:13px;color:#1a1a1a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(r.name)+'</span>'
          + (r.bz?('<span style="font-size:11px;color:#9ca3af;white-space:nowrap;flex-shrink:0">'+esc(r.bz)+'</span>'):'')+'</span>'
          + '<span style="font-size:11px;color:'+(r.dim?'#9ca3af':'#6b7280')+';white-space:nowrap;flex-shrink:0">'+esc(r.right)+'</span></div>';
      }).join('');
    }
    dd.style.display='block';
  };
  window.asVkey = function(ev,di){
    var dd=document.getElementById('asVdd'+di); if(!dd) return;
    var n=(window._asVNav||[]).length;
    if(ev.key==='Escape'){ dd.style.display='none'; return; }
    if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){
      if(!n) return; ev.preventDefault();
      window._asVActive = (ev.key==='ArrowDown') ? Math.min(n-1,(window._asVActive|0)+1) : Math.max(0,(window._asVActive|0)-1);
      Array.prototype.forEach.call(dd.querySelectorAll('.asvd-item'), function(el){
        var on = (+el.getAttribute('data-asvi'))===window._asVActive;
        el.style.background = on ? '#eaf1fb' : '#fff';
        if(on && el.scrollIntoView) el.scrollIntoView({block:'nearest'});
      });
      return;
    }
    if(ev.key==='Enter'){
      ev.preventDefault();
      var idx = (window._asVActive>=0) ? window._asVActive : (n===1?0:-1);
      if(idx>=0) asPickVendor(di, window._asVNav[idx]);
    }
  };
  window.asPickVendor = function(di, nm){
    var dd=document.getElementById('asVdd'+di); if(dd) dd.style.display='none';
    var inp=document.getElementById('asV'+di); if(inp) inp.value=nm;
    asLink(di, nm);
  };""",
    1, '①② 토글·업체 검색 함수')

# ① asLink 가 이름을 직접 받게
rep("""  window.asLink = async function(di){
    var inp=document.getElementById('asV'+di); if(!inp) return;
    var nm=(inp.value||'').trim(); if(!nm){ showInfoModal('업체 연결','업체명을 고르세요.'); return; }""",
    """  window.asLink = async function(di, nmIn){
    var inp=document.getElementById('asV'+di);
    var nm=String(nmIn!=null?nmIn:((inp&&inp.value)||'')).trim();
    if(!nm){ showInfoModal('업체 연결','업체를 고르세요.'); return; }""",
    1, '① asLink 이름 인수')

# ① 쓰지 않는 datalist 제거
rep("""    var opts=''; try{ opts=(allClients()||[]).slice(0,4000).map(function(c){ return '<option value="'+esc(c[0])+'">'; }).join(''); }catch(e){}
    h += '<datalist id="asClients">'+opts+'</datalist></div>';""",
    """    h += '</div>';""",
    1, '① datalist 제거')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r280 2026-11-26 -->')
    print('  ok  test marker %s -> r280' % m.group(0))

for k in ['window.asVdd', 'window.asVkey', 'window.asPickVendor', 'window.asToggleDoc',
          '_asVendorRows', '#pageAudit .q-flat', 'grid-template-columns:repeat(auto-fill,minmax(310px,1fr))',
          '앞 '"'"'+_SHOW+'"'"'줄만 보여 줍니다', '_asEmptyRows', 'dr._missList']:
    assert k in s, 'NEED missing: ' + k
for k in ['renderAuditPage', 'window.asSavePrint', '_asBindDrop', 'id="asDrop"']:
    assert k in s, 'KEEP missing: ' + k
assert 'id="asClients"' not in s, 'FORBIDDEN: 옛 datalist 가 남아 있다'
assert 'list="asClients"' not in s, 'FORBIDDEN: 옛 datalist 참조가 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r280 적용 완료: %d -> %d' % (orig, len(s)))
