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
            <v-flex mb-4 v-if="extra_content.length > 0">
                <div>
                    <span v-for="(word, i) in extra_content" :key="i">
                        <v-btn
                                small
                                v-bind:style="buttonStyle"
                                v-on:click.native=tagAuthor(i)
                                v-bind:color=button_color_extra_text(i)
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                </div>
            </v-flex>
            <v-flex mb-4>
                <h3>
                    {{toggle_text[toggle_selection - 1] }}
                </h3>
                <div>
                    <span v-for="(word, i) in content" :key="i">
                        <v-btn
                                small
                                v-bind:style="buttonStyle"
                                v-on:click.native=tagWord(i)
                                v-bind:color=button_color(i)
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                </div>
                <div>
                    <v-btn class="ma-2" outlined v-on:click.native=loadTextAbove>Load the Rest of the Paragraph</v-btn>
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
                        <v-btn class="ma-2" color="white" v-on:click.native=submit_paragraph(1)>Yes</v-btn>
                        <v-btn class="ma-2" color="white" v-on:click.native=submit_paragraph(0)>No</v-btn>
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
                    Tags: {{sentence_tags}}
                </div>
                <div>
                    Authors: {{author_indices}}
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
        extra_content: [],
        task: 'sentence',
        // 0: no tag, 1: start, 2: end, 3: author
        sentence_tags: [0],
        // relative to the start of the text
        author_indices: [],
        colors: ["black", "deep-orange darken-4", "green darken-4"],
        toggle_selection: 1,
        toggle_text: ["Select the First Word of the Reported Speech",
            "Select the Last Word of the Reported Speech",
            "Select the Author of the Reported Speech"],
        buttonStyle: {
            'min-width': 0,
            'padding': '5px',
        }
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
        loadTextAbove: function () {
            if (this.extra_content.length === 0) {
                const that = this;
                $.ajax({
                    type: 'GET',
                    url: 'http://127.0.0.1:8000/api/loadMoreContent/',
                    data: {
                        'article_id': that.article_id,
                        'paragraph_id': that.paragraph_id,
                        'sentence_id': that.sentence_id[0],
                    },
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        that.extra_content = data['data'];
                    }
                });
            }
        },
        submitTags: function () {
            var that = this;
            $.ajax({
                type: 'POST',
                url: 'http://127.0.0.1:8000/api/submitTags/',
                data: JSON.stringify({
                    'article_id': that.article_id,
                    'paragraph_id': that.paragraph_id,
                    'sentence_id': that.sentence_id,
                    'tags': that.sentence_tags,
                    'authors': that.author_indices,
                }),
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
                // Tag first word in reported speech
                if (this.sentence_tags[index] === 0){
                    this.sentence_tags[index] = 1;
                    this.toggle_selection += 1
                }
            }else if (this.toggle_selection === 2){
                // Tag rest of sentence
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
            }else if ((this.toggle_selection === 3) &&
                (!this.author_indices.includes(index)) &&
                (this.sentence_tags[index] === 0)){
                // Tag author, only if the index isn't already noted as reported speech or an author
                this.author_indices.push(index);
                this.author_indices.sort((a, b) => a - b);
            }
            this.$forceUpdate();
        },
        tagAuthor: function (index) {
            // Only add the author if it hasn't been tagged yet
            if (!this.author_indices.includes(index - this.extra_content.length)) {
                this.author_indices.push(index - this.extra_content.length);
                this.author_indices.sort((a, b) => a - b);
            }
        },
        clearAnswers: function () {
            this.toggle_selection = 1;
            this.sentence_tags.fill(0);
            this.author_indices = [];
            this.$forceUpdate();
        },
        submit_paragraph: function (tag) {
            this.sentence_tags[0] = tag;
            this.submitTags()
        },
        button_color: function (index) {
            if (this.sentence_tags[index] === 1) {
                return "deep-orange lighten-4"
            }else if (this.author_indices.includes(index)){
                return "green lighten-4"
            }else{
                return "white"
            }
        },
        button_color_extra_text: function (index) {
            const relative_index = index - this.extra_content.length;
            if (this.author_indices.includes(relative_index)){
                return "green lighten-4"
            }else{
                return "white"
            }
        },
    },
};
</script>
