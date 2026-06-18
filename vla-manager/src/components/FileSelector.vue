<template>
  <label class="file-select">
    <div
      class="select-button"
      :class="{ 'has-file': modelValue, 'uploading': isUploading  }"
    >
      <span v-if="isUploading">
        Uploading… ({{ uploadProgress }}
      </span>
      <span v-else-if="modelValue">
        Uploaded File: <code>{{ modelValue.name }}</code>
      </span>
      <span v-else>
        Select File
      </span>
    </div>
    <input
      type="file"
      @change="handleFileChange"
      :disabled="isUploading"
    />
  </label>
</template>

<script setup>
  import { ref } from 'vue'

  const isUploading = ref(false)
  const uploadProgress = ref(0)

  const props = defineProps({ modelValue: File, autoUpload: Boolean })
  const emit = defineEmits([
    'update:modelValue',
    'upload',
    'upload-progress',
    'upload-success',
    'upload-error'
  ])

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    emit('update:modelValue', file)
    await uploadFile(file)
  }

  const uploadFile = async (file) => {
    isUploading.value = true
    uploadProgress.value = 0

    try {
      await emit('upload', file, (progress) => {
        uploadProgress.value = Math.round(progress)
        emit('upload-progress', progress)
      })

      emit('upload-success', file)
    } catch (err) {
      emit('upload-error', err)
    } finally {
      isUploading.value = false
      uploadProgress.value = 0
    }

  }
</script>

<style scoped>
  .file-select > .select-button {
    padding: 1rem;
    color: white;
    background-color: #333;
    border-radius: .3rem;
    text-align: center;
    font-weight: bold;
    cursor: pointer;
  }

  .file-select > .select-button.has-file {
    background-color: #2ea169;
  }

  .file-select > .select-button.uploading {
    background-color: #f39c12;
  }
  
  .file-select > input[type="file"] {
    display: none;
  }

  .file-select > input[type="file"]:disabled {
    cursor: not-allowed;
  }
</style>
