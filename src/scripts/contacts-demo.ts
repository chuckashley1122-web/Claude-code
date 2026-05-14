import { Ghl, GhlApiError } from "../ghl/index.js";

async function main() {
  const ghl = new Ghl();

  console.log("Creating a test contact...");
  const created = await ghl.contacts.create({
    firstName: "Smoke",
    lastName: "Test",
    email: `smoke+${Date.now()}@example.com`,
    tags: ["ghl-integration-smoke"],
    source: "ghl-integration smoke test",
  });
  const contactId = created.contact.id;
  console.log(`  created id=${contactId}`);

  console.log("Updating it...");
  await ghl.contacts.update(contactId, { companyName: "Acme (test)" });

  console.log("Searching by tag...");
  const search = await ghl.contacts.search({
    pageLimit: 5,
    filters: [{ field: "tags", operator: "contains", value: "ghl-integration-smoke" }],
  });
  console.log(`  matches: ${search.total}`);

  console.log("Deleting it...");
  await ghl.contacts.delete(contactId);
  console.log("  deleted.");
}

main().catch((err: unknown) => {
  if (err instanceof GhlApiError) {
    console.error(`GHL ${err.status} on ${err.url}:`, err.body);
    process.exit(1);
  }
  console.error(err);
  process.exit(1);
});
