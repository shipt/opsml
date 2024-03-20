

<script lang="ts">
  import logo from '$lib/images/opsml-logo.png';
  import modelcard from '$lib/images/modelcard-circuit.svg';
  import { onMount } from 'svelte';
  import  { getRecentCards } from '$lib/scripts/homepage';
  import HomeSpan from '$lib/Homepage_span.svelte';
  import Card from '$lib/Card.svelte';
	
  interface CardRequest {
  registry_type: string;
  limit: number;
  }

  const cards = getRecentCards();


</script>
  
<div class="container mx-auto mb-4 pt-12 sm:mb-4 sm:pt-20">
  <div class="mb-10 flex items-center justify-center gap-2 text-xl font-bold sm:mb-8">
      <div class="mr-2 h-px flex-1 translate-y-px bg-gradient-to-l from-primary-200 to-white"></div>
        Recent <img src={logo} class="w-12" alt=""> Assets
      <div class="ml-2 h-px flex-1 translate-y-px bg-gradient-to-r from-primary-200 to-white"></div>
  </div>


  <div class="relative grid grid-cols-1 gap-6 lg:grid-cols-3">

    <HomeSpan logo={modelcard} header="ModelCards" >
      {#await cards}
        <div>Loading...</div>
      {:then cards}
        {#each cards.modelcards as modelcard}
          <Card 
            repository= {modelcard.repository} 
            name= {modelcard.name}
            version= {modelcard.version}
            date= {modelcard.date}
          />
        {/each}
      {/await}
    </HomeSpan>

    <HomeSpan logo={modelcard} header="DataCards" >
      {#await cards}
        <div>Loading...</div>
      {:then cards}
        {#each cards.datacards as datacard}
          <Card 
            repository= {datacard.repository} 
            name= {datacard.name}
            version= {datacard.version}
            date= {datacard.date}
          />
        {/each}
      {/await}
    </HomeSpan>

    <HomeSpan logo={modelcard} header="RunCards" >
      {#await cards}
        <div>Loading...</div>
      {:then cards}
        {#each cards.runcards as runcard}
          <Card 
            repository= {runcard.repository} 
            name= {runcard.name}
            version= {runcard.version}
            date= {runcard.date}
          />
        {/each}
      {/await}
    </HomeSpan>

  </div>
</div>


		