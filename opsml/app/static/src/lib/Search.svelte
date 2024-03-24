<script lang="ts">

	export let searchTerm;

</script>



<div class="search-bar">
  <input  class="h-7 min-w-0 flex-1 rounded-full border border-gray-200/70 bg-white pl-7 text-sm placeholder-gray-400 ring-0 focus:outline-none" 
          autocomplete="off" 
          placeholder="Filter artifacts by repository" 
          type="text"
          bind:value={searchTerm}
          on:input />
</div>