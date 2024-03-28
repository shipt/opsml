<script lang="ts">

  import { TabGroup, Tab } from '@skeletonlabs/skeleton';
  import Fa from 'svelte-fa'
  import { faTag } from '@fortawesome/free-solid-svg-icons'

  /** @type {import('./$types').PageData} */
	export let data;

  let registry: string;
  $: registry = data.registry;

  let name: string;
  $: name = data.name;

  let repository: string;
  $: repository = data.repository;

  let version: string;
  $: version = data.version;

  let path: string;
  $: path = data.path;

</script>

<div class="flex flex-1 flex-col">

  <div class="pl-12 sm:pl-20 pt-6 sm:pt-8 bg-slate-50 w-full">
    <h1 class="flex flex-row ... items-center text-lg">
      <div class="group flex flex-none items-center">
        <a class="font-semibold text-gray-800 hover:text-secondary-500" href="/opsml/registry/{path}?respository={repository}">{repository}</a>
        <div class="mx-0.5 text-gray-800">/</div>
      </div>
      <div class="font-bold text-primary-500">{name}</div>
    </h1>
    <div class="pt-2 flex flex-wrap flex-row ... items-center">
      <div>
        <a href="/opsml/registry/{path}/versions?name={name}&repository={repository}&version={version}" class="badge w-16 bg-surface-100 border border-surface-300 hover:bg-gradient-to-b from-surface-50 to-primary-100">
          <Fa icon={faTag} color="#4b3978"/>
          <span class="text-primary-500">{version}</span>
        </a>
      </div>
    </div>
  </div>
    <!-- ... -->
    <div class="bg-white">09</div>

</div>
