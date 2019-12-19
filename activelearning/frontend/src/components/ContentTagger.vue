<template>
    <v-container
        style="width: 800px; background-color: white;"
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
                <div v-if="above_load_id >= 0">
                    <v-btn small color="red lighten-1" v-on:click.native=loadTextAbove>&#x21E7;</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-left
                wrap
                v-if="task==='sentence'"
        >
            <v-flex mb-4>
                <div>
                    <div v-if="text_above.length > 0">
                        <div v-for="(par, i) in text_above" :key="`D-${i}`">
                            <span v-for="(word, j) in par" :key="`A-${j}`">
                                <v-btn
                                        class="text-none"
                                        depressed
                                        v-bind:style="buttonStyle"
                                        v-on:click.native="tagAuthorAbove(i, j)"
                                        v-bind:color="button_color_above(i, j)"
                                >
                                    {{ word }}
                                </v-btn>
                            </span>
                            <br>
                            <br>
                        </div>
                    </div>
                    <br>
                    <div>
                        <span v-for="(word, i) in content" :key="`B-${i}`">
                            <v-btn
                                    class="text-none"
                                    depressed
                                    v-bind:style="buttonStyle"
                                    v-on:click.native="tagWord(i)"
                                    v-bind:color="button_color(i)"
                            >
                                {{ word }}
                            </v-btn>
                        </span>
                    </div>
                    <br>
                    <div>
                        <div v-for="(par, i) in text_below" :key="`D-${i}`">
                            <span v-for="(word, j) in par" :key="`C-${j}`">
                                <v-btn
                                        class="text-none"
                                        depressed
                                        v-bind:style="buttonStyle"
                                        v-on:click.native="tagAuthorBelow(i, j)"
                                        v-bind:color="button_color_below(i, j)"
                                >
                                    {{ word }}
                                </v-btn>
                            </span>
                            <br>
                            <br>
                        </div>
                    </div>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="task==='sentence'"
        >
            <v-flex mb-4>
                <div v-if="!no_more_content">
                    <v-btn small color="red lighten-1" v-on:click.native=loadTextBelow>&#x21E9;</v-btn>
                </div>
                &nbsp;
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
                    Est-ce qu'une citation est présente dans ce paragraphe?
                </h3>
                <div>
                    {{ content[0] }}
                </div>
                <div>
                    <v-btn-toggle tile>
                        <v-btn class="ma-2" color="white" v-on:click.native=submit_paragraph(1)>Oui</v-btn>
                        <v-btn class="ma-2" color="white" v-on:click.native=submit_paragraph(0)>Non</v-btn>
                    </v-btn-toggle>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="task ==='cookies'"
        >
            <v-flex mb-4>
                <h3>
                    Oops! Il semblerait que les cookies ne soient pas activés dans votre browser.
                </h3>
                <div>
                    Nous utilisons des cookies pour vérifier que la même personne n'analyse pas la même phrase
                    plusieures fois.
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="task ==='error'"
        >
            <v-flex mb-4>
                <h3>
                    Oops!
                </h3>
                <div>
                    Nous avons des difficultés internes. Merci de revenir plus tard.
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex xs12>
                <v-img
                        :src="require('../assets/epfl_logo.svg')"
                        class="my-3"
                        contain
                        height="40"
                ></v-img>
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
        above_load_id: 0,
        below_load_id: 0,
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
                        that.above_load_id = that.paragraph_id;
                        that.below_load_id = that.paragraph_id;
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
                    'paragraph_id': that.above_load_id,
                    'sentence_id': that.sentence_id[0],
                },
                success: function (data) {
                    const tokens = data['data'];
                    const p_id = data['paragraph'];
                    if (tokens.length > 0 && p_id >= 0){
                        that.text_above.unshift(that.replace_whitespace(tokens));
                    }
                    that.above_load_id = p_id - 1;
                },
                error: function () {
                    that.task = 'error'
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
                    'paragraph_id': that.below_load_id,
                    'sentence_id': that.sentence_id[0],
                },
                success: function (data) {
                    if (data['data'].length === 0) {
                        that.no_more_content = true;
                    } else {
                        const tokens = data['data'];
                        const p_id = data['paragraph'];
                        if (tokens.length > 0 && p_id >= 0){
                            that.text_below.push(that.replace_whitespace(tokens));
                        }
                        that.below_load_id = p_id + 1;
                        if (p_id === -1){
                            that.no_more_content = true
                        }
                    }
                },
                error: function () {
                    that.task = 'error'
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
                success: function (response) {
                    if (response['success'] === true){
                        that.loadContent()
                    }else if (response['reason'] === 'cookies'){
                        that.task = 'cookies'
                    }else{
                        that.task = 'error'
                    }
                },
                error: function () {
                    that.task = 'error'
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
        tagAuthorAbove: function (par_index, word_index) {
            let words_before = 0;
            const total_length = this.text_above.map(x => x.length).reduce((x, y) => x + y);
            if (par_index > 0){
                const end = this.text_above.length;
                words_before = this.text_above.slice(end - par_index, end).map(x => x.length).reduce((x, y) => x + y);
            }
            word_index = word_index + words_before;
            // Only add the author if it hasn't been tagged yet
            if (!this.author_indices.includes(word_index - total_length)) {
                this.author_indices.push(word_index - total_length);
                this.author_indices.sort((a, b) => a - b);
            }
        },
        tagAuthorBelow: function (par_index, word_index) {
            let words_before = 0;
            if (par_index > 0){
                words_before = this.text_below.slice(0, par_index).map(x => x.length).reduce((x, y) => x + y);
            }
            // Only add the author if it hasn't been tagged yet
            const relative_index = word_index + words_before + this.content.length;
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
            this.above_load_id = this.paragraph_id;
            this.below_load_id = this.paragraph_id;
            this.no_more_content = false;
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
        button_color_above: function (index, word) {
            let words_before = 0;
            const total_length = this.text_above.map(x => x.length).reduce((x, y) => x + y);
            if (index > 0){
                const end = this.text_above.length;
                words_before = this.text_above.slice(end - index, end).map(x => x.length).reduce((x, y) => x + y);
            }
            const relative_index = word + words_before - total_length;
            if (this.author_indices.includes(relative_index)){
                return "green lighten-4"
            }else{
                return "white"
            }
        },
        button_color_below: function (index, word) {
            let words_before = 0;
            if (index > 0){
                words_before = this.text_below.slice(0, index).map(x => x.length).reduce((x, y) => x + y);
            }
            const relative_index = word + words_before + this.content.length;
            if (this.author_indices.includes(relative_index)){
                return "green lighten-4"
            }else{
                return "white"
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
