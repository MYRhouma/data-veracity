<template>
  <Header />

  <div class="content-wrapper">
    <router-view />
  </div>
</template>

<script setup>
  import Header from './components/Header.vue'
</script>

<style scoped>
  .content-wrapper {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
  }
</style>
