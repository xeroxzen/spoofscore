import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { assess, joinTxtData, normaliseDomain } from "./spoofscore.js";

const vectors = JSON.parse(
  readFileSync(new URL("../tests/vectors.json", import.meta.url), "utf-8"),
);

for (const v of vectors) {
  test(`vector: ${v.name}`, () => {
    const result = assess(v.spf, v.dmarc);
    assert.equal(result.verdict, v.verdict);
    assert.deepEqual(result.findings.map((f) => f.code).sort(), [...v.codes].sort());
  });
}

test("joinTxtData concatenates split strings without a separator", () => {
  assert.equal(joinTxtData('"v=spf1 ip4:192.0.2.1" " -all"'), "v=spf1 ip4:192.0.2.1 -all");
});

test("joinTxtData unescapes quotes and decimal escapes", () => {
  assert.equal(joinTxtData('"a\\"b\\059c"'), 'a"b;c');
});

test("normaliseDomain strips scheme, path and mailbox", () => {
  assert.equal(normaliseDomain("https://WWW.Example.com/x"), "www.example.com");
  assert.equal(normaliseDomain("ceo@example.co.zw"), "example.co.zw");
});

test("normaliseDomain rejects junk", () => {
  assert.throws(() => normaliseDomain("localhost"));
  assert.throws(() => normaliseDomain("exa mple.com"));
});
