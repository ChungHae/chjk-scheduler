# -*- coding: utf-8 -*-
# r212(회계): 내용증명 인쇄본 간격을 워드 문서와 똑같이 맞춤
#  증상: 같은 내용인데 워드(.docx)는 1장에 꽉 차게 들어가고, 인쇄(PDF)는 간격이 달라 보인다.
#  원인: 인쇄본 CSS 를 눈대중 값(line-height:1.23, margin 6pt/9pt …)으로 짜서 워드의 실제 계산과 달랐다.
#        ① 워드는 문단 사이 간격을 '앞 문단 space_after + 뒤 문단 space_before' 로 **더한다**.
#           CSS 마진은 서로 겹쳐(collapse) 큰 쪽만 남으므로 그대로 옮기면 좁아진다.
#        ② w:line="295" lineRule="auto" 는 글꼴 기본 줄높이의 1.2292 배이지 글자크기의 1.23 배가 아니다.
#           맑은 고딕 기본 줄높이 = (usWinAscent 2059 + usWinDescent 430)/2048 = 1.2153 em
#           → 본문 9.5pt 한 줄 = 9.5 × 1.2153 × 1.2292 = 14.2pt (CSS 1.23 은 11.7pt — 약 2.5pt 씩 좁았다)
#  처리: 인쇄본을 docx 수치 그대로 다시 짠다.
#   - 글자크기: 본문 9.5 / 제목 22 / 소제목·날짜 10.5 / 발신인명 11.5 pt (docx w:sz 의 절반)
#   - 줄높이: 글자크기 × 1.4939 (= 1.2153 × 1.2292) 를 pt 로 못박는다
#   - 문단 간격: 마진 대신 **빈 칸(스페이서) div** 로 넣어 겹침을 없앤다. 값은 after+before 합:
#       제목→수신자 10 / 수신자→표 2 / 표→발신자 5 / 발신자→표 2 / 표→소제목 7 /
#       소제목→1항 15 / 항목 사이 3 / 5항→계좌표 3 / 계좌표→6항 0 / 6항→7항 3 /
#       7항→가로줄 2 / 가로줄→날짜 14 / 날짜→발신인명 14 / 발신인명→명판 6  (단위 pt)
#   - 표: 행 최소높이 0.68cm=19.3pt, 칸 여백 좌우 0.19cm=5.4pt·상하 0, 테두리 0.5pt #808080
#   - 번호 항목: 들여쓰기 left 11pt · 내어쓰기 -11pt (docx ind 220 twip)
#   - 소제목 밑줄: 글자와 3pt 띄우고 0.75pt (docx pBdr sz=6, space=3)
#   - 머리칸 회색(F2F2F2)이 인쇄에서도 나오게 print-color-adjust:exact
#  사용자 지시: "워드의 간격이 1장에 꽉차게 딱 들어가서 좋은데 PDF도 동일하게 설정할 수 없나?"
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = """    var TB='border-collapse:collapse;width:100%;table-layout:fixed;margin:2px 0 0';
    var TD='border:1px solid #808080;padding:4px 7px;font-size:9.5pt;line-height:1.23;vertical-align:middle';
    var TH=TD+';background:#F2F2F2;font-weight:700;text-align:center';
    var info=function(l1,v1,l2,v2,l3,v3){
      return '<table style="'+TB+'"><colgroup><col style="width:2.2cm"><col style="width:7.6cm"><col style="width:2.2cm"><col></colgroup>'
        + '<tr><td style="'+TH+'">'+l1+'</td><td style="'+TD+'">'+v1+'</td><td style="'+TH+'">'+l2+'</td><td style="'+TD+'">'+v2+'</td></tr>'
        + '<tr><td style="'+TH+'">'+l3+'</td><td style="'+TD+'" colspan="3">'+v3+'</td></tr></table>';
    };
    var html='<!doctype html><html><head><meta charset="utf-8"><title>내용증명 '+esc(D.corp)+'</title>'
      + '<style>@page{size:A4;margin:1.1cm 2.0cm 0.9cm 2.0cm}'
      + 'body{font-family:"맑은 고딕","Malgun Gothic",sans-serif;font-size:9.5pt;line-height:1.23;color:#000;margin:0}'
      + '.t{text-align:center;font-size:22pt;font-weight:700;letter-spacing:.35em;margin:2pt 0 10pt}'
      + '.lb{font-size:10.5pt;font-weight:700;margin:6pt 0 2pt}'
      + '.hr{border-bottom:1px solid #000;padding-bottom:3pt;margin:9pt 0 5pt;font-size:10.5pt;font-weight:700}'
      + '.it{margin:0 0 3pt;text-indent:0;padding-left:1.1em;text-indent:-1.1em}'
      + '.dt{text-align:center;font-size:10.5pt;margin:15pt 0 14pt}'
      + '.hd{text-align:center;font-size:11.5pt;font-weight:700;margin:0 0 8pt}'
      + '</style></head><body>'
      + '<div class="t">내 용 증 명 서</div>'
      + '<div class="lb">수신자</div>' + info('수신인',recv,'전화번호',esc(D.tel),'주소',esc(D.addr))
      + '<div class="lb">발신자</div>' + info('발신인',send,'전화번호',esc(K.tel),'주소',esc(K.addr))
      + '<div class="hr">미수금 지불 촉구의 건</div>'
      + '<div style="height:6pt"></div>'
      + items.slice(0,5).map(function(t,i){ return '<div class="it">'+(i+1)+'. '+esc(t)+'</div>'; }).join('')
      + '<table style="'+TB+';margin:4pt 0"><colgroup><col style="width:3.2cm"><col style="width:5.0cm"><col style="width:4.6cm"><col></colgroup>'
      +   '<tr><td style="'+TH+'">입금은행</td><td style="'+TH+'">계좌번호</td><td style="'+TH+'">예금주</td><td style="'+TH+'">입금액</td></tr>'
      +   '<tr><td style="'+TD+';text-align:center">'+esc(K.bank)+'</td><td style="'+TD+';text-align:center">'+esc(K.acct)+'</td>'
      +   '<td style="'+TD+';text-align:center">'+esc(K.holder)+'</td><td style="'+TD+';text-align:center">'+D.amt.toLocaleString()+'원</td></tr></table>'
      + '<div style="height:4pt"></div>'
      + items.slice(5).map(function(t,i){ return '<div class="it">'+(i+6)+'. '+esc(t)+'</div>'; }).join('')
      + '<div style="border-bottom:1px solid #000;margin:6pt 0 0"></div>'
      + '<div class="dt">'+esc(_nyDateStr(D.date))+'</div>'
      + '<div class="hd">'+esc(K.holder)+'</div>'
      + '<table style="width:100%;table-layout:fixed;border-collapse:collapse"><colgroup><col><col style="width:6.7cm"><col style="width:2.0cm"></colgroup><tr>'
      +   '<td></td>'
      +   '<td style="text-align:center;vertical-align:middle">'+(st?('<img src="data:image/png;base64,'+st.b64+'" style="width:6cm">'):'')+'</td>'
      +   '<td style="text-align:center;vertical-align:middle">'+(sl?('<img src="data:image/png;base64,'+sl.b64+'" style="width:1.5cm">'):'')+'</td>'
      + '</tr></table></body></html>';
    _nyPrintHtml(html);
"""

NEW = """    // r212: 수치를 docx 와 똑같게 맞춘다 (위 주석 참고)
    var LH=function(pt){ return (Math.round(pt*1.4939*100)/100)+'pt'; };   // 워드 줄높이
    var SP=function(pt){ return '<div style="height:'+pt+'pt;font-size:0;line-height:0"></div>'; };
    var TB='border-collapse:collapse;width:100%;table-layout:fixed;margin:0';
    var TD='border:0.5pt solid #808080;padding:0 5.4pt;height:19.3pt;font-size:9.5pt;line-height:'+LH(9.5)+';vertical-align:middle';
    var TH=TD+';background:#F2F2F2;font-weight:700;text-align:center';
    var info=function(l1,v1,l2,v2,l3,v3){
      return '<table style="'+TB+'"><colgroup><col style="width:2.2cm"><col style="width:7.6cm"><col style="width:2.2cm"><col></colgroup>'
        + '<tr><td style="'+TH+'">'+l1+'</td><td style="'+TD+'">'+v1+'</td><td style="'+TH+'">'+l2+'</td><td style="'+TD+'">'+v2+'</td></tr>'
        + '<tr><td style="'+TH+'">'+l3+'</td><td style="'+TD+'" colspan="3">'+v3+'</td></tr></table>';
    };
    var html='<!doctype html><html><head><meta charset="utf-8"><title>내용증명 '+esc(D.corp)+'</title>'
      + '<style>@page{size:A4;margin:1.1cm 2.0cm 0.9cm 2.0cm}'
      + 'html,body{margin:0;padding:0}'
      + 'body{font-family:"맑은 고딕","Malgun Gothic",sans-serif;font-size:9.5pt;line-height:'+LH(9.5)+';color:#000;'
      +   '-webkit-print-color-adjust:exact;print-color-adjust:exact}'
      + 'div{margin:0}'
      + '.t{text-align:center;font-size:22pt;font-weight:700;line-height:'+LH(22)+'}'
      + '.lb{font-size:10.5pt;font-weight:700;line-height:'+LH(10.5)+'}'
      + '.hr{font-size:10.5pt;font-weight:700;line-height:'+LH(10.5)+';padding-bottom:3pt;border-bottom:0.75pt solid #000}'
      + '.it{padding-left:11pt;text-indent:-11pt}'
      + '.dt{text-align:center;font-size:10.5pt;line-height:'+LH(10.5)+'}'
      + '.hd{text-align:center;font-size:11.5pt;font-weight:700;line-height:'+LH(11.5)+'}'
      + '.el{height:'+LH(9.5)+';border-bottom:0.75pt solid #000}'
      + '</style></head><body>'
      + SP(2)
      + '<div class="t">내  용  증  명  서</div>' + SP(10)
      + '<div class="lb">수신자</div>' + SP(2) + info('수신인',recv,'전화번호',esc(D.tel),'주소',esc(D.addr)) + SP(5)
      + '<div class="lb">발신자</div>' + SP(2) + info('발신인',send,'전화번호',esc(K.tel),'주소',esc(K.addr)) + SP(7)
      + '<div class="hr">미수금 지불 촉구의 건</div>' + SP(15)
      + items.slice(0,5).map(function(t,i){ return '<div class="it">'+(i+1)+'. '+esc(t)+'</div>' + SP(3); }).join('')
      + '<table style="'+TB+'"><colgroup><col style="width:3.2cm"><col style="width:5.0cm"><col style="width:4.6cm"><col></colgroup>'
      +   '<tr><td style="'+TH+'">입금은행</td><td style="'+TH+'">계좌번호</td><td style="'+TH+'">예금주</td><td style="'+TH+'">입금액</td></tr>'
      +   '<tr><td style="'+TD+';text-align:center">'+esc(K.bank)+'</td><td style="'+TD+';text-align:center">'+esc(K.acct)+'</td>'
      +   '<td style="'+TD+';text-align:center">'+esc(K.holder)+'</td><td style="'+TD+';text-align:center">'+D.amt.toLocaleString()+'원</td></tr></table>'
      + '<div class="it">6. '+esc(items[5])+'</div>' + SP(3)
      + '<div class="it">7. '+esc(items[6])+'</div>' + SP(2)
      + '<div class="el"></div>' + SP(14)
      + '<div class="dt">'+esc(_nyDateStr(D.date))+'</div>' + SP(14)
      + '<div class="hd">'+esc(K.holder)+'</div>' + SP(6)
      + '<table style="width:100%;table-layout:fixed;border-collapse:collapse"><colgroup><col><col style="width:6.7cm"><col style="width:2.0cm"></colgroup><tr>'
      +   '<td style="padding:0"></td>'
      +   '<td style="padding:0;text-align:center;vertical-align:middle">'+(st?('<img src="data:image/png;base64,'+st.b64+'" style="width:6cm;display:inline-block">'):'')+'</td>'
      +   '<td style="padding:0;text-align:center;vertical-align:middle">'+(sl?('<img src="data:image/png;base64,'+sl.b64+'" style="width:1.5cm;display:inline-block">'):'')+'</td>'
      + '</tr></table></body></html>';
    _nyPrintHtml(html);
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r212 인쇄 레이아웃 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r212 2026-09-29 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
