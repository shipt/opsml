import { getRepos } from "$lib/scripts/repositories";
import { getRegistryPage, getRegistryStats } from "$lib/scripts/registry_page";

/** @type {import('./$types').PageLoad} */
export async function load({ route }) {
  let registry: string = route.id.split("/")[3].replace(/s+$/, "");
  let items: string[] = await getRepos(registry);
  let registryStats = await getRegistryStats(registry, undefined);
  let registryPage = await getRegistryPage(
    registry,
    undefined,
    undefined,
    undefined,
    0
  );

  return {
    args: {
      searchTerm: "",
      items: items,
      registry: registry,
      selectedRepo: null,
      registryStats: registryStats,
      registryPage: registryPage,
    },
  };
}
