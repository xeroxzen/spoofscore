// Pure SPF/DMARC assessment. Mirrors src/spoofscore/assess.py; both are tested
// against tests/vectors.json, so change them together.

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
const DMARC_VERSION = /^[vV]\s*=\s*DMARC1\s*(;|$)/;
const DMARC_LOOKALIKE = /DMARC1|(^|;)\s*p\s*=/i;
const SPF_VERSION = /^v=spf1(\s|$)/i;
const SPF_ALL = /^([+\-~?]?)all$/i;
const SPF_LOOKUP = /^[+\-~?]?(include|a|mx|ptr|exists)(:|\/|$)|^redirect=/i;
const MAX_SPF_LOOKUPS = 10;

const finding = (code, severity, title, fix) => ({ code, severity, title, fix });

export function dmarcTags(record) {
  const tags = {};
  for (const part of record.split(";")) {
    const eq = part.indexOf("=");
    if (eq !== -1) tags[part.slice(0, eq).trim().toLowerCase()] = part.slice(eq + 1).trim();
  }
  return tags;
}

function assessDmarc(records) {
  const valid = records.filter((r) => DMARC_VERSION.test(r.trim()));
  if (valid.length === 0) {
    const broken = records.find((r) => DMARC_LOOKALIKE.test(r));
    if (broken !== undefined) {
      const fixed = broken.trim().startsWith("DMARC1") ? "v=" + broken.trim() : broken;
      return { verdict: "exposed", record: null, findings: [finding(
        "DMARC_MALFORMED", "critical",
        "A DMARC record exists but is malformed, so receivers ignore it entirely.",
        `Publish a record that starts with v=DMARC1, e.g.: ${fixed}`,
      )] };
    }
    return { verdict: "exposed", record: null, findings: [finding(
      "DMARC_MISSING", "high",
      "No DMARC record. Receivers have no instruction to reject mail forging this domain.",
      "Publish _dmarc TXT: v=DMARC1; p=none; rua=mailto:<reports address>, then move to " +
        "p=reject once reports show all legitimate mail passes.",
    )] };
  }
  if (valid.length > 1) {
    return { verdict: "exposed", record: null, findings: [finding(
      "DMARC_MULTIPLE", "high",
      "More than one DMARC record. Receivers treat this as no policy at all.",
      "Keep exactly one v=DMARC1 TXT record at _dmarc.",
    )] };
  }
  return assessDmarcPolicy(valid[0]);
}

function assessDmarcPolicy(record) {
  const tags = dmarcTags(record);
  const policy = (tags.p ?? "").toLowerCase();
  const findings = [];
  if (!("rua" in tags)) {
    findings.push(finding(
      "DMARC_NO_REPORTS", "low",
      "No aggregate report address (rua), so nobody sees who sends mail as this domain.",
      "Add rua=mailto:<reports address>.",
    ));
  }
  if (!["none", "quarantine", "reject"].includes(policy)) {
    findings.push(finding(
      "DMARC_POLICY_INVALID", "high",
      `DMARC policy is missing or invalid (p=${policy || "<absent>"}), so nothing is enforced.`,
      "Set p=reject (or p=quarantine while you confirm legitimate senders).",
    ));
    return { verdict: "exposed", record, findings };
  }
  if (policy === "none") {
    findings.push(finding(
      "DMARC_MONITOR_ONLY", "high",
      "DMARC is monitor-only (p=none). Forged mail is still delivered.",
      "Review the rua reports, align legitimate senders, then set p=quarantine and p=reject.",
    ));
    return { verdict: "exposed", record, findings };
  }
  let verdict = "protected";
  if (policy === "quarantine") {
    findings.push(finding(
      "DMARC_QUARANTINE", "low",
      "Forged mail is sent to spam rather than rejected.",
      "Move to p=reject when ready.",
    ));
  }
  const pct = tags.pct ?? "100";
  if (!/^\d+$/.test(pct) || Number(pct) < 100) {
    verdict = "partial";
    findings.push(finding(
      "DMARC_PARTIAL_PCT", "medium",
      `Policy applies to only pct=${pct}% of failing mail; the rest is delivered.`,
      "Remove pct or set pct=100.",
    ));
  }
  if ((tags.sp ?? "").toLowerCase() === "none") {
    verdict = "partial";
    findings.push(finding(
      "DMARC_SUBDOMAIN_NONE", "medium",
      "Subdomains are unprotected (sp=none), e.g. payments.<domain> can be forged.",
      "Remove sp=none or set sp=reject.",
    ));
  }
  return { verdict, record, findings };
}

function assessSpf(records) {
  const spf = records.filter((r) => SPF_VERSION.test(r.trim()));
  if (spf.length === 0) {
    return { passesEveryone: false, record: null, findings: [finding(
      "SPF_MISSING", "medium",
      "No SPF record. If this domain sends no mail, say so explicitly.",
      "Publish an SPF record listing your senders ending in -all; for a domain that sends " +
        "no mail, publish: v=spf1 -all",
    )] };
  }
  if (spf.length > 1) {
    return { passesEveryone: false, record: null, findings: [finding(
      "SPF_MULTIPLE", "high",
      "More than one SPF record. SPF evaluation fails with a permanent error.",
      "Merge into a single v=spf1 record.",
    )] };
  }
  const record = spf[0].trim();
  const terms = record.split(/\s+/).slice(1);
  const findings = [];
  const lookups = terms.filter((t) => SPF_LOOKUP.test(t)).length;
  if (lookups > MAX_SPF_LOOKUPS) {
    findings.push(finding(
      "SPF_TOO_MANY_LOOKUPS", "high",
      `${lookups} DNS-lookup terms at the top level alone; SPF allows 10, so it fails.`,
      "Flatten or remove includes to stay within 10 lookups.",
    ));
  }
  const allMatch = terms.map((t) => SPF_ALL.exec(t)).find((m) => m !== null);
  if (allMatch === undefined) {
    if (!terms.some((t) => t.toLowerCase().startsWith("redirect="))) {
      findings.push(finding(
        "SPF_NO_ALL", "medium",
        "SPF has no 'all' at the end, so unlisted senders get a neutral result, not a fail.",
        `Append -all: ${record} -all`,
      ));
    }
    return { passesEveryone: false, record, findings };
  }
  const qualifier = allMatch[1] || "+";
  if (qualifier === "+") {
    findings.push(finding(
      "SPF_PASS_ALL", "critical",
      "SPF authorises every server on the internet (+all). Forged mail passes SPF and DMARC.",
      "Replace +all with -all.",
    ));
    return { passesEveryone: true, record, findings };
  }
  if (qualifier === "?") {
    findings.push(finding(
      "SPF_NEUTRAL_ALL", "medium",
      "SPF ends in ?all, which asserts nothing about unlisted senders.",
      "Replace ?all with -all (or ~all while testing).",
    ));
  }
  return { passesEveryone: false, record, findings };
}

export function assess(spfTxt, dmarcTxt) {
  const dmarc = assessDmarc(dmarcTxt);
  const spf = assessSpf(spfTxt);
  const findings = [...dmarc.findings, ...spf.findings].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] || a.code.localeCompare(b.code),
  );
  return {
    verdict: spf.passesEveryone ? "exposed" : dmarc.verdict,
    findings,
    dmarcRecord: dmarc.record,
    spfRecord: spf.record,
  };
}

// DNS-over-HTTPS JSON returns TXT data as one or more quoted strings, e.g.
// "\"v=spf1 ip4:192.0.2.1\" \" -all\"". Per RFC 7208 3.3 they join with no separator.
export function joinTxtData(data) {
  const parts = [];
  const quoted = /"((?:[^"\\]|\\.)*)"/g;
  let match;
  let guard = 0;
  while ((match = quoted.exec(data)) !== null && guard < 256) {
    parts.push(match[1].replace(/\\(\d{3}|.)/g, (_, esc) =>
      esc.length === 3 ? String.fromCharCode(Number(esc)) : esc));
    guard += 1;
  }
  return parts.length > 0 ? parts.join("") : data;
}

export function normaliseDomain(raw) {
  let domain = raw.trim().toLowerCase().replace(/^https?:\/\//, "");
  domain = domain.split("/")[0].split("@").pop().replace(/\.$/, "");
  if (!domain || !domain.includes(".") || domain.length > 253 || !/^[a-z0-9.-]+$/.test(domain)) {
    throw new Error(`not a domain name: ${raw}`);
  }
  return domain;
}
