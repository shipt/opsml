import { getRepos } from "$lib/scripts/repositories";

/** @type {import('./$types').PageLoad} */
export async function load({ route }) {
  let registry: string = route.id.split("/")[3].replace(/s+$/, "");
  let items: string[] = await getRepos(registry);

  return {
    args: {
      searchTerm: "",
      items: items,
      registry: registry,
      selectedRepo: "",
    },
  };
}
