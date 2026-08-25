# -*- coding: utf-8 -*-
# r146: [거래처 중복 원장 방지 + 병합 도구]
#  원인: 원장은 "사업자번호(있으면) 또는 'N|이름'"을 키로 묶고, 사업자번호가 없는
#  슬롯은 이름이 정확히 같은 사업자번호 슬롯에만 자동 병합된다. 그런데 이 "이름"
#  비교가 완전 일치(===)라서, 계산서상 이름과 미배정 매칭 시 등록/선택된 이름 사이에
#  공백(트림/중복 공백) 차이가 있으면 병합되지 않고 별도의 원장 행이 생긴다.
#  → 입금을 매칭해 새 행(잔액 0)은 생기지만, 원래 미수金이 있던 행은 그대로 남아
#    "잔액은 0이 됐는데 채권 연령이 안 바뀐다"처럼 보인다.
#  수정:
#  1) 자동 병합(N|이름 슬롯 → 사업자번호 슬롯, 기초이월 매칭)의 이름 비교를
#     공백 트림/중복공백 정규화 기준으로 완화 (안전한 수준의 자동 처리).
#  2) 관리자용 "중복 거래처 후보" 진단 패널 추가: 공백뿐 아니라 (주)/㈜ 등 법인
#     표기 차이, 대소문자까지 느슨하게 비교해 이름이 사실상 같은데 원장이 갈라진
#     쌍을 찾아 보여주고, 확인 후 한쪽으로 병합(계산서·입금·조정·기초이월·결제조건
#     전부 이관)하는 버튼 제공. 자동 병합은 아니며 관리자가 직접 확인 후 실행.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R146 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r146(s, path):
    # (1) 안전한 공백 정규화 헬퍼 + 자동 병합 비교 완화
    s = rep(s, "  // 사업장별 거래처 원장 구성 (key = 사업자번호 우선, 없으면 이름)",
            r"""  // r146: 공백 차이만 있는 이름을 같은 거래처로 취급 (안전한 수준의 정규화)
  function _fxNormWs(s){ return String(s||'').trim().replace(/\s+/g,' '); }
  // 사업장별 거래처 원장 구성 (key = 사업자번호 우선, 없으면 이름)""", 1, 'HELPERWS')
    s = rep(s, "Object.keys(map).forEach(function(ok){ if(!tgt && ok.indexOf('N|')!==0 && map[ok].name===nm) tgt=map[ok]; });",
            "Object.keys(map).forEach(function(ok){ if(!tgt && ok.indexOf('N|')!==0 && _fxNormWs(map[ok].name)===_fxNormWs(nm)) tgt=map[ok]; });", 1, 'MERGEWS')
    s = rep(s, "Object.keys(map).forEach(function(mk){ if(!target && map[mk].name===p[1]) target=map[mk]; });",
            "Object.keys(map).forEach(function(mk){ if(!target && _fxNormWs(map[mk].name)===_fxNormWs(p[1])) target=map[mk]; });", 1, 'OPENWS')

    # (2) 느슨한 정규화(법인표기·대소문자) + 후보 탐지 + 병합 도구 — _fxRenderArBody 앞에 삽입
    s = rep(s, "  function _fxRenderArBody(){",
            r"""  // r146: 관리자 진단용 — 법인표기(주/㈜ 등)·대소문자까지 무시한 느슨한 비교
  var _fxDupOpen=false;
  function _fxNormName(s){
    return String(s||'').replace(/\s+/g,'').replace(/\(주\)|㈜|\(유\)|\(사\)|\(재\)|주식회사|유한회사/g,'').toLowerCase();
  }
  function _fxDupCandidates(region){
    var rows = _fxLedgers(region==='all'?'all':region);
    var out=[];
    for(var i=0;i<rows.length;i++){
      for(var j=i+1;j<rows.length;j++){
        var a=rows[i], b=rows[j];
        if(a.rgn!==b.rgn || a.name===b.name) continue;
        var na=_fxNormName(a.name);
        if(na && na===_fxNormName(b.name)) out.push([a,b]);
      }
    }
    return out;
  }
  window.fxDupToggle = function(){ _fxDupOpen=!_fxDupOpen; _fxRenderArBody(); };
  function _fxDupPanelHtml(){
    var dups=_fxDupCandidates(_fxRegion);
    if(!dups.length) return '';
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;vertical-align:middle';
    var rows=dups.map(function(p){
      var a=p[0], b=p[1];
      return '<tr>'
        + '<td style="'+TD+'">'+(_fxRegion==='all'?_fxBizBadge(a.rgn):'')+'<b>'+esc(a.name)+'</b> <span style="color:#9ca3af">'+(a.vbiz||'사업자번호 없음')+' · 잔액 '+_fxFmt(a.bal)+'</span></td>'
        + '<td style="'+TD+';text-align:center;color:#9ca3af">↔</td>'
        + '<td style="'+TD+'"><b>'+esc(b.name)+'</b> <span style="color:#9ca3af">'+(b.vbiz||'사업자번호 없음')+' · 잔액 '+_fxFmt(b.bal)+'</span></td>'
        + '<td style="'+TD+';text-align:center;white-space:nowrap">'
        +   '<button type="button" class="btn" onclick="fxMergeDup(\''+a.rgn+'\',\''+a.key.replace(/'/g,"\\'")+'\',\''+b.key.replace(/'/g,"\\'")+'\')" style="font-size:11px;padding:2px 8px;border:1px solid #1B3A6B;color:#14305c;background:#fff;margin-right:4px">◀ A로 병합</button>'
        +   '<button type="button" class="btn" onclick="fxMergeDup(\''+b.rgn+'\',\''+b.key.replace(/'/g,"\\'")+'\',\''+a.key.replace(/'/g,"\\'")+'\')" style="font-size:11px;padding:2px 8px;border:1px solid #1B3A6B;color:#14305c;background:#fff">B로 병합 ▶</button>'
        + '</td></tr>';
    }).join('');
    return '<div style="background:#fff;border:1px solid #d6deea;margin-bottom:12px">'
      + '<div style="padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#14305c">중복 거래처 후보 '
      + '<span style="font-weight:400;color:#8a94a6">— 공백·괄호(주식회사/㈜ 등) 표기만 다르고 이름이 사실상 같은 거래처가 원장에 따로 잡혀 있으면 여기 나타납니다. 같은 회사가 맞을 때만 병합하세요 (되돌릴 수 없음).</span></div>'
      + '<div style="max-height:300px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+';text-align:left">거래처 A</th><th style="'+TH+'"></th><th style="'+TH+';text-align:left">거래처 B</th><th style="'+TH+'">병합</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div></div>';
  }
  window.fxMergeDup = function(rgn, keepKey, dropKey){
    if(!_isAdmin()) return;
    var rows=_fxLedgers(rgn);
    var keep=rows.find(function(r){ return r.key===keepKey; });
    var drop=rows.find(function(r){ return r.key===dropKey; });
    if(!keep || !drop) return;
    showConfirmModal('거래처 병합',
      '"'+drop.name+'"('+(drop.vbiz||'사업자번호 없음')+')의 계산서·입금·조정·기초이월·결제조건 내역을 '
      +'"'+keep.name+'"('+(keep.vbiz||'사업자번호 없음')+')(으)로 합칩니다.\n같은 회사가 맞는지 꼭 확인하세요. 되돌릴 수 없습니다.\n\n계속할까요?',
      function(){
        var kName=keep.name, kVbiz=keep.vbiz||'';
        drop.L.invs.forEach(function(e){ e.vendor=kName; e.vbiz=kVbiz; });
        drop.L.deps.forEach(function(e){ e.vendor=kName; e.vbiz=kVbiz; });
        drop.L.adjs.forEach(function(a2){ a2.vendor=kName; a2.vbiz=kVbiz; });
        var okKey=rgn+'|'+drop.name, nkKey=rgn+'|'+kName;
        if(fxOpenings[okKey]){
          var amt=Number(fxOpenings[okKey].amount)||0, asOf=fxOpenings[okKey].asOf;
          if(fxOpenings[nkKey]){
            fxOpenings[nkKey].amount=(Number(fxOpenings[nkKey].amount)||0)+amt;
            if(!fxOpenings[nkKey].asOf) fxOpenings[nkKey].asOf=asOf;
          } else { fxOpenings[nkKey]={amount:amt, asOf:asOf}; }
          delete fxOpenings[okKey];
        }
        var tKeyOld=rgn+'|'+drop.name, tKeyNew=rgn+'|'+kName;
        if(fxTerms[tKeyOld] && !fxTerms[tKeyNew]) fxTerms[tKeyNew]=fxTerms[tKeyOld];
        delete fxTerms[tKeyOld];
        _fxSaveBig().catch(function(_e){});
        _fxSave();
        _fxRenderArBody();
        showInfoModal('병합 완료', '"'+drop.name+'" 내역을 "'+kName+'"(으)로 합쳤습니다.');
      }, '병합', '#dc2626');
  };
  function _fxRenderArBody(){""", 1, 'DUPTOOL')

    # (3) 칩 줄에 "중복 거래처 후보" 칩 추가 + 패널을 noteHtml에 포함
    s = rep(s, """      if(notes.length) h+='<span onclick="fxNotesToggle()" style="cursor:pointer" title="클릭하면 어음 목록이 열립니다">'+_fxChip('어음', notes.length+'건'+(nSoon?(' · 7일 내 만기 '+nSoon):'')+(_fxNotesOpen?' ▲':' ▼'), false)+'</span>';
      chips.innerHTML=h;
    }
    var noteHtml = (_fxNotesOpen ? _fxNotesPanelHtml() : '') + (_fxExclOpen ? _fxExclPanelHtml() : '');""",
            """      if(notes.length) h+='<span onclick="fxNotesToggle()" style="cursor:pointer" title="클릭하면 어음 목록이 열립니다">'+_fxChip('어음', notes.length+'건'+(nSoon?(' · 7일 내 만기 '+nSoon):'')+(_fxNotesOpen?' ▲':' ▼'), false)+'</span>';
      if(_isAdmin()){
        var nDup=_fxDupCandidates(_fxRegion).length;
        if(nDup) h+='<span onclick="fxDupToggle()" style="cursor:pointer" title="이름이 사실상 같은 거래처가 원장에 따로 잡혀 있을 수 있습니다. 클릭하면 후보 목록이 열립니다">'+_fxChip('중복 거래처 후보', nDup+'쌍'+(_fxDupOpen?' ▲':' ▼'), false)+'</span>';
      }
      chips.innerHTML=h;
    }
    var noteHtml = (_fxNotesOpen ? _fxNotesPanelHtml() : '') + (_fxExclOpen ? _fxExclPanelHtml() : '') + (_isAdmin()&&_fxDupOpen ? _fxDupPanelHtml() : '');""", 1, 'CHIP')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r146(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r145 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r145 2026-08-25 -->', '<!-- test build r146 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
