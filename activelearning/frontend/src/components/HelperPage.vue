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
                    {{intro_text}}
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
                                v-bind:color="button_color(j, quote_markers_0, author_indices_0)"
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
                    <v-btn class="ma-2" outlined>Aucune Citation</v-btn>
                    <v-btn class="ma-2" outlined>Soumettre</v-btn>
                    <v-btn class="ma-2" outlined>Réinitialiser</v-btn>
                    <v-btn class="ma-2" outlined>Sauter</v-btn>
                </div>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    {{sentence_annotation_text_0}}
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
                                v-bind:color="button_color(j, quote_markers_1, author_indices_1)"
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
                    {{sentence_annotation_text_1}}
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
                                v-bind:color="button_color(j, quote_markers_2, author_indices_2)"
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
                    {{sentence_annotation_text_2}}
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
        <v-layout text-centerg wrap>
            <v-flex mb-4>
                <h3>
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
                    {{paragraph_annotation_text_0}}
                </div>
            </v-flex>
        </v-layout>

    </v-container>
</template>

<script>

export default {
    data: () => ({
        //
        intro_text: 'Vous verrez du texte présenté sous deux formes. Soit vous verrez un paragraph entier, soit vous ' +
            'verrez une seule phrase. Si vous voyez un paragraphe, vous devrez simplement indiquer si il contient ' +
            'des citations. Si vous voyez une phrase, vous devrez determiner si elle contient une citation. Si ' +
            'c\'est le cas, votre tâche est de nous indiquer l\'auteur de la citation ainsi que son contenu.',
        sentence_annotation_text_0: 'Si la phrase affichée ne contient pas de citation, ils vous suffit de cliquer ' +
            'sur le bouton "AUCUNE CITATION". Une nouvelle phrase s\'affichera Si elle contient une citation, vous ' +
            'devez commencer par cliquer sur le premier mot qui fait partie de la citation. Il devrait devenir rouge' +
            ', comme c\'est le cas ci-dessous:',
        sentence_annotation_text_1: 'Vous devez ensuite cliquer sur le dernier mot de la citation. Tous les mots ' +
            'entre s\'afficheront en rouge. Ensuite, vous devez cliquer sur le nom de la personne qui est citée, qui ' +
            'deviendra vert.',
        sentence_annotation_text_2: 'Une fois que la citation entière et son auteur est chosis, le bouton ' +
            '"SOUMETTRE" peut être utiliser pour confirmer les réponses. Pour recommencer, le bouton "REINITIALISER" ' +
            ' peut être utilisé. ' +
            'Si vous n\'êtes pas sur si la phrase contient une citation ou pas, cliquez sur "SAUTER". '+
            'Il est possible qu\'une citation soit contenue dans plusieures phrases ' +
            'consécutives, ou que l\'auteur d\'une citation ne soit pas dans le même phrase que le texte cité. ' +
            'C\'est pour cela que deux boutons sont a disposition, qui affichent le text au-dessus ou au-dessous de ' +
            'la phrase.' ,
        paragraph_annotation_text_0: 'Votre tâche est simplement de lire le paragraphe, et de répondre si il contient' +
            'ou non des citations.',
        // List of tokens displayed on the page
        sentence_text: ['Selon\xa0', 'Bastien\xa0', 'Favre', ',\xa0', '"', 'Neuchâtel\xa0', 'Xamax\xa0', 'ne\xa0',
            'se\xa0', 'fera\xa0', 'pas\xa0', 'reléguer\xa0', 'cette\xa0', 'saison', '"', '.'],
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
        this.loadContent()
    },
    methods: {
        button_color: function (index, quote_markers, author_indices) {
            if (quote_markers[index] === 1) {
                return "deep-orange lighten-4"
            }else if (author_indices.includes(index)){
                return "green lighten-4"
            }else{
                return "white"
            }
        },
    },
};

</script>
