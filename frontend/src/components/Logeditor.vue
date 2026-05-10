<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, inject, type Ref } from 'vue'
import { EditorView } from '@codemirror/view'
import { EditorState, Compartment } from '@codemirror/state'
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
const themeCompartment = new Compartment()
let pollInterval: number | null = null

function getExtensions() {
  const extensions = [
    basicSetup,
    EditorState.readOnly.of(true),
    EditorView.editable.of(false),
  ]

  if (currentTheme?.value === 'dark') {
    extensions.push(themeCompartment.of([
      EditorView.theme({
        '&': {
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          color: '#e0e0e0',
          borderRadius: '6px',
        },
        '.cm-content': {
          fontFamily: 'Consolas, Monaco, Courier New, monospace',
          fontSize: '14px',
          lineHeight: '1.6',
          textAlign: 'left',
          caretColor: 'transparent',
          userSelect: 'text',
        },
        '.cm-line': {
          textAlign: 'left',
          userSelect: 'text',
        },
        '.cm-gutters': {
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#888',
        },
        '.cm-activeLineGutter': {
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        '.cm-activeLine': {
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
        },
        '.cm-selectionMatch': {
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        '&.cm-focused .cm-selectionBackground': {
          backgroundColor: 'rgba(100, 150, 255, 0.3)',
        },
        '.cm-selectionBackground': {
          backgroundColor: 'rgba(100, 150, 255, 0.2)',
        },
        '&.cm-focused .cm-cursor': {
          display: 'none',
        },
      }),
    ]))
  } else {
    extensions.push(themeCompartment.of([
      EditorView.theme({
        '&': {
          backgroundColor: 'rgba(0, 0, 0, 0.03)',
          color: '#1F2430',
          borderRadius: '6px',
        },
        '.cm-content': {
          fontFamily: 'Consolas, Monaco, Courier New, monospace',
          fontSize: '14px',
          lineHeight: '1.6',
          textAlign: 'left',
          userSelect: 'text',
        },
        '.cm-line': {
          textAlign: 'left',
          userSelect: 'text',
        },
        '.cm-gutters': {
          backgroundColor: 'rgba(0, 0, 0, 0.02)',
          borderRight: '1px solid rgba(0, 0, 0, 0.1)',
          color: '#888',
        },
        '.cm-activeLineGutter': {
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
        },
        '.cm-activeLine': {
          backgroundColor: 'rgba(0, 0, 0, 0.03)',
        },
        '.cm-selectionMatch': {
          backgroundColor: 'rgba(100, 150, 255, 0.2)',
        },
        '&.cm-focused .cm-selectionBackground': {
          backgroundColor: 'rgba(100, 150, 255, 0.3)',
        },
        '.cm-selectionBackground': {
          backgroundColor: 'rgba(100, 150, 255, 0.2)',
        },
        '&.cm-focused .cm-cursor': {
          display: 'none',
        },
      }),
    ]))
  }

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

watch(() => currentTheme?.value, () => {
  if (editorView) {
    editorView.dispatch({
      effects: themeCompartment.reconfigure(
        currentTheme?.value === 'dark'
          ? [
              EditorView.theme({
                '&': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  color: '#e0e0e0',
                  borderRadius: '6px',
                },
                '.cm-content': {
                  fontFamily: 'Consolas, Monaco, Courier New, monospace',
                  fontSize: '14px',
                  lineHeight: '1.6',
                  textAlign: 'left',
                  caretColor: 'transparent',
                  userSelect: 'text',
                },
                '.cm-line': {
                  textAlign: 'left',
                  userSelect: 'text',
                },
                '.cm-gutters': {
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#888',
                },
                '.cm-activeLineGutter': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
                '.cm-activeLine': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                },
                '.cm-selectionMatch': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
                '&.cm-focused .cm-selectionBackground': {
                  backgroundColor: 'rgba(100, 150, 255, 0.3)',
                },
                '.cm-selectionBackground': {
                  backgroundColor: 'rgba(100, 150, 255, 0.2)',
                },
                '&.cm-focused .cm-cursor': {
                  display: 'none',
                },
              }),
            ]
          : [
              EditorView.theme({
                '&': {
                  backgroundColor: 'rgba(0, 0, 0, 0.03)',
                  color: '#1F2430',
                  borderRadius: '6px',
                },
                '.cm-content': {
                  fontFamily: 'Consolas, Monaco, Courier New, monospace',
                  fontSize: '14px',
                  lineHeight: '1.6',
                  textAlign: 'left',
                  userSelect: 'text',
                },
                '.cm-line': {
                  textAlign: 'left',
                  userSelect: 'text',
                },
                '.cm-gutters': {
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  borderRight: '1px solid rgba(0, 0, 0, 0.1)',
                  color: '#888',
                },
                '.cm-activeLineGutter': {
                  backgroundColor: 'rgba(0, 0, 0, 0.05)',
                },
                '.cm-activeLine': {
                  backgroundColor: 'rgba(0, 0, 0, 0.03)',
                },
                '.cm-selectionMatch': {
                  backgroundColor: 'rgba(100, 150, 255, 0.2)',
                },
                '&.cm-focused .cm-selectionBackground': {
                  backgroundColor: 'rgba(100, 150, 255, 0.3)',
                },
                '.cm-selectionBackground': {
                  backgroundColor: 'rgba(100, 150, 255, 0.2)',
                },
                '&.cm-focused .cm-cursor': {
                  display: 'none',
                },
              }),
            ]
      ),
    })
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
