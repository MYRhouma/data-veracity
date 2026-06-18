<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title">{{ cred.attrs.vc_id }}</h5>
    </div>
    <div class="card-body">
      <vue-json-pretty
        :data="cred"
        :deep="1"
      />
    </div>
  </div>
</template>

<script setup>
  defineProps(['cred'])
</script>

<script>
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'

  export default {
    components: { VueJsonPretty }
  }
</script>

<style scoped>
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
    background-color: #135207;
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
</style>
