const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('ctgdmnDesktop', {
  mode: 'desktop',
  backendUrl: 'http://127.0.0.1:8000'
});