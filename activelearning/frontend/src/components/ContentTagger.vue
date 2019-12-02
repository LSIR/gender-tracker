<template>
    <v-container
        style="width: 800px;"
    >
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
                v-if="task==='None'"
        >
            <v-flex mb-4>
                <h2>
                    Votre travail est terminé. Merci!
                </h2>
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
                    <span v-if="(paragraph_id - above_loads) > 0">
                        <v-btn small color="blue-grey lighten-4" v-on:click.native=loadTextAbove>&#x21E6;</v-btn>
                    </span>
                    &nbsp;
                    <span v-for="(word, i) in text_above" :key="`A-${i}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-on:click.native=tagAuthorAbove(i)
                                v-bind:color=button_color_above(i)
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                    &nbsp;
                    <span v-for="(word, i) in content" :key="`B-${i}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-on:click.native=tagWord(i)
                                v-bind:color=button_color(i)
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                    <span v-for="(word, i) in text_below" :key="`C-${i}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-on:click.native=tagAuthorBelow(i)
                                v-bind:color=button_color_below(i)
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                    &nbsp;
                    <span v-if="!no_more_content">
                        <v-btn small color="blue-grey lighten-4" v-on:click.native=loadTextBelow>&#x21E8;</v-btn>
                    </span>
                </div>

                <div>
                    <v-btn class="ma-2" outlined v-on:click.native=clearAnswers>Effacer les Réponses</v-btn>
                    <v-btn class="ma-2" outlined v-on:click.native=submitTags>Aucune Citation</v-btn>
                    <v-btn class="ma-2" outlined v-on:click.native=submitTags>Soumettre les Réponses</v-btn>
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
        <v-layout
                text-center
                wrap
        >
            <v-flex mb-4>
                <div>
                    {{article_id}}, {{paragraph_id}}, {{sentence_id}}, {{author_indices}}
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
        text_above: [],
        text_below: [],
        above_loads: 0,
        below_loads: 0,
        no_more_content: false,
        task: 'sentence',
        // 0: no tag, 1: start, 2: end, 3: author
        sentence_tags: [0],
        // relative to the start of the text
        author_indices: [],
        colors: ["black", "deep-orange darken-4", "green darken-4"],
        toggle_selection: 1,
        toggle_text: ["Clickez sur le premier mot du text cité, ou sur le boutton \"Aucune Citation\" si il n'y en a pas.",
            "Select the Last Word of the Reported Speech",
            "Select the Author of the Reported Speech"],
        buttonStyle: {
            'min-width': 0,
            'padding': '0px',
        }
    }),
    mounted: function () {
        this.loadContent()
    },
    methods: {
        loadContent: function () {
            this.clearAnswers();
            const that = this;
            $.ajax({
                type: 'GET',
                url: 'http://127.0.0.1:8000/api/loadContent/',
                success: function (data) {
                    that.task = data['task'];
                    if (that.task !== 'None'){
                        that.article_id = data['article_id'];
                        that.paragraph_id = data['paragraph_id'];
                        that.sentence_id = data['sentence_id'];
                        that.task = data['task'];
                        if (that.task === 'sentence'){
                            that.content = that.replace_whitespace(data['data']);
                        }else{
                            that.content = data['data'];
                        }
                        that.sentence_tags = new Array(that.content.length);
                        that.sentence_tags.fill(0)
                    }
                }
            });
        },
        loadTextAbove: function () {
            const that = this;
            $.ajax({
                type: 'GET',
                url: 'http://127.0.0.1:8000/api/loadAbove/',
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                data: {
                    'article_id': that.article_id,
                    'paragraph_id': that.paragraph_id - that.above_loads,
                    'sentence_id': that.sentence_id[0],
                },
                success: function (data) {
                    that.text_above = that.replace_whitespace(data['data']).concat(that.text_above);
                    that.above_loads += 1;
                }
            });
        },
        loadTextBelow: function () {
            const that = this;
            $.ajax({
                type: 'GET',
                url: 'http://127.0.0.1:8000/api/loadBelow/',
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                data: {
                    'article_id': that.article_id,
                    'paragraph_id': that.paragraph_id + that.below_loads,
                    'sentence_id': that.sentence_id[0],
                },
                success: function (data) {
                    if (data['data'].length === 0){
                        that.no_more_content = true;
                    }else {
                        that.text_below = that.text_below.concat(that.replace_whitespace(data['data']));
                        that.below_loads += 1;
                    }
                }
            });
        },
        submitTags: function () {
            const that = this;
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
                success: function () {
                    that.loadContent()
                }
            });
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
        tagAuthorAbove: function (index) {
            // Only add the author if it hasn't been tagged yet
            if (!this.author_indices.includes(index - this.text_above.length)) {
                this.author_indices.push(index - this.text_above.length);
                this.author_indices.sort((a, b) => a - b);
            }
        },
        tagAuthorBelow: function (index) {
            // Only add the author if it hasn't been tagged yet
            const relative_index = index + this.content.length;
            if (!this.author_indices.includes(relative_index)) {
                this.author_indices.push(relative_index);
                this.author_indices.sort((a, b) => a - b);
            }
        },
        clearAnswers: function () {
            this.toggle_selection = 1;
            this.sentence_tags.fill(0);
            this.author_indices = [];
            this.text_above = [];
            this.text_below = [];
            this.above_loads = 0;
            this.below_loads = 0;
            this.$forceUpdate();
        },
        submit_paragraph: function (tag) {
            this.sentence_tags = new Array(this.content.length);
            this.sentence_tags.fill(tag);
            this.submitTags();
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
        button_color_above: function (index) {
            const relative_index = index - this.text_above.length;
            if (this.author_indices.includes(relative_index)){
                return "green lighten-4"
            }else{
                return "grey lighten-4"
            }
        },
        button_color_below: function (index) {
            const relative_index = index + this.content.length;
            if (this.author_indices.includes(relative_index)){
                return "green lighten-4"
            }else{
                return "grey lighten-4"
            }
        },
        replace_whitespace: function (text_array){
            for (let i = 0; i < text_array.length; i++) {
                // \xa0 is the JS whitespace character
                text_array[i] = text_array[i].replace(' ', '\xa0')
            }
            return text_array
        }
    },
};
</script>
