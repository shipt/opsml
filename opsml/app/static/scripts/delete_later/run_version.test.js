
import { exportAllDeclaration } from '@babel/types';
import * as run_utils from './run_version';
import { run } from 'jest-cli';

test('test-run-dropdown', () => {

    // Set up our document body
  document.body.innerHTML = `
        <div id="VersionContainer" style="padding-top:80px; ">
        <h5 class="display-8">Select a project to view available runs</h5>
        <div id="DropdownSelect">
            <select id="ProjectRepositoriesSelect"></select>
        </div>
        </div>;
        `

  let fake_data = {
        "repositories": ["repo1", "repo2", "repo3"]
  }

  run_utils.setDropdown(fake_data, "repo1");
  expect(document.getElementById('ProjectRepositoriesSelect').innerHTML).toBe('<option value="repo1">repo1</option><option value="repo2">repo2</option><option value="repo3">repo3</option>')


  });

test("test params", () => {
  run_utils.resolveParams();
});


