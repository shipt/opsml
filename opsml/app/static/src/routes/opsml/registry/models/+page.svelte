<script lang="ts">

	import Search from "$lib/Search.svelte";
  import Tag from "$lib/Tag.svelte";
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { TabGroup, Tab } from '@skeletonlabs/skeleton';

  /** @type {import('./$types').PageData} */
	export let data;

  // reactive statements
  let items = data.args.items;
  let searchTerm = data.args.searchTerm;
  let selectedRepo: string = data.args.selectedRepo;
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

<div class="bg-slate-50">
  <div class="container mx-auto mb-4 sm:mb-4">
    <div class="grid grid-cols-3 gap-4">
      <div class="hidden md:block col-span-1">
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
        <section class="pt-8 border-gray-100 col-span-full pb-12">
          <div class="mb-4 items-center space-y-3 md:flex md:space-y-0 lg:mb-6">
              <div class="flex items-center text-lg">
                  <h1>Models</h1>
              </div>
          </div>
      </section>
      </div>
    </div>  
  </div>
</div>
