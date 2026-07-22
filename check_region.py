import pyautogui, time

CAL_TOP_RATIO = 0.15
CAL_BOTTOM_RATIO = 0.48

print("3초 뒤 캡처합니다. 예약 화면(달력)을 띄워주세요...")
time.sleep(3)

w, h = pyautogui.size()
top = int(h * CAL_TOP_RATIO)
bottom = int(h * CAL_BOTTOM_RATIO)
shot = pyautogui.screenshot(region=(0, top, w, bottom - top))
shot.save("region_check.png")
print(f"화면크기: {w}x{h}, 잘라낸 세로: {top}~{bottom}px")
print("region_check.png 저장됨 - 열어서 달력 전체가 딱 들어오는지 확인하세요")