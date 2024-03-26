type record = [string, string, number, number, number, number];

interface registryQuery {
  page: record[];
}

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
