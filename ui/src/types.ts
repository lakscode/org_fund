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
  orgs: Org[];
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
  createdAt: string;
  updatedAt: string;
}
