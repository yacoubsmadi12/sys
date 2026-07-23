export interface Token {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
}

export interface UserRead {
  id: string;
  username: string;
  full_name?: string;
  email?: string;
  role: string;
  is_active: boolean;
  last_login?: string;
  created_at: string;
}

export interface LogSource {
  id: string;
  name: string;
  ip_address: string;
  vendor: string;
  system_type: string;
  protocol: string;
  port: number;
  description?: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface LogSourceCreate {
  name: string;
  ip_address: string;
  vendor: string;
  system_type: string;
  protocol: string;
  port: number;
  description?: string;
  enabled: boolean;
}

export interface BlockedUser {
  id: string;
  filter_rule_id: string;
  source_id: string;
  pattern: string;
  created_at: string;
}

export interface FilterRule {
  id: string;
  name: string;
  source_id: string;
  description?: string;
  field: string;
  pattern_type: string;
  action: string;
  enabled: boolean;
  blocked_users: BlockedUser[];
  created_at: string;
  updated_at: string;
}

export interface FilterRuleCreate {
  name: string;
  source_id: string;
  description?: string;
  field: string;
  pattern_type: string;
  action: string;
  enabled: boolean;
  patterns: string[];
}

export interface SyslogEntry {
  id: string;
  received_at: string;
  log_timestamp?: string;
  source_ip: string;
  source_name?: string;
  vendor?: string;
  hostname?: string;
  app_name?: string;
  severity?: number;
  severity_name?: string;
  raw_message: string;
  message?: string;
  parsed_fields?: Record<string, string>;
  username?: string;
  is_dropped: boolean;
  drop_reason?: string;
  forwarded_to_siem: boolean;
  processed: boolean;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  source_ip: string;
  source_name?: string;
  vendor?: string;
  username?: string;
  raw_message: string;
  action: string;
  reason: string;
  rule_id?: string;
  rule_name?: string;
  matched_pattern?: string;
}

export interface DashboardStats {
  total_received: number;
  total_accepted: number;
  total_dropped: number;
  total_forwarded: number;
  logs_by_vendor: { vendor: string; count: number }[];
  logs_by_source: { source_name: string; count: number }[];
  top_users: { username: string; count: number }[];
  recent_events: RecentEvent[];
  active_sources: number;
  total_sources: number;
  active_filter_rules: number;
}

export interface RecentEvent {
  id: string;
  received_at: string;
  source_name?: string;
  vendor?: string;
  severity_name?: string;
  username?: string;
  message?: string;
  is_dropped: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
