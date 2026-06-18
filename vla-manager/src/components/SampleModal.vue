<template>
    <dialog 
      ref="dialog"
      class="modern-modal"
      @click="handleBackdropClick"
    >
      <div class="modal-content">
        <header>
          <h3>{{ props.title ?? 'Insert sample JSON' }}</h3>
        </header>

        <section class="modal-body">
          <!-- File Upload -->
          <section>
            <FileSelector @upload="handleFileUpload" />
          </section>
    
          <!-- Text Input -->
          <section class="paste-area">
            <label for="json-input">Or paste JSON here:</label>
            <div class="paste-json">
              <textarea
                id="json-textarea"
                v-model="jsonText"
                @input="handleTextInput"
                placeholder="Paste your JSON here..."
                rows="20"
                ></textarea>
              <vue-json-pretty
                id="json-input"
                :data="parsedData"
                :virtual="true"
                :height="350"
                :showLineNumber="true"
                :showDoubleQuotes="false"
              />
            </div>
          </section>

          <!-- Dev Picker -->
          <section class="pick-area">
            <label>Or choose a sample from below:</label>
            <div class="pick-options">
              <button
                v-for="d in dummySamples"
                :key="d.name"
                @click="loadSample(d.name)"
              >
                {{ d.name }}
              </button>
            </div>
          </section>
    
          <!-- Error Display -->
          <section v-if="error" class="error-message">
            <strong>Error:</strong> {{ error }}
          </section>
        </section>
        
        <footer>
          <!-- Control Buttons -->
          <button @click="clearAll" class="clear-button">
            Clear All
          </button>
          <button @click="parseJSON" class="parse-button" :disabled="!jsonText.trim()">
            Parse JSON
          </button>
          <button @click="selectSample" class="select-button" :disabled="!jsonText.trim()">
            Select
          </button>
        </footer>
      </div>
    </dialog>
</template>

<script setup>
  import { ref } from 'vue'
  import VueJsonPretty from 'vue-json-pretty'
  import FileSelector from './FileSelector.vue'
  import movieJson from '../data/movie.json'
  import xapiJson from '../data/xapi.json'
  import 'vue-json-pretty/lib/styles.css'

  const dummySamples = [
    { name: 'Movie', sample: movieJson },
    { name: 'xAPI Statement', sample: xapiJson },
  ]

  const dialog = ref(null)
  const jsonText = ref('')
  const error = ref(null)
  const parsedData = ref(null)

  const showModal = async () => dialog.value?.showModal()

  const loadSample = async (name) => {
    const sample = dummySamples.find((s) => s.name === name)
    jsonText.value = JSON.stringify(sample, null, 2)
    parseJSON()
  }

  const handleFileUpload = async (file, progressCallback) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        jsonText.value = e.target.result
        parseJSON()
      } catch (err) {
        error.value = `Failed to read file: ${err.message}`
      }
    }
    reader.onerror = () => {
      error.value = 'Failed to read file'
    }
    reader.readAsText(file)
  }

  const handleTextInput = () => {
    if (error) error.set = null
    parseJSON()
  }

  const parseJSON = () => {
    try {
      parsedData.value = JSON.parse(jsonText.value)
      error.value = null
    } catch (err) {
      error.value = `Invalid JSON: ${err.message}`
      parsedData.value = null
    }
  }

  const handleBackdropClick = (e) => {
    if (e.target === dialog.value) dialog.value?.close()
  }

  const clearAll = () => {
    jsonText.value = ''
    parsedData.value = null
    error.value = ''
  }

  const props = defineProps({ modelValue: Object, title: String })
  defineExpose({ show: showModal })

  const emit = defineEmits(['update:modelValue'])

  const selectSample = () => {
    emit('update:modelValue', parsedData.value)
    dialog.value?.close()
  }
</script>

<style scoped>
  .modern-modal::backdrop {
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    animation: backdropFadeIn 0.3s ease-out;
  }
  
  dialog {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    max-width: 50vw;
    max-height: 90vh;
    border: none;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    animation: dialogSlideIn 0.3s ease-out;
  }
  
  .paste-area {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .paste-json {
    display: flex;
    gap: 1rem;
  }
  
  .pick-area {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .pick-options {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .5rem;
  }
  
  h3 {
    margin: 0;
  }
  
  .modal-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 24px 0;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 16px;
    margin-bottom: 20px;
  }
  
  .modal-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }
  
  .modal-body {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  footer {
    display: flex;
    gap: 1rem;
    align-items: center;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .error-message {
    color: red;
  }

  /* Button styles */
  .parse-button {
    background: #3b82f6;
    color: white;
  }
  
  .select-button {
    background: #08c41e;
    font-weight: bold;
  }
  
  .clear-button {
    background: transparent;
    color: #374151;
    border: 1px solid #d1d5db;
  }
  
  /* Animations */
  @keyframes dialogSlideIn {
    from {
      opacity: 0;
      transform: scale(0.95) translateY(-10px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }
  
  @keyframes backdropFadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  
  /* Responsive adjustments */
  @media (max-width: 640px) {
    .modern-modal {
      width: 95vw;
    }
    
    .modal-header,
    .modal-body,
    .modal-footer {
      padding-left: 16px;
      padding-right: 16px;
    }
    
    .modal-footer {
      flex-direction: column-reverse;
    }
    
    .btn-primary,
    .btn-secondary {
      width: 100%;
    }
  }
</style>
