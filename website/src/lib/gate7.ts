import fixture from '@/data/gate7.json';

export interface RecoveredRouteContract {
  id: string;
  architecture: string;
  repeats: string[];
  cpu: string;
  cuda: string;
  inputs: string;
}
export interface Gate7Presentation {
  commit: string;
  experiment: string;
  sources: { path: string; sha256: string }[];
  models: RecoveredRouteContract[];
  windows: { id: string; start: number; end: number; nominal: number | null }[];
  units: string[];
  figures: { id: string; source: string; kind: string }[];
}
export const atlas = fixture satisfies Gate7Presentation;
