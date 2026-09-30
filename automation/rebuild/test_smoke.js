const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE=process.argv[2], LABEL=process.argv[3]||'?';
(async()=>{
  const b=await chromium.launch({});
  const pg=await (await b.newContext({timezoneId:'Asia/Seoul', viewport:{width:1400,height:900}})).newPage();
  await pg.route(/^https?:\/\//, r=>r.abort());
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e).slice(0,180)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);
  const P=[]; const ok=(n,c,e)=>P.push([n,!!c,e]);
  await pg.evaluate(()=>{
    document.getElementById('authGate').style.display='none';
    __T("_authUser={id:'chjk',name:'chjk',role:'admin'}"); __T("_fbDbUrl='https://stub'");
    __T("_fxLoaded=true"); __T("debouncedFbSave=function(){}"); __T("_fxSave=function(){}");
    __T("_fxSaveBig=async function(){}"); __T("_fxEnsureData=async function(){}");
    __T("showInfoModal=function(t,m){}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    __T(`(function(){
      clientList=[_cliMake('가나전기','111-11-11111','서울','')]; clientInfo={}; customClients=[];
      fxSalesInv=[{biz:'서울',date:'2025-01-10',vendor:'가나전기',vbiz:'111-11-11111',supply:1000000,tax:100000,total:1100000,no:'A1'}];
      fxDeposits=[]; fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={};
    })();`);
  });
  // 모든 주요 페이지를 한 번씩 그려본다
  const pages=['memo','weekly','clients','estimate','inventory','purchase','files','armatch','fx','cardsales','links','meeting','done','project'];
  for(const p of pages){
    const r=await pg.evaluate((pp)=>{ try{ __T("switchPage('"+pp+"')"); return 'ok'; }catch(e){ return 'ERR '+e.message; } }, p);
    ok('페이지 '+p+' 렌더', r==='ok', r);
    await pg.waitForTimeout(80);
  }
  // 회계 3탭
  for(const [p,t] of [['fx','ar'],['fxsum','sum'],['fxup','up']]){
    const r=await pg.evaluate((a)=>{ try{ __T("switchPage('"+a[0]+"')"); return __T("_fxTab"); }catch(e){ return 'ERR '+e.message; } }, [p,t]);
    ok('회계 '+p+' → _fxTab='+t, r===t, String(r));
    await pg.waitForTimeout(80);
  }
  const fns=['fxNyOpen','fxNyPrint','fxNyDocx','fxArPageGo','fxNyAssetPick','mtSaveReps','renderClientsPage','fxImportBank','fxAssignDep','fxSwitchTab'];
  const miss=await pg.evaluate((f)=>f.filter(x=>typeof window[x]!=='function'), fns);
  ok('핵심 함수 '+fns.length+'개 존재', miss.length===0, JSON.stringify(miss));
  console.log('=== ['+LABEL+'] 스모크 ===');
  let pass=0; P.forEach(([n,c,e])=>{ if(c)pass++; else console.log('  FAIL  '+n+'  << '+e); });
  console.log('통과 '+pass+'/'+P.length+' · pageerrors: '+(errs.length?errs.join(' | '):'없음'));
  await b.close(); process.exit((pass===P.length && !errs.length)?0:1);
})();
