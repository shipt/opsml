import showdown from "showdown";
import * as Prism from "prismjs";
import "prismjs/components/prism-json";
import "prismjs/components/prism-sql";
import "prismjs/components/prism-python";
import { Version, Card, pageData } from "./base_version";

interface CardMetadata {
  description: {
    summary: string;
    sample_code: string;
  };
  feature_map: { [key: string]: string };
  interface_type: string;
  data_type: string;
}

interface dataCard extends Card {
  name: string;
  repository: string;
  version: string;
  uid: string;
  data_filename: string;
  data_profile_filename: string;
  profile_uri: string;
  metadata: CardMetadata;
  interface: {
    dependent_vars: string[];
    feature_descriptions: { [key: string]: string };
    sql_logic: { [key: string]: string };
  };
}

interface dataPage extends pageData {
  card: dataCard;
  data_splits: string;
  data_filename: string;
  profile_uri: string;
  data_profile_filename: string;
}

class dataVersion extends Version {
  data: dataPage;
  datacard: dataCard;
  metadata: CardMetadata;

  /**
   * Initialize the data version class
   *
   * @param data - dataPage object containing information for building the UI
   */
  constructor(data: dataPage) {
    super(data, "data");
    this.datacard = data.card;
    this.metadata = data.card.metadata;
  }

  /**
   * Insert the data metadata into the UI
   */
  insertDataMetadata(): void {
    document.getElementById("data-metadata-interface")!.innerHTML =
      this.metadata.interface_type;
    document.getElementById("data-metadata-type")!.innerHTML =
      this.metadata.data_type;

    // insert data
    const dataUri: HTMLElement = document.getElementById("data-uri")!;
    dataUri.setAttribute(
      "href",
      `/opsml/data/download?uid=${this.datacard.uid}`
    );
    dataUri.setAttribute("download", this.data.data_filename);

    if (this.data.profile_uri !== null) {
      const profileUri: HTMLElement =
        document.getElementById("data-profile-uri")!;
      profileUri.setAttribute(
        "href",
        `/opsml/data/download/profile?uid=${this.datacard.uid}`
      );
      profileUri.setAttribute("download", this.data.data_profile_filename);
      $("#data-profile").show();
    }

    // set metadata button
    // summary-button on click
    document.getElementById("data-metadata-button")!.onclick =
      function metaButtonClick() {
        $("#DataMetadata").show();
        $("#DataSummary").hide();
        $("#ProfileBox").hide();
      };
  }

  /**
   * Insert the data extras into the UI
   */
  insertDataExtras(): void {
    if (this.data.data_splits !== null) {
      $("#split-button").show();
      const code: string = this.data.data_splits;
      const html: string = Prism.highlight(code, Prism.languages.json, "json");
      document.getElementById("DataSplitCode")!.innerHTML = html;
    }

    // set depen vars
    const dataInterface: dataCard["interface"] = this.datacard.interface;

    // check if interface has dependent vars
    if (Object.hasOwn(dataInterface, "dependent_vars")) {
      // check if interface has dependent vars
      if (dataInterface.dependent_vars.length > 0) {
        $("#dep-var-button").show();
        const depenVar: HTMLElement =
          document.getElementById("depen-var-body")!;
        depenVar.innerHTML = "";

        for (let i = 0; i < dataInterface.dependent_vars.length; i += 1) {
          const depVar: string = dataInterface.dependent_vars[i];
          depenVar.innerHTML += `
                    <tr>
                        <td>${depVar}</td>
                    </tr>
                    `;
        }
      }
    }

    // set feature_map
    const featureMap: { [key: string]: string } = this.metadata.feature_map;

    // check if feature_map keys > 0
    if (Object.keys(featureMap).length > 0) {
      $("#feature-map-button").show();
      const featureBody: HTMLElement =
        document.getElementById("feature-map-body")!;
      featureBody.innerHTML = "";

      Object.keys(featureMap).forEach((key) => {
        const value: string = featureMap[key];
        featureBody.innerHTML += `
            <tr>
                <td><font color="#999">${key}</font></td>
                <td>${value}</td>
            </tr>
            `;
      });
    }

    // set feature descriptions
    if (Object.hasOwn(dataInterface, "feature_descriptions")) {
      const featDesc: { [key: string]: string } =
        dataInterface.feature_descriptions;

      // check if feature_descriptions keys > 0
      if (Object.keys(featDesc).length > 0) {
        $("#feature-desc-button").show();
        const featureDescBody: HTMLElement =
          document.getElementById("feature-desc-body")!;
        featureDescBody.innerHTML = "";

        Object.keys(featDesc).forEach((key) => {
          const value: string = featDesc[key];
          featureDescBody.innerHTML += `
                <tr>
                    <td><font color="#999">${key}</font></td>
                    <td>${value}</td>
                </tr>
                `;
        });
      }
    }

    // set sql
    if (Object.hasOwn(dataInterface, "sql_logic")) {
      const sqlLogic: { [key: string]: string } = dataInterface.sql_logic;

      if (Object.keys(sqlLogic).length > 0) {
        $("#sql-button").show();
        const sqlDiv: HTMLElement = document.getElementById("sql-div")!;
        sqlDiv.innerHTML = "";

        Object.keys(sqlLogic).forEach((key) => {
          const value: string = sqlLogic[key];

          const htmlLogic = Prism.highlight(value, Prism.languages.sql, "sql");
          sqlDiv.innerHTML += `
                    <h6><i style="color:#04b78a"></i> <font color="#999">${key}</font>
                    <clipboard-copy for="${key}Code">
                        Copy
                        <span class="notice" hidden>Copied!</span>
                    </clipboard-copy>
                    </h6>
                    <pre style="max-height: 500px; overflow: scroll;"><code id="${key}Code">${htmlLogic}</code></pre>
                    `;
        });
      }
    }
  }

  /**
   * Insert the data summary into the UI
   */
  insertSummary(): void {
    if (this.metadata.description.summary !== null) {
      const converter = new showdown.Converter();
      converter.setFlavor("github");
      const text: string = converter.makeHtml(
        this.metadata.description.summary
      );

      document.getElementById(`${this.registry}-summary-markdown`)!.innerHTML =
        text;
      $(`${this.registry}-summary-display`).show();
      $(`${this.registry}-SummaryText`).hide();
    } else {
      $(`${this.registry}-summary-display`).hide();
      $(`${this.registry}-SummaryText`).show();
    }

    if (this.metadata.description.sample_code !== null) {
      const code: string = this.metadata.description.sample_code;
      const html: string = Prism.highlight(
        code,
        Prism.languages.python,
        "python"
      );
      document.getElementById(`${this.registry}-user-sample-code`)!.innerHTML =
        html;
      $(`${this.registry}-SampleCode`).show();
    } else {
      $(`${this.registry}-SampleCode`).hide();
    }

    const opsmlCode: string = `
    from opsml import CardRegistry

    data_registry = CardRegistry("data")
    datacard = model_registry.load_card(
        name="${this.datacard.name}", 
        repository="${this.datacard.repository}",
        version="${this.datacard.version}",
    )
    datacard.load_data()
    `;

    const html: string = Prism.highlight(
      opsmlCode,
      Prism.languages.python,
      "python"
    );

    document.getElementById(`${this.registry}-opsml-sample-code`)!.innerHTML =
      html;

    // summary-button on click
    document.getElementById("data-summary-button")!.onclick =
      function summaryToggle() {
        $("#DataMetadata").hide();
        $("#ProfileBox").hide();
        $("#DataSummary").show();
      };
  }

  /**
   * Insert the data profile into the UI
   */
  insertHtmlIframe() {
    if (this.data.profile_uri !== null) {
      $("#data-profile-button").show();
      const htmlIframe: HTMLElement =
        document.getElementById("data-profile-html")!;
      htmlIframe.setAttribute("src", this.data.profile_uri);
    }

    // profile-button on click
    document.getElementById("data-profile-button")!.onclick =
      function profileToggle() {
        $("#DataMetadata").hide();
        $("#DataSummary").hide();
        $("#ProfileBox").show();
      };
  }

  /**
   * Build the UI
   */
  buildUI(): void {
    this.insertDataMetadata();
    this.insertDataExtras();
    this.insertSummary();
    this.insertHtmlIframe();

    // check if the button is not active
    $(".header-tab").on("click", function dataHeaderFunc() {
      $(".header-tab").removeClass("selected");
      $(".header-tab").css({
        "background-color": "#f1f1f1",
        border: "none",
        color: "rgb(85, 85, 85)",
      });
      $(this).addClass("selected");
      $(this).css({
        "background-color": "white",
        "border-top": "2px solid #04b78a",
        color: "#04b78a",
      });
    });

    // set metadata-button to default
    // first check if summary is not selected
    if (
      !$("#summary-button").hasClass("selected") &&
      !$("#data-profile-button").hasClass("selected")
    ) {
      $("#metadata-button").addClass("selected");
      $("#metadata-button").css({
        "background-color": "white",
        "border-top": "2px solid #04b78a",
        color: "#04b78a",
      });
    }

    // setup extra tabs
    $(".extra-tab").on("click", function extraFunc() {
      // loop over each and hide id
      $(".extra-tab").each(function extraFunc2() {
        $(this).removeClass("selected");
        $(this).css({
          "background-color": "#f1f1f1",
          border: "none",
          color: "rgb(85, 85, 85)",
        });
        const tabID = $(this).data("id");
        $(`#${tabID}`).hide();
      });

      $(this).addClass("selected");
      $(this).css({
        "background-color": "white",
        "border-top": "2px solid #5e0fb7",
        color: "#5e0fb7",
      });

      const tabID = $(this).data("id");
      $(`#${tabID}`).toggle();
    });

    // reset on new version
    $(".extra-tab").each(function extraFunc3() {
      $(this).removeClass("selected");
      $(this).css({
        "background-color": "#f1f1f1",
        border: "none",
        color: "rgb(85, 85, 85)",
      });
      const tabID = $(this).data("id");
      $(`#${tabID}`).hide();
    });
  }
}

export { dataVersion, dataCard, dataPage, CardMetadata };
