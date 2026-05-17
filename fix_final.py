import os
o="E :\\\uff08\backup\\project\\Python\\AutoGame\\temp_vue_f3.vue"
c=open(o,"r",encoding="utf-8").read()

c=c.replace(
'"""async function closeKeyMapping() {
  await saveCurrentMapping()
  editingControlId.value = null
  editingDpadId.value = null  editingDpadDir.value = null
  contextMenu.value.show = false
  isRecordingSwipe.value = false
  pendingSwipe.value = false
  swipePoints.value = []
  teardownKeyCapture()
  showKeyMapping.value = false
  try {
    await callApi("remove_key_mapping")
  } catch {}
  isKeyMappingActive.value = false
}',
'"""async function closeKeyMapping() {
  await saveCurrentMapping()
  editingControlId.value = null
  editingDpadId.value = null  editingDpadDir.value = null
  contextMenu.value.show = false
  isRecordingSwipe.value = false
  pendingSwipe.value = false
  swipePoints.value = []
  teardownKeyCapture()
  showKeyMapping.value = false
  // Activate auto-hide mouse if enabled
  if (autoHideMouse.value) {
    callApi("set_key_mapping_auto_hide", true).catch(() => {})
  }
  isKayMappingActive.value = true}')

c=c.replace(
 'function onOverlayMouseDown(e) {
  if (isRecordingSwipe.value && kmCanvasRef.value) ',
'function onOverlayMouseDown(e) {
  if (pendingSwipe.value && kmCanvasRef.value) ')

c=c.replace('  try { await callApi("remove_key_mapping") } catch {}\n  stopPolling()','  stopPolling()')

c=c.replace('function onAutoHideChange() {\n  if (autoHideMouse.value) {\n    callApi("set_key_mapping_auto_hide", true).catch(() => {})\n  } else {\n    callApi("set_key_mapping_auto_hide", false).catch(() => {})\n  }\n  autoSave()}','function onAutoHideChange() {\n  autoSave()}')

open(o,"w",encoding="utf-8").write(c)
print("OK: "+costr(c.count("\n")))