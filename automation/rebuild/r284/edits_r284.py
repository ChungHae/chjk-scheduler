# -*- coding: utf-8 -*-
# r284 — 감사: 같은 내용이 또 올라오면 중복이라고 알려 준다 (사용자 지시 2026-11-26)
#   같은 **발행일 + 물류출하일 + 업체 + 품목·수량 묶음**이 이미 저장돼 있으면
#   ① 올린 직후 화면에 '이미 저장된 내역' 표시 ② 저장할 때 한 번 더 묻고
#   [그대로 저장] / [취소] 를 고르게 한다.
#  사용:  python3 edits_r284.py <index.html> [--test]
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

assert '_asDupOf' not in s, 'FORBIDDEN(이미 r284 적용됨)'

# ── 중복 찾기 ────────────────────────────────────────────────
rep("""  // ── 저장 ────────────────────────────────────────────────────
  async function _asSaveDocs(draft){""",
    """  // ── 중복 확인 (r284) ────────────────────────────────────────
  // 같은 발행일 + 물류출하일 + 업체 + 품목·수량 묶음이면 같은 자료로 본다.
  function _asRowsSig(rows){
    return (rows||[]).map(function(r){ return _qNorm(r && r.spec) + '*' + (Number(r && r.qty) || 0); })
                     .sort().join('|');
  }
  function _asSameVendor(rec, draft){
    if(rec.vid && draft.vid) return rec.vid === draft.vid;
    return _qNorm(rec.vname) === _qNorm(draft.vname);
  }
  function _asDupOf(draft, d){
    var rows = _asLRows; if(!rows || !rows.length) return null;
    var sig = _asRowsSig(d.rows);
    for(var i=0;i<rows.length;i++){
      var v = rows[i];
      if(!v || v.date !== d.date || String(v.ship||'') !== String(d.ship||'')) continue;
      if(!_asSameVendor(v, draft)) continue;
      if(_asRowsSig(v.rows) !== sig) continue;
      return v;
    }
    return null;
  }
  // 저장된 목록을 한 번만 읽어 둔다 (화면은 건드리지 않는다)
  async function _asEnsureList(){
    if(_asLRows) return _asLRows;
    try{
      var r = await _fbFetch(_asDocUrl(null));
      var d = r && r.ok ? (await r.json()) : null;
      _asLRows = d ? Object.keys(d).map(function(k){ var v=d[k]||{}; if(!v.id) v.id=k; return v; })
                           .filter(function(v){ return v && v.date; }) : [];
      _asLRows.sort(function(a,b){ return String(a.date||'').localeCompare(String(b.date||'')) || ((a.no||0)-(b.no||0)) || ((a.at||0)-(b.at||0)); });
    }catch(e){ _asLRows = null; }
    return _asLRows;
  }
  function _asDupList(draft){
    var out=[];
    (draft.docs||[]).forEach(function(d,ci){ if(d.dup) out.push({ ci:ci, d:d, rec:d.dup }); });
    return out;
  }
  // 올린 직후·업체를 이은 직후에 표시를 달아 준다
  async function _asMarkDup(draft){
    await _asEnsureList();
    (draft.docs||[]).forEach(function(d){ d.dup = draft.vname ? _asDupOf(draft, d) : null; });
    _asRender();
  }
  async function _asMarkDupAll(){
    await _asEnsureList();
    _asDrafts.forEach(function(dr){ (dr.docs||[]).forEach(function(d){ d.dup = dr.vname ? _asDupOf(dr, d) : null; }); });
    _asRender();
  }

  // ── 저장 ────────────────────────────────────────────────────
  async function _asSaveDocs(draft){""",
    1, '① 중복 찾기 함수')

# ── 올린 직후 / 업체 연결 직후 표시 ──────────────────────────
rep("""        _asDrafts.push(dr);
      }
      _asRender();
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }""",
    """        _asDrafts.push(dr);
      }
      _asRender();
      _asMarkDupAll();   // r284: 이미 저장된 것과 같은 내용인지 표시
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }""",
    1, '② 엑셀을 올린 직후 표시')

rep("""    if(!v) showInfoModal('업체 연결','"'+esc(nm)+'" 에는 견적 원장이 없어 품목을 찾아오지 못합니다. 품목은 직접 넣으면 원장이 새로 만들어집니다.');
    _asRender();""",
    """    if(!v) showInfoModal('업체 연결','"'+esc(nm)+'" 에는 견적 원장이 없어 품목을 찾아오지 못합니다. 품목은 직접 넣으면 원장이 새로 만들어집니다.');
    _asRender();
    _asMarkDup(_asDrafts[di]);   // r284""",
    1, '② 업체를 이은 직후 표시')

# ── 화면 표시 ───────────────────────────────────────────────
rep("""          + (d.warn ? ('<div style="margin-top:5px;font-size:11.5px;color:#b45309">'+esc(d.warn)+'</div>') : '')""",
    """          + (d.warn ? ('<div style="margin-top:5px;font-size:11.5px;color:#b45309">'+esc(d.warn)+'</div>') : '')
          // r284: 같은 발행일·출하일·업체·품목·수량이 이미 저장돼 있으면 알려 준다
          + (d.dup ? ('<div style="margin-top:5px;font-size:11.5px;color:#b45309">\\u26a0 이미 저장된 거래명세표와 같은 내용입니다 — '
               + esc(d.dup.date||'') + ' · 번호 ' + esc(String(d.dup.no||'')) + (d.dup.by?(' · '+esc(d.dup.by)):'') + ' 작성</div>') : '')""",
    1, '③ 전표 줄에 중복 표시')

rep("""      h += '<div style="border:1px solid #c8d2de;margin-bottom:18px">';""",
    """      var _dupN = _asDupList(dr).length;   // r284
      h += '<div style="border:1px solid '+(_dupN?'#f0d9b5':'#c8d2de')+';margin-bottom:18px">';
      if(_dupN) h += '<div style="padding:8px 12px;background:#fff8ef;border-bottom:1px solid #f0d9b5;font-size:12.5px;color:#b45309">'
        + '\\u26a0 <b>이미 저장된 거래명세표와 같은 내용이 '+_dupN+'건</b> 있습니다. 그대로 저장하면 같은 자료가 하나 더 쌓입니다.</div>';""",
    1, '③ 묶음 머리에 중복 안내')

# ── 저장할 때 다시 묻는다 ───────────────────────────────────
rep("""  window.asSavePrint = function(di){
    var dr=_asDrafts[di];
    if(!dr.vname){ showInfoModal('거래명세표','업체를 먼저 이어 주세요.'); return; }
    var n=dr.docs.length, miss=_asEmptyRows(dr);
    showConfirmModal('거래명세표 저장·인쇄',
      '거래명세표 '+n+'건을 저장하고 인쇄합니다.' + (miss?('\\n품목이 비어 있는 줄 '+miss+'개는 품번만 찍힙니다.'):'')
      + '\\n양식 용지를 프린터에 넣고 진행하세요.',""",
    """  window.asSavePrint = async function(di){
    var dr=_asDrafts[di];
    if(!dr.vname){ showInfoModal('거래명세표','업체를 먼저 이어 주세요.'); return; }
    var n=dr.docs.length, miss=_asEmptyRows(dr);
    // r284: 저장 직전에 다시 한 번 확인한다 (다른 사람이 그 사이 저장했을 수도 있다)
    await _asEnsureList();
    dr.docs.forEach(function(d){ d.dup = _asDupOf(dr, d); });
    var dups = _asDupList(dr);
    if(dups.length) _asRender();
    var _dupTxt = dups.length
      ? ('\\n\\n\\u26a0 중복 내역 ' + dups.length + '건 — 같은 발행일·물류출하일·업체·품목·수량이 이미 저장돼 있습니다.\\n'
         + dups.slice(0,5).map(function(x){ return '  · ' + (x.d.date||'') + ' 번호 ' + (x.rec.no||'') + ' (' + (x.d.rows.length) + '품목)'; }).join('\\n')
         + (dups.length>5 ? ('\\n  … 모두 '+dups.length+'건') : '')
         + '\\n그대로 저장하면 같은 자료가 하나 더 쌓입니다.')
      : '';
    showConfirmModal(dups.length ? '중복 확인 — 그대로 저장할까요?' : '거래명세표 저장·인쇄',
      '거래명세표 '+n+'건을 저장하고 인쇄합니다.' + (miss?('\\n품목이 비어 있는 줄 '+miss+'개는 품번만 찍힙니다.'):'')
      + '\\n양식 용지를 프린터에 넣고 진행하세요.' + _dupTxt,""",
    1, '④ 저장 직전 중복 확인')

rep("""      }, '저장하고 인쇄', '#1B3A6B');
  };""",
    """      }, dups.length ? '중복이지만 그대로 저장' : '저장하고 인쇄', dups.length ? '#b45309' : '#1B3A6B');
  };""",
    1, '④ 단추 이름·색')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r284 2026-11-26 -->')
    print('  ok  test marker %s -> r284' % m.group(0))

for k in ['_asRowsSig', '_asDupOf', '_asEnsureList', '_asMarkDupAll', '_asDupList',
          '중복이지만 그대로 저장', '이미 저장된 거래명세표와 같은 내용',
          'window.asSavePrint = async function(di)']:
    assert k in s, 'NEED missing: ' + k
for k in ['_asSaveDocs', '_asPushLedger', 'renderAuditPage', 'asLDateIn', 'as-doc-head']:
    assert k in s, 'KEEP missing: ' + k

io.open(path, 'w', encoding='utf-8').write(s)
print('r284 적용 완료: %d -> %d' % (orig, len(s)))
