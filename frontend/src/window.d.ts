export {};

declare global {
  interface Window {
    toggleScreencastFullscreen: () => void;
    disableJsonEditor: () => void;
    enableJsonEditor: () => void;
    saveFile: () => void;
    pywebview: any;
  }
}
