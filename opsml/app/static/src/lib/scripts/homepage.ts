interface CardRequest {
  registry_type: string;
  limit: number;
}

interface CardJson {
  date: string;
  app_env: string;
  uid: string;
  repository: string;
  contact: string;
  name: string;
  version: string;
  timestamp: string;
  tags: Map<string, string>;
}

interface CardResponse {
  cards: CardJson[];
}

interface RecentCards {
  modelcards: CardJson[];
  datacards: CardJson[];
  runcards: CardJson[];
}

async function getCards(registry: string): Promise<CardJson[]> {
  const modelcards = await fetch("/opsml/cards/list", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ registry_type: registry, limit: 10 }),
  });

  let response: CardResponse = await modelcards.json();
  return response.cards;
}

async function getRecentCards(): Promise<RecentCards> {
  let modelcards: CardJson[] = await getCards("model");
  let datacards: CardJson[] = await getCards("data");
  let runcards: CardJson[] = await getCards("run");

  let recentCards: RecentCards = {
    modelcards: modelcards,
    datacards: datacards,
    runcards: runcards,
  };

  return recentCards;
}

export { getRecentCards, getCards };
