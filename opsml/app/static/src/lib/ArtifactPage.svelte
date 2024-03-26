
<script lang="ts">
  export let nbr_names: number;
  export let nbr_versions: number;
  export let nbr_repos: number;
</script>



<div class="flex">
  <div class="flex-initial w-24 ...">
    <div class="items-center text-lg font-bold">
      <h1>Artifacts</h1>
    </div>
  </div>
  <div class="flex-auto ...">
    <span class="badge variant-filled">Names: {nbr_names}</span>
  </div>
  <div class="flex-auto ...">
    <span class="badge variant-filled">Versions: {nbr_versions}</span>
  </div>
</div>


