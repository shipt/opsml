<script lang="ts">

  import Fa from 'svelte-fa'
  import { faCheck } from '@fortawesome/free-solid-svg-icons'
	import Search from "$lib/Search.svelte";
  import Tag from "$lib/Tag.svelte";
  import ArtifactPage from "$lib/ArtifactPage.svelte";
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { TabGroup, Tab } from '@skeletonlabs/skeleton';
  import {
  getRegistryPage,
  getRegistryStats,
} from "$lib/scripts/registry_page";

  /** @type {import('./$types').PageData} */
	export let data;

  // reactive statements
  let items = data.args.items;
  let searchTerm = data.args.searchTerm;
  let selectedRepo: string = data.args.selectedRepo;
  let registryPage = data.args.registryPage;
  let registryStats = data.args.registryStats;
  let activePage: number = 0;


  let filteredItems: string[] = [];
  let tabSet: string = "repos";
  let registry: string = $page.url.pathname.split("/")[3];
  

  const searchItems = () => {	
		return filteredItems = items.filter(item => {
			let itemName = item.toLowerCase();
			return itemName.includes(searchTerm.toLowerCase())
		})
	}

  onMount(() => {
    let selectedRepo = "";
  });

  async function setActiveRepo( name: string) {

    if (selectedRepo === name) {
      selectedRepo = "";
    } else {
      selectedRepo = name;
    }


  }

</script>


<div class="flex">
  <div class="hidden md:block flex-initial w-1/4 pl-16 bg-slate-100 min-h-screen ...">
    <div class="p-4">
      <TabGroup 
      border=""
      active='border-b-2 border-primary-500'
      >
        <Tab bind:group={tabSet} name="repos" value="repos">Repositories</Tab>

      </TabGroup>
      <div class="pt-4">
        <Search bind:searchTerm on:input={searchItems} />
      </div>
      <div class="flex flex-wrap pt-4 gap-1">

        {#if searchTerm && filteredItems.length == 0}
          <p class="text-gray-400">No items found</p>

        {:else if filteredItems.length > 0}
          {#each filteredItems as item}
           
            <button
              class="chip {selectedRepo === item ? 'variant-filled' : 'variant-soft'}"
              on:click={() => { setActiveRepo(item); }}
              on:keypress
            >
              {#if selectedRepo === item}<span><Fa icon={faCheck} /></span>{/if}
              <span>{item}</span>
            </button>

          {/each}

        {:else}
          {#each items as item}

            <button
              class="chip {selectedRepo === item ? 'variant-filled' : 'variant-soft'}"
              on:click={() => { setActiveRepo(item); }}
              on:keypress
            >
              {#if selectedRepo === item}<span><Fa icon={faCheck} /></span>{/if}
              <span>{item}</span>
            </button>
        
          {/each}

        {/if}

      </div>
    </div>
  </div>
  <div class="flex-auto w-64 p-4 bg-white ...">
    <ArtifactPage 
          nbr_names={registryStats.nbr_names}
          nbr_versions={registryStats.nbr_versions}
          nbr_repos={registryStats.nbr_repos} 
        />
  </div>
</div>

