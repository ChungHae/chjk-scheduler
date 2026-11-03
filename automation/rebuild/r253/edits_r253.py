# -*- coding: utf-8 -*-
# r253 (사용자 지시 2026-11-03): 자료 백업 — 자동 일일 스냅샷 + 백업 파일의 구멍 메우기
#
# 배경 (INCIDENT_2026-11-02_teamdata_test.md)
#   11-02 에 `teamdata_test` 노드가 통째로 다시 쓰이면서 '상태(state) 밖 키' 가 사라졌다.
#     sched_mail_cfg(메일 발송 설정) · sched_doc_assets(명판·인감) · sched_rules(내규) ·
#     sched_notice_seen(공지 확인) · sched_quote_saved_bak_*
#   그런데 ① Firebase 에 자동 백업이 전혀 없었고 ② [자료저장] 백업 파일은 `_fullBackupMain()` 에
#   손으로 적어 둔 상태 키만 담아서, 사라진 키들은 **백업 파일에도 없었다** — 되돌릴 방법이 없었다.
#
# 조치
#   ① `_bkEnsureDaily()` — 관리자가 접속하면 하루 1회 `teamdata_backup/<_FB_PATH>/<YYYY-MM-DD>` 에
#      상태 노드 전체 + 계정 노드를 복사해 둔다. **부모 노드(`teamdata_test`)에는 절대 쓰지 않는다.**
#      최근 14개 + 매월 1일분 6개월만 남기고 정리.
#   ② [자료저장] 백업 파일에 `extra` 추가 — 상태 밖 키를 shallow 로 훑어 **전부** 담는다
#      (앞으로 새로 생기는 키도 자동으로 들어간다). 불러오기도 `extra` 를 되살린다.
#   ③ 관리자 헤더에 [백업] 버튼 — 스냅샷 목록 · [지금 백업] · [내려받기] · **[지금 없는 키 되살리기]**
#      (이번 사고 같은 상황을 한 번에 복구. 있는 키는 건드리지 않는다.)
import io, sys

HELPERS = r"""  // ── r253: 자료 백업 (자동 일일 스냅샷 + 상태 밖 키 보관) ─────────────────
  //  11-02 사고: `teamdata_test` 노드가 통째로 다시 쓰여 상태 밖 키(메일 설정·명판/인감·내규)가
  //  사라졌는데 자동 백업이 없었고 백업 파일에도 그 키들이 없었다.
  //  여기서는 **자식 키/별도 노드만** 다룬다 — 부모 노드 PUT 은 하지 않는다.
  var _BK_ROOT = 'teamdata_backup';
  var _BK_KEEP = 14;                     // 최근 N일 + 매월 1일분 6개월 보관
  function _bkToday(){ var d = new Date(Date.now() + 9*3600*1000); return d.toISOString().slice(0,10); }   // 한국 날짜
  function _bkUrl(day){ return _fbDbUrl + '/' + _BK_ROOT + '/' + _FB_PATH + (day ? ('/' + day) : '') + '.json'; }
  function _bkFmtKb(n){ return (n >= 1024) ? ((n/1024).toFixed(1) + ' MB') : (n + ' KB'); }
  async function _bkExtraKeys(){         // 상태(state) 에 안 들어가는 키 = 백업 파일이 놓치던 것
    if(!_fbDbUrl) return [];
    var r = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '.json?shallow=true');
    if(!r || !r.ok) return [];
    var all = Object.keys((await r.json()) || {});
    var known = Object.keys(_fullBackupMain());
    return all.filter(function(k){ return known.indexOf(k) < 0 && k !== '_updatedAt'; });
  }
  async function _bkFetchExtras(){
    var out = {}, ks = await _bkExtraKeys();
    for(var i=0;i<ks.length;i++){
      try{
        var r = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '/' + ks[i] + '.json');
        if(r && r.ok){ var v = await r.json(); if(v != null) out[ks[i]] = v; }
      }catch(_e){}
    }
    return out;
  }
  async function _bkSnapshot(){
    if(!_fbDbUrl) throw new Error('동기화 연결이 필요합니다.');
    if(_isViewer()) throw new Error('조회 전용 계정은 백업할 수 없습니다.');
    var r = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '.json');
    if(!r || !r.ok) throw new Error('자료를 읽지 못했습니다 (HTTP ' + (r ? r.status : '네트워크') + ')');
    var state = await r.json();
    if(!state || Object.keys(state).length < 10) throw new Error('읽어 온 자료가 너무 적어 백업을 중단했습니다.');   // 빈 스냅샷 방지
    var acc = null;
    try{ var r2 = await _fbFetch(_fbDbUrl + '/' + _AUTH_BASE + '_accounts.json'); if(r2 && r2.ok) acc = await r2.json(); }catch(_e){}
    var day = _bkToday();
    var body = { at: Date.now(), day: day, by: ((_authUser && _authUser.name) || ''), keys: Object.keys(state).length,
                 kb: Math.round(JSON.stringify(state).length/1024), state: state };
    if(acc) body.accounts = acc;
    await _fbPutOk(_bkUrl(day), body, '자료 백업');
    try{ localStorage.setItem('sched_bk_day', day); }catch(_e){}
    return day;
  }
  async function _bkList(){
    if(!_fbDbUrl) return [];
    var r = await _fbFetch(_bkUrl('') + '?shallow=true');
    if(!r || !r.ok) return [];
    return Object.keys((await r.json()) || {}).filter(function(k){ return /^\d{4}-\d{2}-\d{2}$/.test(k); }).sort().reverse();
  }
  async function _bkPrune(){
    var days = await _bkList();
    if(days.length <= _BK_KEEP) return 0;
    var keep = {}, n = 0;
    days.slice(0, _BK_KEEP).forEach(function(d){ keep[d] = 1; });
    var sixAgo = new Date(Date.now() - 180*86400000).toISOString().slice(0,10);
    days.forEach(function(d){ if(/-01$/.test(d) && d >= sixAgo) keep[d] = 1; });     // 매월 1일분은 6개월
    for(var i=0;i<days.length;i++){
      if(keep[days[i]]) continue;
      try{ await _fbFetch(_bkUrl(days[i]), {method:'DELETE'}); n++; }catch(_e){}
    }
    return n;
  }
  async function _bkEnsureDaily(){       // 관리자가 접속하면 하루 1회 (조용히)
    try{
      if(!_fbDbUrl || !_fbLoadedOnce || !_isAdmin() || _isViewer()) return;
      var day = _bkToday();
      if(localStorage.getItem('sched_bk_day') === day) return;
      var r = await _fbFetch(_bkUrl(day) + '?shallow=true');
      if(r && r.ok && (await r.json()) != null){ try{ localStorage.setItem('sched_bk_day', day); }catch(_e){} return; }
      await _bkSnapshot();
      await _bkPrune();
    }catch(_e){}
  }
  async function _bkGet(day){
    var r = await _fbFetch(_bkUrl(day));
    if(!r || !r.ok) throw new Error('백업을 읽지 못했습니다 (HTTP ' + (r ? r.status : '네트워크') + ')');
    var v = await r.json();
    if(!v || !v.state) throw new Error('백업 내용이 비어 있습니다.');
    return v;
  }
  window.bkDownload = async function(day){
    try{
      var v = await _bkGet(day);
      var blob = new Blob([JSON.stringify(v)], {type:'application/json'});
      var url = URL.createObjectURL(blob); var a = document.createElement('a');
      a.href = url; a.download = 'chjk-snapshot-' + day + '.json'; a.click(); URL.revokeObjectURL(url);
    }catch(e){ showInfoModal('내려받기 실패', String(e && e.message || e)); }
  };
  window.bkRestoreMissing = async function(day){
    try{
      var v = await _bkGet(day);
      var r = await _fbFetch(_fbDbUrl + '/' + _FB_PATH + '.json?shallow=true');
      var now = (r && r.ok) ? ((await r.json()) || {}) : {};
      var miss = Object.keys(v.state).filter(function(k){ return now[k] === undefined && k !== '_updatedAt'; });
      if(!miss.length){ showInfoModal('되살릴 것 없음', day + ' 백업에 있는 키가 모두 지금도 있습니다.\n(이미 있는 키는 건드리지 않습니다.)'); return; }
      showConfirmModal('없는 키 되살리기',
        day + ' 백업에서 **지금 없는 키 ' + miss.length + '개**만 되살립니다.\n이미 있는 자료는 건드리지 않습니다.\n\n' + miss.join('\n'),
        async function(){
          var okN = 0, fail = [];
          for(var i=0;i<miss.length;i++){
            try{ await _fbPutOk(_fbDbUrl + '/' + _FB_PATH + '/' + miss[i] + '.json', v.state[miss[i]], miss[i]); okN++; }
            catch(e){ fail.push(miss[i]); }
          }
          showInfoModal('되살리기 완료', okN + '개를 되살렸습니다.' + (fail.length ? ('\n실패: ' + fail.join(', ')) : '') + '\n\nCtrl+F5 로 새로고침하세요.');
          try{ bkOpen(); }catch(_e){}
        }, '되살리기', '#b45309');
    }catch(e){ showInfoModal('되살리기 실패', String(e && e.message || e)); }
  };
  window.bkRunNow = async function(){
    var m = document.getElementById('bkMsg'); if(m) m.textContent = '백업 중…';
    try{ var d = await _bkSnapshot(); await _bkPrune(); if(m) m.innerHTML = '<span style="color:#15803d">' + esc(d) + ' 백업 완료</span>'; bkOpen(); }
    catch(e){ if(m) m.innerHTML = '<span style="color:#dc2626">' + esc(String(e && e.message || e)) + '</span>'; }
  };
  window.bkOpen = async function(){
    if(!_isAdmin()){ showInfoModal('권한', '자료 백업은 관리자만 볼 수 있습니다.'); return; }
    var ov = document.getElementById('bkOverlay');
    if(!ov){
      ov = document.createElement('div'); ov.id = 'bkOverlay';
      ov.style.cssText = 'position:fixed;inset:0;z-index:100064;background:rgba(15,23,42,.45);display:none;align-items:center;justify-content:center;padding:16px';
      document.body.appendChild(ov);
      ov.addEventListener('click', function(e){ if(e.target === ov) ov.style.display = 'none'; });
    }
    ov.innerHTML = '<div style="width:100%;max-width:560px;max-height:88vh;overflow:auto;background:#fff;border:1px solid #e0e4ea;border-radius:10px">'
      + '<div style="padding:12px 16px;border-bottom:2px solid #1B3A6B;display:flex;align-items:center;gap:8px">'
        + '<span style="font-size:15px;font-weight:700;color:#1B3A6B">자료 백업</span>'
        + '<span style="flex:1"></span>'
        + '<button class="btn" onclick="bkRunNow()">지금 백업</button>'
        + '<button class="btn" onclick="document.getElementById(\'bkOverlay\').style.display=\'none\'">닫기</button>'
      + '</div>'
      + '<div style="padding:14px 16px">'
        + '<div style="background:#f4f8fe;border:1px solid #d6e4f5;padding:9px 12px;font-size:11.5px;color:#374151;line-height:1.8;margin-bottom:10px">'
          + '관리자가 접속하면 <b>하루 한 번</b> 자동으로 자료를 통째로 복사해 둡니다(최근 14일 + 매월 1일분 6개월).<br>'
          + '파일로도 받아 두려면 <b>[내려받기]</b> — 회사 PC 에 보관하세요.<br>'
          + '자료가 사라졌을 때는 <b>[없는 키 되살리기]</b> — 지금 없는 것만 되돌리고 있는 자료는 건드리지 않습니다.'
        + '</div>'
        + '<div id="bkMsg" style="font-size:12px;color:#6b7280;min-height:18px;margin-bottom:6px">불러오는 중…</div>'
        + '<div id="bkList"></div>'
      + '</div></div>';
    ov.style.display = 'flex';
    try{
      var days = await _bkList();
      var el = document.getElementById('bkList'); if(!el) return;
      document.getElementById('bkMsg').textContent = days.length ? ('보관된 백업 ' + days.length + '개') : '';
      if(!days.length){ el.innerHTML = '<div style="padding:18px;text-align:center;color:#9ca3af;font-size:12.5px">아직 백업이 없습니다. [지금 백업] 을 눌러 주세요.</div>'; return; }
      el.innerHTML = days.map(function(d){
        var r = String(d).replace(/'/g, "\\'");
        return '<div style="display:flex;align-items:center;gap:8px;padding:8px 2px;border-bottom:1px solid #eef1f4">'
          + '<b style="font-size:13px;color:#14305c;min-width:92px">' + esc(d) + '</b>'
          + '<span style="flex:1"></span>'
          + '<button class="btn" style="padding:3px 10px;font-size:12px" onclick="bkDownload(\'' + r + '\')">내려받기</button>'
          + '<button class="btn" style="padding:3px 10px;font-size:12px" onclick="bkRestoreMissing(\'' + r + '\')">없는 키 되살리기</button>'
          + '</div>';
      }).join('');
    }catch(e){ var m2 = document.getElementById('bkMsg'); if(m2) m2.innerHTML = '<span style="color:#dc2626">' + esc(String(e && e.message || e)) + '</span>'; }
  };
"""

OPS = [
 # ① 헤더에 관리자 전용 [백업] 버튼
 ['    <button class="btn" id="btnExport" title="데이터를 JSON 파일로 저장합니다">자료저장</button>\n',
  '    <button class="btn" id="btnExport" title="데이터를 JSON 파일로 저장합니다">자료저장</button>\n'
  '    <button class="btn" id="btnBackupMgr" title="자동 일일 백업 · 스냅샷 관리" style="display:none" onclick="bkOpen()">백업</button>\n',
  1, 'HEADER'],

 # 인쇄할 때는 숨김
 ['      #btnExport { display: none !important; }\n',
  '      #btnExport, #btnBackupMgr { display: none !important; }\n',
  1, 'PRINT_CSS'],

 # ② 관리자에게만 보이기
 ["  function applyConfig() {\n    if (config.appTitle === '팀 스케줄러') config.appTitle = '업무 관리';\n",
  "  function applyConfig() {\n    if (config.appTitle === '팀 스케줄러') config.appTitle = '업무 관리';\n"
  "    try{ var _bkB = document.getElementById('btnBackupMgr'); if(_bkB) _bkB.style.display = _isAdmin() ? '' : 'none'; }catch(_e){}   // r253\n",
  1, 'APPLYCFG'],

 # ③ 로그인·로드 직후 하루 1회 자동 백업 예약
 ['      _fbLoadedOnce = true;   // 여기서부터 저장 허용 (로드 결과를 받은 뒤)\n',
  '      _fbLoadedOnce = true;   // 여기서부터 저장 허용 (로드 결과를 받은 뒤)\n'
  '      try{ setTimeout(_bkEnsureDaily, 15000); }catch(_e){}   // r253: 관리자 접속 시 하루 1회 자동 백업\n',
  1, 'DAILY_HOOK'],

 # ④ 헬퍼·창
 ['  function _fullBackupMain(){\n', HELPERS + '  function _fullBackupMain(){\n', 1, 'HELPERS'],

 # ⑤ [자료저장] 파일에 상태 밖 키(extra) 포함
 ["      var data = { version:3, full:true, exportedAt:new Date().toISOString(), main:main, blobs:blobs };\n",
  "      var _extra = {}; try{ _extra = await _bkFetchExtras(); }catch(_xe){}   // r253: 메일 설정·명판/인감·내규 등 상태 밖 키\n"
  "      var data = { version:3, full:true, exportedAt:new Date().toISOString(), main:main, blobs:blobs, extra:_extra };\n",
  1, 'EXPORT_EXTRA'],

 # ⑥ 불러오기에서 extra 되살리기
 ["            Object.keys(data.main).forEach(function(k){ save(k, data.main[k]); });\n",
  "            Object.keys(data.main).forEach(function(k){ save(k, data.main[k]); });\n"
  "            // r253: 상태 밖 설정 키(메일 설정·명판/인감·내규·공지 확인)도 되살린다\n"
  "            if(data.extra && _fbDbUrl){ for(var _ek in data.extra){ try{ await _fbPutOk(_fbDbUrl+'/'+_FB_PATH+'/'+_ek+'.json', data.extra[_ek], '설정 '+_ek); }catch(_xe2){} } }\n",
  1, 'IMPORT_EXTRA'],
]

MARKER = ["<!-- test build r252 2026-10-29 -->", "<!-- test build r253 2026-11-03 -->"]

NEED = ['_bkEnsureDaily', '_bkSnapshot', 'window.bkOpen', "'teamdata_backup'", 'btnBackupMgr', 'extra:_extra']
KEEP = ['_fullBackupMain()', '_qsMergeFromServer', '_mtMergeFromServer']


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp:
        raise SystemExit('R253 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r253(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for need in NEED:
        if need not in s:
            raise SystemExit('R253 FAIL 누락: ' + need)
    for need in KEEP:
        if need not in s:
            raise SystemExit('R253 FAIL 사라짐: ' + need)
    # 부모 노드 PUT 금지 (사고 재발 방지) — 백업 코드가 '<_FB_PATH>.json' 에 PUT 하지 않는지
    if "_fbPutOk(_fbDbUrl + '/' + _FB_PATH + '.json'" in s or '_fbPutOk(_fbDbUrl+"/"+_FB_PATH+".json"' in s:
        raise SystemExit('R253 FAIL 부모 노드 PUT 발견')
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f:
            s = f.read()
        s = apply_r253(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(s)
        print('r253 applied:', path)
