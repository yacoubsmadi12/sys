import { format, formatDistanceToNow } from "date-fns";

export function fmtDate(iso: string | undefined): string {
  if (!iso) return "—";
  try {
    return format(new Date(iso), "yyyy-MM-dd HH:mm:ss");
  } catch {
    return iso;
  }
}

export function fmtAgo(iso: string | undefined): string {
  if (!iso) return "—";
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true });
  } catch {
    return iso;
  }
}

export function fmtNumber(n: number): string {
  return n.toLocaleString();
}

export function severityClass(name: string | undefined): string {
  switch (name?.toUpperCase()) {
    case "EMERGENCY":
    case "ALERT":
    case "CRITICAL": return "badge-red";
    case "ERROR":    return "badge-red";
    case "WARNING":  return "badge-yellow";
    case "NOTICE":
    case "INFO":     return "badge-blue";
    case "DEBUG":    return "badge-gray";
    default:         return "badge-gray";
  }
}

export function vendorClass(vendor: string | undefined): string {
  switch (vendor?.toLowerCase()) {
    case "huawei":   return "badge-red";
    case "nokia":    return "badge-blue";
    case "ericsson": return "badge-purple";
    default:         return "badge-gray";
  }
}
