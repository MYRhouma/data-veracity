<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title">{{ req.requestID }}</h5>
    </div>
    <div class="card-body">
      <table>
        <tr>
          <th style="width:44%"><v-icon name="fa-people-arrows" /> Data Exchange ID</th>
          <td class="data">{{ req.exchangeID }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-file-signature" /> Contract ID</th>
          <td class="data">{{ req.contractID }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-clock" /> Requested</th>
          <td class="data">{{ req.receivedDate }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-calculator" /> Evaluated</th>
          <td class="data">{{ req.evaluationDate }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-certificate" /> VC Issued</th>
          <td class="data">{{ req.vcIssuedDate }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-certificate" /> VC ID</th>
          <td class="data">{{ req.vcID }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-user" /> Attester</th>
          <td class="data">{{ req.attesterID }}</td>
        </tr>
      </table>

      <div class="badges">
        <span v-if="req.type == 'aov'" class="badge badge-aov"><v-icon name="fa-stamp" /> Attestation</span>
        <span v-else class="badge badge-pov"><v-icon name="fa-code" /> Proof</span>

        <span v-if="req.evaluationPassing" class="badge badge-success"><v-icon name="fa-check" /> Pass</span>
        <span v-else class="badge badge-danger"><v-icon name="fa-times" /> Fail</span>
      </div>

      <hr class="divider" />

      <h6 class="card-subtitle">Data</h6>
      <vue-json-pretty
        :data="req.data"
        :deep="0"
        :virtual="true"
        :height="100"
      />

      <hr class="divider" />

      <h6 class="card-subtitle">Evaluation Results</h6>
      <vue-json-pretty
        :data="JSON.parse(req.evaluationResults)"
        :deep="1"
        :virtual="true"
        :height="150"
      />
    </div>
  </div>
</template>

<script setup>
  defineProps(['req'])
</script>

<script>
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'

  export default {
    components: { VueJsonPretty }
  }
</script>

<style scoped>
  td {
    padding-left: 1rem;
  }

  .card {
    background-color: #F0EAFB;
    border-radius: 0.75rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
    overflow: hidden;
    transition: transform 0.1s, box-shadow 0.1s;
    display: flex;
    flex-direction: column;
    display: flex;
    flex-direction: column;
    text-align: left;
    height: 100%;
  }
  
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .card-header {
    height: 2rem;
    background-color: #4051b5;
    color: #fff;
    padding: 1rem;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .card-title {
    font-family: monospace;
    text-align: center;
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .card-body {
    padding: .6rem;

  }
  
  .divider {
    border: none;
    border-top: 1px solid #DDD;
    margin: 0.75rem 0;
  }
  
  .card-subtitle {
    font-size: 0.95rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    margin-top: 0;
    text-align: center;
    color: #333;
  }
  
  .results-list {
    list-style-type: disc;
    margin: 0;
    padding-left: 1.25rem;
    flex-grow: 1;
  }
  
  .results-list li {
    margin-bottom: 0.25rem;
    font-size: 0.9rem;
    color: #333;
  }
  
  .fw-semibold {
    font-weight: 600;
  }

  .badges {
    margin-top: 1rem;
    display: flex;
    gap: .25rem;
  }
  
  /* Badge overrides */
  .badge {
    padding: 0.5em;
    border-radius: 0.5rem;
    color: #fff;
  }
  .badge-success {
    background-color: #198754;
  }
  .badge-danger {
    background-color: #dc3545;
  }
  .badge-aov {
    background-color: #1e3fb9;
  }
  .badge-pov {
    background-color: #825f00;
  }

  .data {
    font-family: monospace;
  }

  pre {
    height: 4rem;
    overflow: auto;
  }
</style>
