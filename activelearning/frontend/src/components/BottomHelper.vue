<template>
    <v-container
            fluid
            style="width: 800px; background-color: white;"
    >
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div class="mb-4">

                </div>
            </v-flex>
        </v-layout>

        <v-layout text-center wrap>
            <v-flex mb-4>
                <h2 class="font-weight-bold">
                    Heidi Gender Tracker
                </h2>
            </v-flex>
        </v-layout>


        <v-layout text-left wrap>
            <v-flex mb-4>
                <div class="mb-4">
                    Le Heidi Gender Tracker est un projet d’algorithme du média suisse Heidi.news et de l’EPFL pour
                    mesurer la part des femmes dans les articles. Aujourd’hui, les femmes ne représentent que 30 % des
                    experts cités dans la presse. C’est le but de ce projet, et vous pouvez nous aider facilement.
                </div>
                <div class="mb-4">
                    Comment ? C’est très simple, suivez les instructions ci-dessous.
                </div>
                <ol class="mb-4">
                    <li>
                        Regardez le paragraphe et cliquez sur le premier mot de la citation (le premier mot s’affiche
                        en rouge), si une citation est présente dans le texte.
                    </li>
                    <li>
                        Cliquez maintenant sur le dernier mot de la citation (la citation s’affiche en rouge)
                        <ul>
                            <li>
                                Si la citation est "coupée" en plusieures parties, vous pouvez cliquer sur recommencer
                                1. et 2. avec la suite de la citation
                            </li>
                        </ul>
                    </li>
                    <li>
                        Cliquez sur le bouton auteur
                    </li>
                    <li>
                        Cliquez sur le prénom et le nom de l’auteur de la citation, qui s'affiche en vert, puis cliquez
                        sur soumettre (et vous pouvez recommencer)
                    </li>
                </ol>
                <div class="mb-4">
                    Pour plus d'informations, allez sur la page de FAQ (lien en haut à droite).
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


    </v-container>
</template>

<script>
    export default {
        name: "BottomHelper"
    }
</script>

<style scoped>

</style>