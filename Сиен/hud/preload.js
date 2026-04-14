// Файл: hud/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    sendCommand: (command) => ipcRenderer.invoke('send-command', command)
});
