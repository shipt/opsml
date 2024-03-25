<script lang="ts">

	import Search from "$lib/Search.svelte";
  import Tag from "$lib/Tag.svelte";
  import { page } from '$app/stores';
  import { getRepos } from "$lib/scripts/repositories";
  import { onMount } from 'svelte';
  import { TabGroup, Tab } from '@skeletonlabs/skeleton';

  let items: string[] = [];
  let searchTerm = "";
  let filteredRepos: string[] = [];
  let tabSet: number = 0;

  async function getRegistryRepos() {
    let registry: string = $page.url.pathname.split("/")[3];
    items = await getRepos(registry.replace(/s+$/, ''));
    console.log("repo");
  }

  async function getRegistryNames() {
    let registry: string = $page.url.pathname.split("/")[3];
    items = await getRepos(registry.replace(/s+$/, ''));
    console.log("name");
  }

  const searchItems = () => {	
		return filteredItems = items.filter(item => {
			let itemName = item.toLowerCase();
			return itemName.includes(searchTerm.toLowerCase())
		});
	}

  onMount(() => {
    getRegistryRepos();
  });

</script>

<div class="bg-slate-50">
  <div class="container mx-auto mb-4 sm:mb-4">
    <div class="grid grid-cols-3 gap-4">
      <div class="hidden md:block col-span-1">
        <div class="p-4">
          <TabGroup 
          border=""
          active='border-b-2 border-primary-500'
          >
            <Tab on:click={getRegistryNames} bind:group={tabSet} name="names" value={0}>Names</Tab>
            <Tab on:click={getRegistryRepos} bind:group={tabSet} name="repos" value={1}>Repositories</Tab>

          </TabGroup>
          <div class="pt-4">
            <Search bind:searchTerm on:input={searchItems} />
          </div>
          <div class="flex flex-wrap pt-4 gap-1">
            {#each items as item}
              <Tag name={item} />
            {/each}
          </div>
        </div>
      </div>
      <div class="col-span-2 ...">
        <slot></slot>
      </div>
    </div>  
  </div>
</div>
