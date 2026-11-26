// test_r286.js — 감사 > 저장된 명세표 묶음 처리 단추 이름
// 사용법: NODE_PATH=/home/claude/.npm-global/lib/node_modules node test_r286.js <절대경로 __T 주입본> <라벨>
const fs = require('fs');
const path = process.argv[2];
const label = process.argv[3] || '';
if (!path || path[0] !== '/') { console.error('절대경로를 넘기세요'); process.exit(2); }
const src = fs.readFileSync(path, 'utf8');
let pass = 0, fail = 0;
function t(name, cond) { if (cond) { pass++; } else { fail++; console.log('  ✗ ' + name); } }

t('[선택 인쇄] 단추', src.includes("_asBtn('선택 인쇄','asLPrintSel()','primary')"));
t('[선택 삭제] 단추', src.includes("_asBtn('선택 삭제','asLDelSel()','warn')"));
t('옛 이름 [고른 것 인쇄] 없음', !src.includes("_asBtn('고른 것 인쇄'"));
t('옛 이름 [고른 것 삭제] 없음', !src.includes("_asBtn('고른 것 삭제'"));
t('[선택 해제] 는 그대로', src.includes("_asBtn('선택 해제','asLSelNone()')"));
t('선택 인쇄 기능 유지', /window\.asLPrintSel\s*=\s*function/.test(src));
t('선택 삭제 기능 유지', /window\.asLDelSel\s*=\s*function/.test(src));
t('여러 업체 묶음 인쇄 유지', src.includes('_asDocHtmlMany'));
t('전체 선택 체크 유지', src.includes('id="asLAll"'));
t('N건 골랐습니다 안내 유지', src.includes('건 골랐습니다'));

console.log((label ? '[' + label + '] ' : '') + 'r286: ' + pass + '/' + (pass + fail));
process.exit(fail ? 1 : 0);
