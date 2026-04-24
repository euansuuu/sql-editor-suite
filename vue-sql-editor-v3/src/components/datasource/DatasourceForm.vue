<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="100px"
    size="default"
  >
    <el-form-item label="数据源名称" prop="name">
      <el-input v-model="formData.name" placeholder="请输入数据源名称" />
    </el-form-item>

    <el-form-item label="SQL 方言" prop="type">
      <el-select v-model="formData.type" placeholder="请选择 SQL 方言" style="width: 100%">
        <el-option label="Hive SQL" value="hive" />
        <el-option label="Impala SQL" value="impala" />
        <el-option label="Spark SQL" value="spark" />
        <el-option label="MySQL" value="mysql" />
        <el-option label="PostgreSQL" value="postgresql" />
        <el-option label="Trino/Presto" value="trino" />
      </el-select>
    </el-form-item>

    <el-form-item label="主机地址" prop="host">
      <el-input v-model="formData.host" placeholder="请输入主机地址" />
    </el-form-item>

    <el-form-item label="端口" prop="port">
      <el-input-number v-model="formData.port" :min="1" :max="65535" style="width: 100%" />
    </el-form-item>

    <el-form-item label="默认数据库" prop="database">
      <el-input v-model="formData.database" placeholder="请输入默认数据库名称" />
    </el-form-item>

    <el-form-item label="认证方式" prop="authType">
      <el-radio-group v-model="formData.authType">
        <el-radio label="basic">用户名密码</el-radio>
        <el-radio label="kerberos">Kerberos</el-radio>
      </el-radio-group>
    </el-form-item>

    <!-- 用户名密码认证 -->
    <template v-if="formData.authType === 'basic'">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="formData.username" placeholder="请输入用户名" />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
      </el-form-item>
    </template>

    <!-- Kerberos 认证 -->
    <template v-if="formData.authType === 'kerberos'">
      <el-form-item label="Principal" prop="kerberos.principal">
        <el-input v-model="formData.kerberos.principal" placeholder="user@REALM.COM" />
      </el-form-item>

      <el-form-item label="Keytab 文件">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".keytab"
          :on-change="handleKeytabChange"
          :on-remove="handleKeytabRemove"
        >
          <el-button size="small">选择 Keytab 文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              上传 .keytab 格式的 Kerberos 密钥文件
            </div>
          </template>
        </el-upload>
        <div v-if="keytabFile" class="file-info">
          已选择: {{ keytabFile.name }}
        </div>
      </el-form-item>
    </template>

    <el-form-item>
      <el-button type="primary" @click="testConnection" :loading="testing">
        测试连接
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import type { DataSource, SQLDialect } from '../../types'
import { useDatasourceStore } from '../../stores/datasource'

interface Props {
  datasource?: DataSource | null
}

interface Emits {
  (e: 'success'): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const datasourceStore = useDatasourceStore()
const formRef = ref<FormInstance>()
const uploadRef = ref()
const testing = ref(false)
const keytabFile = ref<File | null>(null)

// 表单数据
const formData = reactive<Omit<DataSource, 'id' | 'createdAt' | 'updatedAt'>>({
  name: '',
  type: 'hive' as SQLDialect,
  host: '',
  port: 10000,
  database: '',
  authType: 'basic',
  username: '',
  password: '',
  kerberos: {
    principal: ''
  }
})

// 表单验证规则
const formRules = reactive<FormRules>({
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择 SQL 方言', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' }
  ],
  database: [
    { required: true, message: '请输入默认数据库名称', trigger: 'blur' }
  ],
  'kerberos.principal': [
    {
      required: true,
      message: '请输入 Kerberos Principal',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (formData.authType === 'kerberos' && !value) {
          callback(new Error('请输入 Kerberos Principal'))
        } else {
          callback()
        }
      }
    }
  ]
})

// 处理 Keytab 文件选择
const handleKeytabChange = (file: UploadFile) => {
  keytabFile.value = file.raw || null
}

const handleKeytabRemove = () => {
  keytabFile.value = null
}

// 测试连接
const testConnection = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  testing.value = true
  try {
    const result = await datasourceStore.testConnection(formData)
    if (result.success) {
      ElMessage.success('连接测试成功！')
    } else {
      ElMessage.error(`连接测试失败: ${result.message || '未知错误'}`)
    }
  } catch (error) {
    ElMessage.error(`连接测试失败: ${(error as Error).message}`)
  } finally {
    testing.value = false
  }
}

// 提交表单
const submit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  try {
    // 如果有 keytab 文件，先上传
    let keytabPath: string | undefined
    if (keytabFile.value) {
      // 这里调用上传 keytab 的 API
      // const result = await uploadKeytab(keytabFile.value)
      // keytabPath = result.path
    }

    const data = {
      ...formData,
      kerberos: formData.authType === 'kerberos' ? {
        ...formData.kerberos,
        keytabPath
      } : undefined
    }

    if (props.datasource) {
      await datasourceStore.editDatasource(props.datasource.id, data)
      ElMessage.success('数据源更新成功')
    } else {
      await datasourceStore.addDatasource(data)
      ElMessage.success('数据源创建成功')
    }
    emit('success')
  } catch (error) {
    ElMessage.error(`操作失败: ${(error as Error).message}`)
  }
}

// 初始化表单数据
const initFormData = () => {
  if (props.datasource) {
    Object.assign(formData, {
      name: props.datasource.name,
      type: props.datasource.type,
      host: props.datasource.host,
      port: props.datasource.port,
      database: props.datasource.database,
      authType: props.datasource.authType,
      username: props.datasource.username || '',
      password: props.datasource.password || '',
      kerberos: props.datasource.kerberos || { principal: '' }
    })
  }
}

// 暴露方法
defineExpose({
  submit,
  validate: () => formRef.value?.validate()
})

// 初始化
initFormData()
</script>

<style scoped>
.file-info {
  margin-top: 8px;
  font-size: 12px;
  color: #52c41a;
}
</style>
