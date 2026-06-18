<template>
  <section>
    <div class="card-container">
      <p class="placeholder" v-if="creds.length === 0">No credentials yet</p>
      <CredentialCard :cred="cred" v-for="cred in creds" :key="cred.attrs.vc_id"/>
    </div>
  </section>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import CredentialCard from './CredentialCard.vue'
  
  const creds = ref([])
  
  onMounted(async () => {
    try {
      let url = '/api/credentials'
      if (import.meta.env.MODE === 'production') {
        const BACKEND_URL = import.meta.env.VITE_BACKEND_BASE_URL || 'http://localhost:3000'
	url = `${BACKEND_URL}${url}`
      }
      const credsFromAPI = await axios.get(url)
      creds.value = credsFromAPI.data
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
