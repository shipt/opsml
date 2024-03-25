<script lang="ts">

	import Search from "$lib/Search.svelte";
  import { page } from '$app/stores';
  import { getRepos } from "$lib/scripts/repositories";
  import { onMount } from 'svelte';


  let repos: string[] = [];
  let searchTerm = "";
  let filteredRepos: string[] = [];

  onMount(async () => {
    
    let registry: string = $page.url.pathname.split("/")[3];
		let repos: string[] = await getRepos(registry.replace(/s+$/, ''));
    console.log(repos);
	
	});

  const searchRepos = () => {	
		return filteredRepos = repos.filter(repo => {
			let repoName = repo.toLowerCase();
			return repoName.includes(searchTerm.toLowerCase())
		});
	}

</script>

<div class="container relative flex flex-col lg:grid lg:space-y-0 w-full lg:grid-cols-10 md:flex-1 md:grid-rows-full md:gap-6 ">
  <slot></slot>
</div>