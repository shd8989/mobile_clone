import pyautogui
import time
import sys

# ⚡ PyAutoGUI의 기본 동작 지연 시간 강제 해제
pyautogui.PAUSE = 0 

# 사용할 캡처 이미지 파일명
IMG_SUNDAY = 'sunday.png'
IMG_INSTRUCTOR = 'instructor.png'
IMG_TIME_2030 = 'time_2030.png'
BTN_IMG_RESERVE = 'btn_reserve.png'
IMG_POPUP_CONFIRM = 'popup_confirm.png'
IMG_MENU_RESERVE = 'menu_reserve.png' # 하단 탭의 '수업예약' 메뉴 이미지 추가

CONFIDENCE = 0.85

# ⚡ 스크롤 속도 및 양
SCROLL_UP_AMOUNT = 150       
SCROLL_DOWN_MAX = -2000      

# 요일 간 픽셀 간격 (일요일 기준)
X_OFFSET_PER_DAY = 70  
Y_OFFSET_DATE = 45     

def go_to_bottom():
    """스케줄 리스트를 최하단으로 초고속 이동"""
    for _ in range(3):  
        pyautogui.scroll(SCROLL_DOWN_MAX)
        time.sleep(0.05)

def book_classes():
    print("3초 뒤 예약 매크로를 시작합니다. 미러링 화면을 활성화해주세요...")
    time.sleep(3)
    
    # 1. 일요일 위치 찾기 (상단 기준점)
    try:
        sunday_loc = pyautogui.locateCenterOnScreen(IMG_SUNDAY, confidence=CONFIDENCE)
        if not sunday_loc:
            print("❌ 화면에서 상단 기준점인 '일요일(sunday.png)'을 찾을 수 없습니다.")
            sys.exit()
    except pyautogui.ImageNotFoundException:
        print("❌ 화면에서 상단 기준점인 '일요일(sunday.png)'을 찾을 수 없습니다.")
        sys.exit()

    tuesday_x = sunday_loc.x + (X_OFFSET_PER_DAY * 2)
    thursday_x = sunday_loc.x + (X_OFFSET_PER_DAY * 4)
    target_y = sunday_loc.y + Y_OFFSET_DATE

    target_days = [("화요일", tuesday_x, target_y), ("목요일", thursday_x, target_y)]

    for day_name, target_x, target_y in target_days:
        print(f"\n[{day_name}] 탐색 시작...")
        
        # 요일 날짜 클릭
        pyautogui.click(target_x, target_y)
        time.sleep(0.05)# 날짜 변경 로딩 대기

        # 2. 하단 '수업예약' 메뉴 아이콘 찾기 (스크롤 기준점)
        try:
            menu_loc = pyautogui.locateCenterOnScreen(IMG_MENU_RESERVE, confidence=CONFIDENCE)
            if menu_loc:
                # '수업예약' 아이콘에서 Y좌표를 150픽셀 위로 올려서 스케줄 리스트 영역에 마우스 올리기
                pyautogui.moveTo(menu_loc.x, menu_loc.y - 150)
                time.sleep(0.1)
            else:
                print("⚠️ 하단 '수업예약' 메뉴를 찾지 못해 임의의 위치에서 스크롤을 시도합니다.")
                pyautogui.moveTo(sunday_loc.x, sunday_loc.y + 300)
        except pyautogui.ImageNotFoundException:
            print("⚠️ 하단 '수업예약' 메뉴를 찾지 못해 임의의 위치에서 스크롤을 시도합니다.")
            pyautogui.moveTo(sunday_loc.x, sunday_loc.y + 300)
        
        # 스케줄을 최하단으로 빠르게 이동
        go_to_bottom()
        time.sleep(0.05)

        reserve_success = False
        
        # 3. 위로 스크롤하며 20:30 수업 초고속 탐색
        print("위로 스크롤하며 20:30 수업을 찾고 있습니다...")
        for i in range(15): 
            try:
                time_loc = pyautogui.locateOnScreen(IMG_TIME_2030, confidence=CONFIDENCE)
                instructor_loc = pyautogui.locateOnScreen(IMG_INSTRUCTOR, confidence=CONFIDENCE)
                
                if time_loc and instructor_loc:
                    reserve_btn = pyautogui.locateCenterOnScreen(BTN_IMG_RESERVE, confidence=CONFIDENCE)
                    if reserve_btn:
                        pyautogui.click(reserve_btn)
                        print(f"-> {day_name} 20:30 수업 '예약' 버튼 클릭!")
                        time.sleep(0.05)
                        
                        popup_btn = pyautogui.locateCenterOnScreen(IMG_POPUP_CONFIRM, confidence=CONFIDENCE)
                        if popup_btn:
                            pyautogui.click(popup_btn)
                            print(f"-> {day_name} 팝업창 '확인/예약' 클릭 성공!")
                        else:
                            print("❌ 팝업창 확인 버튼을 찾지 못했습니다.")
                            
                        reserve_success = True
                        time.sleep(0.05)
                        break 
                        
            except pyautogui.ImageNotFoundException:
                pass
            
            # 못 찾았다면 위로 스크롤
            if not reserve_success:
                pyautogui.scroll(SCROLL_UP_AMOUNT)
                time.sleep(0.05)
        
        if not reserve_success:
            print(f"❌ {day_name} 목록에서 20:30 노보람 강사 수업을 찾지 못했습니다.")

    print("\n모든 예약 매크로 프로세스가 종료되었습니다.")

if __name__ == "__main__":
    book_classes()