<template>
    <v-container
            fluid
            style="width: 800px; background-color: white;"
    >
        <v-layout
                text-left
                wrap
        >
            <v-flex mb-4>
                <div v-if="quote_count === 0" class="mb-2">
                    Vous n'avez pas encore trouvé une citation.
                </div>
                <div v-else class="mb-2">
                    Vous avez annoté {{quote_count}} citations!
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="tagging_task==='None'"
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
                v-if="tagging_task==='sentence'"
        >
            <v-flex mb-4>
                <div class="heidi_red--text subtitle-1 font-weight-bold mb-6">
                    ETAPE {{helper_text_shown + 1}} SUR 4
                </div>
                <h3 class="subtitle-1 font-weight-bold mb-6">
                    {{helper_text[helper_text_shown]}}
                </h3>
                <div class="mb-6">
                    <v-btn-toggle
                            v-model="selecting_author"
                            shaped
                            mandatory
                    >
                        <v-tooltip left>
                            <template v-slot:activator="{ on }">
                                <v-btn
                                        v-on="on"
                                        v-on:click="update_helper_text(2)"
                                        v-bind:color="selecting_author === 0 ? 'deep-orange lighten-4' : 'white'"
                                >
                                    Citation
                                </v-btn>
                            </template>
                            <span>Pour ajouter plus de texte à la citation, cliquez ici.</span>
                        </v-tooltip>
                        <v-tooltip v-model="show_author_tip" right>
                            <template v-slot:activator="{ on }">
                                <v-btn
                                        v-on="on"
                                        v-on:click="update_helper_text(3)"
                                        v-bind:color="selecting_author === 1 ? 'green lighten-4' : 'white'"
                                >
                                    Auteur
                                </v-btn>
                            </template>
                            <span>Si toute la citation à été annotée, cliquez ici pour annoter l'auteur.</span>
                        </v-tooltip>
                    </v-btn-toggle>
                </div>
                <hr class="heidi_red mb-6">
                <div v-if="first_sentence > 0">
                    <v-btn small color="blue lighten-5" v-on:click.native=loadTextAbove>⇡</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-left
                wrap
                v-if="tagging_task==='sentence'"
        >
            <v-flex mb-4>
                <div v-for="(p_edges, i) in paragraph_indices" :key="`A-${i}`">
                    <br>
                    <span v-for="(word, j) in text.slice(p_edges[0], p_edges[1])" :key="`B-${j}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-on:click.native="tagWord(p_edges[0] + j)"
                                v-on:mousedown.native="start_dragging(p_edges[0] + j)"
                                v-on:mouseup.native="stop_dragging()"
                                v-on:mouseover.native="drag_tag(p_edges[0] + j)"
                                v-bind:color="button_color(p_edges[0] + j)"
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                    <br>
                    <br>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="tagging_task==='sentence'"
        >
            <v-flex mb-4>
                <div v-if="!no_more_content">
                    <v-btn small color="blue lighten-5" v-on:click.native=loadTextBelow>⇣</v-btn>
                </div>
                <br>
                <hr class="mb-6 heidi_red">
                <br>
                <div>
                    <v-btn class="ma-2" width="180px" mb-10 outlined v-on:click.native=submitTags>Soumettre</v-btn>
                </div>
                <div>
                    <v-btn class="ma-2" width="180px" outlined v-on:click.native=submitTags>Aucune Citation</v-btn>
                    <v-btn class="ma-2" width="180px" outlined v-on:click.native=clearAnswers>Réinitialiser</v-btn>
                    <v-btn class="ma-2" width="180px" outlined v-on:click.native=skip_sentence>Sauter</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="tagging_task==='paragraph'"
        >
            <v-flex mb-4>
                <h3 class="subtitle-1 font-weight-bold mb-2">
                    Est-ce qu'une citation est présente dans ce paragraphe?
                </h3>
            </v-flex>
        </v-layout>
        <v-layout
                text-left
                wrap
                v-if="tagging_task==='paragraph'"
        >
            <v-flex mb-4>
                <div>
                    {{ text.reduce((acc, val) => acc + val)}}
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
                v-if="tagging_task==='paragraph'"
        >
            <v-flex mb-4>
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
                v-if="tagging_task ==='cookies'"
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
                v-if="tagging_task ==='error'"
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
        <v-layout text-center wrap v-if="admin">
            <v-flex mb-4>
                <div class="red--text">
                    ADMIN
                </div>
            </v-flex>
        </v-layout>
    </v-container>
</template>

<script>
import $ from 'jquery'

export default {
    data: () => ({
        // Information on the user
        admin: false,
        quote_count: 0,

        // Information on the sentence to tag
        article_id: -1,
        sentence_id: [-1],

        // Information on extra text loaded.
        first_sentence: -1,
        last_sentence: -1,

        // The task to perform.
        //   * 'sentence', if a sentence needs to be annotated
        //   * 'paragraph', if the user needs to confirm that no quote is in the paragraph
        //   * 'None', if there are no more articles to annotate
        //   * 'cookies', if the user doesn't have cookies activated
        tagging_task: 'sentence',

        // List of tokens displayed on the page
        text: ['No sentence has been loaded yet.'],
        // Token indices that are at the edges of paragraphs: [[first, last + 1], [first, last + 1], ....]
        paragraph_indices: [[0, 1]],
        // Boolean marker to indicate if each token is part of a quote
        quote_markers: [0],
        // Index of tokens that are authors of a quote
        author_indices: [],
        // Index of the first token of the original sentence
        sentence_start_index: 0,
        // Index of the last token of the original sentence
        sentence_end_index: 0,
        // If no more content is available for the article
        no_more_content: false,

        // The colors to use for the text
        //   * 0: for regular tokens
        //   * 1: for tokens inside a quote
        //   * 2: for tokens representing authors
        colors: ["black", "deep-orange darken-4", "green darken-4"],

        // Whether or not the user has clicked on the first token of a quote
        quote_open: false,
        quote_first_token: 0,

        // Whether the user is tagging the quote (0) or the author (1)
        selecting_author: 0,

        // Whether or not to show the tooltip to annotate the author
        show_author_tip: false,

        // Whether the user is doing click and drag
        dragging: false,

        // Helper text to be displayed
        helper_text: [
            "Observez le texte ci-dessous. Cliquez sur le premier mot de la citation ou sur «aucune citation» s’il " +
            "n’y en a pas.",
            "Cliquez sur le dernier mot de la citation. Vous pouvez utiliser les flèches ⇡ et ⇣ pour naviguer dans " +
            "le texte.",
            "Cliquez sur le bouton auteur en-dessus.",
            "Sélectionner l’auteur de la citation, puis cliquez sur «soumettre» en bas. Merci! Vous pouvez " +
            "recommencer."
        ],
        helper_text_shown: 0,

        // The style of buttons to use
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
                url: '/api/loadContent/',
                success: function (data) {
                    that.tagging_task = data['task'];
                    if (that.tagging_task !== 'None'){
                        that.admin = data['admin'];
                        that.article_id = data['article_id'];
                        that.sentence_id = data['sentence_id'];
                        if (that.tagging_task === 'sentence'){
                            that.text = that.replace_whitespace(data['data']);
                        }else if (that.tagging_task === 'paragraph'){
                            that.text = data['data'];
                        }

                        that.quote_count = data['quote_count'];

                        that.first_sentence = that.sentence_id[0];
                        that.last_sentence = that.sentence_id[that.sentence_id.length - 1];
                        that.paragraph_indices = [[0, that.text.length]];

                        that.quote_markers = (new Array(that.text.length)).fill(0);
                        that.author_indices = [];
                        that.sentence_start_index = 0;
                        that.sentence_end_index = that.text.length - 1;

                        that.no_more_content = false;
                        that.toggle_selection = 0;
                    }
                }
            });
        },
        clearAnswers: function () {
            // Set initial quote markers
            this.quote_markers = (new Array(this.text.length)).fill(0);
            // Set initial authors
            this.author_indices = [];
            // Set content variables to default
            this.no_more_content = false;
            this.quote_open = false;
            this.selecting_author = 0;
            this.helper_text_shown = 0;
            this.$forceUpdate();
        },
        loadTextAbove: function () {
            const that = this;
            $.ajax({
                type: 'GET',
                url: '/api/loadAbove/',
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                data: {
                    'article_id': that.article_id,
                    'first_sentence': that.first_sentence,
                },
                success: function (data) {
                    let tokens = data['data'];
                    const first_sentence = data['first_sentence'];
                    if (tokens.length > 0){
                        tokens = that.replace_whitespace(tokens);
                    }
                    // Add new tokens to text
                    that.text = tokens.concat(that.text);
                    // Change new sentence to be actual sentence
                    that.first_sentence = first_sentence;
                    // Modify indices of tokens that are the edge of the original sentence
                    that.sentence_start_index += tokens.length;
                    that.sentence_end_index += tokens.length;
                    // Append '0' quote markers to the newly loaded text
                    that.quote_markers = ((new Array(tokens.length)).fill(0)).concat(that.quote_markers);
                    // Modify paragraph edges to reflect the new size of text
                    that.paragraph_indices = that.paragraph_indices.map(x => x.map(y => y + tokens.length));
                    that.paragraph_indices = [[0, tokens.length]].concat(that.paragraph_indices);
                    // Modify author tags to reflect the new size of text
                    that.author_indices = that.author_indices.map(x => x + tokens.length);
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
                url: '/api/loadBelow/',
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                data: {
                    'article_id': that.article_id,
                    'last_sentence': that.last_sentence,
                },
                success: function (data) {
                    let tokens = data['data'];
                    if (tokens.length === 0){
                        that.no_more_content = true;
                    }else{
                        tokens = that.replace_whitespace(tokens);
                        const last_sentence = data['last_sentence'];
                        // Add new tokens to text
                        that.text = that.text.concat(tokens);
                        // Change new sentence to be actual sentence
                        that.last_sentence = last_sentence;
                        // Append '0' quote markers to the newly loaded text
                        that.quote_markers = that.quote_markers.concat((new Array(tokens.length)).fill(0));
                        // Add new paragraph edges
                        that.paragraph_indices = that.paragraph_indices.concat([
                            [that.text.length - tokens.length, that.text.length]
                        ]);
                    }
                },
                error: function () {
                    that.task = 'error'
                }
            });
        },
        submitTags: function () {
            // Don't let the user report a quote with no author
            const reducer = (accumulator, currentValue) => accumulator + currentValue;
            if ((this.quote_markers.reduce(reducer) > 0) &&
                    (this.author_indices.length === 0) &&
                    (this.tagging_task === 'sentence')) {
                alert("Vous avez indiqué la présence d'un citation, mais pas d'auteur. Merci de sélectionner le nom " +
                    "la personne qui est citée. Si la phrase ne contient pas de citation, vous pouvez recommencer en " +
                    "cliquant sur le bouton \"réinitialiser\". ");
            }else if ((this.quote_markers.reduce(reducer) === 0) &&
                        (this.author_indices.length > 0) &&
                        (this.tagging_task === 'sentence')){
                alert("Vous avez indiqué la présence d'un auteur, mais pas de citation. Merci de sélectionner le " +
                    "texte qui à été dit par l'auteur. Si la phrase ne contient pas de citation, vous pouvez " +
                    "recommencer en cliquant sur le bouton \"réinitialiser\". ");
            }else{
                const that = this;
                $.ajax({
                    type: 'POST',
                    url: '/api/submitTags/',
                    data: JSON.stringify({
                        'article_id': that.article_id,
                        'sentence_id': that.sentence_id,
                        'first_sentence': that.first_sentence,
                        'last_sentence': that.last_sentence,
                        'tags': that.quote_markers,
                        'authors': that.author_indices,
                        'task': that.tagging_task,
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
            }
        },
        skip_sentence: function () {
            const that = this;
            $.ajax({
                type: 'POST',
                url: '/api/submitTags/',
                data: JSON.stringify({
                    'article_id': that.article_id,
                    'sentence_id': that.sentence_id,
                    'first_sentence': that.first_sentence,
                    'last_sentence': that.last_sentence,
                    'tags': [],
                    'authors': [],
                    'task': that.tagging_task,
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
            // Tagging author tokens, only if the index isn't already noted as reported speech or an author
            if (this.selecting_author === 1 &&
                    !this.author_indices.includes(index) &&
                    this.quote_markers[index] === 0){
                this.author_indices.push(index);
                this.author_indices.sort((a, b) => a - b);
            }
            // Tagging the first word in the quote
            else if (this.selecting_author === 0 && !this.quote_open){
                if (this.quote_markers[index] === 0) {
                    this.quote_markers[index] = 1;
                    this.quote_open = true;
                    this.quote_first_token = index;
                    this.update_helper_text(1);
                }else{
                    this.quote_markers[index] = 0;
                    this.update_helper_text(2);
                }
            }
            // Tagging the last word in the quote, must be after the start of the quote
            else if (this.selecting_author === 0 && this.quote_open && this.quote_first_token <= index){
                for (let i = this.quote_first_token; i <= index; ++i){
                    this.quote_markers[i] = 1
                }
                this.quote_open = false;
                this.show_author_tip = true;
                this.update_helper_text(2);
            }
            this.$forceUpdate();
        },
        update_helper_text: function(value) {
            this.helper_text_shown = value;
        },
        start_dragging: function (index) {
            // You can only drag for authors
            if (this.selecting_author === 1){
                this.dragging = true;
                this.tagWord(index)
            }
        },
        stop_dragging: function () {
            this.dragging = false;
        },
        drag_tag: function (index) {
            if (this.dragging && this.selecting_author === 1) {
                this.tagWord(index)
            }
        },
        submit_paragraph: function (tag) {
            const sentence_tags = new Array(this.text.length);
            sentence_tags.fill(tag);
            const that = this;
            $.ajax({
                type: 'POST',
                url: '/api/submitTags/',
                data: JSON.stringify({
                    'article_id': that.article_id,
                    'sentence_id': that.sentence_id,
                    'first_sentence': that.first_sentence,
                    'last_sentence': that.last_sentence,
                    'tags': sentence_tags,
                    'authors': [],
                    'task': that.tagging_task,
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
        button_color: function (index) {
            if (this.author_indices.includes(index)){
                return "green lighten-4"
            }else if (this.quote_markers[index] === 1){
                return "deep-orange lighten-4"
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
        },
    },
};
</script>
