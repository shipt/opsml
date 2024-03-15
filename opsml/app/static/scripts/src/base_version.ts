// base card interface
interface Card {
  name: string;
  repository: string;
  version: string;
  uid: string;
}

// base  data interface
interface pageData {
  card: Card;
}

// base version class to use for setting UIs
class Version {
  data: pageData;
  registry: string;

  constructor(data: pageData, registry: string) {
    this.data = data;
    this.registry = registry;
  }

  // build the UI
  buildUI(): void {
    console.log(`building UI for ${this.data.card.name}`);
  }
}

export { Version, Card, pageData };
