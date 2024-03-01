
import { set_dropdown } from './run_version.js';

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

  set_dropdown(fake_data, "repo1");
  });