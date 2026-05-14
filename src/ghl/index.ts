import { GhlClient, type GhlClientOptions } from "./client.js";
import { Contacts } from "./contacts.js";
import { Opportunities } from "./opportunities.js";
import { Conversations } from "./conversations.js";

export { GhlApiError, GhlClient } from "./client.js";
export type { GhlClientOptions, RequestOptions } from "./client.js";
export { Contacts } from "./contacts.js";
export type { Contact, ContactInput, ListContactsParams, SearchContactsBody } from "./contacts.js";
export { Opportunities } from "./opportunities.js";
export type {
  Opportunity,
  OpportunityInput,
  OpportunityStatus,
  Pipeline,
  PipelineStage,
  SearchOpportunitiesParams,
} from "./opportunities.js";
export { Conversations } from "./conversations.js";
export type {
  Conversation,
  ConversationMessage,
  ConversationMessageType,
  SearchConversationsParams,
  SendMessageInput,
} from "./conversations.js";

export class Ghl {
  readonly client: GhlClient;
  readonly contacts: Contacts;
  readonly opportunities: Opportunities;
  readonly conversations: Conversations;

  constructor(options: GhlClientOptions = {}) {
    this.client = new GhlClient(options);
    this.contacts = new Contacts(this.client);
    this.opportunities = new Opportunities(this.client);
    this.conversations = new Conversations(this.client);
  }

  getLocation() {
    return this.client.get<{ location: Record<string, unknown> }>(
      `/locations/${this.client.locationId}`,
    );
  }
}
