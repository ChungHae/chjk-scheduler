"""
SemPlus / KIS정보통신 (화성 지점) 오프라인 매장 단말기 카드매출 - 거래건별 상세내역 스크래퍼.

SemPlus는 WebSquare라는 구형 전자정부 프레임워크 기반 사이트로,
- 클래식 <frameset>/<frame> + 그 안에 다시 <iframe> 여러 겹으로 중첩된 구조이고
- 화면이 쓰는 실제 AJAX 요청(selectCreditTranList.do)이 XML 기반의
  복잡한 자체 포맷이라, 요청/응답을 직접 흉내 내는 것보다
  "사람이 쓰는 화면을 그대로 자동화 + 이미 있는 엑셀 다운로드 기능을
  이용해 정형 데이터를 받는" 방식이 훨씬 안정적이다.

동작 방식:
  1) Playwright로 로그인 (라벨 텍스트 기준으로 아이디/비밀번호 칸을 찾음).
  2) 상단 메뉴 "거래내역 > 신용거래"로 이동.
  3) 조회기간을 "1주일"(최근 7일) 퀵버튼으로 설정 → 검색.
  4) 그 화면에 있는 "엑셀" 다운로드 버튼을 눌러 결과를 엑셀 파일로 받는다
     (Playwright의 download 이벤트로 파일을 저장).
  5) 받은 엑셀을 openpyxl로 파싱해 표 형태 그대로 레코드로 변환.
  6) Firebase에 기록.

필요한 GitHub Secrets:
  SEMPLUS_ID, SEMPLUS_PW

주의: 비밀번호 값은 어떤 경우에도 print/log하지 않는다.

※ 이 사이트는 화면 구조가 자주 바뀔 수 있는 레거시 프레임워크라,
   실제 배포 전 workflow_dispatch로 한 번 수동 실행해 셀렉터가
   맞는지 반드시 확인이 필요하다 (특히 로그인 폼과 메뉴 클릭 부분).
"""
import asyncio
import datetime as _dt
import os
import sys
import tempfile
from decimal import Decimal

import openpyxl
from playwright.async_api import async_playwright

from common_firebase import write_transactions

BASE_URL = "https://semplus.kisvan.co.kr/"

# 로그인 폼 후보 선택자들 - 위에서부터 순서대로 시도
# (2026-08-04 workflow_dispatch 실행에서 "로그인 폼(비밀번호 입력칸)을 찾지 못했습니다"
#  오류 발생 → 로그아웃 상태의 실제 로그인 화면 DOM을 직접 확인함.
#  로그인 폼은 WebSquare 프레임워크가 그려 넣는 별도 frame
#  (websquare.html#w2xPath=/main/kr/co/kisvan/login/login.xml) 안에 있고,
#  아이디/비밀번호 입력칸은 커스텀 위젯(class="w2input w2input_mandatory")이며
#  로그인 버튼은 <button>이 아니라 클릭 가능한 <div id="grp_login">이다.)
ID_FIELD_CANDIDATES = [
    '#ibx_userId', 'input[placeholder*="아이디"]', 'input[name*="id" i]', '#userId', '#usr_id', '#mbr_id',
]
PW_FIELD_CANDIDATES = ['#ibx_Password', 'input[type="password"]']
LOGIN_SUBMIT_CANDIDATES = ['#grp_login', 'button:has-text("로그인")', 'a:has-text("로그인")', 'input[type="submit"]']

# WebSquare는 화면을 자바스크립트로 그려 넣는 구형 프레임워크라, 헤드리스/CI
# 환경(특히 매번 새로 뜨는 GitHub Actions 러너)에서는 렌더링이 끝날 때까지
# 예상보다 오래 걸릴 수 있다 - 넉넉하게 잡는다.
LOGIN_FRAME_TIMEOUT_MS = 25000


async def _first_frame_with(page, selector, timeout=8000):
    """page.frames를 훑어서 selector가 존재하는 첫 프레임을 찾는다.
    (frameset 안에 iframe이 중첩돼 있어 어느 frame이 실제 콘텐츠인지 미리 알 수 없음)"""
    deadline = asyncio.get_event_loop().time() + timeout / 1000
    while asyncio.get_event_loop().time() < deadline:
        for f in page.frames:
            try:
                if await f.locator(selector).count() > 0:
                    return f
            except Exception:
                continue
        await asyncio.sleep(0.3)
    return None


async def _find_first_in_frame(frame, selectors, timeout=3000):
    for sel in selectors:
        try:
            loc = frame.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
    return None


async def _first_visible(scope, selector, timeout=8000):
    """selector에 매칭되는 요소가 여러 개일 수 있다 - WebSquare는 같은 글자가
    서로 다른(하나는 숨겨진) 메뉴에 동시에 들어있는 경우가 많다. 실제로
    "text=신용거래"가 '거래내역' 드롭다운의 '신용거래'뿐 아니라 '일마감'
    드롭다운의 '신용거래집계' 항목에도 부분 문자열로 걸려서, 화면에 없는
    (visible 아닌) 엉뚱한 요소를 클릭하려다 30초 타임아웃이 난 적이 있다.
    그래서 매칭된 요소들 중 실제로 화면에 보이는(visible) 첫 번째 것만
    고른다."""
    deadline = asyncio.get_event_loop().time() + timeout / 1000
    while asyncio.get_event_loop().time() < deadline:
        try:
            loc = scope.locator(selector)
            n = await loc.count()
            for i in range(n):
                item = loc.nth(i)
                try:
                    if await item.is_visible():
                        return item
                except Exception:
                    continue
        except Exception:
            pass
        await asyncio.sleep(0.3)
    return None


async def _first_visible_anywhere(page, selector, timeout=8000):
    """_first_visible과 비슷하지만 frame 하나로 좁히지 않고 page.frames
    전체를 매 폴링마다 훑는다. WebSquare는 탭(예: '신용거래')마다 내용을
    별도 iframe으로 그려 넣는 경우가 있어서, "selector가 존재하는 첫
    frame"(_first_frame_with)과 "실제로 보이는 요소가 있는 frame"이 다를
    수 있다 - 실제로 '검색' 버튼을 이 방식으로 못 찾은 사례가 있었다
    (다른 frame의 숨겨진 '검색' 관련 텍스트가 먼저 걸렸을 가능성이 큼).
    그래서 아예 모든 frame을 다 뒤져서 그 중 화면에 보이는 첫 요소를
    찾는, 더 확실한 방식으로 바꾼다."""
    deadline = asyncio.get_event_loop().time() + timeout / 1000
    while asyncio.get_event_loop().time() < deadline:
        for f in page.frames:
            try:
                loc = f.locator(selector)
                n = await loc.count()
            except Exception:
                continue
            for i in range(n):
                item = loc.nth(i)
                try:
                    if await item.is_visible():
                        return item
                except Exception:
                    continue
        await asyncio.sleep(0.3)
    return None


async def _is_logged_in(page) -> bool:
    """로그아웃 링크가 보이면 로그인된 상태로 판단(로그인 성공 판정과 동일 기준)."""
    return (await _first_frame_with(page, 'text=로그아웃', timeout=3000)) is not None


async def login(page):
    """SemPlus 로그인 (재시도 포함).

    2026-08-05 실제 운영에서 관측된 간헐 실패에 대응:
    야간 자동 실행/백필에서 "로그아웃 링크를 찾을 수 없음"으로 실패했다가
    그냥 다시 돌리면 성공하는 일이 있었다(사이트 응답 지연으로 추정).
    그래서 최대 3회까지 재시도하되,
      - SMS 2차 인증 요구는 재시도해도 사람이 필요하므로 즉시 실패 처리,
      - 재시도 진입 시 이미 로그인돼 있으면(직전 시도가 판정 타임아웃 때문에
        실패로 보였을 뿐 실제로는 성공) 그대로 통과한다.
    """
    last_err = None
    for attempt in range(1, 4):
        try:
            if attempt > 1 and await _is_logged_in(page):
                print(f"[안내] SemPlus 로그인 재확인: {attempt-1}회차 시도가 실제로는 성공한 상태였음 - 계속 진행")
                return
            await _login_once(page)
            return
        except RuntimeError as e:
            if "2차 인증" in str(e):
                raise
            last_err = e
            if attempt < 3:
                print(f"[경고] SemPlus 로그인 {attempt}회차 실패: {e} - 10초 후 재시도합니다.")
                await page.wait_for_timeout(10000)
    raise last_err


async def _login_once(page):
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    try:
        # WebSquare는 백그라운드 폴링(남은시간 카운트다운 등) 때문에 완전히
        # idle 상태가 되지 않을 수 있으므로, 실패해도 무시하고 진행한다.
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    # 로그인 폼이 어느 프레임에 있는지 불확실하므로, 비밀번호 input이 있는 프레임을 우선 탐색
    pw_frame = await _first_frame_with(page, PW_FIELD_CANDIDATES[0], timeout=LOGIN_FRAME_TIMEOUT_MS)
    if not pw_frame:
        raise RuntimeError("SemPlus 로그인 폼(비밀번호 입력칸)을 찾지 못했습니다.")

    id_field = await _find_first_in_frame(pw_frame, ID_FIELD_CANDIDATES)
    pw_field = await _find_first_in_frame(pw_frame, PW_FIELD_CANDIDATES)
    if not id_field or not pw_field:
        raise RuntimeError("SemPlus 입력칸을 찾지 못했습니다 - 화면 구조 확인 필요.")

    # WebSquare의 w2input 위젯은 화면에 보이는 값과 별개로, 내부적으로는
    # 키 입력 이벤트(keydown/keyup)를 하나하나 받아서 자기만의 데이터
    # 모델에 반영하는 경우가 많다. Playwright의 fill()은 값을 한 번에
    # 넣고 input 이벤트 한 번만 보내기 때문에, 화면엔 값이 보여도 위젯의
    # 내부 모델은 비어 있거나 예전 값 그대로라 로그인 버튼을 눌러도
    # 실제로는 빈 아이디/비밀번호로 시도된 것처럼 실패할 수 있다.
    # → 진짜 타이핑처럼 한 글자씩 키 이벤트를 보내는 press_sequentially를 사용.
    await id_field.click()
    await id_field.fill("")
    await id_field.press_sequentially(os.environ["SEMPLUS_ID"], delay=40)

    await pw_field.click()
    await pw_field.fill("")
    await pw_field.press_sequentially(os.environ["SEMPLUS_PW"], delay=40)

    # 일부 WebSquare 위젯은 blur 시점에야 값 검증/모델 확정을 하므로,
    # 로그인 버튼을 누르기 전에 Tab으로 포커스를 옮겨 blur를 발생시킨다.
    await pw_field.press("Tab")
    await page.wait_for_timeout(300)

    submit = await _find_first_in_frame(pw_frame, LOGIN_SUBMIT_CANDIDATES)
    if submit:
        await submit.click()
    else:
        await pw_field.press("Enter")

    await page.wait_for_timeout(2000)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    # 신규/미등록 환경(예: GitHub Actions처럼 매번 IP가 바뀌는 러너)에서 로그인하면
    # SemPlus가 SMS 2차 인증(#ibx_2Factor)을 요구할 수 있다. 이 경우 사람이 문자로
    # 받은 인증번호를 입력해야 해서 완전 자동화가 불가능하므로, 원인을 명확히 구분해
    # 알린다 (단순 선택자 문제와 헷갈리지 않도록).
    twofactor_frame = await _first_frame_with(page, '#ibx_2Factor', timeout=3000)
    if twofactor_frame:
        try:
            twofactor_visible = await twofactor_frame.locator('#ibx_2Factor').first.is_visible()
        except Exception:
            twofactor_visible = True
        if twofactor_visible:
            raise RuntimeError(
                "SemPlus에서 SMS 2차 인증(#ibx_2Factor)을 요구하고 있습니다. "
                "GitHub Actions처럼 매번 IP가 바뀌는 환경은 신규 기기로 인식되어 "
                "2차 인증이 뜰 수 있는데, 이 경우 자동 로그인은 불가능합니다 - "
                "SemPlus 고객센터에 해당 계정의 신규기기 2차 인증을 끄거나 예외 처리할 "
                "수 있는지 문의가 필요합니다."
            )

    # (2026-08-05) 사이트 응답이 느린 날 성공 판정이 8초 안에 안 끝나 실패로
    # 오인되는 일이 있어 판정 대기시간을 15초로 늘림.
    if await _first_frame_with(page, 'text=로그아웃', timeout=15000) is None:
        # 원인 파악을 돕기 위해, 화면에 남아있는 오류 메시지가 있다면 함께 남긴다.
        # (비밀번호 값 자체가 아니라 "비밀번호가 일치하지 않습니다" 같은 안내
        #  문구만 찾는 것이므로 자격증명이 로그에 노출되지 않는다.)
        # 로그인 화면 자체에 늘 떠 있는 라벨(체크박스/링크 등)은 오류 메시지가
        # 아니므로 제외한다 - 예: "아이디저장" 체크박스 라벨이 "아이디"
        # 키워드에 걸려 오탐되는 문제가 있었음.
        _NOISE_LINES = {
            "아이디저장", "회원가입", "비밀번호 찾기", "아이디/비밀번호 찾기",
            "사업자번호/고객ID", "비밀번호", "1대1 문의", "아이디",
        }
        err_text = None
        try:
            for f in page.frames:
                try:
                    body_text = await f.locator("body").inner_text(timeout=1000)
                except Exception:
                    continue
                for line in body_text.splitlines():
                    line = line.strip()
                    if (
                        line and len(line) < 80
                        and line not in _NOISE_LINES
                        and any(
                            kw in line for kw in
                            ("일치하지", "잠겼", "잠김", "차단", "다시 시도", "존재하지 않는",
                             "오류가", "실패했습니다", "인증번호를 입력", "확인해 주세요")
                        )
                    ):
                        err_text = line
                        break
                if err_text:
                    break
        except Exception:
            pass
        msg = "SemPlus 로그인 실패로 보입니다 (로그아웃 링크를 찾을 수 없음)."
        if err_text:
            msg += f" 화면 표시 메시지로 추정: {err_text!r}"
        raise RuntimeError(msg)


async def open_credit_transaction_list(page):
    # 상단 메뉴 "거래내역" 클릭 → 드롭다운의 "신용거래" 클릭.
    # "신용거래"는 정확히 일치(text="...")하는 것만, 그리고 그 중에서도
    # 실제로 화면에 보이는(visible) 것만 골라 클릭한다 - '일마감' 메뉴의
    # 숨겨진 '신용거래집계' 항목을 잘못 클릭하려다 타임아웃 났던 버그를
    # 재발 방지하기 위함. frame이 여러 개일 수 있어(탭마다 별도 iframe),
    # "텍스트가 존재하는 frame"이 아니라 "실제로 보이는 frame"을 페이지
    # 전체에서 찾는 _first_visible_anywhere를 쓴다.
    top_item = await _first_visible_anywhere(page, 'text="거래내역"')
    if not top_item:
        raise RuntimeError("'거래내역' 메뉴가 화면에 보이지 않습니다.")
    await top_item.click()
    await page.wait_for_timeout(500)

    sub_item = await _first_visible_anywhere(page, 'text="신용거래"', timeout=5000)
    if not sub_item:
        raise RuntimeError(
            "'신용거래' 하위 메뉴가 화면에 보이지 않습니다 "
            "(거래내역 드롭다운이 열리지 않았을 수 있음)."
        )
    await sub_item.click()
    await page.wait_for_timeout(1000)


async def search_last_week(page):
    # '검색' 버튼 찾기가 실제로 실패한 적이 있음 - 원인으로 가장 유력한
    # 것은, WebSquare가 '신용거래' 탭 내용을 별도 iframe으로 그려 넣는데
    # _first_frame_with가 "'검색'이라는 글자가 존재하는 첫 frame"을
    # 골랐지만 그 frame에서는 해당 글자가 숨겨진 채로만 있고, 실제로
    # 보이는 '검색' 버튼은 다른 frame에 있었을 가능성. 그래서 frame을
    # 하나로 좁히지 않고 페이지 전체 frame을 다 뒤지는
    # _first_visible_anywhere로 통일한다.
    week_btn = await _first_visible_anywhere(page, 'text=1주일')
    if not week_btn:
        raise RuntimeError("'1주일' 조회기간 버튼이 화면에 보이지 않습니다.")
    await week_btn.click()

    search_btn = await _first_visible_anywhere(page, 'text=검색')
    if not search_btn:
        raise RuntimeError("'검색' 버튼이 화면에 보이지 않습니다.")
    await search_btn.click()
    await page.wait_for_timeout(2000)


async def download_excel(page) -> str:
    """엑셀 다운로드 (긴 타임아웃 + 1회 재시도).

    2026-08-05 야간 자동 실행에서 "Timeout 20000ms exceeded while waiting for
    event 'download'"로 실패한 사례가 실제로 있었다 - 서버가 엑셀 파일을
    만드는 데 20초 넘게 걸린 것으로 보인다(머니온도 같은 증상을 타임아웃
    60초로 늘려 해결). 타임아웃을 60초로 늘리고, 그래도 실패하면 버튼을
    다시 찾아 한 번 더 시도한다(클릭이 씹혔을 가능성 대비)."""
    last_err = None
    for attempt in (1, 2):
        excel_btn = await _first_visible_anywhere(page, 'text=엑셀')
        if not excel_btn:
            raise RuntimeError("'엑셀' 다운로드 버튼이 화면에 보이지 않습니다.")
        try:
            async with page.expect_download(timeout=60000) as dl_info:
                await excel_btn.click()
            download = await dl_info.value
            path = os.path.join(tempfile.gettempdir(), "semplus_credit_tran.xlsx")
            await download.save_as(path)
            return path
        except Exception as e:
            last_err = e
            if attempt == 1:
                print(f"[경고] 엑셀 다운로드 1회차 실패({e}) - 5초 후 한 번 더 시도합니다.")
                await page.wait_for_timeout(5000)
    raise last_err


def _json_safe(v):
    """Firebase(REST API/Admin SDK)는 JSON으로 직렬화 가능한 값만 받는다.
    openpyxl은 날짜/시간 셀을 datetime.datetime/date 객체로 돌려주는데,
    이걸 그대로 Firebase에 쓰려고 하면
    "Invalid data; couldn't parse JSON object..." 오류가 난다(실제로
    발생했던 오류). 날짜/시간/Decimal 값을 문자열/숫자로 안전하게 바꾼다."""
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


# 엑셀 맨 위 몇 줄은 제목/조회조건 요약("요약정보" 등)이라 진짜 헤더가 아닐 수
# 있다(실제로 1행을 헤더로 가정했다가 빈 헤더만 잡힌 적이 있음) - 아래
# 키워드 중 2개 이상이 있는 첫 행을 진짜 헤더 행으로 판단한다.
_HEADER_HINTS = ("가맹점명", "카드번호", "승인번호", "거래금액", "전표", "고객ID")


def _find_header_row(rows):
    for idx, row in enumerate(rows):
        cells = [str(c).strip() if c is not None else "" for c in row]
        hits = sum(1 for c in cells if c in _HEADER_HINTS)
        if hits >= 2:
            return idx, cells
    return None, None


def parse_excel(path: str):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header_idx, header = _find_header_row(rows)
    if header_idx is None:
        # 못 찾으면 예전처럼 첫 행을 시도(안전한 fallback) - 다만 이 경우
        # 헤더가 실제와 다를 가능성이 있으므로 호출부에서 헤더 샘플을 찍어
        # 확인할 수 있게 해둔다.
        header_idx, header = 0, [str(h).strip() if h else "" for h in rows[0]]
    records = []
    for row in rows[header_idx + 1:]:
        if not any(row):
            continue
        rec = {k: _json_safe(v) for k, v in zip(header, row)}
        records.append(rec)
    return records


def _first_present(rec, *keys):
    for k in keys:
        v = rec.get(k)
        if v not in (None, ""):
            return v
    return None


def _to_record(rec: dict) -> dict:
    """SemPlus 엑셀 1행 → 공통 스키마로 정규화.

    2026-08-05 사용자가 실제로 받은 엑셀 파일을 직접 확인해, 아래 25개
    컬럼이 실제 헤더인 것을 확인함: NO/고객ID/단말기ID/가맹점명/발급사/
    대리점/체크/카드번호/봉사료/부가세/거래금액/승인번호/할부/원거래일자/
    거래일자/거래시간/매입사/가맹점번호/매입일자/입금예정일자/정산상태/
    거래유형/수수료/입금예정액/인증거래값 - "거래일자"·"거래시간"은 걱정과
    달리 실제로 존재함이 이때 확인됨. 다만 "공급금액"이라는 컬럼은 없어서
    거래금액에서 부가세를 뺀 값으로 계산해 채운다.

    ※ 신용/체크 구분(체크 컬럼)은 2026-08-05 사용자 요청으로 표시하지 않기로
      해서 더 이상 읽지 않음(머니온 쪽엔 애초에 이 정보가 없어 통일성을
      위해 SemPlus 쪽도 함께 제외 - scrape_moneyon.py 참고).
    """
    date_raw = _first_present(rec, "거래일자", "매입일자", "승인일자", "거래일", "일자")
    date = str(date_raw or "").replace("-", "").replace(".", "")[:8]

    # 승인번호가 카드사에서 발급하는 실제 고유 식별자라 우선 사용한다.
    # "전표"는 화면에서 보면 데이터 값이 아니라 "전표보기" 같은 액션
    # 링크의 라벨일 수 있어(그렇다면 모든 행에서 값이 똑같아 서로 다른
    # 거래를 구분 못 하게 됨), 승인번호를 최우선으로 둔다.
    approval_no = _first_present(rec, "승인번호")
    txn_id = (
        approval_no
        or _first_present(rec, "전표")
        or f"{date}_{rec.get('NO')}_{rec.get('카드번호')}"
    )

    supply_amt = _first_present(rec, "공급금액")
    amount = _first_present(rec, "거래금액") or 0
    tax_amt = _first_present(rec, "부가세") or 0
    if supply_amt is None:
        # "공급금액" 컬럼이 따로 없으면(실제로 화면엔 안 보였음) 거래금액에서
        # 부가세를 뺀 값으로 추정한다.
        try:
            supply_amt = float(amount) - float(tax_amt)
        except (TypeError, ValueError):
            supply_amt = 0

    return {
        "id": str(txn_id),
        "date": date,
        "time": str(_first_present(rec, "거래시간", "시간") or ""),
        "merchant": _first_present(rec, "가맹점명") or "",
        "issuer": str(_first_present(rec, "발급사") or ""),
        "installment": str(_first_present(rec, "할부") or ""),
        "cardNoMasked": _first_present(rec, "카드번호") or "",
        "approvalNo": str(approval_no or ""),
        "amount": amount,
        "supplyAmt": supply_amt,
        "taxAmt": tax_amt,
        "source": "semplus",
        "raw": {k: v for k, v in rec.items()},
    }


DEBUG_SCREENSHOT_PATH = "semplus_login_debug.png"


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(accept_downloads=True)
        try:
            await login(page)
            await open_credit_transaction_list(page)
            await search_last_week(page)
            xlsx_path = await download_excel(page)
            raw_records = parse_excel(xlsx_path)
            print(f"SemPlus: 엑셀에서 {len(raw_records)}행 파싱됨 (헤더 확인 필요 시 첫 행 출력 참고)")
            if raw_records:
                print("헤더 샘플:", list(raw_records[0].keys()))
            records = [_to_record(r) for r in raw_records]

            # 화면(신용거래 목록)에 거래일자 컬럼이 안 보였던 적이 있어,
            # 엑셀에도 실제로 날짜 컬럼이 없으면 date가 빈 문자열로 남는다.
            # 그 상태로 Firebase에 쓰면 teamdata_test_cardsales/hwaseong/
            # (빈 문자열)/... 아래로 전부 뒤섞이므로, 빈 날짜는 오늘 날짜로
            # 대체하고 - 정확한 날짜 컬럼명을 찾을 때까지 임시방편임을 -
            # 로그에 크게 남긴다.
            missing_date = [r for r in records if not r.get("date")]
            if missing_date:
                today_str = _dt.date.today().strftime("%Y%m%d")
                print(
                    f"[경고] {len(missing_date)}건은 엑셀에서 거래일자를 찾지 못해 "
                    f"오늘 날짜({today_str})로 임시 기록합니다 - 위 '헤더 샘플'을 "
                    "확인해 실제 날짜 컬럼명을 _to_record()의 date_raw 후보 목록에 "
                    "추가해야 합니다."
                )
                for r in missing_date:
                    r["date"] = today_str

            if records:
                write_transactions("hwaseong", records)
                print("Firebase 기록 완료 (branch=hwaseong)")
        except Exception:
            # 실패 시점의 화면을 스크린샷으로 남겨 GitHub Actions 아티팩트로
            # 업로드한다 - 텍스트 오류 메시지만으로 원인을 못 좁힐 때, 이
            # 스크린샷을 다운로드해서 대화창에 올려주시면 화면을 직접 보고
            # 원인을 파악할 수 있다. (비밀번호 칸은 항상 점(●)으로
            # 마스킹되어 보이므로 실제 비밀번호 문자가 찍히는 일은 없다.)
            try:
                await page.screenshot(path=DEBUG_SCREENSHOT_PATH, full_page=True)
                print(f"[디버그] 실패 시점 스크린샷 저장: {DEBUG_SCREENSHOT_PATH}")
            except Exception:
                pass
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[SemPlus 스크래퍼 오류] {e}", file=sys.stderr)
        sys.exit(1)
