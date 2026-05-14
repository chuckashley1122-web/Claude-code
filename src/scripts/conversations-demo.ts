import { Ghl, GhlApiError } from "../ghl/index.js";

async function main() {
  const ghl = new Ghl();

  console.log("Searching recent conversations...");
  const result = await ghl.conversations.search({ limit: 5, sort: "desc" });
  console.log(`  found: ${result.conversations.length}`);

  for (const convo of result.conversations) {
    console.log(`\nConversation ${convo.id} (contact ${convo.contactId})`);
    console.log(`  last: [${convo.lastMessageType ?? "?"}] ${convo.lastMessageBody ?? ""}`);

    const msgs = await ghl.conversations.messages(convo.id, { limit: 3 });
    for (const m of msgs.messages.messages) {
      console.log(`    ${m.direction} ${m.type}: ${m.body ?? ""}`);
    }
  }
}

main().catch((err: unknown) => {
  if (err instanceof GhlApiError) {
    console.error(`GHL ${err.status} on ${err.url}:`, err.body);
    process.exit(1);
  }
  console.error(err);
  process.exit(1);
});
