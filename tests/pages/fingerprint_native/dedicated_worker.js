importScripts('probe_worker.js');
const nested = new Worker('nested_worker.js');
const nestedReport = new Promise((resolve) => {
  nested.onmessage = (event) => resolve(event.data);
});
report().then(async (own) => {
  self.postMessage({ own: own, nested: await nestedReport });
});
