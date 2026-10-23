/**
 * Storage of customer profiles.
 */

import fs from "fs";

export function storeProfile(userId: string, profile: unknown) {

  fs.writeFileSync(`/var/data/profiles/${userId}.json`, JSON.stringify(profile));
  return { ok: true };
}
