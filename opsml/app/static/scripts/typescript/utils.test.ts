/* eslint-disable */

import { setRepositoryPage } from './utils';
import * as repoUtils from './repositories';

const mockGetData = jest.spyOn(repoUtils, 'getRepoNamesPage').mockImplementation((registry, repository) => 'Hello !!! ');

test('test-set-repository-page', () => {
  document.body.innerHTML = `
            <div id="card-version-page"></div>
            <div id="run-version-page"></div>
            <div id="audit-version-page"></div>
        `;

  setRepositoryPage('test', 'test');
  expect(mockGetData).toHaveBeenCalled();
});
