/** @type {import('./$types').PageLoad} */
export async function load({ params, url }) {
  let name = url.searchParams.get("name");
  let repository = url.searchParams.get("repository");
  let registry = params.registry.replace(/s+$/, "");
  let path = params.registry;

  return {
    registry: registry,
    repository: repository,
    name: name,
    version: "1.0.0",
    path: path,
  };
}

/** @type {import('./$types').EntryGenerator} */
export function entries() {
  return [{ registry: "data" }, { registry: "models" }];
}
