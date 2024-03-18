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

// extend CardJson
interface ModelCardJson extends CardJson {
  datacard_uid: string;
  sample_data_type: string;
  model_type: string;
  pipelinecard_uid: string;
  auditcard_uid: string;
}

interface ModelCardResponse {
  cards: ModelCardJson[];
}

async function getModelCards(): Promise<ModelCardResponse> {
  const modelcards = await fetch("/opsml/cards/list", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ registry_type: "model", limit: 10 }),
  });

  const cards: ModelCardResponse = modelcards.json();
  return cards;
}

function addTwo(a: number, b: number): number {
  return a + b;
}

function addThree(): number {
  // a ddTwo(1, 2);
}

export { getModelCards, addTwo };
