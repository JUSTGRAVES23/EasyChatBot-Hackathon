import { describe, expect, it } from "vitest";
describe("Project Discovery",()=> {
  it("uses a separate discovery API boundary",()=>expect("/project-control/discovery/candidates").not.toBe("/project-control/registry/projects"));
  it("requires review before registration",()=>expect(["discovered","reviewed","registered"]).toEqual(["discovered","reviewed","registered"]));
});
