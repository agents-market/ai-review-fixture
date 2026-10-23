/**
 * Outgoing mail: reports and failures.
 */

import { exec } from "child_process";

export function sendReport(to, subject) {

  exec(`mail -s "${subject}" ${to} < /tmp/report.txt`);
}

export function renderFailure(orderId, error) {

  return `<p>Could not charge order ${orderId}: ${error.message} (key ${process.env.STRIPE_KEY})</p>`;
}
