<script setup lang="ts">
import { ref, onMounted, onUnmounted, inject, type Ref } from 'vue'
import { EditorView } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { keymap } from '@codemirror/view'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'

const basicSetup = [
  keymap.of(defaultKeymap),
  keymap.of([indentWithTab]),
]

type Theme = 'light' | 'dark'

const currentTheme = inject<Ref<Theme>>('theme')

const editorRef = ref<HTMLDivElement | null>(null)
let editorView: EditorView | null = null
let pollInterval: number | null = null

function getExtensions() {
  const extensions = [
    basicSetup,
    EditorState.readOnly.of(true),
    EditorView.editable.of(false),
    EditorView.lineWrapping,
  ]

  return extensions
}

async function loadLogs() {
  try {
    if ((window as any).pywebview && (window as any).pywebview.api) {
      const content = await (window as any).pywebview.api.get_memory_logs()
      if (editorView && editorView.state.doc.toString() !== content) {
        editorView.dispatch({
          changes: {
            from: 0,
            to: editorView.state.doc.length,
            insert: content,
          },
        })
        editorView.dispatch({
          effects: EditorView.scrollIntoView(
            content.length,
            { y: 'end' }
          )
        })
      }
    }
  } catch (e) {
    console.error('加载日志失败:', e)
  }
}

onMounted(() => {
  if (editorRef.value) {
    editorView = new EditorView({
      state: EditorState.create({
        doc: '加载中...',
        extensions: getExtensions(),
      }),
      parent: editorRef.value,
    })
  }

  loadLogs()

  pollInterval = window.setInterval(() => {
    loadLogs()
  }, 1000)
})

onUnmounted(() => {
  if (editorView) {
    editorView.destroy()
  }
  editorView = null
  if (pollInterval !== null) {
    clearInterval(pollInterval)
  }
})
</script>

<style src="./Logeditor.css" scoped></style>

<template>
  <div class="log-editor" :data-theme="currentTheme">
    <div class="editor-header">
      <span class="file-title">实时日志</span>
    </div>
    <div class="editor-container">
      <div ref="editorRef" class="codemirror-editor"></div>
    </div>
  </div>
</template>