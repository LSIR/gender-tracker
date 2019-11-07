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
  </v-app>
</template>

<script>
// import HelloWorld from './components/HelloWorld';
// import SentenceDisplayer from './components/SentenceDisplayer';
import ContentTagger from "./components/ContentTagger";

export default {
  name: 'App',
  components: {
    ContentTagger,
  },
  data: () => ({
    //
  }),
};
</script>
