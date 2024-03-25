<script lang="ts">

	export let searchTerm;

</script>



<div class="search-bar">

  <input  class="h-7 rounded-full w-full border border-gray-200/70 bg-white pl-2 text-sm placeholder-gray-400 ring-0 focus:outline-primary-500" 
          autocomplete="off" 
          placeholder="Filter artifacts" 
          type="text"
          bind:value={searchTerm}
          on:input />
</div>