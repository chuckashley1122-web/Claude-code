import { Ghl, GhlApiError } from "../ghl/index.js";

async function main() {
  const ghl = new Ghl();

  console.log(`Base URL  : ${process.env.GHL_BASE_URL ?? "https://services.leadconnectorhq.com"}`);
  console.log(`Location  : ${ghl.client.locationId}`);
  console.log("");

  console.log("[1/3] Fetching location...");
  const { location } = await ghl.getLocation();
  console.log(`  name=${(location as { name?: string }).name ?? "(unknown)"}`);

  console.log("[2/3] Listing 1 contact...");
  const contacts = await ghl.contacts.list({ limit: 1 });
  console.log(`  contacts returned: ${contacts.contacts?.length ?? 0}`);

  console.log("[3/3] Listing pipelines...");
  const { pipelines } = await ghl.opportunities.listPipelines();
  console.log(`  pipelines: ${pipelines.length}`);
  for (const p of pipelines.slice(0, 5)) {
    console.log(`    - ${p.name} (${p.stages.length} stages)`);
  }

  console.log("\nOK. Auth + read scopes look good.");
}

main().catch((err: unknown) => {
  if (err instanceof GhlApiError) {
    console.error(`\nGHL API error ${err.status} on ${err.url}`);
    console.error(err.body);
    if (err.status === 401) {
      console.error("\nHint: 401 usually means the Private Integration Token is wrong,");
      console.error("revoked, or doesn't include the required scope for this endpoint.");
    }
    process.exit(1);
  }
  console.error(err);
  process.exit(1);
});
