importScripts('probe_worker.js');
report().then((data) => self.postMessage(data));
