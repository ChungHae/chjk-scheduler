"""
머니온(MoneyOn, 서울 지점) 오프라인 매장 단말기 카드매출 - 거래건별 상세내역 스크래퍼.

동작 방식:
  1) Playwright로 실제 로그인 페이지를 열고 아이디/비밀번호를 입력해 로그인한다
     (로그인 폼의 정확한 input 이름을 코드에 하드코딩하지 않고, 화면에 보이는
      라벨/플레이스홀더를 기준으로 필드를 찾는다 - 사이트 마크업이 바뀌어도
      비교적 안전하게 동작하도록).
  2) 로그인 후 "매출상세조회" 화면으로 이동해, 화면의 날짜 입력칸에 조회기간을
     넣고 그 화면이 실제로 쓰는 검색 함수(doSearch())를 그대로 호출한다.
     → 이 방식은 getSalesDetail.do 요청에 필요한 20여 개 폼 파라미터의
       기본값을 우리가 일일이 추측할 필요가 없다(페이지 스스로 채워서 보낸다).
  3) 그 요청의 실제 응답(JSON)을 가로채서 파싱하고, Firebase에 기록한다.
  4) TOTROWS가 페이지당 건수보다 많으면 page_no를 늘려가며 반복 조회한다.

필요한 GitHub Secrets:
  MONEYON_ID, MONEYON_PW

주의: 비밀번호 값은 어떤 경우에도 print/log하지 않는다.
"""
import asyncio
import datetime
import os
import sys

from playwright.async_api import async_playwright

from common_firebase import write_transactions

LOGIN_URL = "https://www.moneyon.com/login/loginForm.do"
DETAIL_URL = "https://www.moneyon.com/sales/auth/salesDetail.do?menu_no1=s1&menu_no2=4"
DETAIL_ENDPOINT_MARKER = "getSalesDetail.do"

# 최근 며칠치를 매번 다시 긁어와 upsert할지 (정산 지연/취소 반영 등을 위해 여유있게)
LOOKBACK_DAYS = 7

# 로그인 폼 후보 선택자들 - 위에서부터 순서대로 시도
# (2026-08-04 workflow_dispatch 첫 실행에서 "로그인 입력칸을 찾지 못했습니다" 오류 발생 →
#  실제 로그인 폼(https://www.moneyon.com/login/loginForm.do)의 DOM을 직접 확인해
#  정확한 필드명(#user_id, #password, #loginBtn)을 반영함)
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


async def _find_first(page, selectors, timeout=3000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
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


async def fetch_detail_page(page, date_fr: str, date_to: str, page_no: int):
    await page.evaluate(
        """([fr, to]) => {
            document.getElementById('cal_date_fr').value = fr;
            document.getElementById('cal_date_to').value = to;
        }""",
        [date_fr, date_to],
    )
    if page_no > 1:
        # doSearch()는 보통 1페이지 기준이라, 페이징은 전역 변수/함수가 있다면 그걸 우선 사용.
        # 없으면 page_no를 별도 hidden input에 넣고 동일 함수를 호출하는 사이트가 많다.
        try:
            await page.evaluate("(p) => { if (typeof goPage === 'function') goPage(p); }", page_no)
        except Exception:
            pass

    # 2026-08-05 백필 첫 실행에서, 최근 구간(현재로부터 최근 며칠)은 성공하지만
    # 오래된 과거 구간(예: 2026-01~07월)은 매번 20초 타임아웃으로 실패하는 것을
    # 확인함 - 오래된/넓은 기간일수록 서버 쪽 조회에 시간이 더 걸릴 가능성을
    # 고려해 넉넉하게 60초로 늘림.
    async with page.expect_response(lambda r: DETAIL_ENDPOINT_MARKER in r.url, timeout=60000) as resp_info:
        await page.evaluate("() => { if (typeof doSearch === 'function') doSearch(); }")
    resp = await resp_info.value
    return await resp.json()


def _valid_yyyymmdd(v) -> str:
    """"00000000"(미확정)나 빈 값은 실제 날짜가 아니므로 걸러낸다."""
    s = str(v or "").replace("-", "")[:8]
    return s if (len(s) == 8 and s != "00000000") else ""


def _to_record(row: dict) -> dict:
    """머니온 getSalesDetail.do 응답 1건 → 공통 스키마로 정규화.

    2026-08-05 카드매출 화면 개편(달력 + 항목 보강) 작업 중, 실제 응답 JSON을
    직접 캡처해 필드명을 재확인함 - 기존 코드가 아래 3가지를 잘못 매핑하고
    있었던 것을 발견해 함께 고침:
      - "amount"(거래금액 합계)는 input_amt가 아니라 total_amt(=amount 필드
        자체)여야 함. input_amt는 수수료를 뗀 "실입금액"이라 다른 값이었음
        (예: 합계 104,016원인데 input_amt는 102,456원 - 수수료 1,560원 차이).
      - "supplyAmt"(공급가액)는 service_amt가 아니라 supply_amt여야 함.
        service_amt는 실제로 확인해보니 그냥 "0"으로만 찍히는 무관한 필드.
      - "taxAmt"(세액/부가세)는 tax_gain_amt가 아니라 tax_amt여야 함.
        tax_gain_amt는 이름과 달리 실제로는 공급가액과 같은 값이 찍힘
        (세액이 아님 - 이름만 보고 매핑했다가 생긴 오류로 추정).
    추가로 카드사/할부/신용·체크 구분도 이번에 새로 확인한 실제 필드로 채움:
      - issuer(카드사/발급사): isu_name/mbr_isu_name (예: "신한","삼성" 등 -
        화면의 "매입사" 컬럼과 동일한 값. SemPlus의 "발급사"에 대응).
      - installment(할부): install_period ("00"=일시불, 그 외엔 개월수).
      - txnType(신용/체크 구분): check_card_flag (공백="신용", "Y"="체크").
    """
    date = (
        _valid_yyyymmdd(row.get("auth_date"))
        or _valid_yyyymmdd(row.get("money_rcv_date"))
        or _valid_yyyymmdd(row.get("settle_date"))
        or _valid_yyyymmdd(row.get("transaction_date"))
        or ""
    )
    install_period = str(row.get("install_period") or "").strip()
    installment = "" if install_period in ("", "00") else install_period
    check_flag = str(row.get("check_card_flag") or "").strip()
    return {
        "id": row.get("transaction_id") or row.get("reference_no") or row.get("serial_no"),
        "date": date,
        "time": row.get("tran_time") or "",
        "merchant": row.get("jijum_name") or "",
        "txnType": "체크" if check_flag else "신용",
        "settleStatus": row.get("capture_status_name") or row.get("result_name") or "",
        "issuer": row.get("isu_name") or row.get("mbr_isu_name") or "",
        "installment": installment,
        "cardNoMasked": row.get("card_no") or "",
        "approvalNo": row.get("reference_no") or "",
        "amount": row.get("total_amt") or row.get("amount") or row.get("input_amt") or 0,
        "supplyAmt": row.get("supply_amt") or 0,
        "taxAmt": row.get("tax_amt") or 0,
        "source": "moneyon",
        "raw": row,
    }


async def main():
    date_to = datetime.date.today()
    date_fr = date_to - datetime.timedelta(days=LOOKBACK_DAYS)
    fr_str = date_fr.strftime("%y%m%d")
    to_str = date_to.strftime("%y%m%d")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        try:
            await login(page)
            await page.goto(DETAIL_URL, wait_until="domcontentloaded")

            all_rows = []
            page_no = 1
            while True:
                data = await fetch_detail_page(page, fr_str, to_str, page_no)
                rows = data.get("data") or []
                all_rows.extend(rows)
                total = data.get("TOTROWS", len(rows))
                if len(all_rows) >= total or not rows:
                    break
                page_no += 1
                if page_no > 50:  # 안전장치: 무한루프 방지
                    print(f"[경고] 페이지가 50페이지를 넘어 중단합니다 (TOTROWS={total})")
                    break

            records = [_to_record(r) for r in all_rows if r]
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
