<template>
  <v-app>
    <v-app-bar app>
      <v-toolbar-title class="headline text-uppercase">
        <span>GENDERTRACKER</span>
        <span class="font-weight-light">PROJECT</span>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn
        text
        href="https://www.heidi.news/"
        target="_blank"
      >
        <span class="mr-2">HEIDI.NEWS</span>
      </v-btn>
    </v-app-bar>

    <v-content>
      <ContentTagger/>
    </v-content>

    <v-layout text-center wrap>
      <v-flex xs12>
        <img
          :src="image"
          alt="Logo EPFL"
          class="my-3"
          height="40"
        >
      </v-flex>
    </v-layout>
  </v-app>
</template>

<script>

import ContentTagger from "./components/ContentTagger";

export default {
  name: 'App',
  components: {
    ContentTagger,
  },
  data: () => ({
      image: require('@/assets/epfl_logo.svg')
  }),
};
</script>
