export type AuthType = "oauth_token" | "api_key" | "none";

export interface CredentialSpec {
  name: string;
  description: string;
  sensitive: boolean;
  header_name?: string;
}

export interface MCPCatalogItem {
  id: string;
  name: string;
  url_template: string;
  auth_type: AuthType;
  token_guide_url?: string;
  scopes?: string[];
  credentials_required: CredentialSpec[];
  credentials_optional: CredentialSpec[];
  tools: string[];
}

export interface MCPCatalogResponse {
  servers: MCPCatalogItem[];
  total: number;
}

export type ServerStatus = "active" | "error" | "disconnected";

export interface MCPServer {
  id: string;
  name: string;
  template?: string;
  url: string;
  status: ServerStatus;
  created_at: string;
  last_used?: string;
  error_message?: string;
}

export interface MCPServerDetail extends MCPServer {
  tools: MCPTool[];
}

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

export interface MCPServerListResponse {
  servers: MCPServer[];
  total: number;
}

export interface CreateMCPServerFromTemplate {
  template: string;
  name: string;
  credentials: Record<string, string>;
  oauth_token_ref?: string;
}

export interface CreateMCPServerCustom {
  name: string;
  url: string;
  credentials?: Record<string, string>;
  headers?: Record<string, string>;
}

export type CreateMCPServerRequest = CreateMCPServerFromTemplate | CreateMCPServerCustom;

export interface MCPHealthStatus {
  server_id: string;
  name: string;
  status: ServerStatus;
  error?: string;
}

export interface MCPHealthResponse {
  servers: MCPHealthStatus[];
  total_active: number;
  total_error: number;
  total_disconnected: number;
}

export interface OAuthAuthorizeResponse {
  authorization_url: string;
  service: string;
}

export interface OAuthCallbackResponse {
  refresh_token: string;
  service: string;
  message: string;
}
