/** @type {import('./$types').PageLoad} */
export async function load({ params, url }) {
  let name = url.searchParams.get("name");
  let repository = url.searchParams.get("repository");

  console.log(params);
  console.log(url);

  console.log(name);
  console.log(repository);

  let registry = params.registry.replace(/s+$/, "");
  console.log(registry);
}

/** @type {import('./$types').EntryGenerator} */
export function entries() {
  return [{ registry: "data" }, { registry: "models" }];
}
