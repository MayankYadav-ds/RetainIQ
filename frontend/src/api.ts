export interface Version {
  name: "RetainIQ";
  version: string;
  phase: number;
}
export interface Readiness {
  status: "ready";
  database: "reachable";
}
export interface Connection {
  version: Version;
  readiness: Readiness;
}
export const base = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export async function verifyConnection(
  signal?: AbortSignal,
): Promise<Connection> {
  const timeout = AbortSignal.timeout(5000);
  const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
  const responses = await Promise.all([
    fetch(`${base}/api/v1/version`, { signal: combined, credentials: "omit" }),
    fetch(`${base}/ready`, { signal: combined, credentials: "omit" }),
  ]);
  if (responses.some((response) => !response.ok))
    throw new Error("Backend is not ready");
  const [version, readiness]: unknown[] = await Promise.all(
    responses.map((response) => response.json()),
  );
  if (
    !version ||
    typeof version !== "object" ||
    !("version" in version) ||
    typeof version.version !== "string" ||
    !("name" in version) ||
    version.name !== "RetainIQ" ||
    !("phase" in version) ||
    typeof version.phase !== "number" ||
    !readiness ||
    typeof readiness !== "object" ||
    !("status" in readiness) ||
    readiness.status !== "ready" ||
    !("database" in readiness) ||
    readiness.database !== "reachable"
  ) {
    throw new Error("Unexpected backend response");
  }
  return { version: version as Version, readiness: readiness as Readiness };
}
