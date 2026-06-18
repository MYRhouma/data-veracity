<template>
  <SampleModal v-model="sampleData" ref="sampleModal" />
  <SampleModal
    title="Upload test data"
    v-model="testData"
    ref="testModal"
    @update:modelValue="handleTestDataSelected"
  />
  <ReqModal
    :element="lastPath"
    ref="reqModal"
    @req-added="handleReqAdded"
  />
  <div class="content">
    <header>
      <h2>Create a new VLA</h2>
    </header>
    <div class="main-part">
      <button
        v-if="sampleData === null"
        @click="showSampleModal"
        class="add-button"
      >
        Add sample data
      </button>

      <div v-if="sampleData !== null" class="editor-area">
        <section class="column">
          <h3>Sample data structure</h3>
          <vue-json-pretty
            :data="sampleData"
            :showDoubleQuotes="false"
            :showLength="true"
            rootPath=""
            :virtual="true"
            :height="600"
            @node-click="onNodeClick"
          />
        </section>

        <section class="column toolbox">
          <h3>Toolbox</h3>

          <div class="req-box">
            <p
              v-if="lastPath === null"
              class="json-selection"
              style="font-style:italic"
            >
              Select a JSON element…
            </p>
            <p
              v-else
              class="json-selection"
            >
              {{ lastPath }}
            </p>
            <button
              @click="showReqModal"
            >
              Add requirement
            </button>
          </div>
        </section>

        <section class="column fragments">
          <h3>List of Fragments</h3>
          <div v-for="frag in fragments" class="fragment">
            <div class="fragment-display">
              <table>
                <tr>
                  <th>Fragment Name</th>
                  <td>{{ frag.requirement.name }}</td>
                </tr>
                <tr>
                  <th>Quality Engine</th>
                  <td><code>{{ frag.requirement.evaluationMethod.engine }}</code></td>
                </tr>
                <tr>
                  <th>Template String</th>
                  <td><code>{{ frag.requirement.evaluationMethod.implementationTemplate }}</code></td>
                </tr>
              </table>
              <vue-json-pretty :data="frag.data" />
              <button
                class="btn-test"
                @click="showTestModal(frag)"
              >
                Test
              </button>
              <div v-if="testedFragment === frag && testResult !== null">
                <h4>Evaluation results:</h4>
                <vue-json-pretty
                  :data="testResult"
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
    <footer>
      <button
        @click="handleCreateVLA"
        class="final-button"
        :disabled="sampleData === null"
      >
        Create VLA
      </button>
    </footer>
  </div>
</template>

<script setup>
  import { ref } from 'vue'
  import { toRaw } from 'vue'
  import { useRouter } from 'vue-router'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import axios from 'axios'

  import SampleModal from './SampleModal.vue'
  import ReqModal from './ReqModal.vue'

  const sampleModal = ref(null)
  const testModal = ref(null)
  const reqModal = ref(null)
  const genericReqModal = ref(null)

  const sampleData = ref(null)
  const testData = ref(null)
  const lastPath = ref(null)
  const fragments = ref([])

  const testedFragment = ref(null)
  const testResult = ref(null)

  const showSampleModal = () => sampleModal.value?.show()
  const showTestModal = (frag) => {
    testModal.value?.show()
    testedFragment.value = frag
  }
  const showReqModal = () => reqModal.value?.show()

  const onNodeClick = (node) => lastPath.value = node.path

  const handleReqAdded = (req) => {
    fragments.value.push(req)
  }

  const handleTestDataSelected = async () => {
    console.log(testedFragment.value)
    const body = {
      templateID: testedFragment.value.data.id,
      templateModel: testedFragment.value.data.model,
      data: testData.value
    }
    console.log('Sending evaluate request to backend with body:')
    console.log(body)
    let resp = null
    try {
      resp = await axios.post('/api/evaluate/from-template', body)
    } catch (err) {
      console.error('Error while evaluating on backend:')
      console.error(err)
      return
    }

    testResult.value = resp.data
  }

  const router = useRouter()

  const handleCreateVLA = async () => {
    console.log("posting")
    const body = {
      description: "Data is recent and valid",
      schema: {
        properties: {
          timestamp: {
            type: "string"
          },
          result: {
            type: "integer"
          }
        }
      },
      qualityTemplates: [...toRaw(fragments.value.map((f) => f.data))]
    }

    console.log(JSON.stringify(body))
    try {
      await axios.post('/api/vla/from-templates', body)
    } catch (err) {}
    alert(`Created VLA from ${fragments.value.length} fragments`)
    router.push({ path: "/list" })
  }
</script>

<style scoped>
  h2 {
    justify-self: stretch;
    border-top: 4px solid #e08b1b;
    border-bottom: 4px solid #e08b1b;
    padding: 1rem;
    text-align: center;
    margin: 0;
    margin-bottom: 1rem;
  }

  .content {
    flex-grow: 1;
    flex-direction: column;
    display: flex;
    padding: 1rem;
  }

  .main-part {
    flex-grow: 1;
    display: flex;
  }

  .add-button {
    font-size: 2rem;
    align-self: center;
    margin: auto;
  }

  .editor-area {
    flex-grow: 1;
    display: flex;
    justify-content: space-between;
  }

  .column {
    width: 30vw;
  }

  .toolbox {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }

  .fragments {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .json-selection {
    font-family: monospace;
    font-size: 1.25rem;
    background: #ccc;
    padding: 1rem;
    margin: 0 2rem;
    flex-grow: 1;
  }

  .fragment {
    padding: 1rem;
    border: 2px solid black;
    border-radius: 12px;
  }

  .fragment-display {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  footer {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  table {
    border: 1px solid black;
    border-collapse: collapse;
  }
  th, td {
    padding: .5rem;
  }
  th {
    border-right: 1px solid #444;
  }

  .btn-test {
    align-self: end;
  }

  .final-button {
    width: 15rem;
    background-color: #e08b1b;
    font-size: 1.5rem;
  }

  .req-box {
    align-self: stretch;
    text-align: center;
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    align-items: center;
  }
</style>
