/* eslint-disable */
//@ts-nocheck

import { setDropdown, resolveParams } from "./run_version";

test("setDropdown", () => {
    
    document.body.innerHTML = `
    <select id="ProjectRepositoriesSelect"></select>
    `;

    const data = {
        repositories: ["test"],
        names: ["test"],
    };
    const repository = "test";

    // test with values
    setDropdown(data, repository);
    expect(document.getElementById("ProjectRepositoriesSelect")?.innerHTML).toBe('<option value="test">test</option>');

    // test with no values
    data.repositories = [];
    setDropdown(data, repository);
    expect(document.getElementById("ProjectRepositoriesSelect")?.innerHTML).toBe('<option value="No repositories found">No repositories found</option>');
});

test("resolveParams", () => {
    const params = resolveParams("None", "None", "None");

    expect(params).toEqual([undefined, undefined, undefined]);
});
