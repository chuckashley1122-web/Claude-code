import type { GhlClient } from "./client.js";

export type ConversationMessageType =
  | "SMS"
  | "Email"
  | "WhatsApp"
  | "GMB"
  | "IG"
  | "FB"
  | "Custom"
  | "Live_Chat";

export interface Conversation {
  id: string;
  locationId: string;
  contactId: string;
  lastMessageBody?: string;
  lastMessageType?: ConversationMessageType;
  unreadCount?: number;
  [key: string]: unknown;
}

export interface ConversationMessage {
  id: string;
  type: ConversationMessageType;
  direction: "inbound" | "outbound";
  body?: string;
  dateAdded?: string;
  [key: string]: unknown;
}

export interface SearchConversationsParams {
  contactId?: string;
  assignedTo?: string;
  query?: string;
  status?: "all" | "read" | "unread" | "starred" | "recents";
  limit?: number;
  startAfterDate?: number;
  sort?: "asc" | "desc";
}

export interface SendMessageInput {
  type: ConversationMessageType;
  contactId: string;
  message?: string;
  html?: string;
  subject?: string;
  attachments?: string[];
  emailFrom?: string;
  emailTo?: string;
  emailCc?: string[];
  emailBcc?: string[];
  fromNumber?: string;
  toNumber?: string;
  conversationId?: string;
}

export class Conversations {
  constructor(private readonly client: GhlClient) {}

  search(params: SearchConversationsParams = {}) {
    return this.client.get<{ conversations: Conversation[]; total?: number }>(
      "/conversations/search",
      { query: { locationId: this.client.locationId, ...params } },
    );
  }

  get(conversationId: string) {
    return this.client.get<{ conversation: Conversation }>(`/conversations/${conversationId}`);
  }

  messages(conversationId: string, params: { limit?: number; lastMessageId?: string; type?: ConversationMessageType } = {}) {
    return this.client.get<{ messages: { messages: ConversationMessage[]; lastMessageId?: string } }>(
      `/conversations/${conversationId}/messages`,
      { query: params },
    );
  }

  sendMessage(input: SendMessageInput) {
    return this.client.post<{ conversationId: string; messageId: string }>(
      "/conversations/messages",
      input,
    );
  }
}
