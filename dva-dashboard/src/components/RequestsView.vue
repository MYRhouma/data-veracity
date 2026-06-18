<template>
  <section>
    <div class="card-container">
      <p class="placeholder" v-if="reqs.length === 0">No requests yet</p>
      <RequestCard :req="req" v-for="req in reqs" :key="req.requestID"/>
    </div>
  </section>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import RequestCard from './RequestCard.vue'
  
  const reqs = ref([])
  
  onMounted(async () => {
    try {
      let url = '/api/info/requests'
      const reqsFromAPI = await axios.get(url)
      reqs.value = reqsFromAPI.data
    } catch (err) {
      console.error('Fetch error:', err)
    }
  })
</script>

<style scoped>
  .card-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }

  .placeholder {
    font-style: italic;
  }

  @media (max-width: 1670px) {
    .card-container {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  @media (max-width: 1350px) {
    .card-container {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 980px) {
    .card-container {
      grid-template-columns: repeat(1, 1fr);
    }
  }
</style>
