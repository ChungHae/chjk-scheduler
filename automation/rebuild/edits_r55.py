# -*- coding: utf-8 -*-
# r55: 담당자 행에 이메일 칸 추가
R55_EDITS = [
("""      + f('dept','부서',c.dept) + f('rank','직급',c.rank) + f('name','담당자명',c.name) + f('phone','연락처',c.phone,'oninput="clxPhoneInput(this)" onchange="clxPhoneBlur(this)"')""",
 """      + f('dept','부서',c.dept) + f('rank','직급',c.rank) + f('name','담당자명',c.name) + f('phone','연락처',c.phone,'oninput="clxPhoneInput(this)" onchange="clxPhoneBlur(this)"') + f('email','이메일',c.email)"""),
("""      if(o.dept||o.rank||o.name||o.phone) contacts.push(o);""",
 """      if(o.dept||o.rank||o.name||o.phone||o.email) contacts.push(o);"""),
]
def apply_r55(s, path):
    for i,(old,new) in enumerate(R55_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R55 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r55(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r54 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r54 2026-08-13 -->', '<!-- test build r55 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
