import type { ServiceSLAReport } from "../types";
import api from "./client";

export const getSLAReport = (days: number) =>
  api.get<ServiceSLAReport[]>("/reports/sla", { params: { days } }).then((r) => r.data);
