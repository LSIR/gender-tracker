<template>
  <v-container>
    <v-layout
      text-center
      wrap
    >

      <v-flex mb-4>
        <h1 class="display-2 font-weight-bold mb-3">
          Active Learning for the Gender Tracker Project
        </h1>
        <v-layout justify-center>
          <div>
            <span v-for="(word, i) in sentence" :key="i">
              <v-btn-toggle
                v-model="toggle_exclusive"
                multiple
              >
                <v-btn
                  outlined color="indigo"
                >
                  {{word}}
                </v-btn>
              </v-btn-toggle>
            </span>
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            <v-btn class="ma-2" outlined color="indigo" v-on:click.native=loadSentence>Load Sentence</v-btn>
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
    sentence: ['No sentence has been loaded yet.']
  }),
  methods: {
    loadSentence: function () {
      var that = this;
      $.ajax({
          type: 'GET',
          url: 'http://localhost:8000/api/loadSentence',
          success: function (data) {
            that.sentence = data['sentence'];
          }
      })
    }
  },
};
</script>
