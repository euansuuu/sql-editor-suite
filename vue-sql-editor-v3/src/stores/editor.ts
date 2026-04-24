import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SQLDialect } from '../types'
import { formatDialect, mariadb, mysql, postgresql, spark, trino } from 'sql-formatter'

// 方言映射
const dialectMap: Record<SQLDialect, any> = {
  mysql: mysql,
  postgresql: postgresql,
  hive: spark,
  impala: spark,
  spark: spark,
  trino: trino
}

export const useEditorStore = defineStore('editor', () => {
  // 状态
  const currentDialect = ref<SQLDialect>('hive')
  const fontSize = ref(14)
  const theme = ref<'light' | 'dark'>('light')
  const showLineNumbers = ref(true)
  const autoFormat = ref(false)

  // 计算属性
  const dialectOptions = computed(() => [
    { label: 'Hive SQL', value: 'hive' },
    { label: 'Impala SQL', value: 'impala' },
    { label: 'Spark SQL', value: 'spark' },
    { label: 'MySQL', value: 'mysql' },
    { label: 'PostgreSQL', value: 'postgresql' },
    { label: 'Trino/Presto', value: 'trino' }
  ])

  // 设置 SQL 方言
  const setDialect = (dialect: SQLDialect) => {
    currentDialect.value = dialect
  }

  // 设置字体大小
  const setFontSize = (size: number) => {
    fontSize.value = size
  }

  // 设置主题
  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
  }

  // 切换显示行号
  const toggleLineNumbers = () => {
    showLineNumbers.value = !showLineNumbers.value
  }

  // SQL 格式化
  const formatSql = (sql: string, dialect?: SQLDialect): string => {
    if (!sql.trim()) return sql

    try {
      const targetDialect = dialect || currentDialect.value
      const formatter = dialectMap[targetDialect] || spark

      return formatDialect(sql, {
        dialect: formatter,
        tabWidth: 2,
        keywordCase: 'upper',
        linesBetweenQueries: 2,
        indentStyle: 'standard'
      })
    } catch (error) {
      console.warn('SQL format failed:', error)
      return sql
    }
  }

  // 提取 SQL 语句（支持多语句分割）
  const extractSqlStatements = (sql: string): string[] => {
    // 简单的分号分割，忽略引号内的分号
    const statements: string[] = []
    let current = ''
    let inSingleQuote = false
    let inDoubleQuote = false
    let inBacktick = false

    for (let i = 0; i < sql.length; i++) {
      const char = sql[i]

      if (char === "'" && !inDoubleQuote && !inBacktick) {
        inSingleQuote = !inSingleQuote
      } else if (char === '"' && !inSingleQuote && !inBacktick) {
        inDoubleQuote = !inDoubleQuote
      } else if (char === '`' && !inSingleQuote && !inDoubleQuote) {
        inBacktick = !inBacktick
      }

      if (char === ';' && !inSingleQuote && !inDoubleQuote && !inBacktick) {
        const statement = current.trim()
        if (statement) {
          statements.push(statement)
        }
        current = ''
      } else {
        current += char
      }
    }

    const lastStatement = current.trim()
    if (lastStatement) {
      statements.push(lastStatement)
    }

    return statements
  }

  // 生成 SELECT * 查询
  const generateSelectQuery = (database: string, table: string, limit = 100): string => {
    return `SELECT *\nFROM \`${database}\`.\`${table}\`\nLIMIT ${limit};`
  }

  // 生成 COUNT 查询
  const generateCountQuery = (database: string, table: string): string => {
    return `SELECT COUNT(*) AS total\nFROM \`${database}\`.\`${table}\`;`
  }

  // 生成 DESCRIBE 查询
  const generateDescribeQuery = (database: string, table: string): string => {
    return `DESCRIBE \`${database}\`.\`${table}\`;`
  }

  return {
    currentDialect,
    fontSize,
    theme,
    showLineNumbers,
    autoFormat,
    dialectOptions,
    setDialect,
    setFontSize,
    setTheme,
    toggleLineNumbers,
    formatSql,
    extractSqlStatements,
    generateSelectQuery,
    generateCountQuery,
    generateDescribeQuery
  }
})
