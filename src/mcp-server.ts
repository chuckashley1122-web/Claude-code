#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { Ghl, GhlApiError } from "./ghl/index.js";

function makeServer() {
  const ghl = new Ghl();
  const server = new McpServer(
    { name: "ghl-mcp", version: "0.1.0" },
    { capabilities: { tools: {} } },
  );

  const ok = (data: unknown) => ({
    content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
  });
  const fail = (err: unknown) => {
    const text = err instanceof GhlApiError
      ? `GHL API ${err.status} ${err.url}\n${JSON.stringify(err.body, null, 2)}`
      : err instanceof Error
      ? err.message
      : String(err);
    return { content: [{ type: "text" as const, text }], isError: true };
  };
  const wrap = <T>(fn: () => Promise<T>) => fn().then(ok).catch(fail);

  server.registerTool(
    "ghl_get_location",
    {
      title: "Get GHL location info",
      description: "Returns details about the GHL sub-account this server is connected to. Use as a connectivity / auth smoke test.",
      inputSchema: {},
    },
    () => wrap(() => ghl.getLocation()),
  );

  server.registerTool(
    "ghl_list_contacts",
    {
      title: "List GHL contacts",
      description: "Lists contacts in the location. Use `query` for a simple name/email/phone substring filter.",
      inputSchema: {
        limit: z.number().int().min(1).max(100).optional().describe("Max 100, default 20"),
        query: z.string().optional().describe("Substring search on name/email/phone"),
        startAfterId: z.string().optional(),
        startAfter: z.number().optional(),
      },
    },
    (args) => wrap(() => ghl.contacts.list(args)),
  );

  server.registerTool(
    "ghl_get_contact",
    {
      title: "Get a GHL contact by id",
      description: "Returns full details of one contact.",
      inputSchema: { contactId: z.string().describe("GHL contact id") },
    },
    ({ contactId }) => wrap(() => ghl.contacts.get(contactId)),
  );

  server.registerTool(
    "ghl_create_contact",
    {
      title: "Create a GHL contact",
      description: "Creates a new contact in the location. At least one of email or phone is recommended.",
      inputSchema: {
        firstName: z.string().optional(),
        lastName: z.string().optional(),
        email: z.string().email().optional(),
        phone: z.string().optional(),
        companyName: z.string().optional(),
        source: z.string().optional(),
        tags: z.array(z.string()).optional(),
      },
    },
    (args) => wrap(() => ghl.contacts.create(args)),
  );

  server.registerTool(
    "ghl_update_contact",
    {
      title: "Update a GHL contact",
      description: "Updates fields on an existing contact.",
      inputSchema: {
        contactId: z.string(),
        firstName: z.string().optional(),
        lastName: z.string().optional(),
        email: z.string().email().optional(),
        phone: z.string().optional(),
        companyName: z.string().optional(),
        tags: z.array(z.string()).optional(),
      },
    },
    ({ contactId, ...rest }) => wrap(() => ghl.contacts.update(contactId, rest)),
  );

  server.registerTool(
    "ghl_delete_contact",
    {
      title: "Delete a GHL contact",
      description: "Permanently deletes a contact. Confirm with the user before calling.",
      inputSchema: { contactId: z.string() },
      annotations: { destructiveHint: true },
    },
    ({ contactId }) => wrap(() => ghl.contacts.delete(contactId)),
  );

  server.registerTool(
    "ghl_add_contact_tags",
    {
      title: "Add tags to a contact",
      inputSchema: { contactId: z.string(), tags: z.array(z.string()).min(1) },
    },
    ({ contactId, tags }) => wrap(() => ghl.contacts.addTags(contactId, tags)),
  );

  server.registerTool(
    "ghl_list_pipelines",
    {
      title: "List opportunity pipelines",
      description: "Lists all pipelines and their stages for the location.",
      inputSchema: {},
    },
    () => wrap(() => ghl.opportunities.listPipelines()),
  );

  server.registerTool(
    "ghl_search_opportunities",
    {
      title: "Search opportunities",
      description: "Search/list opportunities, optionally filtered by pipeline, stage, status, or assignee.",
      inputSchema: {
        pipeline_id: z.string().optional(),
        pipeline_stage_id: z.string().optional(),
        status: z.enum(["open", "won", "lost", "abandoned", "all"]).optional(),
        assigned_to: z.string().optional(),
        contact_id: z.string().optional(),
        query: z.string().optional(),
        limit: z.number().int().min(1).max(100).optional(),
      },
    },
    (args) => wrap(() => ghl.opportunities.search(args)),
  );

  server.registerTool(
    "ghl_create_opportunity",
    {
      title: "Create an opportunity",
      description: "Creates a new opportunity in a pipeline stage for a given contact.",
      inputSchema: {
        pipelineId: z.string(),
        pipelineStageId: z.string(),
        name: z.string(),
        status: z.enum(["open", "won", "lost", "abandoned"]),
        contactId: z.string(),
        monetaryValue: z.number().optional(),
        assignedTo: z.string().optional(),
        source: z.string().optional(),
      },
    },
    (args) => wrap(() => ghl.opportunities.create(args)),
  );

  server.registerTool(
    "ghl_update_opportunity_status",
    {
      title: "Update opportunity status",
      description: "Marks an opportunity as open/won/lost/abandoned.",
      inputSchema: {
        opportunityId: z.string(),
        status: z.enum(["open", "won", "lost", "abandoned"]),
      },
    },
    ({ opportunityId, status }) => wrap(() => ghl.opportunities.updateStatus(opportunityId, status)),
  );

  server.registerTool(
    "ghl_search_conversations",
    {
      title: "Search conversations",
      description: "List recent conversations, newest first by default.",
      inputSchema: {
        contactId: z.string().optional(),
        query: z.string().optional(),
        status: z.enum(["all", "read", "unread", "starred", "recents"]).optional(),
        limit: z.number().int().min(1).max(100).optional(),
        sort: z.enum(["asc", "desc"]).optional(),
      },
    },
    (args) => wrap(() => ghl.conversations.search(args)),
  );

  server.registerTool(
    "ghl_get_conversation_messages",
    {
      title: "Get messages from a conversation",
      inputSchema: {
        conversationId: z.string(),
        limit: z.number().int().min(1).max(100).optional(),
      },
    },
    ({ conversationId, limit }) => wrap(() => ghl.conversations.messages(conversationId, limit !== undefined ? { limit } : {})),
  );

  server.registerTool(
    "ghl_send_message",
    {
      title: "Send a message in a conversation",
      description: "Send an SMS, Email, or other supported channel to a contact. Always confirm with the user before sending.",
      inputSchema: {
        type: z.enum(["SMS", "Email", "WhatsApp", "GMB", "IG", "FB", "Custom", "Live_Chat"]),
        contactId: z.string(),
        message: z.string().optional().describe("Plain text body (SMS, or Email fallback)"),
        html: z.string().optional().describe("HTML body for Email"),
        subject: z.string().optional().describe("Subject for Email"),
        emailFrom: z.string().optional(),
        emailTo: z.string().optional(),
        fromNumber: z.string().optional(),
        toNumber: z.string().optional(),
        conversationId: z.string().optional(),
      },
      annotations: { destructiveHint: true },
    },
    (args) => wrap(() => ghl.conversations.sendMessage(args)),
  );

  return server;
}

async function main() {
  const server = makeServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Failed to start ghl-mcp:", err);
  process.exit(1);
});
