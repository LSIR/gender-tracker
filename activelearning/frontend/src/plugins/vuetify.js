import Vue from 'vue';
import Vuetify from 'vuetify/lib';

Vue.use(Vuetify);

export default new Vuetify({
  icons: {
    iconfont: 'mdi',
  },
  theme: {
    themes: {
      light: {
          heidi_red: '#d5121e',
      },
      dark: {
        heidi_red: '#d5121e',
      }
    }
  },
});
