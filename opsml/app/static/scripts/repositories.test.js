import { exportAllDeclaration } from '@babel/types';
import * as repo_utils from './repositories';
import { run } from 'jest-cli';

test('test-dropdown', () => {

    // Set up our document body
  document.body.innerHTML = `

        <nav class="navbar navbar-expand navbar-light px-5" id="ModelSubnav" >
        <div class="container-fluid">
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav">
            <li class="nav-item">
                <a class="nav-link" aria-current="page" href="" style="font-size: 20px;" id="available"> <i></i>Available</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" aria-current="page" href="" style="font-size: 20px;" id="versions"> <i></i>Versions</a>
            </li>
            </ul>
        </div>
        </div>
        </nav>

        <div class="container" style="padding-top:50px;">
        <div class="row">
        <h5 class="display-8">Select a repository to view available artifacts</h5>
        </div>
        <div id="DropdownSelect">
            <select id="RepositoriesSelect"></select>
        </div>

        <br>

        <!---- Form for selecting model -------->
        <div class="container">
            <div class="repository-header" id="repository-header" >
            <!---- <h2>{{selected_repository}}</h2> ---->
            </div>
        </div>
        <br>
        <div class="model-container">
        <div class="row row-cols-md-5" id="artifact-card-div">
        </div>
        </div>
        </div>
        `

  let fake_data = {
        "repositories": ["repo1", "repo2", "repo3"],
        "names": ["name1", "name2", "name3"]
  }
  repo_utils.setDropdown(fake_data, "data");
  expect(document.getElementById('RepositoriesSelect').innerHTML).toBe('<option value="repo1">repo1</option><option value="repo2">repo2</option><option value="repo3">repo3</option>')

  // get total number of divs inside artifact-card-div
let divs = document.getElementById('artifact-card-div').getElementsByClassName('stretched-link');
expect(divs.length).toBe(3);

  });