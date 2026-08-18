# -*- coding: utf-8 -*-
# r57: 사업자번호 자동 하이픈 (XXX-XX-XXXXX)
R57_EDITS = [
("""_clxFld('bizNo','사업자번호',bz,1)""",
 """_clxFld('bizNo','사업자번호',bz,1,'oninput="clxBizInput(this)" onchange="clxBizBlur(this)"')"""),
("""  window.clxSave = function(orig){""",
 """  // 사업자번호 하이픈 자동 삽입 (XXX-XX-XXXXX)
  function _clxFmtBiz(v){
    var s=String(v||'');
    var d=s.replace(/\\D/g,'');
    if(!d) return s.trim()===''?'':s;
    if(/[^\\d\\s-]/.test(s)) return s;
    if(d.length<=3) return d;
    if(d.length<=5) return d.slice(0,3)+'-'+d.slice(3);
    if(d.length<=10) return d.slice(0,3)+'-'+d.slice(3,5)+'-'+d.slice(5);
    return s;   // 10자리 초과는 입력 그대로
  }
  window.clxBizInput = function(el){ if(el.selectionStart!==el.value.length) return; var f=_clxFmtBiz(el.value); if(f!==el.value) el.value=f; };
  window.clxBizBlur = function(el){ var f=_clxFmtBiz(el.value); if(f!==el.value) el.value=f; };
  window.clxSave = function(orig){"""),
("""    var bz=get('bizNo');
    var dupName=_findClientByBiz(bz, orig||null);""",
 """    var bz=_clxFmtBiz(get('bizNo'));
    var dupName=_findClientByBiz(bz, orig||null);"""),
]
def apply_r57(s, path):
    for i,(old,new) in enumerate(R57_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R57 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r57(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r56 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r56 2026-08-13 -->', '<!-- test build r57 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
