<template>
    <v-container
            fluid
            style="width: 800px; background-color: white;"
    >
        <v-layout text-center wrap>
            <v-flex mb-4>
                <h1 class="font-weight-bold mt-12">
                    Heidi Gender Tracker
                </h1>
            </v-flex>
        </v-layout>
        <v-layout text-left wrap>
            <v-flex mb-4>
                <div>
                  Bienvenue sur le projet d’algorithme développé par Heidi.news et l’EPFL. Son but: mesurer la part des femmes citées dans les articles de presse. En quelques clics, vous pouvez nous aider à «entraîner» cet algorithme. C'est très simple, et ne prend que quelques minutes: d'abord: vous devez identifier le texte qui est une citation, puis identifier son auteur. <br />
C'est parti, suivez les étapes ci-dessous! 
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
