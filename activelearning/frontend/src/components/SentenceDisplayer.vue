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
                <div>
                    {{toggle_text[toggle_selection - 1] }}
                </div>
                <v-layout justify-center>
                  <div>
                    <span v-for="(word, i) in sentence" :key="i">
                      <v-btn
                              small
                            text
                            v-on:click.native=tagWord(i)
                            v-bind:color=colors[sentence_tags[i]]
                            outlined
                      >
                  {{ word }}
                </v-btn>
              </span>
          </div>
        </v-layout>
        <v-layout justify-center>
          <div>
            <v-btn class="ma-2" outlined v-on:click.native=loadSentence>Load New Sentence</v-btn>
            <v-btn class="ma-2" outlined v-on:click.native=clearAnswers>Clear Answers</v-btn>
          </div>
        </v-layout>

        <div>
          <v-btn class="ma-2" outlined v-on:click.native=submitTags>No Reported Speech</v-btn>
          <v-btn class="ma-2" outlined v-on:click.native=submitTags>Submit Reported Speech Tags</v-btn>
        </div>
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
    colors: ["black", "deep-orange darken-4", "green darken-4"],
    toggle_selection: 1,
    toggle_text: ["Select the Start of the Reported Speech",
                  "Select the End of the Reported Speech",
                  "Select the Author of the Reported Speech"],
  }),
  mounted: function () {
    this.loadSentence()
  },
  methods: {
    loadSentence: function () {
      this.clearAnswers()
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
      var tags_values = this.sentence_tags
      $.ajax({
          type: 'POST',
          url: 'http://localhost:8000/api/submitTags/',
          data: JSON.stringify({ tags: tags_values }),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          success: function (data) {
            alert(data)
          }
      })
      this.loadSentence()
    },
    tagWord: function (index) {
      if (this.toggle_selection === 1){
        if (this.sentence_tags[index] === 0){
          this.sentence_tags[index] = 1
          this.toggle_selection += 1
        }
      }else if (this.toggle_selection === 2){
        var tag = false
        for (var i = 0; i <= index; ++i){
          if (tag) {
            this.sentence_tags[i] = 1
          }else{
            tag = this.sentence_tags[i] === 1
          }
        }
        if (tag){
          this.toggle_selection += 1
        }
      }else{
        if (this.sentence_tags[index] === 0){
          this.sentence_tags[index] = 2
        }
      }
      this.$forceUpdate();
    },
    clearAnswers: function () {
      this.toggle_selection = 1
      this.sentence_tags.fill(0)
      this.$forceUpdate();
    },
  },
};
</script>
