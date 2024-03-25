interface repositories {
  repositories: string[];
}

interface names {
  names: string[];
}

async function getRepos(registry: string) {
  const repos = await fetch(
    "/opsml/cards/repositories?" +
      new URLSearchParams({
        registry_type: registry,
      })
  );

  const response: repositories = await repos.json();
  return response.repositories;
}

async function getNames(registry: string) {
  const repos = await fetch(
    "/opsml/cards/names?" +
      new URLSearchParams({
        registry_type: registry,
      })
  );

  const response: names = await repos.json();
  return response.names;
}

export { getRepos, getNames };
