# -*- coding: utf-8 -*-
# r123: [매입매출 2단계] 기존 앱 누적본 이관 + 대용량 분리 저장.
#  - 계산서·입금(대용량)은 메인 동기화에서 분리 → Firebase `{_FB_PATH}_fx/{키}.json` 블롭
#    (견적 원장 _qBlob 패턴과 동일). 별칭·조정·결제조건 등 소용량은 메인 동기화 유지.
#  - 누적본 zip 이관: JSZip(cdnjs) + SheetJS. 파일명 CP949/UTF-8 모두 처리.
#    거래처 파일(서울/화성) → 계산서·입금 추출, 설정 5종(별칭/예외/제외/기준/재배정) 자동 인식.
#    재이관 안전(거래처별 legacy 데이터 교체, 설정은 키 병합).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R123 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, start, end, repl, label):
    i1 = s.find(start)
    if i1 < 0 or s.find(start, i1+1) >= 0: raise SystemExit('R123 FAIL %s start' % label)
    i2 = s.find(end, i1)
    if i2 < 0: raise SystemExit('R123 FAIL %s end' % label)
    return s[:i1] + repl + s[i2:]

FX_JS = r"""  // ─── 매입매출(신) (r122 골격 → r123 이관·분리 저장) ──────────────
  var _fxTab = 'ar';
  var _fxLoaded = false, _fxLoading = null;
  var _fxBlobCache = {};
  // 대용량(계산서·입금)은 메인 동기화와 분리된 Firebase 블롭에 저장 (견적 원장 패턴)
  async function _fxBlobPut(key, rows){
    if(_isViewer()) return;
    if(!_fbDbUrl) throw new Error('동기화 연결 필요');
    await _fbPutOk(_fbDbUrl+'/'+_FB_PATH+'_fx/'+key+'.json', rows, '매입매출 자료');
    try{ _fxBlobCache[key]=JSON.parse(JSON.stringify(rows)); }catch(_e){ delete _fxBlobCache[key]; }
  }
  async function _fxBlobGet(key){
    if(!_fbDbUrl) return null;
    if(key in _fxBlobCache){ try{ return JSON.parse(JSON.stringify(_fxBlobCache[key])); }catch(_e){} }
    try{
      var r=await _fbFetch(_fbDbUrl+'/'+_FB_PATH+'_fx/'+key+'.json');
      if(!r.ok) return null;
      var d=await r.json();
      if(d!=null){ try{ _fxBlobCache[key]=JSON.parse(JSON.stringify(d)); }catch(_e){} }
      return d;
    }catch(_e){ return null; }
  }
  async function _fxEnsureData(force){
    if(_fxLoaded && !force) return;
    if(_fxLoading && !force) return _fxLoading;
    _fxLoading = (async function(){
      var ks=['sales_서울','sales_화성','purch_서울','purch_화성','dep_서울','dep_화성'];
      if(force) ks.forEach(function(k){ delete _fxBlobCache[k]; });
      var got={};
      for(var i=0;i<ks.length;i++){ got[ks[i]] = (await _fxBlobGet(ks[i])) || []; }
      fxSalesInv = got['sales_서울'].concat(got['sales_화성']);
      fxPurchInv = got['purch_서울'].concat(got['purch_화성']);
      fxDeposits = got['dep_서울'].concat(got['dep_화성']);
      _fxLoaded = true;
    })();
    try{ await _fxLoading; } finally { _fxLoading = null; }
  }
  async function _fxSaveBig(){
    var jobs=[];
    ['서울','화성'].forEach(function(b){
      jobs.push(_fxBlobPut('sales_'+b, fxSalesInv.filter(function(e){ return e.biz===b; })));
      jobs.push(_fxBlobPut('purch_'+b, fxPurchInv.filter(function(e){ return e.biz===b; })));
      jobs.push(_fxBlobPut('dep_'+b,   fxDeposits.filter(function(e){ return e.biz===b; })));
    });
    for(var i=0;i<jobs.length;i++){ await jobs[i]; }
  }
  function _fxSave(){   // 소용량 설정만 메인 동기화로
    save('sched_fx_alias', fxAlias);
    save('sched_fx_openings', fxOpenings);
    save('sched_fx_adjusts', fxAdjusts);
    save('sched_fx_terms', fxTerms);
    save('sched_fx_excluded', fxExcluded);
    localStorage.setItem('sched_local_ts', Date.now().toString());
    try{ debouncedFbSave(); }catch(_e){}
  }
  function _ensureJsZip(){
    if(window.JSZip) return Promise.resolve();
    if(window._jszipLoading) return window._jszipLoading;
    window._jszipLoading = new Promise(function(res,rej){
      var sc=document.createElement('script');
      sc.src='https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
      sc.onload=function(){ res(); };
      sc.onerror=function(){ rej(new Error('zip 라이브러리 로드 실패')); };
      document.head.appendChild(sc);
    });
    return window._jszipLoading;
  }
  // 날짜 정규화 → 'YYYY-MM-DD' (Date 객체·문자열·다양한 구분자)
  function _fxD(v){
    if(v==null || v==='') return null;
    if(v instanceof Date){
      if(isNaN(v.getTime())) return null;
      var y=v.getFullYear(), m=v.getMonth()+1, d=v.getDate();
      if(v.getHours()>=12 && typeof v.getTimezoneOffset==='function' && v.getTimezoneOffset()<0){ /* KST에서 UTC자정 보정 불필요 */ }
      return y+'-'+(m<10?'0':'')+m+'-'+(d<10?'0':'')+d;
    }
    var s=String(v).trim().replace(/[./]/g,'-').replace(/\s.*$/,'');
    var m2=s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if(!m2) return null;
    return m2[1]+'-'+(m2[2].length<2?'0':'')+m2[2]+'-'+(m2[3].length<2?'0':'')+m2[3];
  }
  function _fxN(v){   // 금액 정규화
    if(v==null || v==='') return null;
    if(typeof v==='number') return isFinite(v)?v:null;
    var n=Number(String(v).replace(/[,\s원]/g,''));
    return isFinite(n)?n:null;
  }
  window.fxSwitchTab = function(t){ _fxTab = t; renderFxPage(); };
  function _fxFmt(n){ return (Number(n)||0).toLocaleString(); }
  function renderFxPage(){
    var body = document.getElementById('fxBody'); if(!body) return;
    document.querySelectorAll('#fxSubTabs .pf-btn').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });
    var meta = document.getElementById('fxMeta');
    if(meta) meta.textContent = _fxLoaded ? ('매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건') : '';
    var _empty = function(msg){ return '<div style="text-align:center;padding:56px 20px;color:#b6bec9;font-size:13px;line-height:1.9">'+msg+'</div>'; };
    if(_fxTab==='ar' || _fxTab==='sum'){
      body.innerHTML = '<div style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">자료 불러오는 중…</div>';
      _fxEnsureData().then(function(){
        if(_fxTab!=='ar' && _fxTab!=='sum') return;
        if(meta) meta.textContent = '매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';
        if(!fxSalesInv.length && !fxDeposits.length && !fxPurchInv.length){
          body.innerHTML = _empty('자료가 아직 없습니다.<br><b style="color:#5b7ba6">자료 업로드</b> 탭에서 기존 앱 누적본(zip)을 가져오거나 계산서·입금 자료를 올려주세요.');
          return;
        }
        // r123: 이관 검증용 사업장 요약 (미수 원장 화면은 다음 단계)
        var rows=['서울','화성'].map(function(b){
          var sv=fxSalesInv.filter(function(e){return e.biz===b;});
          var dp=fxDeposits.filter(function(e){return e.biz===b;});
          var pv=fxPurchInv.filter(function(e){return e.biz===b;});
          var vend={}; sv.forEach(function(e){ vend[e.vendor]=1; }); dp.forEach(function(e){ if(e.vendor) vend[e.vendor]=1; });
          var sSum=sv.reduce(function(a,e){return a+(e.total||0);},0);
          var dSum=dp.reduce(function(a,e){return a+(e.amount||0);},0);
          return '<tr>'
            + '<td style="padding:9px 12px;border-bottom:1px solid #eef2f7;font-weight:700;color:#14305c">'+b+'</td>'
            + '<td style="padding:9px 12px;border-bottom:1px solid #eef2f7;text-align:center">'+Object.keys(vend).length+'</td>'
            + '<td style="padding:9px 12px;border-bottom:1px solid #eef2f7;text-align:right">'+sv.length+'건 · '+_fxFmt(sSum)+'</td>'
            + '<td style="padding:9px 12px;border-bottom:1px solid #eef2f7;text-align:right">'+dp.length+'건 · '+_fxFmt(dSum)+'</td>'
            + '<td style="padding:9px 12px;border-bottom:1px solid #eef2f7;text-align:right">'+_fxFmt(sSum-dSum)+'</td>'
            + '<td style="padding:9px 12px;border-bottom:1px solid #eef2f7;text-align:center">'+pv.length+'건</td>'
            + '</tr>';
        }).join('');
        var TH='padding:9px 12px;background:#fafafa;color:#888;font-weight:500;font-size:12px;border-bottom:2px solid #d3dce6;white-space:nowrap';
        body.innerHTML =
          '<div style="font-size:12px;color:#8a94a6;margin-bottom:10px">이관 자료 요약 — 거래처별 미수 원장 화면은 다음 단계(r124)에서 붙습니다. 합계는 부가세 포함 기준.</div>'
          + '<div style="background:#fff;border:1px solid #d6deea;max-width:860px"><table style="width:100%;border-collapse:collapse;font-size:12.5px">'
          + '<thead><tr><th style="'+TH+';text-align:left">사업장</th><th style="'+TH+'">거래처 수</th><th style="'+TH+';text-align:right">매출 계산서</th><th style="'+TH+';text-align:right">입금·어음</th><th style="'+TH+';text-align:right">차액(총미수)</th><th style="'+TH+'">매입 계산서</th></tr></thead>'
          + '<tbody>'+rows+'</tbody></table></div>'
          + '<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">설정: 별칭 '+Object.keys(fxAlias).length+'건 · 조정 '+fxAdjusts.length+'건 · 결제조건 '+Object.keys(fxTerms).length+'건 · 제외 거래처 '+fxExcluded.length+'곳</div>';
      });
      return;
    }
    // 자료 업로드 탭
    body.innerHTML =
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;max-width:980px">'
      + [['기존 앱 누적본 가져오기','legacy','입출금 앱 누적자료 zip (거래처 파일·설정표 자동 인식, 재업로드 안전)', true],
         ['홈택스 매출 계산서','sales','매출 세금계산서 목록 엑셀 (다음 단계 연결)', false],
         ['홈택스 매입 계산서','purch','매입 세금계산서 목록 엑셀 (다음 단계 연결)', false],
         ['은행 입금·어음 내역','bank','은행 거래내역·어음 엑셀 (다음 단계 연결)', false]]
        .map(function(x){
          var btn = x[3]
            ? '<label class="btn" style="display:inline-block;font-size:12px;padding:5px 14px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;cursor:pointer">파일 선택…<input type="file" accept=".zip" style="display:none" onchange="fxImportLegacy(this)"></label>'
            : '<button type="button" class="btn" disabled style="font-size:12px;padding:5px 14px;border:1px solid #dfe5ec;color:#a8b3c0;background:#f4f6f9;cursor:default">다음 단계</button>';
          return '<div style="background:#fff;border:1px solid #d6deea;padding:16px 18px">'
            + '<div style="font-size:13px;font-weight:700;color:#14305c;margin-bottom:4px">'+x[0]+'</div>'
            + '<div style="font-size:11.5px;color:#8a94a6;margin-bottom:10px">'+x[2]+'</div>'
            + btn + '</div>';
        }).join('')
      + '</div>'
      + '<div id="fxUpResult" style="margin-top:14px;max-width:980px"></div>';
  }
  // ── 누적본 zip 이관 ──
  window.fxImportLegacy = async function(inp){
    var file = inp.files && inp.files[0];
    inp.value='';
    if(!file) return;
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 이관할 수 없습니다.'); return; }
    var out = document.getElementById('fxUpResult');
    function log(html){ if(out) out.innerHTML = '<div style="background:#fff;border:1px solid #d6deea;padding:14px 16px;font-size:12.5px;color:#374151;line-height:1.8">'+html+'</div>'; }
    try{
      log('라이브러리 로드 중…');
      await _ensureJsZip(); await _ensureXlsxLib();
      await _fxEnsureData();
      log('압축 해제 중…');
      var buf = await file.arrayBuffer();
      var dec$ = null;
      var zip = await JSZip.loadAsync(buf, { decodeFileName: function(bytes){
        try{ return new TextDecoder('utf-8',{fatal:true}).decode(bytes); }
        catch(_e){ try{ return new TextDecoder('euc-kr').decode(bytes); }catch(_e2){ return String.fromCharCode.apply(null, bytes); } }
      }});
      var names = Object.keys(zip.files).filter(function(n){ return !zip.files[n].dir; });
      var vendFiles=[], setFiles=[], skipped=[];
      names.forEach(function(n){
        var base = n.split('/').pop();
        if(/^_?(거래처별칭표|예외처리표|제외거래처표|거래처기준설정표|입금재배정표)/.test(base.replace(/^_/,'')) || /별칭표|예외처리표|제외거래처표|기준설정표|입금재배정표/.test(base)){ setFiles.push(n); return; }
        if(/(서울|화성)\)/.test(base) && /\((\d{3}-\d{2}-\d{5})\)/.test(base) && /\.xlsx?$/i.test(base)){ vendFiles.push(n); return; }
        skipped.push(base);
      });
      if(!vendFiles.length && !setFiles.length){ log('<b style="color:#dc2626">인식할 수 있는 파일이 없습니다.</b> 누적자료 zip(서울/화성 거래처 파일) 또는 설정표 zip을 올려주세요.'); return; }
      // 1) 거래처 파일 → 계산서·입금 (재이관 안전: 해당 거래처의 legacy 데이터 교체)
      var nInv=0, nDep=0, nVend=0, errs=[];
      for(var i=0;i<vendFiles.length;i++){
        var n=vendFiles[i], base=n.split('/').pop();
        if(i%25===0) log('거래처 파일 처리 중… ('+(i+1)+'/'+vendFiles.length+')');
        var m = base.match(/(서울|화성)\)\s*(.+?)\s*\((\d{3}-\d{2}-\d{5})\)\s*\.xlsx?$/i);
        if(!m){ skipped.push(base); continue; }
        var biz=m[1], vendor=m[2].trim(), vbiz=m[3];
        try{
          var ab = await zip.files[n].async('arraybuffer');
          var wb = XLSX.read(ab, {type:'array', cellDates:true});
          var ws = wb.Sheets[wb.SheetNames[0]];
          var rows = XLSX.utils.sheet_to_json(ws, {header:1, raw:true, defval:null});
          // 기존 legacy 데이터 제거 (이 거래처)
          var keyf=function(e){ return !(e.src==='legacy' && e.biz===biz && e.vbiz===vbiz); };
          fxSalesInv = fxSalesInv.filter(keyf);
          fxDeposits = fxDeposits.filter(function(e){ return !(e.src==='legacy' && e.biz===biz && (e.srcv ? e.srcv===vbiz : e.vendor===vendor)); });
          var seq=0, dseq=0;
          for(var r=2;r<rows.length;r++){
            var row=rows[r]||[];
            var idate=_fxD(row[0]), sup=_fxN(row[2]);
            if(idate && sup!=null && sup!==0){
              var tax=Math.round(sup*0.1), tot=sup+tax;
              fxSalesInv.push({ id:'L|'+biz+'|'+vbiz+'|'+idate+'|'+sup+'|'+(seq++), biz:biz, date:idate,
                                vendor:vendor, vbiz:vbiz, supply:sup, tax:tax, total:tot, src:'legacy',
                                note:(row[10]!=null?String(row[10]).trim():'') });
              nInv++;
            }
            var ddate=_fxD(row[7]), amt=_fxN(row[8]);
            if(ddate && amt!=null && amt!==0){
              fxDeposits.push({ id:'L|'+biz+'|'+vbiz+'|'+ddate+'|'+amt+'|'+(dseq++), biz:biz, date:ddate,
                                amount:amt, payer:vendor+' (이관)', vendor:vendor, vbiz:vbiz, srcv:vbiz,
                                kind:'bank', bank:(row[6]!=null?String(row[6]).trim():''), src:'legacy' });
              nDep++;
            }
          }
          nVend++;
        }catch(e){ errs.push(base+': '+(e&&e.message||e)); }
      }
      // 2) 설정표
      var setCnt={alias:0, adj:0, excl:0, terms:0, re:0};
      for(var j=0;j<setFiles.length;j++){
        var sn=setFiles[j], sb=sn.split('/').pop();
        try{
          var ab2 = await zip.files[sn].async('arraybuffer');
          var wb2 = XLSX.read(ab2, {type:'array', cellDates:true});
          var ws2 = wb2.Sheets[wb2.SheetNames[0]];
          var rw = XLSX.utils.sheet_to_json(ws2, {header:1, raw:true, defval:null});
          if(/별칭표/.test(sb)){
            for(var a=1;a<rw.length;a++){ var r1=rw[a]||[];
              var bz=r1[0], py=r1[1], tg=r1[2];
              if(bz && py && tg){ fxAlias[String(bz).trim()+'|'+String(py).trim()] = String(tg).split(',')[0].trim(); setCnt.alias++; }
            }
          } else if(/예외처리표/.test(sb)){
            for(var a2=1;a2<rw.length;a2++){ var r2=rw[a2]||[];
              var d2=_fxD(r2[3]), am2=_fxN(r2[4]);
              if(r2[0] && r2[1] && d2 && am2){
                var exid='EX|'+String(r2[0]).trim()+'|'+String(r2[2]||'').trim()+'|'+d2+'|'+am2;
                if(!fxAdjusts.some(function(x){ return x.id===exid; })){
                  fxAdjusts.push({ id:exid, biz:String(r2[0]).trim(), date:d2, vendor:String(r2[1]).trim(),
                                   vbiz:String(r2[2]||'').trim(), amount:-am2, memo:'예외처리: '+String(r2[5]||'').trim(), author:'이관' });
                  setCnt.adj++;
                }
              }
            }
          } else if(/제외거래처표/.test(sb)){
            for(var a3=1;a3<rw.length;a3++){ var r3=rw[a3]||[];
              if(r3[0] && r3[1]){
                var ex={ biz:String(r3[0]).trim(), vendor:String(r3[1]).trim(), vbiz:String(r3[2]||'').trim(), reason:String(r3[3]||'').trim() };
                if(!fxExcluded.some(function(x){ return x.biz===ex.biz && x.vendor===ex.vendor; })){ fxExcluded.push(ex); setCnt.excl++; }
              }
            }
          } else if(/기준설정표/.test(sb)){
            for(var a4=1;a4<rw.length;a4++){ var r4=rw[a4]||[];
              if(r4[0] && r4[1] && r4[3]){ fxTerms[String(r4[0]).trim()+'|'+String(r4[1]).trim()] = String(r4[3]).trim(); setCnt.terms++; }
            }
          } else if(/입금재배정표/.test(sb)){
            for(var a5=1;a5<rw.length;a5++){ var r5=rw[a5]||[];
              var rd=_fxD(r5[0]), ra=_fxN(r5[1]);
              var wrongV=String(r5[4]||'').trim(), rightV=String(r5[5]||'').trim(), rightB=String(r5[3]||'').trim();
              if(rd && ra && wrongV && rightV && wrongV!==rightV){
                fxDeposits.forEach(function(e){
                  if(e.src==='legacy' && e.date===rd && e.amount===ra && e.vendor===wrongV){ e.vendor=rightV; e.vbiz=rightB; setCnt.re++; }
                });
              }
            }
          }
        }catch(e2){ errs.push(sb+': '+(e2&&e2.message||e2)); }
      }
      // 3) 저장
      log('저장 중… (Firebase)');
      await _fxSaveBig();
      _fxSave();
      _fxLoaded = true;
      var meta=document.getElementById('fxMeta');
      if(meta) meta.textContent = '매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';
      var html = '<b style="color:#15803d">이관 완료</b> — 거래처 '+nVend+'곳 · 계산서 '+nInv+'건 · 입금 '+nDep+'건';
      var setLine=[];
      if(setCnt.alias) setLine.push('별칭 '+setCnt.alias);
      if(setCnt.adj) setLine.push('예외→조정 '+setCnt.adj);
      if(setCnt.excl) setLine.push('제외 '+setCnt.excl);
      if(setCnt.terms) setLine.push('결제조건 '+setCnt.terms);
      if(setCnt.re) setLine.push('입금 재배정 '+setCnt.re);
      if(setLine.length) html += '<br>설정: '+setLine.join(' · ');
      if(skipped.length) html += '<br><span style="color:#9ca3af">인식 제외 '+skipped.length+'개: '+esc(skipped.slice(0,8).join(', '))+(skipped.length>8?' 외':'')+'</span>';
      if(errs.length) html += '<br><span style="color:#dc2626">오류 '+errs.length+'건: '+esc(errs.slice(0,5).join(' / '))+'</span>';
      html += '<br><span style="color:#8a94a6">미수 현황 탭에서 사업장 요약을 확인하세요. 같은 zip을 다시 올려도 중복되지 않습니다.</span>';
      log(html);
    }catch(e){
      log('<b style="color:#dc2626">이관 실패:</b> '+esc(String(e&&e.message||e)));
    }
  };
"""

def apply_r123(s, path):
    # (1) 대용량 3종: 선언에서 localStorage 로드 제거 (블롭 저장으로 전환)
    s = rep(s, """  let fxSalesInv  = load('sched_fx_sales')    ?? [];  // 매출 세금계산서 [{id,date,vendor,supply,tax,total,no}]
  let fxPurchInv  = load('sched_fx_purch')    ?? [];  // 매입 세금계산서 (구조 동일)
  let fxDeposits  = load('sched_fx_deposits') ?? [];  // 입금 [{id,date,amount,payer,vendor}]""",
 """  let fxSalesInv  = [];  // 매출 세금계산서 — 대용량: Firebase _fx 블롭 저장 (r123)
  let fxPurchInv  = [];  // 매입 세금계산서 — 〃
  let fxDeposits  = [];  // 입금·어음 — 〃""", 1, 'D1')
    # (2) doFbSave 페이로드에서 대용량 3종 제거
    s = rep(s, """        sched_fx_sales: fxSalesInv,
        sched_fx_purch: fxPurchInv,
        sched_fx_deposits: fxDeposits,
""", '', 1, 'D2')
    # (3) reloadState 에서 대용량 3종 제거
    s = rep(s, """    fxSalesInv       = load('sched_fx_sales')    ?? [];
    fxPurchInv       = load('sched_fx_purch')    ?? [];
    fxDeposits       = load('sched_fx_deposits') ?? [];
""", '', 1, 'D3')
    # (4) r122 골격 JS 전체를 r123 구현으로 교체
    s = cut(s, '  // ─── 매입매출(신) 페이지 (r122 골격) ──────────────────',
            '  function parseExcelDate(excelDate) {', FX_JS, 'JS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r123(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r122 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r122 2026-08-21 -->', '<!-- test build r123 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
