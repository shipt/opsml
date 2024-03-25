<script lang="ts">

	import Search from "$lib/Search.svelte";
  import Tag from "$lib/Tag.svelte";
  import { page } from '$app/stores';
  import { getRepos, getNames } from "$lib/scripts/repositories";
  import { onMount } from 'svelte';
  import { TabGroup, Tab } from '@skeletonlabs/skeleton';
  import js from "jquery";

  let items: string[] = [];
  let searchTerm = "";
  let filteredItems: string[] = [];
  let tabSet: string = "names";
  let selectedTags: string[] = [];
  let registry: string = $page.url.pathname.split("/")[3];
  
  let showNameTags: boolean = true;
  let showRepoTags: boolean = true;

  let activeTag: string = "";

  async function getRegistryRepos() {
    items = await getRepos(registry.replace(/s+$/, ''));
  }

  async function getRegistryNames() {
    items = await getNames(registry.replace(/s+$/, ''));
  }

  const searchItems = () => {	
		return filteredItems = items.filter(item => {
			let itemName = item.toLowerCase();
			return itemName.includes(searchTerm.toLowerCase())
		});
	}

  onMount(() => {
    window.jq = js;
    getRegistryNames();
  });

  function toggleActiveTag() {
    window.jq(this).find('span').toggleClass('active');
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
            <Tab on:click={getRegistryNames} bind:group={tabSet} name="names" value="names">Names</Tab>
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
                on:click={toggleActiveTag}
                />
              {/each}

            {:else}
              {#each items as item}
                <Tag 
                  name={item} 
                  searchType={tabSet}
                  on:click={toggleActiveTag}
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
