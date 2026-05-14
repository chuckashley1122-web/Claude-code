import { Ghl, GhlApiError } from "../ghl/index.js";

async function main() {
  const ghl = new Ghl();

  const { pipelines } = await ghl.opportunities.listPipelines();
  if (pipelines.length === 0) {
    console.log("No pipelines configured for this location.");
    return;
  }

  for (const pipeline of pipelines) {
    console.log(`\nPipeline: ${pipeline.name} (${pipeline.id})`);
    for (const stage of pipeline.stages) {
      console.log(`  - stage: ${stage.name}`);
    }

    const result = await ghl.opportunities.search({ pipeline_id: pipeline.id, limit: 3 });
    console.log(`  recent opportunities: ${result.opportunities.length}`);
    for (const opp of result.opportunities) {
      console.log(`    * ${opp.name} [${opp.status}]`);
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
