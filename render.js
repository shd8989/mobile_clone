const scheduleList = document.getElementById('scheduleList');
let htmlContent = '';

// 08시부터 22시까지 반복하면서 카드 HTML 생성
for (let i = 8; i <= 22; i++) {
    // 시간을 두 자리 숫자로 맞춤 (예: 8 -> 08)
    const startHour = i.toString().padStart(2, '0');
    
    htmlContent += `
    <div class="schedule-card">
        <div class="card-header">
        <div class="time-wrap">
            <span class="time-marker"></span>
            <span class="time-text">${startHour}:00 ~ ${startHour}:50</span>
        </div>
        <button class="action-btn">예약취소</button>
        </div>
        
        <div class="card-body">
        <span class="material-symbols-outlined avatar" style="font-variation-settings: 'FILL' 1;">account_circle</span>
        <div class="info">
            <div class="class-name">리포머</div>
            <div class="class-desc">노보람 강사 | 리포머 룸</div>
        </div>
        </div>
        
        <div class="card-footer">
        <span class="material-symbols-outlined">person</span>
        <span>예약 7 / 7명</span>
        </div>
    </div>
    `;
}

// 생성된 HTML을 스케줄 리스트 영역에 삽입
scheduleList.innerHTML = htmlContent;