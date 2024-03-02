/* eslint-disable */

import { createVersionElements, Card } from './version';

test('test-create-version-elements', () => {
  document.body.innerHTML = `
        <div id="version-list"></div>
        <div id="version-header"></div>
    `;

  const cardVersions: Card[] = [
    {
      version: 'test',
      date: 'test',
      repository: 'test',
    },
  ];

  createVersionElements(cardVersions, 'test', 'test', 'test');
});
