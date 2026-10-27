# -*- coding: utf-8 -*-
# r250 (사용자 보고 2026-10-27): "견적 작성 후 PDF 다운로드하면 다운로드는 되는데 견적이 저장이 안 된다"
#
# 원인 (실제 Firebase 자료로 확인)
#   견적 저장은 두 군데로 나뉜다.
#     ① 품목  : _qsBlobPut() 이 `<db>/teamdata_test_qsaved/<id>` 로 **즉시 직접 PUT**
#     ② 목록  : quoteSaved 배열에 넣고 saveAll() → debouncedFbSave() → **0.8초 뒤** 상태 전체 PATCH
#   그 0.8초 사이에 다른 직원의 저장이 서버에 닿으면, 2초마다 도는 _pollSync 가
#   sched_quote_saved 를 **통째로 덮어쓰고**(회의록만 r236 병합 보호를 받는다) reloadState() 가
#   그 사본을 메모리에 올린다 → 방금 추가한 항목이 사라지고, 뒤이어 올라가는 저장본에도 없다.
#   품목은 이미 저장됐으므로 "다운로드는 됐는데 저장이 안 된" 것처럼 보인다.
#   실제 증거: 품목만 있고 목록에 없는 견적 4건
#     2026-07-27 12:15 (주)코스메틱코리아(빈 건) / 08-28 16:37 (주)동신포리마 123,000
#     08-31 09:30 주식회사 재원 482,400 / 09-30 09:46 (주)아이에스티이 110,510
#     10-27 09:04 솔브레인엘티케이 5행 631,400  ← 이번에 보고된 건
#   (삭제는 qDelSaved 가 품목까지 지우므로, 품목만 남은 건은 삭제분이 아니라 유실분이다.)
#
#   두 번째 결함: 내용이 빈 견적(거래처만 잡힌 빈 줄)에서 저장이 눌리면
#   _qEnsureQuoteNo() 가 _qCartHasContent() 에서 조용히 빠져나가는데 _qPersistQuote() 는 그대로 진행해
#   `_qsaved/null` 과 {id:null, title:null} 쓰레기 항목이 생긴다(10-27 09:13 실제 발생). 안내도 없다.
#
# 조치 — r236(회의록 동시 작성 병합)과 같은 틀을 저장 견적 목록에 적용
#   ① 묘비 _qsDelMap(`sched_quote_del`) — 삭제를 기록해 다른 PC 사본이 되살리지 못하게
#   ② _qsPend — 아직 서버에 안 올라간 내 항목. 병합 때 '내가 방금 저장한 것'만 되살린다(옛 삭제분 부활 방지)
#   ③ doFbSave: 올리기 전에 _qsMergeFromServer() 로 서버 목록과 id 단위 병합
#   ④ _pollSync: sched_quote_saved 를 덮지 않고 _qsMerge() 로 합쳐 받음
#   ⑤ 올린 뒤 2.5초 _qsVerify(): 서버에 내 항목이 없으면 다시 합쳐 올림 (최대 3회)
#   ⑥ 빈 견적·번호 미발급·동기화 끊김은 조용히 넘어가지 않고 오류를 던진다(호출부가 안내창을 띄움)
import io, sys

HELPERS = """  // ── r250: 저장 견적 목록(quoteSaved) 동시 저장 보호 ──────────────────
  //  품목(_qsaved/<id>)은 직접 PUT 이라 바로 들어가는데 목록은 상태 전체 PATCH(0.8초 지연)라,
  //  그 사이 다른 직원의 저장이 서버에 닿으면 2초 폴링이 목록을 통째로 덮어써서 내 견적이 사라졌다.
  //  r236(회의록)과 같은 틀 — 올리기 전 합치기 · 받을 때 합치기 · 삭제는 묘비 · 올린 뒤 검증.
  function _qsArr(x){ return Array.isArray(x) ? x.filter(function(e){ return e && e.id; }) : []; }
  function _qsU(x){ return Number((x && (x.upd || x.savedAt)) || 0); }
  function _qsMerge(mine, srv, serverDel){
    var del = Object.assign({}, (serverDel && typeof serverDel === 'object') ? serverDel : {}, _qsDelMap || {});
    _qsDelMap = del;
    var m = _qsArr(mine), s = _qsArr(srv), byId = {}, out = [], seen = {};
    m.forEach(function(x){ byId[x.id] = x; });
    s.forEach(function(x){
      if(del[x.id] || seen[x.id]) return;
      var mi = byId[x.id];
      out.push((mi && (_qsPend[x.id] || _qsU(mi) > _qsU(x))) ? mi : x);
      seen[x.id] = 1;
    });
    // 서버에 아직 없는 건 '내가 방금 저장한 것'만 되살린다 (옛 삭제분 부활 방지)
    var add = m.filter(function(x){ return !seen[x.id] && !del[x.id] && _qsPend[x.id]; });
    return add.concat(out);
  }
  async function _qsMergeFromServer(){
    if(!_fbDbUrl) return false;
    var r = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '/sched_quote_saved.json');
    if(!r || !r.ok) return false;
    var s = await r.json();
    var r2 = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '/sched_quote_del.json');
    var sd = (r2 && r2.ok) ? (await r2.json()) : null;
    quoteSaved = _qsMerge(quoteSaved, s, sd);
    save('sched_quote_saved', quoteSaved); save('sched_quote_del', _qsDelMap);
    return true;
  }
  var _qsVerifyTimer = null, _qsVerifyTries = 0;
  function _qsScheduleVerify(){ if(_qsVerifyTimer) clearTimeout(_qsVerifyTimer); _qsVerifyTimer = setTimeout(_qsVerify, 2500); }
  async function _qsVerify(){   // 같은 순간 두 사람이 올렸으면 한쪽이 덮인다 → 서버에 내 견적이 남아 있는지 확인
    _qsVerifyTimer = null;
    try{
      var ids = Object.keys(_qsPend || {});
      if(!ids.length){ _qsVerifyTries = 0; return; }
      if(!_fbDbUrl) return;
      var r = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '/sched_quote_saved.json');
      if(!r || !r.ok) return;
      var s = _qsArr(await r.json()), have = {};
      s.forEach(function(x){ have[x.id] = 1; });
      var miss = ids.filter(function(id){ return !have[id] && !_qsDelMap[id]; });
      var ghost = s.some(function(x){ return _qsDelMap[x.id]; });
      if((!miss.length && !ghost) || _qsVerifyTries >= 3){ _qsPend = {}; _qsVerifyTries = 0; return; }
      _qsVerifyTries++;
      await _qsMergeFromServer();
      debouncedFbSave();
    }catch(_e){}
  }
"""

OPS = [
 # ① 묘비·대기 선언 (회의록 묘비 바로 옆 — 폴링·저장보다 먼저 만들어져야 한다)
 ["  let _mtDelMap = load('sched_meetings_del') ?? {};   // r236 회의록 묘비(삭제 기록)\n",
  "  let _mtDelMap = load('sched_meetings_del') ?? {};   // r236 회의록 묘비(삭제 기록)\n"
  "  let _qsDelMap = load('sched_quote_del') ?? {};   // r250 저장 견적 묘비(삭제 기록) {id:ts}\n"
  "  let _qsPend = {};   // r250 아직 서버에 안 올린 저장 견적 {id:ts}\n",
  1, "DECL"],

 # ② saveAll
 ["    save('sched_quote_saved', quoteSaved);\n",
  "    save('sched_quote_saved', quoteSaved);\n    save('sched_quote_del', _qsDelMap);   // r250\n",
  1, "SAVEALL"],

 # ③ reloadState
 ["      quoteSaved       = load('sched_quote_saved') ?? [];\n",
  "      quoteSaved       = load('sched_quote_saved') ?? [];\n    _qsDelMap        = load('sched_quote_del') ?? {};   // r250\n",
  1, "RELOAD"],

 # ④ doFbSave 에 묘비도 같이 올린다
 ["        sched_quote_saved: quoteSaved,\n",
  "        sched_quote_saved: quoteSaved,\n        sched_quote_del: _qsDelMap,   // r250\n",
  1, "FB_KEY"],

 # ⑤ doFbSave: 올리기 전에 서버 목록과 합친다
 ["    if (_mtWasDirty) { try { await _mtMergeFromServer(); } catch(_me) {} }   // r236: 올리기 전에 서버 회의록과 항목 단위로 합친다\n",
  "    if (_mtWasDirty) { try { await _mtMergeFromServer(); } catch(_me) {} }   // r236: 올리기 전에 서버 회의록과 항목 단위로 합친다\n"
  "    const _qsWasDirty = Object.keys(_qsPend || {}).length > 0;   // r250\n"
  "    if (_qsWasDirty) { try { await _qsMergeFromServer(); } catch(_qe) {} }   // r250: 올리기 전에 서버 견적 목록과 id 단위로 합친다\n",
  1, "FB_MERGE"],

 # ⑥ doFbSave 성공 뒤 검증 예약
 ["      if (_mtWasDirty) { _mtDirty = false; _mtScheduleVerify(); }   // r236\n",
  "      if (_mtWasDirty) { _mtDirty = false; _mtScheduleVerify(); }   // r236\n"
  "      if (_qsWasDirty) { _qsScheduleVerify(); }   // r250\n",
  1, "FB_DONE"],

 # ⑦ 폴링이 견적 목록을 덮지 않고 합치게
 ["if (k === 'sched_meetings_del') { save(k, Object.assign({}, d[k] || {}, _mtDelMap || {})); return; } save(k, d[k]); });",
  "if (k === 'sched_meetings_del') { save(k, Object.assign({}, d[k] || {}, _mtDelMap || {})); return; }"
  " if (k === 'sched_quote_saved') { save(k, _qsMerge(quoteSaved, d[k], d.sched_quote_del)); return; }"
  " if (k === 'sched_quote_del') { save(k, Object.assign({}, d[k] || {}, _qsDelMap || {})); return; } save(k, d[k]); });",
  1, "POLL"],

 # ⑧ 두 KEYS 목록에 묘비 키 추가 (폴링 1곳 · 최초 로드 1곳)
 ["'sched_meetings','sched_meetings_del','sched_fx_alias'",
  "'sched_meetings','sched_meetings_del','sched_quote_del','sched_fx_alias'",
  2, "KEYS"],

 # ⑨ 헬퍼 (함수 선언이라 호이스팅 — doFbSave·_pollSync 보다 뒤에 두어도 된다)
 ["  async function _qPersistQuote(){\n", HELPERS + "  async function _qPersistQuote(){\n", 1, "HELPERS"],

 # ⑩ 빈 견적·번호 미발급·동기화 끊김을 조용히 넘기지 않는다
 ["    if(!_qCart.length) return;\n    _qEnsureQuoteNo();\n    if(!_fbDbUrl) return;\n",
  "    if(!_qCart.length) return;\n"
  "    // r250: 내용이 빈 견적은 저장하지 않는다 (번호·id 없이 저장돼 목록에 null 항목이 생기던 문제)\n"
  "    if(!_qCartHasContent()) throw new Error('견적 내용이 비어 있습니다.\\n품목을 한 줄 이상 입력한 뒤 저장해 주세요.');\n"
  "    _qEnsureQuoteNo();\n"
  "    if(!_qLoadedId || !_qQuoteNo) throw new Error('견적번호를 발급하지 못했습니다.\\n거래처와 품목을 확인한 뒤 다시 시도해 주세요.');\n"
  "    if(!_fbDbUrl) throw new Error('동기화 연결이 끊겨 있습니다.\\n연결된 뒤 다시 저장해 주세요.');\n",
  1, "GUARD"],

 # ⑪ 저장 시 upd 기록 + 대기 표시 + 검증 예약
 ["    else { quoteSaved.unshift({id:_qLoadedId, title:_qQuoteNo, vname:vn, vid:vid, count:_qCart.length, total:supply, nego:_qNego, memo:_qMemo, note:_qNote, savedBy:who, savedAt:Date.now(), cols:JSON.parse(JSON.stringify(_qCols||[]))}); }\n    saveAll();\n",
  "    else { quoteSaved.unshift({id:_qLoadedId, title:_qQuoteNo, vname:vn, vid:vid, count:_qCart.length, total:supply, nego:_qNego, memo:_qMemo, note:_qNote, savedBy:who, savedAt:Date.now(), upd:Date.now(), cols:JSON.parse(JSON.stringify(_qCols||[]))}); }\n"
  "    delete _qsDelMap[_qLoadedId];     // r250: 지웠다 다시 저장하면 묘비 해제\n"
  "    _qsPend[_qLoadedId]=Date.now();   // r250: 아직 서버에 안 올라간 내 항목\n"
  "    saveAll();\n"
  "    _qsScheduleVerify();              // r250: 올린 뒤 서버에 실제로 남아 있는지 확인\n",
  1, "PERSIST_NEW"],

 ["ex.cols=JSON.parse(JSON.stringify(_qCols||[])); }\n",
  "ex.cols=JSON.parse(JSON.stringify(_qCols||[])); ex.upd=Date.now(); }\n",
  1, "PERSIST_UPD"],

 # ⑫ 삭제는 묘비로
 ["      quoteSaved=quoteSaved.filter(function(x){ return x.id!==id; });\n      _qsBlobDel(id); saveAll();",
  "      quoteSaved=quoteSaved.filter(function(x){ return x.id!==id; });\n"
  "      _qsDelMap[id]=Date.now(); delete _qsPend[id];   // r250: 삭제는 묘비로 — 다른 PC 사본이 되살리지 못하게\n"
  "      _qsBlobDel(id); saveAll();",
  1, "DEL"],
]

MARKER = ["<!-- test build r241 2026-10-19 -->", "<!-- test build r250 2026-10-27 -->"]

KEEP = ["_qsBlobPut(_qLoadedId, items)", "_qsBlobDel(id)", "_mtMergeFromServer()", "_mtScheduleVerify()"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp:
        raise SystemExit('R250 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r250(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for need in KEEP:
        if need not in s:
            raise SystemExit('R250 FAIL 사라짐: ' + need)
    for need in ['_qsMerge(', '_qsMergeFromServer', '_qsScheduleVerify', "'sched_quote_del'", '_qsPend[']:
        if need not in s:
            raise SystemExit('R250 FAIL 누락: ' + need)
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f:
            s = f.read()
        s = apply_r250(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(s)
        print('r250 applied:', path)
