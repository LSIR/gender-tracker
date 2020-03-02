<template>
    <v-container
            fluid
            style="width: 800px; background-color: white;"
    >
        <v-layout text-left wrap>
            <v-flex mb-4>
                <h2 class="display-0 font-weight-bold mb-2">
                    C’est quoi le Heidi Gender Tracker ?
                </h2>
                <div class="mb-6">
                    Le Heidi Gender Tracker est un projet d’algorithme du média suisse Heidi.news avec l’aide de l’EPFL
                    pour mesurer la part des femmes dans les articles. Aujourd’hui, les femmes ne représentent que 30 %
                    des experts cités dans la presse. Nous voulons développer un outil pour mesurer la part des femmes
                    et la part des hommes dans la production en ligne.
                </div>
                <h2 class="display-0 font-weight-bold mb-2">
                    Qui s’occupe de ce projet ?
                </h2>
                <div class="mb-6">
                    Ce projet est porté par le média suisse Heidi.news et l’Ecole Polytechnique Fédérale de Lausanne.
                </div>
                <h2 class="display-0 font-weight-bold mb-2">
                    D’où viennent les textes qui s’affichent ?
                </h2>
                <div class="mb-6">
                    Les articles proviennent de Heidi.news et de plusieurs médias francophones qui ont accepté que nous
                    puissions afficher de très courts extraits de leurs contenus. Qu’ils en soient ici remerciés : Le
                    Parisien, Nice Matin, Rue89 Strabourg, La Nouvelle République.
                </div>
                <h2 class="display-0 font-weight-bold mb-2">
                    Comment fonctionne cet algorithme ?
                </h2>
                <div class="mb-6">
                    On a écrit un article dessus, que vous pouvez lire ici (lien Médium).
                </div>
                <h2 class="display-0 font-weight-bold mb-2">
                    Que deviennent les réponses que je fournis ?
                </h2>
                <div class="mb-6">
                    Ces données sont utilisées pour «entraîner» l’algorithme. Elles resteront évidemment anonymes.
                </div>
                <h2 class="display-0 font-weight-bold mb-2">
                    Comment créer des annotations au texte?
                </h2>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Vous verrez du texte présenté sous deux formes. Soit vous verrez un paragraph entier, soit vous
                    verrez une seule phrase. Si vous voyez un paragraphe, vous devrez simplement indiquer si il contient
                    des citations. Si vous voyez une phrase, vous devrez determiner si elle contient une citation. Si
                    c'est le cas, votre tâche est de nous indiquer l'auteur de la citation ainsi que son contenu.
                </div>
            </v-flex>
        </v-layout>


        <v-layout text-left wrap>
            <v-flex mb-4>
                <h3>
                    Annotation une phrase à la fois.
                </h3>
                <div>
                    Si votre tâche est d'annoter une phrase, la page aura le format ci-dessous.
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <h3 class="subtitle-1 font-weight-bold mb-2">
                    {{helper_text[helper_text_shown]}}
                </h3>
                <div>
                    <v-btn-toggle
                            v-model="selecting_author"
                            shaped
                            mandatory
                    >
                        <v-btn
                                small
                                v-on:click="update_helper_text(2)"
                                v-bind:color="selecting_author === 0 ? 'deep-orange lighten-4' : 'white'"
                        >
                            Citation
                        </v-btn>
                        <v-btn
                                small
                                v-on:click="update_helper_text(3)"
                                v-bind:color="selecting_author === 1 ? 'green lighten-4' : 'white'"
                        >
                            Auteur
                        </v-btn>
                    </v-btn-toggle>
                </div>
                <br>
                <div>
                    <v-btn small color="blue lighten-5">Montrer le texte au-dessus</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout>
            <v-flex mb-4>
                <div>
                    <span v-for="(word, j) in sentence_text" :key="`${j}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-on:click.native="tagWord(j)"
                                v-on:mousedown.native="start_dragging(j)"
                                v-on:mouseup.native="stop_dragging()"
                                v-on:mouseover.native="drag_tag(j)"
                                v-bind:color="button_color(j)"
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap >
            <v-flex mb-4>
                <div>
                    <v-btn small color="blue lighten-5">Montrer le texte au-dessous</v-btn>
                </div>
                <br>
                <div>
                    <v-btn class="ma-2" width="180px" outlined v-on:click="clearAnswers">Soumettre</v-btn>
                </div>
                <div>
                    <v-btn class="ma-2" width="180px" outlined v-on:click="clearAnswers">Aucune Citation</v-btn>
                    <v-btn class="ma-2" width="180px" outlined v-on:click="clearAnswers">Réinitialiser</v-btn>
                    <v-btn class="ma-2" width="180px" outlined v-on:click="clearAnswers">Sauter</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Si la phrase affichée ne contient pas de citation, ils vous suffit de cliquer sur le bouton "AUCUNE
                    CITATION". Si la phrase contient une citation, vous devez commencer par cliquer sur le premier mot
                    qui fait partie de la citation. Il devrait devenir rouge comme c'est le cas ci-dessous.
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <div>
                    <span v-for="(word, j) in sentence_text" :key="`${j}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-bind:color="button_color_fake(j, quote_markers_1, author_indices_1)"
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Si vous n'êtes pas sûrs si la phrase est une citation ou pas, vous pouvez cliquer sur le
                    bouton 'SAUTER', et une nouvelle phrase s'affichera. Si vous avez fait une erreur, cliquer sur le
                    bouton 'réinitialiser' enlève les annotations faites à la phrase.
                </div>
                <br>
                <div>
                    Vous devez ensuite cliquer sur le dernier mot de la citation. Tous les mots entre s'afficheront en
                    rouge.
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <div>
                    <span v-for="(word, j) in sentence_text" :key="`${j}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-bind:color="button_color_fake(j, quote_markers_2, author_indices_1)"
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Si il reste du texte cité dans la phrase, vous pouvez l'annoter de la même façon. Lorsque tout le
                    texte cité est sélectionné, il faut cliquer sur le bouton 'Auteur', qui deviendra vert. Ensuite,
                    vous pouvez cliquer sur le nom et prénom de la personne qui est citée, qui deviendront vert.
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <div>
                    <span v-for="(word, j) in sentence_text" :key="`${j}`">
                        <v-btn
                                class="text-none"
                                depressed
                                v-bind:style="buttonStyle"
                                v-bind:color="button_color_fake(j, quote_markers_2, author_indices_2)"
                        >
                            {{ word }}
                        </v-btn>
                    </span>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Lorsque vous avez fini, cliquez sur soumettre pour valider vos réponses.
                </div>
            </v-flex>
        </v-layout>


        <v-layout text-left wrap>
            <v-flex mb-4>
                <h3>
                    Annotation d'un paragraph entier.
                </h3>
                <div>
                    Si votre tâche est d'annoter un paragraphe entier, la page aura le format ci-dessous.
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-center wrap>
            <v-flex mb-4>
                <h3 class="subtitle-1 font-weight-bold mb-2">
                    Est-ce qu'une citation est présente dans ce paragraphe?
                </h3>
            </v-flex>
        </v-layout>
        <v-layout
                text-left
                wrap
        >
            <v-flex mb-4>
                <div>
                    {{ paragraph_text }}
                </div>
            </v-flex>
        </v-layout>
        <v-layout
                text-center
                wrap
        >
            <v-flex mb-4>
                <div>
                    <v-btn-toggle tile>
                        <v-btn class="ma-2" color="white">Oui</v-btn>
                        <v-btn class="ma-2" color="white">Non</v-btn>
                    </v-btn-toggle>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Votre tâche est de lire le paragraphe, et de répondre si il contient ou non des citations.
                </div>
            </v-flex>
        </v-layout>

    </v-container>
</template>

<script>

export default {
    data: () => ({
        // List of tokens displayed on the page
        sentence_text: ['Selon\xa0', 'Bastien\xa0', 'Favre', ',\xa0', '"', 'Neuchâtel\xa0', 'Xamax\xa0', 'ne\xa0',
            'se\xa0', 'fera\xa0', 'pas\xa0', 'reléguer\xa0', 'cette\xa0', 'saison', '"', '.'],

        // Stuff to make the logic work. Commented in ContentTaggerDrag
        quote_markers: [0],
        author_indices: [],
        colors: ["black", "deep-orange darken-4", "green darken-4"],
        quote_open: false,
        quote_first_token: 0,
        selecting_author: 0,
        helper_text: [
            "Regardez le texte et cliquez sur le premier mot de la citation (le premier mot s’affiche en rouge)," +
                " si une citation y est présente. Sinon, cliquez sur \"Aucune Citation\"",
            "Clickez sur le dernier mot du text cité (la citation s’affiche en rouge).",
            "Cliquez sur le bouton \"Auteur\" si tout le text cité est sélectionné. Sinon, " +
                "sélectionnez le reste de la citation.",
            "Cliquez sur le prénom et le nom de l’auteur de la citation, qui s'affiche en vert, puis cliquez " +
                "sur soumettre."],
        helper_text_shown: 0,

        // Whether or not to show the tooltip to annotate the author
        show_author_tip: false,

        // Whether the user is doing click and drag
        dragging: false,

        quote_markers_0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        author_indices_0: [],
        quote_markers_1: [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        author_indices_1: [],
        quote_markers_2: [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        author_indices_2: [1, 2],

        paragraph_text: 'Selon Bastien Favre "Neuchâtel Xamax ne se fera pas reléguer cette saison". Il pense que l' +
            '\'addition de Geoffrey Serey Die est suffisante pour les garder dans l\'élite Suisse. Il sera quand ' +
            'même difficile pour eux d\'échapper aux barrages.',

        // The style of buttons to use
        buttonStyle: {
            'min-width': 0,
            'padding': '0px',
        }
    }),
    mounted: function () {
        this.quote_markers = (new Array(this.sentence_text.length)).fill(0);
    },
    methods: {
        clearAnswers: function () {
            // Set initial quote markers
            this.quote_markers = (new Array(this.sentence_text.length)).fill(0);
            // Set initial authors
            this.author_indices = [];
            // Set content variables to default
            this.quote_open = false;
            this.selecting_author = 0;
            this.helper_text_shown = 0;
            this.$forceUpdate();
        },
        button_color_fake: function (index, quote_markers, author_indices) {
            if (quote_markers[index] === 1) {
                return "deep-orange lighten-4"
            }else if (author_indices.includes(index)){
                return "green lighten-4"
            }else{
                return "white"
            }
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
        button_color: function (index) {
            if (this.author_indices.includes(index)){
                return "green lighten-4"
            }else if (this.quote_markers[index] === 1){
                return "deep-orange lighten-4"
            }else{
                return "white"
            }
        },
    },
};

</script>
