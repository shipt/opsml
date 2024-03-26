<script lang="ts">

	import Search from "$lib/Search.svelte";
  import Tag from "$lib/Tag.svelte";
  import { page } from '$app/stores';
  import { getRepos } from "$lib/scripts/repositories";
  import { onMount } from 'svelte';
  import { TabGroup, Tab } from '@skeletonlabs/skeleton';
  import { navigating } from '$app/stores';

  let items: string[] = [];
  let filteredItems: string[] = [];

  let searchTerm = "";
  let tabSet: string = "repos";
  let registry: string = $page.url.pathname.split("/")[3];
  let selectedRepo: string = "";
  

  async function getRegistryRepos() {
    items = await getRepos(registry.replace(/s+$/, ''));
  }

  const searchItems = () => {	
		return filteredItems = items.filter(item => {
			let itemName = item.toLowerCase();
			return itemName.includes(searchTerm.toLowerCase())
		});
	}

  onMount(() => {
    getRegistryRepos();
    console.log(selectedRepo);
  });

  function setActiveRepo( name: string) {
    selectedRepo = name;
    console.log(selectedRepo);
  }

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
            <Tab on:click={getRegistryRepos} bind:group={tabSet} name="repos" value="repos">Repositories</Tab>

          </TabGroup>
          <div class="pt-4">
            <Search bind:searchTerm on:input={searchItems} />
          </div>
          <div class="flex flex-wrap pt-4 gap-1">

          

            {#if searchTerm && filteredItems.length == 0}
              <p class="text-gray-400">No items found</p>

            {:else if filteredItems.length > 0}
              {#each filteredItems as item}
                <Tag 
                name={item} 
                searchType={tabSet} 
                active={selectedRepo}
                on:click={() => setActiveRepo(item)}
                />
              {/each}

            {:else}
              {#each items as item}

                <Tag 
                  name={item} 
                  searchType={tabSet}
                  active={selectedRepo}
                  on:click={() => setActiveRepo(item)}
                />
              {/each}

            {/if}

          </div>
        </div>
      </div>
      <div class="col-span-2 ...">
        <slot></slot>
      </div>
    </div>  
  </div>
</div>
