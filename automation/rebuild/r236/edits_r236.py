# -*- coding: utf-8 -*-
# r236 (사용자 보고 2026-10-16): "회의록 동시 작성이 안 된다".
#   원인: 회의록(sched_meetings)은 배열 통째로 저장(PATCH)된다. 두 사람이 몇 초 안에 각자 저장하면 나중 저장이 먼저 저장을
#         덮어쓴다(자기 포함 안 된 상대 항목이 사라짐). 2초 폴링·자기 저장 직후 1회 폴링 건너뜀(_fbSkipNext)·탭 숨김 시 폴링 중지가
#         겹치면 창이 몇 초 된다. 입력 중에는 화면 갱신을 건너뛰므로 사용자는 "동시에 쓰면 날아간다"고 느낀다.
#   조치: 항목 단위 병합(merge). 저장 직전 서버의 sched_meetings 를 받아 로컬과 **항목 id 로 합친 뒤** 올린다.
#     - 안건·업무 항목: 양쪽 합집합(id), 같은 id 면 upd(수정·완료 시각) 큰 쪽.
#     - 삭제: 묘비(tombstone) — 항목은 m.del[iid]=ts, 회의록은 sched_meetings_del[mid]=ts. 합칠 때 묘비에 있는 건 뺀다
#       (안 그러면 상대 사본에서 되살아남).
#     - 회의 머리(제목·날짜·상태 등)는 updatedAt 큰 쪽, 참석자는 합집합, 담당자별 업무는 이름별 합집합.
#     - 폴링으로 서버 상태를 받을 때도 로컬에 아직 안 올린 변경(_mtDirty)이 있으면 덮지 않고 합친다.
#     - 올린 뒤 2.5초 후 서버를 다시 읽어 내 항목이 빠졌으면(같은 순간 두 사람이 올린 경우) 다시 합쳐 올린다(_mtVerify).
import io, sys, json

JS = r"""  // ─── r236: 회의록 동시 작성 병합 ───
  function _mtArr(x){ if(Array.isArray(x)) return x; if(x&&typeof x==='object') return Object.keys(x).map(function(k){ return x[k]; }); return []; }
  function _mtTs(x){ return Number((x&&(x.upd||x.at))||0); }
  function _mtMergeItems(a, b, dmap){
    var map={}, ord=[];
    _mtArr(a).concat(_mtArr(b)).forEach(function(it){ if(!it||!it.id) return; if(dmap&&dmap[it.id]) return; var ex=map[it.id]; if(!ex){ map[it.id]=it; ord.push(it.id); } else if(_mtTs(it)>_mtTs(ex)) map[it.id]=it; });
    return ord.map(function(i){ return map[i]; });
  }
  function _mtMergeMeeting(l, s){
    var dm=Object.assign({}, s.del||{}, l.del||{});
    var base=(Number(l.updatedAt||0)>=Number(s.updatedAt||0))?l:s, other=(base===l)?s:l;
    var out=Object.assign({}, other, base);
    out.del=dm;
    out.agenda=_mtMergeItems(l.agenda, s.agenda, dm);
    var names=[], rmap={};
    _mtArr(l.reports).concat(_mtArr(s.reports)).forEach(function(r){ if(!r||!r.name) return; if(!rmap[r.name]){ rmap[r.name]={ name:r.name, items:[] }; names.push(r.name); } rmap[r.name].items=_mtMergeItems(rmap[r.name].items, r.items, dm); });
    out.reports=names.map(function(n){ return rmap[n]; });
    var att=[]; _mtArr(l.attendees).concat(_mtArr(s.attendees)).forEach(function(n){ if(n&&att.indexOf(n)<0) att.push(n); }); out.attendees=att;
    return out;
  }
  // local(내 사본) + server(서버 사본) → 합친 목록. 묘비(서버·로컬)는 합쳐서 _mtDelMap 에 둔다.
  function _mtMerge(local, server, serverDel){
    var del=Object.assign({}, (serverDel&&typeof serverDel==='object')?serverDel:{}, _mtDelMap||{}); _mtDelMap=del;
    var byId={}, order=[];
    _mtArr(server).concat(_mtArr(local)).forEach(function(m){ if(!m||!m.id||del[m.id]) return; if(!byId[m.id]){ byId[m.id]=m; order.push(m.id); } else byId[m.id]=_mtMergeMeeting(m, byId[m.id]); });
    return order.map(function(i){ return byId[i]; });
  }
  function _mtPull(server, serverDel){   // 서버 사본을 받을 때: 내가 지운 것(묘비)이 서버에 되살아나 있으면 걸러내고 다시 올린다
    var del=Object.assign({}, (serverDel&&typeof serverDel==='object')?serverDel:{}, _mtDelMap||{}); _mtDelMap=del;
    var loc={}; _mtArr(meetings).forEach(function(m){ if(m&&m.id) loc[m.id]=m; });
    var changed=false, out=[];
    _mtArr(server).forEach(function(m){
      if(!m||!m.id) return;
      if(del[m.id]){ changed=true; return; }
      var l=loc[m.id]; var ld=(l&&l.del)||{}; var sd=m.del||{}; var nd=Object.assign({}, sd, ld);
      if(Object.keys(nd).length){
        var f=function(it){ if(it&&it.id&&nd[it.id]){ changed=true; return false; } return true; };
        if(m.agenda) m.agenda=_mtArr(m.agenda).filter(f);
        if(m.reports) m.reports=_mtArr(m.reports).map(function(r){ if(r&&r.items) r.items=_mtArr(r.items).filter(f); return r; });
        if(Object.keys(ld).some(function(k){ return !sd[k]; })) changed=true;
        m.del=nd;
      }
      out.push(m);
    });
    if(changed){ _mtDirty=true; debouncedFbSave(); }
    return out;
  }
  async function _mtMergeFromServer(){
    if(!_fbDbUrl) return false;
    var r=await _fbFetch(_fbDbUrl+'/'+_FB_PATH+'/sched_meetings.json'); if(!r||!r.ok) return false;
    var s=await r.json();
    var r2=await _fbFetch(_fbDbUrl+'/'+_FB_PATH+'/sched_meetings_del.json'); var sd=(r2&&r2.ok)?(await r2.json()):null;
    meetings=_mtMerge(meetings, s, sd);
    save('sched_meetings', meetings); save('sched_meetings_del', _mtDelMap);
    return true;
  }
  function _mtIdSet(list){ var o={}; _mtArr(list).forEach(function(m){ if(!m||!m.id) return; o['m:'+m.id]=1; _mtArr(m.agenda).forEach(function(a){ if(a&&a.id) o[a.id]=1; }); _mtArr(m.reports).forEach(function(r){ _mtArr(r&&r.items).forEach(function(i){ if(i&&i.id) o[i.id]=1; }); }); }); return o; }
  var _mtVerifyTimer=null;
  function _mtScheduleVerify(){ if(_mtVerifyTimer) clearTimeout(_mtVerifyTimer); _mtVerifyTimer=setTimeout(_mtVerify, 2500); }
  async function _mtVerify(){   // 같은 순간 두 사람이 올렸으면 한쪽이 덮인다 → 서버에 내 항목이 다 있는지 확인하고 없으면 다시 합쳐 올린다
    _mtVerifyTimer=null;
    try{
      if(!_fbDbUrl || !_fbReady) return;
      var r=await _fbFetch(_fbDbUrl+'/'+_FB_PATH+'/sched_meetings.json'); if(!r||!r.ok) return;
      var s=await r.json(); var have=_mtIdSet(s), mine=_mtIdSet(meetings), miss=0;
      Object.keys(mine).forEach(function(k){ if(!have[k] && !_mtDelMap[k.replace(/^m:/,'')]) miss++; });
      // 내가 지운 것이 서버에 되살아나 있으면(상대가 묘비 없는 사본을 같은 순간 올림) 그것도 다시 합친다
      Object.keys(_mtDelMap||{}).forEach(function(mid){ if(have['m:'+mid]) miss++; });
      _mtArr(meetings).forEach(function(m){ Object.keys((m&&m.del)||{}).forEach(function(iid){ if(have[iid]) miss++; }); });
      if(miss){ _mtDirty=true; debouncedFbSave(); }
    }catch(_e){}
  }
"""

OPS = [
  ["  let meetings = load('sched_meetings') ?? [];",
   "  let meetings = load('sched_meetings') ?? [];\n  let _mtDelMap = load('sched_meetings_del') ?? {};   // r236 회의록 묘비(삭제 기록)\n  let _mtDirty = false;   // r236 아직 서버에 안 올린 회의록 변경이 있음", 1, "DECL"],
  ["    save('sched_meetings', meetings);   // r187",
   "    save('sched_meetings', meetings);   // r187\n    save('sched_meetings_del', _mtDelMap);   // r236", 1, "SAVEALL"],
  ["'sched_meetings','sched_fx_alias'", "'sched_meetings','sched_meetings_del','sched_fx_alias'", 2, "KEYS"],
  ["    meetings         = load('sched_meetings') ?? [];   // r187",
   "    meetings         = load('sched_meetings') ?? [];   // r187\n    _mtDelMap        = load('sched_meetings_del') ?? {};   // r236", 1, "RELOAD"],
  ["        sched_meetings: meetings,   // r187\n        sched_comments: schedComments,",
   "        sched_meetings: meetings,   // r187\n        sched_meetings_del: _mtDelMap,   // r236\n        sched_comments: schedComments,", 1, "PAYLOAD"],
  ["    _fbSkipNext = true;\n    const ts = Date.now();\n    try {\n      await _syncPost({",
   "    _fbSkipNext = true;\n    const _mtWasDirty = _mtDirty;   // r236\n    if (_mtWasDirty) { try { await _mtMergeFromServer(); } catch(_me) {} }   // r236: 올리기 전에 서버 회의록과 항목 단위로 합친다\n    const ts = Date.now();\n    try {\n      await _syncPost({", 1, "MERGE_BEFORE"],
  ["      });\n      _fbLastUpdatedAt = ts;",
   "      });\n      _fbLastUpdatedAt = ts;\n      if (_mtWasDirty) { _mtDirty = false; _mtScheduleVerify(); }   // r236", 1, "AFTER_POST"],
  ["      KEYS.forEach(k => { if (d[k] !== undefined) save(k, d[k]); });\n      // ── 바로가기(sched_links) 보호 ──",
   "      KEYS.forEach(k => { if (d[k] === undefined) return; if (k === 'sched_meetings') { save(k, _mtDirty ? _mtMerge(meetings, d[k], d.sched_meetings_del) : _mtPull(d[k], d.sched_meetings_del)); return; } if (k === 'sched_meetings_del') { save(k, Object.assign({}, d[k] || {}, _mtDelMap || {})); return; } save(k, d[k]); });   // r236: 안 올린 회의록 변경이 있으면 덮지 않고 합치고, 내 묘비는 지키며 받는다\n      // ── 바로가기(sched_links) 보호 ──", 1, "POLL"],
  ["  function _mtSave(){ save('sched_meetings', meetings);",
   JS + "  function _mtSave(){ _mtDirty=true; save('sched_meetings_del', _mtDelMap); save('sched_meetings', meetings);", 1, "MTSAVE"],
  ["function(){ meetings=meetings.filter(function(x){ return x.id!==id; }); _mtSave();",
   "function(){ _mtDelMap[id]=Date.now(); meetings=meetings.filter(function(x){ return x.id!==id; }); _mtSave();", 1, "DEL_MEETING"],
  ["    m.agenda=(m.agenda||[]).filter(function(x){ return x.id!==iid; });",
   "    m.del=m.del||{}; m.del[iid]=Date.now();   // r236 묘비\n    m.agenda=(m.agenda||[]).filter(function(x){ return x.id!==iid; });", 1, "DEL_ITEM"],
  ["    if(it.done){ it.done=false; it.doneAt=0; it.doneBy=''; } else { it.done=true; it.doneAt=Date.now(); it.doneBy=_mtMe(); }",
   "    if(it.done){ it.done=false; it.doneAt=0; it.doneBy=''; } else { it.done=true; it.doneAt=Date.now(); it.doneBy=_mtMe(); }\n    it.upd=Date.now();   // r236", 1, "TOGGLE"],
  ["      if(it.title!=null){ var p=_mtParseAgenda(v); it.title=p.title; it.text=p.text; } else it.text=v;",
   "      if(it.title!=null){ var p=_mtParseAgenda(v); it.title=p.title; it.text=p.text; } else it.text=v;\n      it.upd=Date.now();   // r236", 1, "EDIT"],
  ["<!-- test build r235 2026-10-14 -->", "<!-- test build r236 2026-10-16 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R236 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r236(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r236 브라우저 적용기 — edits_r236.py 의 OPS. r235(live 028d3574 / test 96f271fb) 위에 적용.",
             "function r236Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R236 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r236Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r236(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r236 applied:', path)
