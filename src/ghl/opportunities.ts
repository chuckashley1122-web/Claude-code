import type { GhlClient } from "./client.js";

export type OpportunityStatus = "open" | "won" | "lost" | "abandoned" | "all";

export interface PipelineStage {
  id: string;
  name: string;
  position?: number;
}

export interface Pipeline {
  id: string;
  name: string;
  locationId: string;
  stages: PipelineStage[];
  [key: string]: unknown;
}

export interface OpportunityInput {
  pipelineId: string;
  pipelineStageId: string;
  name: string;
  status: OpportunityStatus;
  contactId: string;
  monetaryValue?: number;
  assignedTo?: string;
  source?: string;
  customFields?: Array<{ id: string; field_value: unknown }>;
}

export interface Opportunity extends Omit<OpportunityInput, "status"> {
  id: string;
  status: OpportunityStatus;
  locationId: string;
  [key: string]: unknown;
}

export interface SearchOpportunitiesParams {
  pipeline_id?: string;
  pipeline_stage_id?: string;
  status?: OpportunityStatus;
  assigned_to?: string;
  contact_id?: string;
  query?: string;
  limit?: number;
  startAfter?: number;
  startAfterId?: string;
  date?: string;
}

export class Opportunities {
  constructor(private readonly client: GhlClient) {}

  listPipelines() {
    return this.client.get<{ pipelines: Pipeline[] }>("/opportunities/pipelines", {
      query: { locationId: this.client.locationId },
    });
  }

  search(params: SearchOpportunitiesParams = {}) {
    return this.client.get<{ opportunities: Opportunity[]; meta?: unknown }>(
      "/opportunities/search",
      { query: { location_id: this.client.locationId, ...params } },
    );
  }

  get(opportunityId: string) {
    return this.client.get<{ opportunity: Opportunity }>(`/opportunities/${opportunityId}`);
  }

  create(input: OpportunityInput) {
    return this.client.post<{ opportunity: Opportunity }>("/opportunities/", {
      locationId: this.client.locationId,
      ...input,
    });
  }

  update(opportunityId: string, input: Partial<OpportunityInput>) {
    return this.client.put<{ opportunity: Opportunity }>(`/opportunities/${opportunityId}`, input);
  }

  updateStatus(opportunityId: string, status: OpportunityStatus) {
    return this.client.put<{ opportunity: Opportunity }>(
      `/opportunities/${opportunityId}/status`,
      { status },
    );
  }

  delete(opportunityId: string) {
    return this.client.delete<{ succeeded: boolean }>(`/opportunities/${opportunityId}`);
  }
}
