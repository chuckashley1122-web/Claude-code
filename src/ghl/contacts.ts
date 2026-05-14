import type { GhlClient } from "./client.js";

export interface ContactName {
  firstName?: string;
  lastName?: string;
}

export interface ContactInput extends ContactName {
  email?: string;
  phone?: string;
  name?: string;
  companyName?: string;
  address1?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
  website?: string;
  timezone?: string;
  source?: string;
  tags?: string[];
  customFields?: Array<{ id: string; field_value: unknown } | { key: string; field_value: unknown }>;
}

export interface Contact extends ContactInput {
  id: string;
  locationId: string;
  dateAdded?: string;
  dateUpdated?: string;
  [key: string]: unknown;
}

export interface ListContactsParams {
  limit?: number;
  startAfter?: number;
  startAfterId?: string;
  query?: string;
}

export interface SearchContactsBody {
  pageLimit?: number;
  page?: number;
  searchAfter?: unknown[];
  filters?: unknown[];
  sort?: Array<{ field: string; direction: "asc" | "desc" }>;
}

export class Contacts {
  constructor(private readonly client: GhlClient) {}

  list(params: ListContactsParams = {}) {
    return this.client.get<{ contacts: Contact[]; meta?: unknown }>("/contacts/", {
      query: { locationId: this.client.locationId, ...params },
    });
  }

  get(contactId: string) {
    return this.client.get<{ contact: Contact }>(`/contacts/${contactId}`);
  }

  create(input: ContactInput) {
    return this.client.post<{ contact: Contact }>("/contacts/", {
      locationId: this.client.locationId,
      ...input,
    });
  }

  update(contactId: string, input: Partial<ContactInput>) {
    return this.client.put<{ contact: Contact }>(`/contacts/${contactId}`, input);
  }

  delete(contactId: string) {
    return this.client.delete<{ succeeded: boolean }>(`/contacts/${contactId}`);
  }

  search(body: SearchContactsBody = {}) {
    return this.client.post<{ contacts: Contact[]; total: number }>("/contacts/search", {
      locationId: this.client.locationId,
      ...body,
    });
  }

  addTags(contactId: string, tags: string[]) {
    return this.client.post<{ tags: string[] }>(`/contacts/${contactId}/tags`, { tags });
  }

  removeTags(contactId: string, tags: string[]) {
    return this.client.delete<{ tags: string[] }>(`/contacts/${contactId}/tags`, {
      headers: { "Content-Type": "application/json" },
      query: { tags: tags.join(",") },
    });
  }
}
