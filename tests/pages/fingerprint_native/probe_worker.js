async function report() {
  const out = {
    platform: self.navigator.platform,
    userAgent: self.navigator.userAgent,
    hardwareConcurrency: self.navigator.hardwareConcurrency,
    deviceMemory: self.navigator.deviceMemory,
    languages: Array.from(self.navigator.languages),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  };
  try {
    const adapter = self.navigator.gpu ? await self.navigator.gpu.requestAdapter() : null;
    out.webgpuVendor = adapter ? adapter.info.vendor : 'no adapter';
  } catch (e) {
    out.webgpuVendor = 'err';
  }
  try {
    const high = await self.navigator.userAgentData.getHighEntropyValues(['formFactors']);
    out.formFactors = high.formFactors;
  } catch (e) {
    out.formFactors = 'err';
  }
  return out;
}
