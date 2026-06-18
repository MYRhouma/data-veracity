<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title">{{ pres.thread_id }}</h5>
    </div>
    <div class="card-body">
      <table>
        <tr>
          <th style="width:44%"><v-icon name="fa-people-arrows" /> Data Exchange ID</th>
          <td class="data">{{ pres.by_format.pres_request.indy.requested_attributes.attr_data_exchange_id.restrictions[0]['attr::data_exchange_id::value'] }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-plus" /> Created</th>
          <td class="data">{{ pres.created_at }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-pencil-alt" /> Updated</th>
          <td class="data">{{ pres.updated_at }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-user-cog" /> Role</th>
          <td class="data">{{ pres.role }}</td>
        </tr>
      </table>

      <hr class="divider" />

      <h6 class="card-subtitle">Revealed Attributes</h6>

      <table>
        <tr>
          <th style="width:44%"><v-icon name="fa-user-check" /> Subject</th>
          <td class="data">{{ pres.by_format.pres.indy.requested_proof.revealed_attrs.attr_subject.raw }}</td>
        </tr>
        <tr>
          <th><v-icon name="fa-people-arrows" /> Data Exchange ID</th>
          <td class="data">{{ pres.by_format.pres.indy.requested_proof.revealed_attrs.attr_data_exchange_id.raw }}</td>
        </tr>
        <tr>
          <th style="width:44%"><v-icon name="fa-file-signature" /> Contract ID</th>
          <td class="data">{{ pres.by_format.pres.indy.requested_proof.revealed_attrs.attr_contract_id.raw }}</td>
        </tr>
        <tr>
          <th style="width:44%"><v-icon name="fa-certificate" /> VC ID</th>
          <td class="data">{{ pres.by_format.pres.indy.requested_proof.revealed_attrs.attr_vc_id.raw }}</td>
        </tr>
        <tr>
          <th style="width:44%"><v-icon name="fa-user" /> Issuer</th>
          <td class="data">{{ pres.by_format.pres.indy.requested_proof.revealed_attrs.attr_issuer_id.raw }}</td>
        </tr>
      </table>
      
      <hr class="divider" />

      <div class="badges">
        <!-- TODO -->
        <span class="badge badge-success"><v-icon name="fa-check" /> Verified</span>
      </div>

      <hr class="divider" />

      <h6 class="card-subtitle">Revealed Results</h6>
      <vue-json-pretty
        :data="JSON.parse(pres.by_format.pres.indy.requested_proof.revealed_attrs.attr_payload.raw)"
        :deep="1"
        :virtual="true"
        :height="150"
      />
    </div>
  </div>
</template>

<script setup>
  defineProps(['pres'])
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
    background-color: #a80cad;
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
