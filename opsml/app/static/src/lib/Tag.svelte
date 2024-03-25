<script lang="ts">
    import js from "jquery";
    export let name:string;
    export let searchType:string;




</script>

<a class='{searchType}-tag' on:click href="?{searchType}={name}">
    <span id={name} class="badge variant-ghost-secondary text-secondary-800 hover:bg-secondary-300">{name}</span>
</a>


<style>
    a span.active {
        background-color: pink;
    }
</style>


