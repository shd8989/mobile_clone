# -*- coding: utf-8 -*-
"""
수업예약 매크로 (이미지 매칭 기반, cell 클릭 방식)

변경 요약
  1. 시작 시 tkinter 팝업으로 예약할 날짜를 입력받음 (M/D 형식)
  2. 최대 4개 날짜까지 입력 가능
  3. 입력 날짜의 '월'이 현재 달력과 다르면 자동으로 이전/다음달 버튼을 눌러 이동
  4. 날짜는 OCR 대신 '고정 이미지'(images/dates/<일>.png)로 탐색
  5. 20:00 시작 '노보람 강사' 수업을 아래 두 조건 중 하나로 판별:
       (A) 21:00 예약정보 '바로 위'에 '노보람 강사'가 있음
       (B) 20:00 강의 '바로 밑'에 '노보람 강사'가 있음
     → 조건 충족 시 해당 cell(카드)을 클릭
  6. 예전의 '예약' 버튼 클릭 → 삭제. cell 클릭 시 예약 팝업이 뜨며,
     팝업의 '확인' 버튼을 눌러 예약 확정

필요 패키지
    pip install pyautogui pillow pygetwindow
    (OCR/pytesseract는 더 이상 사용하지 않음)
"""

import sys
import time
import datetime

import pyautogui
import pygetwindow as gw

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    tk = None

# ⚡ PyAutoGUI 기본 지연 해제
pyautogui.PAUSE = 0

# =========================================================
# 🎯 사용자 설정
# =========================================================
# 미러링 창 제목의 '일부' (대소문자 무시). 확인:  py reserve_macro.py windows
MIRROR_WINDOW_TITLE = "Mobile Clone - 수업예약"

# 창 내부에서 달력이 차지하는 세로 구간 (0.0=맨위, 1.0=맨아래) - 날짜 이미지 탐색 범위 제한용
CAL_TOP_RATIO = 0.15
CAL_BOTTOM_RATIO = 0.60

# 이미지 매칭 신뢰도
CONFIDENCE = 0.85

# 스크롤 양
SCROLL_UP_AMOUNT = 150
SCROLL_DOWN_MAX = -2000

# '바로 위 / 바로 밑' 판정 시 허용하는 세로 픽셀 간격 (카드 1개 높이 근사)
#   너무 크면 다른 카드까지 인접으로 오인, 너무 작으면 인식 실패.
CARD_V_GAP = 220
# 같은 카드로 볼 때의 가로 정렬 허용 오차(px)
CARD_X_TOL = 400

# =========================================================
# 📷 이미지 파일 경로
# =========================================================
# 날짜 이미지는 images/dates/<일>.png 형태로 준비 (예: images/dates/7.png)
IMG_DATE_DIR = 'images/dates'

IMG_INSTRUCTOR = 'images/instructor_noboram.png'  # '노보람 강사' 텍스트 캡처
IMG_TIME_2000 = 'images/time_2000.png'            # '20:00' 시간 캡처
IMG_TIME_2100 = 'images/time_2100.png'            # '21:00' 시간 캡처
IMG_POPUP_CONFIRM = 'images/popup_confirm.png'    # 예약 확인 팝업의 '확인' 버튼
IMG_MENU_RESERVE = 'images/menu_reserve.png'      # 하단 '수업예약' 탭 (스크롤 기준점)
BTN_IMG_NEXT_MONTH = 'images/btn_next_month.png'  # 달력 '다음달' 화살표
BTN_IMG_PREV_MONTH = 'images/btn_prev_month.png'  # 달력 '이전달' 화살표


# =========================================================
# 창 / 영역 유틸
# =========================================================
def list_windows():
    """열려있는 창 제목 목록 출력 (MIRROR_WINDOW_TITLE 설정용)"""
    print("=== 현재 열려있는 창 목록 ===")
    for w in gw.getAllWindows():
        if w.title.strip() and w.visible and w.width > 0:
            print(f"  [{w.width}x{w.height}] '{w.title}'")
    print("=> 미러링 창 제목의 고유한 일부를 MIRROR_WINDOW_TITLE 에 넣으세요.")


def get_mirror_region():
    """미러링 창의 화면상 사각형 (left, top, width, height). 없으면 전체화면."""
    if MIRROR_WINDOW_TITLE:
        wins = [w for w in gw.getAllWindows()
                if MIRROR_WINDOW_TITLE.lower() in w.title.lower()
                and w.visible and w.width > 0 and w.height > 0]
        if wins:
            w = wins[0]
            return (w.left, w.top, w.width, w.height)
        print(f"⚠️ '{MIRROR_WINDOW_TITLE}' 창을 못 찾음 → 전체화면 사용. "
              f"( py reserve_macro.py windows 로 제목 확인 )")
    sw, sh = pyautogui.size()
    return (0, 0, sw, sh)


def get_calendar_region():
    """달력 날짜 이미지 탐색을 제한할 영역 (left, top, width, height)."""
    wx, wy, ww, wh = get_mirror_region()
    top = wy + int(wh * CAL_TOP_RATIO)
    height = int(wh * (CAL_BOTTOM_RATIO - CAL_TOP_RATIO))
    return (wx, top, ww, height)


def _locate(img, region=None):
    """locateCenterOnScreen 래퍼 (예외 삼킴). 못 찾으면 None."""
    try:
        return pyautogui.locateCenterOnScreen(img, confidence=CONFIDENCE, region=region)
    except Exception:
        return None


def _locate_box(img, region=None):
    """locateOnScreen 래퍼 → Box(left,top,width,height) 또는 None."""
    try:
        return pyautogui.locateOnScreen(img, confidence=CONFIDENCE, region=region)
    except Exception:
        return None


# =========================================================
# 1~2. 날짜 입력 팝업 (최대 4개)
# =========================================================
def input_dates_popup():
    """
    tkinter 팝업으로 예약 날짜 입력. 'M/D' 형식, 콤마 구분, 최대 4개.
    반환: [(month, day), ...]  (연도는 현재연도 기준, 지난 달이면 내년으로 롤오버)
    """
    if tk is None:
        # tkinter 불가 환경 → 콘솔 입력 대체
        raw = input("예약 날짜 입력 (예: 7/8, 7/9, 8/14) 최대 4개: ")
        return _parse_dates(raw)

    result = {'dates': None}
    root = tk.Tk()
    root.title("예약 날짜 입력")
    root.attributes('-topmost', True)
    root.geometry("360x180")

    tk.Label(root, text="예약할 날짜를 입력하세요 (최대 4개)",
             font=("맑은 고딕", 11, "bold")).pack(pady=(14, 2))
    tk.Label(root, text="형식: M/D  콤마로 구분   예) 7/8, 7/9, 8/14",
             fg="#555").pack()

    entry = tk.Entry(root, width=34, font=("맑은 고딕", 12), justify="center")
    entry.pack(pady=10)
    entry.focus_set()

    def on_ok(event=None):
        try:
            dates = _parse_dates(entry.get())
        except ValueError as e:
            messagebox.showerror("입력 오류", str(e), parent=root)
            return
        if not dates:
            messagebox.showerror("입력 오류", "날짜를 최소 1개 입력하세요.", parent=root)
            return
        if len(dates) > 4:
            messagebox.showerror("입력 오류", "날짜는 최대 4개까지만 입력할 수 있습니다.", parent=root)
            return
        result['dates'] = dates
        root.destroy()

    tk.Button(root, text="예약 시작", width=14, command=on_ok).pack(pady=6)
    root.bind('<Return>', on_ok)
    root.mainloop()
    return result['dates']


def _parse_dates(raw):
    """'7/8, 7/9, 8/14' → [(7,8),(7,9),(8,14)]  (검증 포함, 오타 방어)"""
    # 전각 콤마/슬래시, 공백 정규화
    raw = (raw.replace('，', ',')   # 전각 콤마
              .replace('／', '/')   # 전각 슬래시
              .replace(' ', ''))
    dates = []
    for token in raw.split(','):
        token = token.strip('/')      # 앞뒤에 붙은 여분 슬래시 제거 (예: '7/28/')
        if not token:
            continue
        parts = [p for p in token.split('/') if p != '']  # 빈 조각 제거
        if len(parts) != 2:
            raise ValueError(f"'{token}' 는 M/D 형식이 아닙니다. (예: 8/14)")
        try:
            month, day = int(parts[0]), int(parts[1])
        except ValueError:
            raise ValueError(f"'{token}' 에 숫자가 아닌 값이 있습니다. (예: 8/14)")
        if not (1 <= month <= 12) or not (1 <= day <= 31):
            raise ValueError(f"'{token}' 의 월/일 범위가 올바르지 않습니다.")
        dates.append((month, day))
    return dates


# =========================================================
# 3. 월(月) 이동
# =========================================================
def _resolve_year(month):
    """현재보다 과거 달이면 내년으로 간주."""
    today = datetime.date.today()
    year = today.year
    if month < today.month:
        year += 1
    return year


def navigate_to_month(target_month, displayed):
    """
    displayed(year,month) 기준으로 target_month 로 이동.
    다음/이전달 버튼을 필요한 횟수만큼 클릭. 새 displayed(year,month) 반환.
    """
    disp_year, disp_month = displayed
    target_year = _resolve_year(target_month)
    diff = (target_year * 12 + target_month) - (disp_year * 12 + disp_month)

    if diff == 0:
        return displayed

    btn_img = BTN_IMG_NEXT_MONTH if diff > 0 else BTN_IMG_PREV_MONTH
    region = get_mirror_region()
    for _ in range(abs(diff)):
        loc = _locate(btn_img, region=region)
        if not loc:
            print(f"⚠️ 월 이동 버튼({btn_img})을 찾지 못했습니다.")
            break
        pyautogui.click(loc)
        time.sleep(0.35)
    return (target_year, target_month)


# =========================================================
# 4. 날짜 이미지 클릭
# =========================================================
def find_date_position(day):
    """images/dates/<day>.png 를 달력 영역에서 찾아 중심 좌표 반환."""
    img = f"{IMG_DATE_DIR}/{day}.png"
    region = get_calendar_region()
    loc = _locate(img, region=region)
    if loc:
        return (loc.x, loc.y)
    # 영역 제한으로 못 찾으면 전체화면 재시도
    loc = _locate(img)
    return (loc.x, loc.y) if loc else None


def select_date(month, day, displayed):
    """월 이동 후 날짜 클릭. 갱신된 displayed 반환."""
    displayed = navigate_to_month(month, displayed)
    time.sleep(0.2)

    pos = find_date_position(day)
    if not pos:
        print(f"❌ 달력에서 '{day}일' 이미지({IMG_DATE_DIR}/{day}.png)를 찾지 못했습니다.")
        return displayed, False

    pyautogui.click(pos[0], pos[1])
    print(f"-> {month}/{day} 날짜 클릭 (x={pos[0]}, y={pos[1]})")
    time.sleep(0.3)
    return displayed, True


# =========================================================
# 5. 20:00 '노보람 강사' 카드 판별 + 클릭
# =========================================================
def go_to_bottom():
    """스케줄 리스트를 최하단으로 이동."""
    for _ in range(3):
        pyautogui.scroll(SCROLL_DOWN_MAX)
        time.sleep(0.05)


def _center_of_box(box):
    return (box.left + box.width / 2, box.top + box.height / 2)


def find_noboram_cell():
    """
    현재 화면에서 20:00 '노보람 강사' 카드를 찾아 '클릭할 좌표'를 반환.
    판정:
      (A) '노보람 강사'가 21:00 시간 '바로 위'  → instructor.y < t21.y, 간격 CARD_V_GAP 이내
      (B) '노보람 강사'가 20:00 시간 '바로 밑'  → instructor.y > t20.y, 간격 CARD_V_GAP 이내
    두 조건 중 하나라도 참이면 노보람 카드 좌표 반환, 아니면 None.
    """
    instr = _locate_box(IMG_INSTRUCTOR)
    if not instr:
        return None
    ins_cx, ins_cy = _center_of_box(instr)

    box20 = _locate_box(IMG_TIME_2000)
    box21 = _locate_box(IMG_TIME_2100)

    def aligned(cx):
        return abs(cx - ins_cx) <= CARD_X_TOL

    # (A) 21:00 이 노보람 바로 아래에 존재 (= 노보람이 21:00 바로 위)
    cond_a = False
    if box21:
        t21_cx, t21_cy = _center_of_box(box21)
        if aligned(t21_cx) and 0 < (t21_cy - ins_cy) < CARD_V_GAP:
            cond_a = True

    # (B) 20:00 이 노보람 바로 위에 존재 (= 노보람이 20:00 바로 밑)
    cond_b = False
    if box20:
        t20_cx, t20_cy = _center_of_box(box20)
        if aligned(t20_cx) and 0 < (ins_cy - t20_cy) < CARD_V_GAP:
            cond_b = True

    if cond_a or cond_b:
        # 카드(cell) 클릭 좌표 = 노보람 강사 텍스트 위치 (카드 내부이므로 카드 클릭으로 동작)
        return (int(ins_cx), int(ins_cy))
    return None


def confirm_reservation_popup(label):
    """cell 클릭 후 뜨는 예약 팝업의 '확인' 버튼 클릭."""
    for _ in range(10):
        btn = _locate(IMG_POPUP_CONFIRM)
        if btn:
            pyautogui.click(btn)
            print(f"-> {label} 예약 팝업 '확인' 클릭 성공!")
            time.sleep(0.1)
            return True
        time.sleep(0.1)
    print("❌ 예약 팝업의 '확인' 버튼을 찾지 못했습니다.")
    return False


def reserve_on_current_date(label):
    """현재 선택된 날짜에서 20:00 노보람 강사 카드를 찾아 클릭 → 예약 확정."""
    # 스크롤 기준점(하단 메뉴) 위로 마우스 이동
    menu = _locate(IMG_MENU_RESERVE)
    if menu:
        pyautogui.moveTo(menu.x, menu.y - 150)
    else:
        pyautogui.moveTo(pyautogui.size().width // 2, pyautogui.size().height // 2)
    time.sleep(0.1)

    go_to_bottom()
    time.sleep(0.05)

    print("위로 스크롤하며 20:00 '노보람 강사' 수업을 찾고 있습니다...")
    for _ in range(15):
        cell = find_noboram_cell()
        if cell:
            pyautogui.click(cell[0], cell[1])
            print(f"-> {label} 20:00 노보람 강사 cell 클릭! (x={cell[0]}, y={cell[1]})")
            time.sleep(0.2)
            confirm_reservation_popup(label)
            return True
        pyautogui.scroll(SCROLL_UP_AMOUNT)
        time.sleep(0.05)
    return False


# =========================================================
# 메인 흐름
# =========================================================
def book_classes():
    dates = input_dates_popup()
    if not dates:
        print("입력된 날짜가 없어 종료합니다.")
        return

    print(f"예약 대상: {['%d/%d' % (m, d) for m, d in dates]}")
    print("3초 뒤 시작합니다. 미러링(예약) 화면을 활성화해주세요...")
    time.sleep(3)

    # 현재 달력이 표시 중인 월 = 오늘 기준
    today = datetime.date.today()
    displayed = (today.year, today.month)

    for month, day in dates:
        label = f"{month}/{day}"
        print(f"\n[{label}] 탐색 시작...")

        displayed, ok = select_date(month, day, displayed)
        if not ok:
            continue

        if not reserve_on_current_date(label):
            print(f"❌ {label} 목록에서 20:00 노보람 강사 수업을 찾지 못했습니다.")

    print("\n모든 예약 매크로 프로세스가 종료되었습니다.")


# =========================================================
# 보정용 debug
# =========================================================
def debug_region():
    print("3초 뒤 캡처합니다. 미러링(예약 달력) 화면을 띄워주세요...")
    time.sleep(3)
    wx, wy, ww, wh = get_mirror_region()
    print(f"미러 창 영역: left={wx}, top={wy}, w={ww}, h={wh}")
    cx, cy, cwd, cht = get_calendar_region()
    shot = pyautogui.screenshot(region=(cx, cy, cwd, cht))
    shot.save("region_check.png")
    print("region_check.png 저장됨 (달력 날짜가 이 영역에 들어오는지 확인).")
    print("=> 날짜가 잘리면 CAL_TOP_RATIO / CAL_BOTTOM_RATIO 를 0.02~0.05씩 조정.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "windows":
        list_windows()
    elif mode == "debug":
        debug_region()
    else:
        book_classes()