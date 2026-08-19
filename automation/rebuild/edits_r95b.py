# -*- coding: utf-8 -*-
# r95b: _pmRender 재진입 가드. (재작성본 v2)

OLD = """  function _pmRender(force){
    var box=document.getElementById('projMemoBoard'); if(!box) return;"""
NEW = """  var _pmRendering=false, _pmRenderQueued=false;
  function _pmRender(force){
    if(_pmRendering){ _pmRenderQueued=true; return; }
    _pmRendering=true;
    try{ _pmRenderCore(force); }
    finally{
      _pmRendering=false;
      if(_pmRenderQueued){ _pmRenderQueued=false; setTimeout(function(){ _pmRender(true); },0); }
    }
  }
  function _pmRenderCore(force){
    var box=document.getElementById('projMemoBoard'); if(!box) return;"""

def apply_r95b(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R95B FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r95b(s, path)
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
