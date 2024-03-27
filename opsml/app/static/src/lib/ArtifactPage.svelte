
<script lang="ts">

  import Search from "$lib/Search.svelte";
  import { getRegistryPage } from "$lib/scripts/registry_page";

  type record = [string, string, number, number, number, number];

  interface registryQuery {
    page: record[];
  }

  export let nbr_names: number;
  export let nbr_versions: number;
  export let nbr_repos: number;
  export let registryPage: registryQuery;
  export let registry: string;
  export let selectedRepo: string;


  let searchTerm: string | undefined = undefined;


  const searchPage = async function () {
    console.log(searchTerm);
    registryPage = await getRegistryPage(registry, undefined, selectedRepo, searchTerm, 0);

    console.log(registryPage);
  }

function delay(fn, ms) {
  let timer = 0
  return function(...args) {
    clearTimeout(timer)
    timer = setTimeout(fn.bind(this, ...args), ms || 0)
  }
}

function hello() {
  console.log(searchTerm);
}



</script>




<div class="flex flex-row items-center text-lg font-bold">
    <h1>Artifacts</h1>
</div>

<div class="flex flex-row">
  <div>
    <span class="badge variant-filled">{nbr_names} artifacts</span>
  </div>
  <div class="pl-3">
    <span class="badge variant-filled">{nbr_versions} versions</span>
  </div>
  <div class="pl-3">
    <span class="badge variant-filled">{nbr_repos} repos</span>
  </div>
  <div class="pl-3 md:w-1/2">
    <Search bind:searchTerm on:keydown={delay(searchPage, 1000)} />
  </div>
</div>


