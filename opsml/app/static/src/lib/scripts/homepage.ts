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

async function getModelCards(): Promise<CardJson[]> {
  const modelcards = await fetch("/opsml/cards/list", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ registry_type: "model", limit: 10 }),
  });

  let response: CardResponse = await modelcards.json();
  console.log(response);
  return response.cards;
}

async function getDataCards(): Promise<CardJson[]> {
  const modelcards = await fetch("/opsml/cards/list", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ registry_type: "data", limit: 10 }),
  });

  let response: CardResponse = await modelcards.json();
  console.log(response);
  return response.cards;
}

async function getRunCards(): Promise<CardJson[]> {
  const modelcards = await fetch("/opsml/cards/list", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ registry_type: "run", limit: 10 }),
  });

  let response: CardResponse = await modelcards.json();
  console.log(response);
  return response.cards;
}

export { getModelCards, getDataCards, getRunCards };
