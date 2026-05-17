<script setup name="publishinform">
import OAMain from '@/components/OAMain.vue';
import { ref, reactive, onBeforeUnmount, shallowRef, onMounted } from "vue"
import '@wangeditor/editor/dist/css/style.css' 
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import staffHttp from '@/api/staffHttp';
import { ElMessage } from "element-plus"
import { useAuthStore } from '@/stores/auth';
import informHttp from '@/api/informHttp';
import { i18nChangeLanguage } from '@wangeditor/editor'
import { useRouter } from 'vue-router';

i18nChangeLanguage('en')

const authStore = useAuthStore()
const router = useRouter()

let informForm = reactive({
  title: '',
  content: '',
  department_ids: [],
  is_top: false
})
const rules = reactive({
  title: [{ required: true, message: "Please enter the title.", trigger: 'blur' }],
  content: [{ required: true, message: "Please enter the content.", trigger: 'blur' }],
  department_ids: [{ required: true, message: "Please select a department.", trigger: 'change' }]
})
let formRef = ref()
let formLabelWidth = "200px"
let departments = ref([])
let submitting = ref(false)

////////////// wangEditor //////////////
const editorRef = shallowRef()

// Add uploadFile button into the toolbar
const toolbarConfig = {
  insertKeys: {
    index: 22,
    keys: ['uploadFile']
  }
}
const editorConfig = {
  placeholder: "Please enter content...",

  MENU_CONF: {
    uploadImage: {
      server: `${import.meta.env.VITE_BASE_URL}/inform/image/upload`,
      fieldName: 'image',
      maxFileSize: 25 * 1024 * 1024,
      maxNumberOfFiles: 20,
      allowedFileTypes: ['image/*'],
      headers: {
        Authorization: "JWT " + authStore.token
      },
      timeout: 30 * 1000,

      customInsert(res, insertFn) {
        if (res.errno == 0) {
          const data = res.data[0]
          let url = import.meta.env.VITE_BASE_URL + data.url
          let href = import.meta.env.VITE_BASE_URL + data.href
          let alt = data.alt;
          insertFn(url, alt, href)
        } else {
          ElMessage.error(res.message)
        }
      },
      onFailed(file, res) {
        ElMessage.error(`${file.name} upload failed: ${res.message || ''}`)
      },
      onError(file, err, res) {
        if (file.size > 25 * 1024 * 1024) {
          ElMessage.error('Image size cannot exceed 25MB.')
        } else {
          ElMessage.error('Image upload failed.')
        }
      },
    },
    uploadFile: {
      server: `${import.meta.env.VITE_BASE_URL}/inform/file/upload`,
      fieldName: 'file',
      maxFileSize: 25 * 1024 * 1024,
      maxNumberOfFiles: 10,
      allowedFileTypes: [],
      headers: {
        Authorization: "JWT " + authStore.token
      },
      timeout: 30 * 1000,

      customInsert(res, insertFn) {
        if (res.errno == 0) {
          let url = import.meta.env.VITE_BASE_URL + res.data.url
          insertFn(url, res.data.name, url)
        } else {
          ElMessage.error(res.message)
        }
      },
      onFailed(file, res) {
        ElMessage.error(`${file.name} upload failed: ${res.message || ''}`)
      },
      onError(file, err, res) {
        if (file.size > 25 * 1024 * 1024) {
          ElMessage.error('File size cannot exceed 25MB.')
        } else {
          ElMessage.error('File upload failed.')
        }
      },
    }
  }
}
// editorConfig.MENU_CONF['uploadImage']
let mode = "default"


onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor == null) return
  editor.destroy()
})

const handleCreated = (editor) => {
  editorRef.value = editor // Store the editor instance
}

// Handle drag-and-drop of non-image files onto the editor
const onEditorDrop = (e) => {
  const files = Array.from(e.dataTransfer?.files || [])
  if (!files.length) return
  const nonImages = files.filter(f => !f.type.startsWith('image/'))
  if (!nonImages.length) return  // let wangEditor handle images natively

  e.preventDefault()
  e.stopPropagation()

  nonImages.forEach(async (file) => {
    if (file.size > 25 * 1024 * 1024) {
      ElMessage.error(`${file.name} exceeds 25MB limit.`)
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${import.meta.env.VITE_BASE_URL}/inform/file/upload`, {
        method: 'POST',
        headers: { Authorization: 'JWT ' + authStore.token },
        body: formData
      })
      const data = await res.json()
      if (data.errno === 0) {
        const url = import.meta.env.VITE_BASE_URL + data.data.url
        editorRef.value.insertNode({
          type: 'link',
          url,
          target: '_blank',
          children: [{ text: data.data.name }]
        })
      } else {
        ElMessage.error(data.message || `${file.name} upload failed.`)
      }
    } catch {
      ElMessage.error(`${file.name} upload failed.`)
    }
  })
}
////////////// wangEditor //////////////

onMounted(async () => {
  try {
    let data = await staffHttp.getAllDepartment()
    if (authStore.user.is_superuser) {
      // Superuser can choose any department
      departments.value = data
    } else {
      // Regular user can only choose their own department
      const userDeptId = authStore.user.department?.id
      departments.value = userDeptId
        ? data.filter(d => d.id === userDeptId)
        : []
    }
  } catch (detail) {
    ElMessage.error(detail)
  }
})

const onSubmit = () => {
  formRef.value.validate(async (valid, fields) => {
    if (valid) {
      submitting.value = true
      try {
        await informHttp.publishInform(informForm)
        ElMessage.success('Notification published successfully.')
        informForm.title = ''
        informForm.content = ''
        informForm.department_ids = []
        informForm.is_top = false
        editorRef.value.setHtml('')
        router.push({ name: 'inform_list' })
      } catch (detail) {
        ElMessage.error(detail)
      } finally {
        submitting.value = false
      }
    }
  })
}

const onDepartmentsChange = (value) => {
  if (value.includes(0) && value.length > 1) {
    informForm.department_ids = [0]
  }
}

</script>

<template>
  <OAMain title="Publish Notification" subtitle="Compose rich announcements and target the right audience.">
    <template #actions>
      <el-button icon="Back" @click="router.push({ name: 'inform_list' })">Back to List</el-button>
    </template>
    <el-card class="oa-panel publish-card">
      <el-form :model="informForm" :rules="rules" ref="formRef">
        <el-form-item label="Title" :label-width="formLabelWidth" prop="title">
          <el-input v-model="informForm.title" autocomplete="off" placeholder="Notification title" />
        </el-form-item>
        <el-form-item label="Visible Departments" :label-width="formLabelWidth" prop="department_ids">
          <el-select multiple v-model="informForm.department_ids" style="width: 100%" @change="onDepartmentsChange">
            <el-option :value="0" label="All Departments"></el-option>
            <el-option v-for="department in departments" :label="department.name" :value="department.id"
              :key="department.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="Pinned" :label-width="formLabelWidth">
          <el-switch v-model="informForm.is_top" active-text="Pin to top" />
        </el-form-item>
        <el-form-item label="Content" :label-width="formLabelWidth" prop="content">
          <div class="editor-shell" @drop="onEditorDrop" @dragover.prevent>
            <Toolbar class="editor-toolbar" :editor="editorRef" :defaultConfig="toolbarConfig"
              :mode="mode" />
            <Editor class="editor-body" v-model="informForm.content"
              :defaultConfig="editorConfig" :mode="mode" @onCreated="handleCreated" />
          </div>
        </el-form-item>
        <el-form-item>
          <div class="submit-row">
            <el-button @click="router.push({ name: 'inform_list' })">Cancel</el-button>
            <el-button type="primary" :loading="submitting" icon="Promotion" @click="onSubmit">Publish</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </OAMain>
</template>

<style scoped>
.publish-card {
  max-width: 1120px;
}

.editor-shell {
  width: 100%;
  overflow: hidden;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 8px;
  background: white;
}

.editor-toolbar {
  border-bottom: 1px solid rgba(37, 99, 235, 0.14);
}

.editor-body {
  height: 480px;
  overflow-y: hidden;
}

.submit-row {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
