export type Job = {
  id: string;
  company: string;
  title: string;
  location: string;
  url: string;
  description: string;
  status: string;
  notes: string;
  application_date: string | null;
  folder: string | null;
  created_at: string;
  selected_project_id: string | null;
};
export type Report = {
  summary: string;
  report: string;
  sources: { title: string; url: string; accessed_at: string }[];
  limitations: string[];
};
export type Run = {
  id: string;
  kind: string;
  job_id: string | null;
  state: string;
  result: any;
  error: string | null;
  created_at: string;
  updated_at: string;
};
export type Mail = {
  id: string;
  job_id: string | null;
  company: string;
  role: string;
  kind: string;
  subject: string;
  sender: string;
  received_at: string;
  submission_date: string | null;
  excerpt: string;
  reason: string;
  confidence: string;
  state: string;
};
export type Goals = {
  date: string;
  weekly_target: number;
  current_week_target: number;
  week_completed: number;
  daily_base: number;
  carryover: number;
  ahead: number;
  today_target: number;
  today_completed: number;
  remaining_today: number;
  week_remaining: number;
  schedule: {
    date: string;
    label: string;
    planned: number;
    completed: number;
    today: boolean;
  }[];
  settings: { weekly_target: number; workdays: number[]; start_date: string };
};
export type Agent = {
  id: string;
  name: string;
  reads: string;
  profile_access: boolean;
  does: string;
  implementation: string;
  guide: string;
};
export type Summary = {
  jobs: Job[];
  goals: Goals;
  mail: {
    connection: {
      connected: boolean;
      email?: string;
      last_synced_at?: string;
      coverage?: string;
      mode?: string;
    };
    messages: Mail[];
  };
  runs: Run[];
  agents: Agent[];
  profile_dirty: boolean;
  counts: {
    saved: number;
    applied: number;
    interviews: number;
    offers: number;
  };
  activity: { id: number; action: string; occurred_at: string; details: any }[];
};
export type Knowledge = {
  id: string;
  kind: string;
  title: string;
  summary: string;
  data: Record<string, any>;
  source: string;
  revision: number;
  review_state: string;
  deleted: boolean;
};
export type ProfileData = {
  items: Knowledge[];
  removed: number;
  registry: Record<string, any>;
  configuration: Record<string, any>;
  sources: Record<string, string>;
  agents: Agent[];
  profile_dirty: boolean;
  skills: { name: string; purpose: string; path: string }[];
};
