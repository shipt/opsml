
<script lang="ts">

  type record = [string, string, number, number, number, number];

  interface registryQuery {
    page: record[];
  }

  export let nbr_names: number;
  export let nbr_versions: number;
  export let nbr_repos: number;
  export let registryPage: registryQuery;
</script>




<div class="items-center text-lg font-bold">
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
</div>


