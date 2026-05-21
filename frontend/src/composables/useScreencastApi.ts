function ensureApi() {
  if (!(window as any).pywebview?.api) throw new Error("pywebview API is not available")
}

async function callApi(method: string, ...args: any[]): Promise<any> {
  ensureApi()
  return await (window as any).pywebview.api[method](...args)
}

function base64ToBytes(payload: string) {
  return Uint8Array.from(atob(payload), c => c.charCodeAt(0))
}

export { callApi, base64ToBytes }
