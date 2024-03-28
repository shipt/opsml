import {
  type registryStats,
  type registryPage,
  type repositories,
} from "$lib/scripts/types";

export const ssr = false;

/** @type {import('./$types').EntryGenerator} */
export function entries() {
  return [{ registry: "data" }, { registry: "models" }];
}

/** @type {import('./$types').PageLoad} */
export async function load({ fetch, params }) {
  let registry: string = params.registry.replace(/s+$/, "");

  // get the repositories
  const repos: repositories = await fetch(
    "/opsml/cards/repositories?" +
      new URLSearchParams({
        registry_type: registry,
      })
  ).then((res) => res.json());

  // get initial stats and page
  const stats: registryStats = await fetch(
    `/opsml/card/registry/stats?registry_type=${registry}`
  ).then((res) => res.json());

  // get page
  const page: registryPage = await fetch(
    `/opsml/cards/registry/query/page?registry_type=${registry}&page=0`
  ).then((res) => res.json());

  return {
    args: {
      searchTerm: undefined,
      repos: repos.repositories,
      registry: registry,
      selectedRepo: undefined,
      registryStats: stats,
      registryPage: page,
    },
  };
}