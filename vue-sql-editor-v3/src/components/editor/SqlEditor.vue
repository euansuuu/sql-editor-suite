<template>
  <div class="sql-editor-container" ref="containerRef">
    <div ref="editorRef" class="sql-editor"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { EditorState, EditorStateConfig } from '@codemirror/state'
import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightSpecialChars, drawSelection, rectangularSelection, crosshairCursor } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { syntaxHighlighting, defaultHighlightStyle, foldGutter, foldKeymap, indentOnInput, bracketMatching } from '@codemirror/language'
import { autocompletion, closeBrackets, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete'
import { StandardSQL, sql, MySQL, PostgreSQL, SQLite } from '@codemirror/lang-sql'
import { lintKeymap } from '@codemirror/lint'
import { useEditorStore } from '../../stores/editor'

interface Props {
  modelValue: string
  dialect?: string
  readonly?: boolean
  lineWrapping?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
  (e: 'cursorChange', position: { line: number; column: number }): void
  (e: 'focus'): void
  (e: 'blur'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  dialect: 'hive',
  readonly: false,
  lineWrapping: true
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLElement>()
const editorRef = ref<HTMLElement>()
let editorView: EditorView | null = null

const editorStore = useEditorStore()

// SQL 方言配置
const getDialectConfig = (dialect: string) => {
  const dialectMap: Record<string, any> = {
    mysql: MySQL,
    postgresql: PostgreSQL,
    spark: StandardSQL,
    hive: StandardSQL,
    impala: StandardSQL,
    trino: StandardSQL,
    sqlite: SQLite
  }
  return dialectMap[dialect] || StandardSQL
}

// 创建编辑器
const createEditor = () => {
  if (!editorRef.value) return

  const dialectConfig = getDialectConfig(props.dialect)
  
  const extensions: EditorStateConfig['extensions'] = [
    lineNumbers(),
    highlightActiveLine(),
    highlightSpecialChars(),
    history(),
    foldGutter(),
    drawSelection(),
    EditorState.allowMultipleSelections.of(true),
    indentOnInput(),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    bracketMatching(),
    closeBrackets(),
    autocompletion(),
    rectangularSelection(),
    crosshairCursor(),
    sql({ dialect: dialectConfig }),
    keymap.of([
      ...closeBracketsKeymap,
      ...defaultKeymap,
      ...historyKeymap,
      ...foldKeymap,
      ...completionKeymap,
      ...lintKeymap,
      indentWithTab
    ]),
    EditorView.updateListener.of(update => {
      if (update.docChanged) {
        const value = update.state.doc.toString()
        emit('update:modelValue', value)
        emit('change', value)
      }
      if (update.selectionSet) {
        const cursor = update.state.selection.main.head
        const line = update.state.doc.lineAt(cursor)
        emit('cursorChange', {
          line: line.number - 1,
          column: cursor - line.from
        })
      }
    }),
    EditorView.theme({
      '&': {
        height: '100%',
        fontSize: `${editorStore.fontSize}px`
      },
      '.cm-scroller': {
        overflow: 'auto',
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace',
        lineHeight: '1.6'
      }
    })
  ]

  if (props.lineWrapping) {
    extensions.push(EditorView.lineWrapping)
  }

  if (props.readonly) {
    extensions.push(EditorView.editable.of(false))
  }

  const state = EditorState.create({
    doc: props.modelValue,
    extensions
  })

  editorView = new EditorView({
    state,
    parent: editorRef.value
  })
}

// 更新编辑器内容
const updateContent = (content: string) => {
  if (!editorView) return
  
  const currentContent = editorView.state.doc.toString()
  if (currentContent !== content) {
    editorView.dispatch({
      changes: {
        from: 0,
        to: currentContent.length,
        insert: content
      }
    })
  }
}

// 重新配置方言
const updateDialect = (dialect: string) => {
  if (!editorView) return
  
  const dialectConfig = getDialectConfig(dialect)
  editorView.dispatch({
    effects: EditorView.reconfigure.of([
      editorView.state.config.extensions.filter(ext => {
        // 过滤掉旧的 sql 配置
        return true
      }),
      sql({ dialect: dialectConfig })
    ])
  })
}

// 获取选中的文本
const getSelectedText = (): string => {
  if (!editorView) return ''
  const { main } = editorView.state.selection
  return editorView.state.sliceDoc(main.from, main.to)
}

// 获取光标位置的 SQL 语句
const getCurrentSqlStatement = (): string => {
  if (!editorView) return ''
  
  const cursor = editorView.state.selection.main.head
  const doc = editorView.state.doc.toString()
  
  // 查找当前语句的开始和结束
  let start = 0
  let end = doc.length
  
  // 向前查找分号
  for (let i = cursor - 1; i >= 0; i--) {
    if (doc[i] === ';') {
      start = i + 1
      break
    }
  }
  
  // 向后查找分号
  for (let i = cursor; i < doc.length; i++) {
    if (doc[i] === ';') {
      end = i + 1
      break
    }
  }
  
  return doc.slice(start, end).trim()
}

// 聚焦
const focus = () => {
  editorView?.focus()
}

// 格式化 SQL
const formatSql = () => {
  if (!editorView) return
  const sql = editorView.state.doc.toString()
  const formatted = editorStore.formatSql(sql, props.dialect as any)
  updateContent(formatted)
}

// 暴露方法
defineExpose({
  focus,
  formatSql,
  getSelectedText,
  getCurrentSqlStatement
})

watch(() => props.modelValue, (newVal) => {
  updateContent(newVal)
})

watch(() => props.dialect, (newDialect) => {
  updateDialect(newDialect)
})

watch(() => editorStore.fontSize, () => {
  if (editorView) {
    // 重新创建编辑器以应用新字体大小
    editorView.destroy()
    nextTick(() => {
      createEditor()
    })
  }
})

onMounted(() => {
  createEditor()
})

onUnmounted(() => {
  if (editorView) {
    editorView.destroy()
    editorView = null
  }
})
</script>

<style scoped>
.sql-editor-container {
  width: 100%;
  height: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.sql-editor {
  width: 100%;
  height: 100%;
}
</style>
