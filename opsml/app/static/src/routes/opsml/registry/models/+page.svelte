<script lang="ts">

  import Fa from 'svelte-fa'
  import { faCheck } from '@fortawesome/free-solid-svg-icons'
	import Search from "$lib/Search.svelte";
  import Tag from "$lib/Tag.svelte";
  import ArtifactPage from "$lib/ArtifactPage.svelte";
  import PageCard from "$lib/PageCard.svelte";
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { TabGroup, Tab } from '@skeletonlabs/skeleton';
  import {
  getRegistryPage,
  getRegistryStats,
} from "$lib/scripts/registry_page";
import { Paginator } from '@skeletonlabs/skeleton';
import js from "jquery";

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
  let registry: string = $page.url.pathname.split("/")[3].replace(/s+$/, "");
  

  const searchItems = () => {	
		return filteredItems = items.filter(item => {
			let itemName = item.toLowerCase();
			return itemName.includes(searchTerm.toLowerCase())
		})
	}
  const source = [ 0,1,2,3,4];
  let paginationSettings = {
    page: 0,
    limit: 30,
    size: registryStats.nbr_names,
    amounts: [],
  } satisfies PaginationSettings;


  onMount(() => {
    window.jq = js;
    let selectedRepo = "";
    
  });

  async function setActiveRepo( name: string) {

    if (selectedRepo === name) {
      selectedRepo = "";
    } else {
      selectedRepo = name;
    }


  }

  async function onPageChange(e: CustomEvent): void {
    let page = e.detail;
    let repoToQuery: string | undefined;
    let searchText: string | undefined;
    
    if (selectedRepo === "") {
      repoToQuery = undefined;
    } else {
      repoToQuery = selectedRepo;
    }

    if (searchTerm === "") {
      searchText = undefined;
    } else {
      searchText = searchTerm;
    }


  registryPage = await getRegistryPage(registry, undefined, repoToQuery, searchText, page);
  $: paginationSettings.page = page;

  }



</script>


<div class="flex">
  <div class="hidden md:block flex-initial w-1/4 pl-16 bg-surface-100 dark:bg-surface-600 min-h-screen ...">
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
              class="chip hover:bg-primary-300 {selectedRepo === item ? 'bg-primary-300' : 'variant-soft'}"
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
              class="chip hover:bg-primary-300 {selectedRepo === item ? 'bg-primary-300' : 'variant-soft'}"
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
  <div class="flex-auto w-64 p-4 bg-white dark:bg-surface-900 min-h-screen pr-16 ...">
    <ArtifactPage 
        nbr_names={registryStats.nbr_names}
        nbr_versions={registryStats.nbr_versions}
        nbr_repos={registryStats.nbr_repos} 
      />
    <div class="pt-8 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {#each registryPage.page as item}
        <PageCard 
          name={item[0]}
          repository={item[1]}
          nbr_versions={item[2]}
          updated_at={item[3]}
        />
      {/each}
    </div>

    <div class="pt-8 flex items-center">
   
      <div class="flex-1 mb-12 w-64 content-center">
        <Paginator
          bind:settings={paginationSettings}
          showFirstLastButtons="{true}"
          showPreviousNextButtons="{true}"
          justify="justify-center"
          on:page={onPageChange}
        />
      </div>
    </div>
  </div>
</div>

