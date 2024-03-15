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

import { setNavigo, setRepositoryPage, Registries } from "./router";

// add select2 to jquery typing
declare global {
  interface JQuery {
    select2(): any; // eslint-disable-line @typescript-eslint/no-explicit-any
  }
}

// set active class on nav item
// registry: string
function setNavLink(registry: string) {
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
  const registry: string = Registries.Model;

  setNavigo();
  setNavLink(Registries.Model);
  setRepositoryPage(registry);
  console.log("page loaded");
});
