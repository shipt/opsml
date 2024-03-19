

<script lang="ts">
  import logo from '$lib/images/opsml-logo.png';
  import modelcard from '$lib/images/modelcard-circuit.svg';
  import { onMount } from 'svelte';
  import  { getModelCards } from '$lib/scripts/homepage';
  import Card from '$lib/card.svelte';
	
  interface CardRequest {
  registry_type: string;
  limit: number;
  }

  const modelcards = getModelCards();


</script>
  
<div class="container mx-auto mb-16 pt-12 sm:mb-32 sm:pt-20">
  <div class="mb-10 flex items-center justify-center gap-2 text-xl font-bold sm:mb-8">
      <div class="mr-2 h-px flex-1 translate-y-px bg-gradient-to-l from-primary-200 to-white"></div>
        Recent <img src={logo} class="w-8" alt=""> Assets
      <div class="ml-2 h-px flex-1 translate-y-px bg-gradient-to-r from-primary-200 to-white"></div>
  </div>
  <div class="relative grid grid-cols-1 gap-6 lg:grid-cols-3">
    <div class="relative col-span-1 flex flex-col items-stretch text-center">
      <h2 class="mb-5 flex items-center justify-center  text-lg font-semibold 2xl:mb-6 2xl:text-xl">
        <img src={modelcard} class="w-24" alt="">
        ModelCards
      </h2>
      <div class="mb-3 flex flex-col items-center gap-2.5 rounded-xl bg-white/40 p-3 backdrop-blur-lg sm:mb-7">
        {#await modelcards}
          <div>Loading...</div>
        {:then modelcards}
          {#each modelcards as modelcard}
            <Card 
              color="to-primary-200"
              repository= {modelcard.repository} 
              name= {modelcard.name}
              version= {modelcard.version}
              registry= {modelcard.registry}
              date= {modelcard.date}
            />
          {/each}
        {/await}
      </div>
    </div>
    <div class="relative col-span-1 flex flex-col items-stretch text-center">
      <h2 class="mb-5 flex items-center justify-center  text-lg font-semibold 2xl:mb-6 2xl:text-xl">
        <img src={modelcard} class="w-24" alt="">
        DataCards
      </h2>
      <div class="mb-3 flex flex-col items-center gap-2.5 rounded-xl bg-white/40 p-3 backdrop-blur-lg sm:mb-7">
        {#await modelcards}
          <div>Loading...</div>
        {:then modelcards}
          {#each modelcards as modelcard}
            <Card 
              repository= {modelcard.repository} 
              name= {modelcard.name}
              version= {modelcard.version}
              registry= {modelcard.registry}
              date= {modelcard.date}
            />
          {/each}
        {/await}
      </div>
    </div>
    <div class="relative col-span-1 flex flex-col items-stretch text-center">
      <h2 class="mb-5 flex items-center justify-center  text-lg font-semibold 2xl:mb-6 2xl:text-xl">
        <img src={modelcard} class="w-24" alt="">
        Runs
      </h2>
    </div>
  </div>
</div>


		