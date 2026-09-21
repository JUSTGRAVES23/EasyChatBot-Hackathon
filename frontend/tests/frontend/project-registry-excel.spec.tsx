import { describe, expect, it, vi } from "vitest";

import {
  exportProjectRegistry,
  importProjectRegistry,
} from "@/app/lib/api/projectRegistry";

describe("Project Registry Excel API", () => {
  it("exports the registry as a blob", async () => {
    const blob = new Blob(["xlsx"], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(blob, { status: 200 }),
    ));

    const result = await exportProjectRegistry();

    expect(result).toBeInstanceOf(Blob);
    expect(fetch).toHaveBeenCalledWith(
      "/project-control/registry/projects/export",
      expect.objectContaining({ method: "GET", credentials: "include" }),
    );
  });

  it("imports an XLSX using FormData", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ imported: 1, mode: "create_only", projects: [] }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    ));

    const file = new File(["xlsx"], "registry.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const result = await importProjectRegistry(file);

    expect(result.imported).toBe(1);
    expect(fetch).toHaveBeenCalledTimes(1);
    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(init?.credentials).toBe("include");
    expect(init?.body).toBeInstanceOf(FormData);
  });
});
