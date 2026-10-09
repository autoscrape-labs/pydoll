self.addEventListener('install', function () {
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('message', function (event) {
  const uaData = self.navigator.userAgentData;
  const payload = {
    platform: self.navigator.platform,
    uaDataPlatform: uaData ? uaData.platform : null,
    userAgent: self.navigator.userAgent,
  };
  if (event.ports && event.ports[0]) {
    event.ports[0].postMessage(payload);
  }
});
