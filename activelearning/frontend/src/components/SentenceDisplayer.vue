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
      </v-flex>


    </v-layout>
  </v-container>
</template>

<script>
import $ from 'jquery'
  
export default {
  data: () => ({
    sentence: '"Apples are delicious!", said Marc.'
  }),
  mounted: function () {
    var that = this;
      $.ajax({
          type: 'GET',
          url: '/api/hello',
          success: function (data) {
              that.sentence = data;
          }
      })
  }
};
</script>
