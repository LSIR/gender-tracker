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
        v-on:click.native="change_helper()"
      >
        <span class="mr-2">{{helper_text}}</span>
      </v-btn>
    </v-app-bar>

    <v-content v-if="helper_page">
      <HelperPage/>
    </v-content>
    <v-content v-else>
      <ContentTagger/>
    </v-content>

    <v-layout text-center wrap>
      <v-flex xs12>
        <img
          :src="epfl_logo"
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
import HelperPage from "./components/HelperPage";

export default {
  name: 'App',
  components: {
    ContentTagger,
    HelperPage,
  },
  data: () => ({
      helper_page: false,
      helper_text: 'FAQ',
      epfl_logo: require('@/assets/epfl_logo.svg'),
  }),
  methods: {
      change_helper: function () {
          this.helper_page = !this.helper_page;
          if (this.helper_page){
              this.helper_text = 'RETOUR AU GENDERTRACKER'
          }else{
              this.helper_text = 'FAQ'
          }
      },

  }
};
</script>
