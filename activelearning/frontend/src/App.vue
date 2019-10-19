<template>
  <v-app>
    <v-app-bar app>
      <v-toolbar-title class="headline text-uppercase">
        <span>GENDER-TRACKER</span>
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
      <SentenceDisplayer/>
    </v-content>
  </v-app>
</template>

<script>
// import HelloWorld from './components/HelloWorld';
import SentenceDisplayer from './components/SentenceDisplayer';

export default {
  name: 'App',
  components: {
    SentenceDisplayer,
  },
  data: () => ({
    //
  }),
};
</script>
