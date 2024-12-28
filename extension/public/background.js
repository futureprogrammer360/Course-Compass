chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'search',
    title: 'Course Compass: Course Search',
    contexts: ['selection']
  });
});

chrome.contextMenus.onClicked.addListener(info => {
  if (info.menuItemId === 'search') {
    let query = info.selectionText;

    chrome.action.openPopup()
      .then(async () => {
        let i = 0;
        let success = false;
        while (i < 5 && !success) {
          try {
            await chrome.runtime.sendMessage({ 'query': query });
            success = true;
          } catch {
            console.log('Could not establish connection. Receiving end (popup) does not exist. Retrying...');
          } finally {
            i++;
          }
        }
      })
      .catch(() => {
        console.log('No active browser window.');
      });
  }
});
