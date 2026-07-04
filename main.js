const { app, BrowserWindow } = require('electron');
const path = require('path');

function createMobileWindow() {
  const win = new BrowserWindow({
    width: 360,          // 모바일 일반 가로 폭
    height: 740,         // 모바일 일반 세로 높이
    resizable: false,    // 사용자가 창 크기를 조절하지 못하도록 고정 (매크로 좌표 유지용)
    maximized: false,    // 최대화 방지
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // 메뉴바 숨기기 (실제 앱처럼 보이게)
  win.setMenu(null);

  // 불러올 HTML 파일
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createMobileWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMobileWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});