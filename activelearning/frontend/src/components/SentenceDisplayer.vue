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
            <v-btn-toggle
              v-model="toggle_sentence"
              multiple
              dense
            >
              <span v-for="(word, i) in sentence" :key="i">
                <v-btn
                  v-on:click.native=tagWord(i)
                  v-bind:color=colors[sentence_tags[i]]
                  outlined
                >
                  {{ word }}
                </v-btn>
              </span>
            </v-btn-toggle>
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            <v-btn class="ma-2" outlined v-on:click.native=loadSentence>Load Sentence</v-btn>
            <v-btn class="ma-2" outlined v-on:click.native=submitTags>Submit Answers</v-btn>
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            <v-btn-toggle
              v-model="toggle_selection"
              mandatory
            >
              <v-btn value=1> Start of Reported Speech </v-btn>
              <v-btn value=2> End of Reported Speech </v-btn>
              <v-btn value=3> Author </v-btn>
            </v-btn-toggle>
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            Words selected: {{toggle_sentence}}
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            Button selected: {{toggle_selection}}
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            {{sentence}}
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            {{sentence_tags}}
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
    sentence: ['No sentence has been loaded yet.'],
    // 0: no tag, 1: start, 2: end, 3: author
    sentence_tags: [0],
    colors: ["black", "yellow", "deep-orange", "green"],
    toggle_selection: 1,
    toggle_sentence: [],
  }),
  methods: {
    loadSentence: function () {
      var that = this;
      $.ajax({
          type: 'GET',
          url: 'http://localhost:8000/api/loadSentence',
          success: function (data) {
            that.sentence = data['sentence'];
            that.sentence_tags = new Array(that.sentence.length)
            that.sentence_tags.fill(0)
          }
      })
    },
    submitTags: function () {
      var that = this;
      $.ajax({
          type: 'POST',
          url: 'http://localhost:8000/api/submitTags/',
          data: JSON.stringify({ tags: that.sentence_tags }),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          success: function (data) {
            alert(data)
          }
      })
    },
    tagWord: function (index) {
      var tagSelected = parseInt(this.toggle_selection)
      if (this.sentence_tags[index] === tagSelected){
        this.sentence_tags[index] = 0
      }else{
        this.sentence_tags[index] = tagSelected
      }
    },
  },
};
</script>
