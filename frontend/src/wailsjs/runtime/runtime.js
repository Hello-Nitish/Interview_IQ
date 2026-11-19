export function LogInfo(message) {
  if (window['runtime'] && window['runtime']['LogInfo']) {
    window['runtime']['LogInfo'](message);
  } else {
    console.log('[Wails Runtime]', message);
  }
}

export function LogError(message) {
  if (window['runtime'] && window['runtime']['LogError']) {
    window['runtime']['LogError'](message);
  } else {
    console.error('[Wails Runtime]', message);
  }
}
