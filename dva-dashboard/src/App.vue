<template>
  <Header />

  <div class="content-wrapper">
    <sidebar-menu
      :menu="menu"
      width="220px"
      :relative="true"
      theme="white-theme"
    />

    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
  import Header from './components/Header.vue'
</script>

<script>
export default {
  name: 'App',
  data () {
    return {
      menu: [
        { header: 'Navigation' },
        {
          href: '/requests',
          title: 'Attestations',
          icon: {
            element: 'v-icon',
            attributes: { name: 'fa-list-ul' }
          }
        },
        {
          href: '/verifications',
          title: 'Verifications',
          icon: {
            element: 'v-icon',
            attributes: { name: 'fa-check-double' }
          }
        },
        {
          href: '/credentials',
          title: 'Credentials',
          icon: {
            element: 'v-icon',
            attributes: { name: 'fa-certificate' }
          }
        }
      ]
    }
  }
}
</script>

<style scoped>
  .content-wrapper {
    display: flex;
    height: 100%;
  }

  .content {
    flex-grow: 1;
    padding: 2rem;
  }
</style>
