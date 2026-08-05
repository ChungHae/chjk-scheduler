"""
머니온(MoneyOn, 서울 지점) 오프라인 매장 단말기 카드매출 - 거래건별 상세내역 스크래퍼.

2026-08-05 재작성(엑셀 다운로드 방식으로 전환):
  기존에는 화면이 쓰는 getSalesDetail.do JSON 응답을 가로채서 그 필드명을
  추정으로 매핑하는 방식이었는데(auth_date/tran_time/jijum_name 등), 그중
  거래시간(tran_time으로 추정)·가맹점명(jijum_name으로 추정)·카드사가 실제
  화면에는 안 나오는 문제가 있었다. 사용자가 화면에서 직접 "저장" 버튼으로
  받은 엑셀 파일 2개(하나는 기본 컬럼만, 하나는 "할부" 컬럼을 추가해서
  받은 것)를 직접 열어 확인한 결과, 아래 헤더가 전부 실제 값으로 정상
  채워져 있는 것을 확인함:

    거래일자, 거래시간, 상호, 거래유형(승인/취소), 카드번호, 승인번호, 매입사,
    공급가액, 금액, 처리현황, 입금예정, 취소여부, 취소일시, 할부

  → 실제 확인된 이 엑셀 파일을 SemPlus와 동일한 방식(화면의 "저장" 버튼을
    눌러 받은 엑셀을 그대로 파싱)으로 바꿔서, 더 이상 API 필드명을 추정하지
    않도록 한다.

  ※ 신용/체크 구분(txnType)은 이 화면/엑셀 어디에도 존재하지 않는 것으로
    확인되어, 사용자 요청에 따라 머니온·SemPlus 양쪽 모두에서 제거함
    (SemPlus 쪽 코드는 scrape_semplus.py 참고).

동작 방식:
  1) Playwright로 로그인 (기존과 동일 - 이미 안정적으로 동작 확인됨).
  2) 매출상세조회 화면으로 이동해, 조회기간을 넣고 화면이 쓰는 검색 함수
     (doSearch())를 그대로 호출한다 (기존과 동일 - 이미 안정적으로 동작 확인됨).
  3) 결과 상세 내역 표 옆의 "저장" 버튼을 눌러 엑셀로 받는다(SemPlus와 동일한
     방식 - Playwright의 download 이벤트로 파일을 저장).
  4) 받은 엑셀을 openpyxl로 파싱해 공통 스키마로 변환.
  5) Firebase에 기록.

필요한 GitHub Secrets:
  MONEYON_ID, MONEYON_PW

주의: 비밀번호 값은 어떤 경우에도 print/log하지 않는다.

2026-08-05 백필 재실행에서 6개 구간 전부 "'저장' 버튼을 화면에서 찾지 못했습니다"로
실패하는 것을 발견해 실제 화면을 다시 열어 DOM을 직접 확인함(read_page로 접근성
트리 조회). 원인: "저장"은 실제 텍스트 노드가 아니라 아이콘 이미지라서
text="저장"/has-text("저장") 류의 선택자가 애초에 아무것도 못 찾고 있었음.
실제로는 아래쪽 상세표 옆 링크의 href가 정확히 javascript:excelDownload(); 이고,
위쪽 요약표 옆 링크는 href가 javascript:excelDownload_each(); 로 서로 다르다는
것을 확인함 - 그래서 이제 href 기준으로 정확히 상세표 쪽만 골라 클릭하도록
고쳤다(더 이상 "화면에 보이는 것 중 마지막" 같은 휴리스틱에 의존하지 않음).

또한 이 버튼을 클릭하면 "처리 중입니다... (처리완료 후 '닫기' 버튼을
눌러주세요.)"라는 진행 모달이 뜨는 것도 실제로 확인함(서버 쪽에서 엑셀을
생성하는 데 시간이 걸리는 것으로 보임) - Playwright의 expect_download()는
브라우저 다운로드 이벤트 자체를 기다리는 것이라 화면에 이 모달이 떠 있어도
무관하게 동작하지만, 처리 시간을 감안해 다운로드 대기 시간을 넉넉히 늘렸다.
"""
import asyncio
import datetime
import os
import sys
import tempfile
from decimal import Decimal

import openpyxl
from playwright.async_api import async_playwright

from common_firebase import write_transactions

LOGIN_URL = "https://www.moneyon.com/login/loginForm.do"
DETAIL_URL = "https://www.moneyon.com/sales/auth/salesDetail.do?menu_no1=s1&menu_no2=4"

# 최근 며칠치를 매번 다시 긁어와 upsert할지 (정산 지연/취소 반영 등을 위해 여유있게)
LOOKBACK_DAYS = 7

# 로그인 폼 후보 선택자들 - 위에서부터 순서대로 시도
ID_FIELD_CANDIDATES = [
    '#user_id', 'input[name="user_id"]',
    'input[name="usr_id"]', 'input[name="mbr_id"]', 'input[name="userId"]',
    'input[name="id"]', 'input[placeholder*="아이디"]', 'input[placeholder*="ID"]',
    '#usr_id', '#mbr_id', '#userId', '#id',
]
PW_FIELD_CANDIDATES = [
    '#password', 'input[type="password"]',
]
LOGIN_SUBMIT_CANDIDATES = [
    '#loginBtn', 'button:has-text("로그인")', 'a:has-text("로그인")', 'input[type="submit"][value*="로그인"]',
]

# "저장" 버튼 후보. 2026-08-05 실제 DOM 확인 결과 "저장"은 텍스트가 아니라
# 아이콘 이미지라서 텍스트 기반 선택자는 전혀 매칭되지 않았음(백필 실패 원인).
# 실제로 확인된 정확한 선택자는 href="javascript:excelDownload();" 하나뿐이고,
# 이는 아래쪽 상세표 옆 버튼에만 붙어 있어 위쪽 요약표 버튼(excelDownload_each())과
# 확실히 구분된다 - 그래서 이걸 최우선으로 시도한다. 나머지는 사이트 개편 시를
# 대비한 예비 후보.
SAVE_BTN_CANDIDATES = [
    'a[href="javascript:excelDownload();"]', 'a[href*="excelDownload()"]',
    'text="저장"', 'a:has-text("저장")', 'button:has-text("저장")',
    '[alt*="저장"]', '[title*="저장"]',
]


async def _find_first(page, selectors, timeout=3000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
    return None


async def _last_visible_anywhere(page, selectors, timeout=8000):
    """selectors(후보 여러 개, 순서대로 시도)에 매칭되는 요소 중, 실제로 화면에
    보이는 것들 중 DOM 순서상 "마지막" 것을 고른다. 매출상세조회 화면엔
    위쪽 요약표와 아래쪽 상세표에 각각 "저장" 버튼이 있는데, 우리가 받고
    싶은 건 아래쪽 상세표(거래일자/거래시간/상호 등이 나오는 표) 옆의
    버튼이라 이렇게 골라야 한다."""
    deadline = asyncio.get_event_loop().time() + timeout / 1000
    while asyncio.get_event_loop().time() < deadline:
        for sel in selectors:
            try:
                loc = page.locator(sel)
                n = await loc.count()
            except Exception:
                continue
            visible = []
            for i in range(n):
                item = loc.nth(i)
                try:
                    if await item.is_visible():
                        visible.append(item)
                except Exception:
                    continue
            if visible:
                return visible[-1]
        await asyncio.sleep(0.3)
    return None


async def login(page):
    await page.goto(LOGIN_URL, wait_until="domcontentloaded")

    id_field = await _find_first(page, ID_FIELD_CANDIDATES)
    pw_field = await _find_first(page, PW_FIELD_CANDIDATES)
    if not id_field or not pw_field:
        raise RuntimeError(
            "로그인 입력칸을 찾지 못했습니다. 사이트 마크업이 바뀌었을 수 있습니다 - "
            "ID_FIELD_CANDIDATES/PW_FIELD_CANDIDATES를 실제 화면에 맞게 갱신하세요."
        )

    await id_field.fill(os.environ["MONEYON_ID"])
    await pw_field.fill(os.environ["MONEYON_PW"])

    submit = await _find_first(page, LOGIN_SUBMIT_CANDIDATES)
    if submit:
        await submit.click()
    else:
        await pw_field.press("Enter")

    await page.wait_for_load_state("networkidle", timeout=15000)

    # 로그인 성공 여부 확인 (실패 시 비밀번호 값은 절대 로그에 남기지 않는다)
    if await page.locator('text=로그아웃').count() == 0:
        raise RuntimeError("머니온 로그인 실패로 보입니다 (로그아웃 버튼이 보이지 않음).")


async def search_range(page, date_fr: str, date_to: str):
    """조회기간을 YYMMDD 형식으로 설정하고 화면의 검색 함수를 호출한다
    (기존 코드와 동일한 부분 - 이미 안정적으로 동작 확인됨)."""
    await page.evaluate(
        """([fr, to]) => {
            document.getElementById('cal_date_fr').value = fr;
            document.getElementById('cal_date_to').value = to;
        }""",
        [date_fr, date_to],
    )
    await page.evaluate("() => { if (typeof doSearch === 'function') doSearch(); }")
    # 오래된/넓은 기간일수록 서버 조회에 시간이 더 걸릴 수 있어 넉넉히 대기.
    await page.wait_for_timeout(2500)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass


async def download_excel(page) -> str:
    """상세 내역 표(아래쪽) 옆의 "저장" 버튼을 눌러 엑셀로 받는다.

    2026-08-05 확인: 클릭하면 "처리 중입니다..." 진행 모달이 뜨고, 서버가
    엑셀을 만드는 동안 시간이 걸린 뒤에야 실제 다운로드가 시작된다. 그래서
    다운로드 대기 시간을 SemPlus보다 넉넉하게 잡는다(처리 시간이 데이터量에
    따라 달라질 수 있음)."""
    save_btn = await _last_visible_anywhere(page, SAVE_BTN_CANDIDATES)
    if not save_btn:
        raise RuntimeError("'저장' 버튼을 화면에서 찾지 못했습니다.")
    async with page.expect_download(timeout=60000) as dl_info:
        await save_btn.click()
    download = await dl_info.value
    path = os.path.join(tempfile.gettempdir(), "moneyon_sales_detail.xlsx")
    await download.save_as(path)
    return path


def _json_safe(v):
    """openpyxl은 날짜/시간 셀을 datetime 객체로 돌려줄 수 있는데, 이걸 그대로
    Firebase에 쓰면 JSON 직렬화 오류가 나므로 문자열/숫자로 안전하게 바꾼다
    (scrape_semplus.py와 동일한 이유의 동일한 처리)."""
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


# 엑셀 맨 위 1~2줄은 "* 대상기간 : ..." 같은 제목 줄이라 진짜 헤더가 아니다 -
# 아래 힌트 컬럼 중 3개 이상이 있는 첫 행을 진짜 헤더 행으로 판단한다.
_HEADER_HINTS = ("거래일자", "거래시간", "상호", "승인번호", "카드번호", "매입사")


def _find_header_row(rows):
    for idx, row in enumerate(rows):
        cells = [str(c).strip() if c is not None else "" for c in row]
        hits = sum(1 for c in cells if c in _HEADER_HINTS)
        if hits >= 3:
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
        raise RuntimeError(
            "머니온 엑셀에서 헤더 행을 찾지 못했습니다 - 화면 양식이 바뀌었을 수 있습니다. "
            "(_HEADER_HINTS를 실제 헤더에 맞게 갱신 필요)"
        )
    records = []
    for row in rows[header_idx + 1:]:
        if not any(row):
            continue
        rec = {k: _json_safe(v) for k, v in zip(header, row)}
        records.append(rec)
    return records


def _to_num(v) -> float:
    try:
        return float(v) if v not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0


def _to_record(rec: dict) -> dict:
    """머니온 엑셀 1행 → 공통 스키마로 정규화.

    2026-08-05 실제로 확인된 헤더(사용자가 화면에서 직접 다운받아 확인함):
      거래일자, 거래시간, 상호, 거래유형(승인/취소), 카드번호, 승인번호, 매입사,
      공급가액, 금액, 처리현황, 입금예정, 취소여부, 취소일시, 할부

    ※ 승인번호는 "취소" 거래가 원래 "승인" 거래와 같은 승인번호를 그대로
      쓰는 경우가 실제 데이터에서 확인됨(취소 시 원 승인건을 참조하는
      방식) - 승인번호만으로 Firebase 키를 만들면 취소 레코드가 원래
      승인 레코드를 덮어써서 사라지는 문제가 생긴다. 그래서 거래시간까지
      합쳐서 고유 키를 만든다(같은 승인번호라도 취소 이벤트는 다른
      시간에 일어나므로 이렇게 하면 항상 구분됨 - 실제 데이터로 검증함).
    """
    date_raw = str(rec.get("거래일자") or "").strip()
    date = date_raw.replace("-", "").replace(".", "")[:8]
    time_ = str(rec.get("거래시간") or "").strip()
    merchant = str(rec.get("상호") or "").strip()
    approval_no = str(rec.get("승인번호") or "").strip()
    card_no = str(rec.get("카드번호") or "").strip()
    issuer = str(rec.get("매입사") or "").strip()
    installment_raw = str(rec.get("할부") or "").strip()
    installment = "" if installment_raw in ("", "00") else installment_raw

    supply_amt = _to_num(rec.get("공급가액"))
    amount = _to_num(rec.get("금액"))
    # 이 엑셀엔 부가세(세액) 컬럼이 따로 없어 금액-공급가액으로 계산한다
    # (표준 세금계산서 구조상 공급가액+세액=금액이며, 실제 데이터로도
    # 10% 부가세와 정확히 맞아떨어지는 것을 확인함).
    tax_amt = round(amount - supply_amt, 2)

    settle_status = str(rec.get("처리현황") or "").strip()
    txn_id = f"{approval_no}_{time_}" if approval_no else f"{date}_{time_}_{card_no}"

    return {
        "id": txn_id,
        "date": date,
        "time": time_,
        "merchant": merchant,
        "settleStatus": settle_status,
        "issuer": issuer,
        "installment": installment,
        "cardNoMasked": card_no,
        "approvalNo": approval_no,
        "amount": amount,
        "supplyAmt": supply_amt,
        "taxAmt": tax_amt,
        "source": "moneyon",
        "raw": {k: v for k, v in rec.items()},
    }


async def main():
    date_to = datetime.date.today()
    date_fr = date_to - datetime.timedelta(days=LOOKBACK_DAYS)
    fr_str = date_fr.strftime("%y%m%d")
    to_str = date_to.strftime("%y%m%d")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(accept_downloads=True)
        try:
            await login(page)
            await page.goto(DETAIL_URL, wait_until="domcontentloaded")
            await search_range(page, fr_str, to_str)
            xlsx_path = await download_excel(page)
            raw_records = parse_excel(xlsx_path)
            records = [_to_record(r) for r in raw_records]
            print(f"머니온: {fr_str}~{to_str} 기간 {len(records)}건 조회됨")
            if records:
                write_transactions("seoul", records)
                print("Firebase 기록 완료 (branch=seoul)")
        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[머니온 스크래퍼 오류] {e}", file=sys.stderr)
        sys.exit(1)
