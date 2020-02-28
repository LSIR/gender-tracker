<template>
    <v-container
            fluid
            style="width: 800px; background-color: white;"
    >
        <v-layout text-center wrap>
            <v-flex mb-4>
                <h1 class="font-weight-bold">
                    Heidi Gender Tracker
                </h1>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                    Le Heidi Gender Tracker est un projet d’algorithme du média suisse Heidi.news et de l’EPFL pour
                    mesurer la part des femmes dans les articles. Aujourd’hui, les femmes ne représentent que 30 % des
                    experts cités dans la presse. C’est le but de ce projet, et vous pouvez nous aider facilement. Pour
                    plus d'informations, allez sur la page de FAQ (lien en haut à droite).
                </div>
            </v-flex>
        </v-layout>
    </v-container>
</template>

<script>
    export default {
        name: "IntroText"
    }
</script>

<style scoped>

</style>