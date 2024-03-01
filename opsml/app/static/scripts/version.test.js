import { createVersionElements } from './version';

test ('test-create-version-elements', () => {
    document.body.innerHTML = `
        <div id="VersionList"></div>
        <div id="version-header"></div>
    `;
    
    let cardVersions = [
        {
        "version": "test",
        "date": "test"
        }
    ];
    
    createVersionElements(cardVersions, "test", "test", "test");
});