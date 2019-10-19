<template>
  <v-container>
    <v-layout
      text-center
      wrap
    >

      <v-flex mb-4>
        <h1 class="display-2 font-weight-bold mb-3">
          This displays a sentence!
        </h1>
        <v-layout justify-center>
          <div>
              {{sentence}}
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            <button v-on:click="loadSentence">Load</button>
          </div>
        </v-layout>
      </v-flex>


    </v-layout>
  </v-container>
</template>

<script>
import $ from 'jquery'
  
export default {
  data: () => ({
    sentence: 'No sentence was loaded yet.'
  }),
  methods: {
    loadSentence: function () {
      var that = this;
      $.ajax({
          type: 'GET',
          url: 'http://localhost:8000/api/hello',
          success: function (data) {
            that.sentence = data;
          }
      })
    }
  },
};
</script>
