import { Capacitor } from '@capacitor/core';
import { Keyboard, KeyboardResize } from '@capacitor/keyboard';
import { StatusBar, Style } from '@capacitor/status-bar';

let initialized = false;

function setKeyboardState(isOpen, keyboardHeight = 0) {
  const root = document.documentElement;
  root.classList.toggle('is-keyboard-open', isOpen);
  root.style.setProperty('--app-keyboard-height', isOpen ? `${Math.max(0, Number(keyboardHeight) || 0)}px` : '0px');
}

export async function initializeMobileRuntime() {
  if (initialized) return;
  initialized = true;

  const root = document.documentElement;
  root.style.setProperty('--app-keyboard-height', '0px');

  if (!Capacitor.isNativePlatform()) {
    return;
  }

  const platform = Capacitor.getPlatform();
  root.classList.add('is-capacitor', `is-capacitor-${platform}`);

  try {
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setOverlaysWebView({ overlay: false });
  } catch {
  }

  try {
    await Keyboard.setResizeMode({ mode: KeyboardResize.Body });
  } catch {
  }

  Keyboard.addListener('keyboardWillShow', event => {
    setKeyboardState(true, event?.keyboardHeight || 0);
  });

  Keyboard.addListener('keyboardDidHide', () => {
    setKeyboardState(false, 0);
  });
}
