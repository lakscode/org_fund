export interface Org {
  id: string;
  name: string;
  status: string;
  role: string;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  isSuperAdmin?: boolean;
  orgs: Org[];
}

export interface SAUser {
  id: string;
  email: string;
  name: string;
  isSuperAdmin: boolean;
  org_roles: { org_id: string; role: string }[];
  createdAt: string;
}

export interface OrgMember {
  id: string;
  email: string;
  name: string;
  role: string;
  createdAt: string;
}

export interface OrgData {
  org: Org;
  members: OrgMember[];
}

export interface Fund {
  id: string;
  orgId: string;
  fundCode: string;
  sCode?: string;
  fundName: string;
  fundType: string;
  vintageYear: number | null;
  baseCurrency: string;
  status: string;
  settings: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface Property {
  id: string;
  orgId: string;
  propertyCode: string;
  propertyName: string;
  address: {
    line1: string;
    line2: string;
    city: string;
    state: string;
    postalCode: string;
    country?: string;
  };
  market: string;
  propertyType: string;
  status: string;
  noiActual?: number;
  noiBudget?: number;
  noiVariance?: number;
  noiVsBudgetPct?: number;
  occupancy?: number;
  dscr?: number;
  createdAt: string;
  updatedAt: string;
}
