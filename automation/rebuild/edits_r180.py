# -*- coding: utf-8 -*-
# r180: 체크(☐) 누르면 팝업 없이 바로 완료 (사용자 요청 2026-09-11)
#  · 종류별 기본 동작을 자동 적용: 미팅 → 일정 저장(날짜=적힌 날짜 없으면 작성일, 시간=적힌 시간 없으면 종일)
#    납품 → 일정 저장(시간 없음, 날짜=적힌 날짜 없으면 작성일, 완료 상태로) / 프로젝트 → 프로젝트 저장(시작=작성일, 종료=오늘)
#    담당자 줄(하위 '이름 010-…'·명함) → 업체를 알면 담당자 등록. 그 다음 취소선 처리.
#  · 완료 창(_mmCompleteOpen)은 더 이상 호출하지 않는다(코드는 남겨 둠).
#  · 상위 줄마다 [댓글] 버튼 — 누르면 입력칸이 그 줄의 하위 모드가 되어 어느 줄에든 계속 하위 글(코멘트)을 붙일 수 있다.
#    이미 완료돼 프로젝트로 저장된 줄에 붙이면 그 프로젝트의 기록(logs)에도 같이 들어간다.
# 적용 순서: r179 결과물에 python3 edits_r180.py index.html testpage/index.html
# 결과 git blob sha: live 7d5d870453e49c0c704c4109be00eac32b5cb435 / test e4215538d7668c8d6ea33f2f57d1737f15b2623f
# (r180/apply_r180.js 는 같은 치환을 브라우저에서 수행하는 JS 포팅)
import io, sys

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R180 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

AUTO = r'''
  // ── r180: 어느 상위 줄에든 댓글(하위 글) 붙이기 ──
  var _mmChildTarget=null;   // 입력칸이 붙을 상위 줄 id (없으면 마지막 미완료 상위 줄)
  window.mmReplyTo = function(id){
    var l=_mmFind(id); if(!l) return;
    _mmChildTarget=id; _mmChildMode=true; _mmSetChildUI();
    var inp=document.getElementById('mmInput'); if(inp){ try{ inp.focus(); }catch(_e){} }
  };
  function _mmTargetLabel(){
    var sub=document.querySelector('#mmInRow .mm-sub'); if(!sub) return;
    var t=_mmChildTarget?_mmFind(_mmChildTarget):null;
    sub.textContent = t ? ('└ '+String(t.text||'').slice(0,18)+(t.text.length>18?'…':'')) : '└ 하위';
  }
  // ── r180: 팝업 없이 바로 완료 — 종류별 기본 동작 자동 적용 ──
  function _mmCompleteAuto(l){
    var today=_mmToday(); var msgs=[];
    var kids=_mmChildren(l.id).filter(function(c){ return c.kind!=='contact' && !c.card; });
    var contacts=_mmContactsOf(l);
    try{
      if(l.kind==='meeting'){ _mmSaveSched(l, '미팅', (l.when&&l.when.date)||l.date||today, (l.when&&l.when.time)||''); msgs.push('일정 저장'); }
      else if(l.kind==='delivery'){ _mmSaveSched(l, '납품', (l.when&&l.when.date)||l.date||today, ''); msgs.push('납품 완료 저장'); }
      else if(l.kind==='project'){ _mmSaveProject(l, kids); msgs.push('프로젝트 저장'); }
      if(contacts.length && l.vendor){ var n=_mmSaveContacts(l, contacts); if(n) msgs.push('담당자 '+n+'명 등록'); }
    }catch(_e){ try{ showInfoModal('메모 완료', '저장 중 문제가 있었습니다: '+_e); }catch(_x){} }
    _mmMarkDone(l); _mmSave(); renderMemoPage(true);
  }
'''

def apply_r180(s, path):
    is_test = 'testpage' in path or '/test/' in path
    s = rep(s, "    if(l.owner!==me) return;\n    _mmCompleteOpen(l);\n  };",
               "    if(l.owner!==me) return;\n    _mmCompleteAuto(l);   // r180: 팝업 없이 바로 완료\n  };", 1, 'HOOK')
    s = rep(s, "  function _mmMarkDone(l){", AUTO + "  function _mmMarkDone(l){", 1, 'AUTO')
    # 납품은 시간 없이 그 날짜에 완료된 일정으로
    s = rep(s,
        "    var it={ id:uid(), memberId:myMemberId||'', ownerName:me, date:d, endDate:d, time:t||'종일', category:cat, bizName:l.vendor||'', title:l.text, note:'', done:false, src:'memo', memoId:l.id };",
        "    var isDlv=(cat==='납품');   // r180: 납품은 시간 없이 그 날짜에 완료된 일정으로\n"
        "    var it={ id:uid(), memberId:myMemberId||'', ownerName:me, date:d, endDate:d, time:(isDlv?'종일':(t||'종일')), category:cat, bizName:l.vendor||'', title:l.text, note:'', done:isDlv, src:'memo', memoId:l.id };",
        1, 'SAVE')
    # 안내 문구
    s = rep(s, "완료(☐)를 누를 때 일정·프로젝트·담당자 저장 여부를 정합니다. 완료된 줄은 24시간 뒤 사라집니다.",
               "완료(☐)를 누르면 바로 완료되며 미팅·납품은 일정으로, 프로젝트는 프로젝트로 저장됩니다. 완료된 줄은 24시간 뒤 사라집니다.", 1, 'HINT')
    s = rep(s, "      '· 완료(☐)하면 취소선+흐림, 24시간 뒤 사라짐. 다시 누르면 완료 취소.');",
               "      '· 완료(☐)하면 바로 완료(팝업 없음): 미팅·납품은 일정, 프로젝트는 프로젝트, 담당자 줄은 업체 담당자로 저장. 24시간 뒤 사라짐. 다시 누르면 완료 취소.');", 1, 'HELP')
    # 댓글 버튼(상위 줄, 내 줄) + 입력 대상 표시
    s = rep(s, "      h+='<button onclick=\"mmEditStart(\\''+l.id+'\\')\" title=\"수정\">'+_MM_SVG_EDIT+'</button>';",
               "      if(!l.parent) h+='<button onclick=\"mmReplyTo(\\''+l.id+'\\')\" title=\"이 줄에 하위 글(댓글) 붙이기\">'+_MM_SVG_REPLY+'</button>';   // r180\n"
               "      h+='<button onclick=\"mmEditStart(\\''+l.id+'\\')\" title=\"수정\">'+_MM_SVG_EDIT+'</button>';", 1, 'BTN')
    s = rep(s, "  var _MM_SVG_FB=", "  var _MM_SVG_REPLY='<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M9 17l-5-5 5-5\"/><path d=\"M20 18v-2a4 4 0 0 0-4-4H4\"/></svg>';   // r180 댓글\n  var _MM_SVG_FB=", 1, 'SVG')
    # 완료된 줄에도 댓글 버튼(프로젝트 기록 추가용) — mine && !l.done 블록 밖
    s = rep(s, "    if(mine && !l.done){\n      if(l.vendor || l.kind==='contact' || l.parent)",
               "    if(mine && l.done && !l.parent) h+='<button onclick=\"mmReplyTo(\\''+l.id+'\\')\" title=\"댓글 붙이기\">'+_MM_SVG_REPLY+'</button>';   // r180\n"
               "    if(mine && !l.done){\n      if(l.vendor || l.kind==='contact' || l.parent)", 1, 'BTN2')
    # _mmCommit: 대상 줄이 있으면 거기에, 완료+프로젝트 연결 줄이면 프로젝트 기록에도
    s = rep(s, "    if(child){ var lt=_mmLastTop(me); if(lt) parent=lt.id; }",
               "    if(child){ var tg=_mmChildTarget?_mmFind(_mmChildTarget):null; if(tg && tg.owner===me && !tg.parent) parent=tg.id; else { var lt=_mmLastTop(me); if(lt) parent=lt.id; } }   // r180", 1, 'COMMIT1')
    s = rep(s, "    memoLines.push(line);\n    _mmSave();\n    inp.value=''; _mmChildMode=false; _mmSetChildUI();",
               "    memoLines.push(line);\n"
               "    if(parent){ var pl2=_mmFind(parent); if(pl2 && pl2.done && pl2.linked && pl2.linked.proj){   // r180: 완료된 프로젝트 줄의 댓글은 프로젝트 기록으로\n"
               "      var pj=(projectsList||[]).find(function(x){ return x.id===pl2.linked.proj; });\n"
               "      if(pj){ pj.logs=pj.logs||[]; pj.logs.push({ id:'lg'+now+'_'+Math.random().toString(36).slice(2,6), date:_mmToday(), text:text, ts:now, done:false }); pj.updatedAt=now; _projSave(); }\n"
               "      if(!line.done){ line.done=true; line.doneAt=now; } } }\n"
               "    _mmSave();\n    inp.value=''; _mmChildMode=false; _mmChildTarget=null; _mmSetChildUI();", 1, 'COMMIT2')
    s = rep(s, "  function _mmSetChildUI(){ var r=document.getElementById('mmInRow'); if(r) r.classList.toggle('mm-in-child', _mmChildMode); }",
               "  function _mmSetChildUI(){ var r=document.getElementById('mmInRow'); if(r) r.classList.toggle('mm-in-child', _mmChildMode); if(!_mmChildMode) _mmChildTarget=null; _mmTargetLabel(); }", 1, 'UI')
    if is_test:
        s = rep(s, "<!-- test build r179 2026-09-10 -->", "<!-- test build r180 2026-09-11 -->", 1, 'MARKER')
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r180(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r180 applied:', path)
