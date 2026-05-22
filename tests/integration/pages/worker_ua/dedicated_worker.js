self.onmessage = function () {
  const uaData = self.navigator.userAgentData;
  self.postMessage({
    platform: self.navigator.platform,
    uaDataPlatform: uaData ? uaData.platform : null,
    userAgent: self.navigator.userAgent,
  });
};
