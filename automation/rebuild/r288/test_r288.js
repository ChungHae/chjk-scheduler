// r288 테스트 — 찍히는 글씨체를 양식 글꼴(바탕)에 맞춘다
// 사용법: NODE_PATH=/home/claude/.npm-global/lib/node_modules node test_r288.js <절대경로> <라벨>
const fs = require('fs');
const path = process.argv[2], label = process.argv[3] || '';
if (!path || path[0] !== '/') { console.error('절대경로를 넘기세요'); process.exit(2); }
const src = fs.readFileSync(path, 'utf8');
let pass = 0, fail = 0;
function t(n, c) { if (c) pass++; else { fail++; console.log('  ✗ ' + n); } }

t('전표 글꼴이 바탕 먼저', src.includes('font-family:Batang,"바탕",BatangChe,"바탕체",serif;'));
t('옛 바탕체 먼저 차례 없음', !src.includes('font-family:"바탕체",BatangChe,Batang'));
t('선으로 그린 양식도 바탕 먼저', src.includes('font-family="Batang, BatangChe, serif"'));
t('양식 그림은 페이지 전체 그대로', src.includes('as-pageform'));
t('칸 좌표 모델 그대로', src.includes('cVname') && src.includes('rowPad'));
t('자동 축소 그대로', src.includes('_asShrink') && src.includes('_asTwoLines'));

console.log((label ? '[' + label + '] ' : '') + 'r288: ' + pass + '/' + (pass + fail));
process.exit(fail ? 1 : 0);
