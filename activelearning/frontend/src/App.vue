<template>
  <v-app>
    <v-app-bar app>
      <v-toolbar-title class="headline">
        <span>GenderTracker</span>
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
      <IntroText/>
      <ContentTaggerDrag/>
    </v-content>

    <v-container fluid style="width: 800px;">
      <v-row dense justify="center" align="center">
        <v-col cols="4">
          <v-img
              :src="epfl_logo"
              alt="Logo EPFL"
              class="ma-3 pa-6"
              height="50"
              contain
            ></v-img>
        </v-col>
        <v-col cols="4">
            <v-img
              :src="heidi_logo"
              alt="Logo Heidi News"
              class="ma-3 pa-6"
              height="100"
              contain
            ></v-img>
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script>

// import ContentTagger from "./components/ContentTagger";
import ContentTaggerDrag from "./components/ContentTaggerDrag";
import HelperPage from "./components/HelperPage";
// import BottomHelper from "./components/BottomHelper";
import IntroText from "./components/IntroText";

export default {
  name: 'App',
  components: {
    // ContentTagger,
    ContentTaggerDrag,
    HelperPage,
    // BottomHelper,
    IntroText,
  },
  data: () => ({
      helper_page: false,
      drag_mode: false,
      helper_text: 'FAQ',
      epfl_logo: require('@/assets/epfl_logo.svg'),
      heidi_logo: require('@/assets/heidi_news.png'),
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
      change_drag: function () {
          this.drag_mode = !this.drag_mode
      }
  }
};
</script>
