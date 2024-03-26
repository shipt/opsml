type record = [string, string, number, number, number, number];

interface registryQuery {
  page: record[];
}

interface registryStats {
  nbr_names: number;
  nbr_versions: number;
  nbr_repos: number;
}

// Function for searching general stats given a registry and search term
//
// Args:
//   registry: string - the registry to search
//   searchTerm: string - the search term to use
//
// Returns:
//   registryQuery - the general stats for the registry
async function getRegistryStats(
  registry: string,
  searchTerm: string | undefined
): Promise<registryStats> {
  let params = new URLSearchParams();
  params.append("registry_type", registry);
  if (searchTerm) {
    params.append("search_term", searchTerm);
  }

  const page_resp = await fetch("/opsml/card/registry/stats?" + params);

  const response: registryStats = await page_resp.json();
  return response;
}

// Function for searching a registry page given a registry, sort_by, repository, name, and page
//
// Args:
//   registry: string - the registry to search
//   sort_by: string - the sort_by to use
//   repository: string - the repository to use
//   name: string - the name to use
//   page: number - the page to use
//
// Returns:
//   registryQuery - the page for the registry
async function getRegistryPage(
  registry: string,
  sort_by: string | undefined,
  repository: string | undefined,
  name: string | undefined,
  page: number | undefined
): Promise<registryQuery> {
  // build request
  let params = new URLSearchParams();
  params.append("registry_type", registry);

  if (sort_by) {
    params.append("sort_by", sort_by);
  }
  if (repository) {
    params.append("repository", repository);
  }
  if (name) {
    params.append("name", name);
  }
  if (page) {
    params.append("page", (page - 1).toString());
  }

  const page_resp = await fetch("/opsml/cards/registry/query/page?" + params);

  const response: registryQuery = await page_resp.json();
  return response;
}

export { getRegistryStats, getRegistryPage };