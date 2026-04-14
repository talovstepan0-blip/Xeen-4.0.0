// Файл: hud/main.js
const { app, BrowserWindow, Tray, Menu, ipcMain } = require('electron');
const path = require('path');

let mainWindow;
let tray = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 900,
        height: 700,
        frame: false,
        transparent: true,
        backgroundColor: '#0a0a0f',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        },
        alwaysOnTop: false,
        skipTaskbar: false
    });

    mainWindow.loadFile('index.html');
    
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function createTray() {
    // Создаем трей-иконку (заглушка)
    tray = new Tray(path.join(__dirname, 'icon.png'));
    
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Показать', click: () => mainWindow.show() },
        { label: 'Свернуть', click: () => mainWindow.hide() },
        { type: 'separator' },
        { label: 'Выход', click: () => app.quit() }
    ]);
    
    tray.setToolTip('Сиен HUD');
    tray.setContextMenu(contextMenu);
}

app.whenReady().then(() => {
    createWindow();
    createTray();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

ipcMain.handle('send-command', async (event, command) => {
    // Отправка команды через WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    return new Promise((resolve, reject) => {
        ws.onopen = () => {
            ws.send(JSON.stringify(command));
        };
        ws.onmessage = (event) => {
            resolve(JSON.parse(event.data));
        };
        ws.onerror = reject;
    });
});
