import $ from "jquery";
require("select2");

import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@github/clipboard-copy-element";
import "select2/dist/css/select2.css";
import "@fortawesome/fontawesome-free/js/fontawesome";
import "@fortawesome/fontawesome-free/js/solid";

import "bootstrap/dist/css/bootstrap.min.css";
import "./styles/prism.css";
import "./styles/style.css";
import "bootstrap-icons/font/bootstrap-icons.css";

import { setNavigo, setPage, Registries, router } from "./router";

// add select2 to jquery typing
declare global {
  interface JQuery {
    select2(): any; // eslint-disable-line @typescript-eslint/no-explicit-any
  }
}

// set active class on nav item
// registry: string
function setNavLink() {
  // set active class on nav-link click
  $(".nav-link").click(function () {
    $(".nav-link").removeClass("active");
    $(this).addClass("active");
  });
}

function executed() {
  console.log("executed");
}

export { setNavLink };

// default page to load
$(document).ready(() => {
  const searchParams = new URLSearchParams(window.location.search);

  let registry: string | undefined = searchParams.get("registry");
  let repository: string | undefined = searchParams.get("repository");
  let name: string | undefined = searchParams.get("name");
  let version: string | undefined = searchParams.get("version");

  console.log("registryType: ", registry);

  setNavigo();
  setNavLink();
  router.resolve();
  //setRepositoryPage(registry);
  //console.log("page loaded");
});
