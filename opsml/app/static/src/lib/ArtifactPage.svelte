
<script lang="ts">
  export let nbr_names: number;
  export let nbr_versions: number;
  export let nbr_repos: number;
</script>


<section class="pt-8 border-gray-100 col-span-full pb-12">
  <div class="mb-4 items-center space-y-3 md:flex md:space-y-0 lg:mb-6">
    <div class="flex items-center text-lg">
        <h1>Artifacts</h1>
        <div class="ml-3 w-16 font-normal text-gray-400">Names: {nbr_names}</div>
        <div class="ml-3 w-16 font-normal text-gray-400">Versions: {nbr_versions}</div>
        <div class="ml-3 w-16 font-normal text-gray-400">Repositories: {nbr_repos}</div>
    </div>
  </div>
</section>