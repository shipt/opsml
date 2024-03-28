type record = [string, string, number, number, number, number];

export interface registryPage {
  page: record[];
}

export interface registryStats {
  nbr_names: number;
  nbr_versions: number;
  nbr_repos: number;
}

export interface repositories {
  repositories: string[];
}
