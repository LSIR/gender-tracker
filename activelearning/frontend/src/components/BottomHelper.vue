<template>
    <v-container
            fluid
            style="width: 800px; background-color: white;"
    >
        <v-layout text-center wrap>
            <v-flex mb-4>
                <h2 class="font-weight-bold">
                    Légende
                </h2>
            </v-flex>
        </v-layout>


        <v-layout text-left wrap>
            <v-flex mb-4>
                <div class="mb-4">
                    Le texte sélectionné comme citation se colorie en rouge, et celui comme auteur de la
                    citation en vert.
                </div>
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