<template>
    <v-container>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <h1 class="display-2 font-weight-bold mb-3">
                    Gender Tracker Project
                </h1>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="task==='sentence'"
        >
            <v-flex mb-4>
                <h3>
                    {{toggle_text[toggle_selection - 1] }}
                </h3>
                <div>
                    <span v-for="(word, i) in content" :key="i">
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
                <div>
                    <v-btn class="ma-2" outlined v-on:click.native=clearAnswers>Clear Answers</v-btn>
                    <v-btn class="ma-2" outlined v-on:click.native=submitTags>No Reported Speech</v-btn>
                    <v-btn class="ma-2" outlined v-on:click.native=submitTags>Submit Response</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="task==='paragraph'"
        >
            <v-flex mb-4>
                <h3>
                    Does this paragraph contain reported speech?
                </h3>
                <div>
                    {{ content[0] }}
                </div>
                <div>
                    <v-btn-toggle tile>
                        <v-btn class="ma-2" outlined color="black" v-on:click.native=submit_paragraph(1)>Yes</v-btn>
                        <v-btn class="ma-2" outlined color="black" v-on:click.native=submit_paragraph(0)>No</v-btn>
                    </v-btn-toggle>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <div>
                    <v-btn class="ma-2" outlined v-on:click.native=loadContent>Load New Sentence</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <div>
                    Button selected: {{toggle_selection}}
                </div>
                <div>
                    {{sentence_tags}}
                </div>
            </v-flex>
        </v-layout>
    </v-container>
</template>

<script>
import $ from 'jquery'

export default {
    data: () => ({
        article_id: 0,
        paragraph_id: 0,
        sentence_id: 0,
        content: ['No sentence has been loaded yet.'],
        task: 'sentence',
        // 0: no tag, 1: start, 2: end, 3: author
        sentence_tags: [0],
        colors: ["black", "deep-orange darken-4", "green darken-4"],
        toggle_selection: 1,
        toggle_text: ["Select the First Word of the Reported Speech",
            "Select the Last Word of the Reported Speech",
            "Select the Author of the Reported Speech"],
    }),
    mounted: function () {
        this.loadContent()
    },
    methods: {
        loadContent: function () {
            this.clearAnswers();
            var that = this;
            $.ajax({
                type: 'GET',
                // url: 'http://localhost:8000/api/loadContent/',
                url: 'http://127.0.0.1:8000/api/loadContent/',
                success: function (data) {
                    that.article_id = data['article_id'];
                    that.paragraph_id = data['paragraph_id'];
                    that.sentence_id = data['sentence_id'];
                    that.content = data['data'];
                    that.task = data['task'];
                    that.sentence_tags = new Array(that.content.length)
                    that.sentence_tags.fill(0)
                }
            });
        },
        submitTags: function () {
            var tags_values = this.sentence_tags;
            $.ajax({
                type: 'POST',
                // url: 'http://localhost:8000/api/submitTags/',
                url: 'http://127.0.0.1:8000/api/submitTags/',
                data: JSON.stringify({ tags: tags_values }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function (data) {
                    alert(data)
                }
            });
            this.loadContent()
        },
        tagWord: function (index) {
            if (this.toggle_selection === 1){
                if (this.sentence_tags[index] === 0){
                    this.sentence_tags[index] = 1;
                    this.toggle_selection += 1
                }
            }else if (this.toggle_selection === 2){
                var tag = false;
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
            this.toggle_selection = 1;
            this.sentence_tags.fill(0);
            this.$forceUpdate();
        },
        submit_paragraph: function (tag) {
            this.sentence_tags[0] = tag;
            this.submitTags()
        },
    },
};
</script>
