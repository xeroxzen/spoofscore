import { assess, joinTxtData, normaliseDomain } from "./spoofscore.js";

const DOH_ENDPOINT = "https://cloudflare-dns.com/dns-query";
const TXT_TYPE = 16;
const NXDOMAIN = 3;

const HEADLINES = {
  exposed: ["Yes, very likely.", "Email forged to look like it came from this domain will probably reach inboxes."],
  partial: ["Partly.", "Some forged email is blocked, but some still gets through."],
  protected: ["Unlikely.", "Receiving mail servers are told to reject or quarantine forged email from this domain."],
};

class LookupError extends Error {}

async function lookupTxt(name) {
  const url = `${DOH_ENDPOINT}?name=${encodeURIComponent(name)}&type=TXT`;
  const response = await fetch(url, { headers: { accept: "application/dns-json" } });
  if (!response.ok) throw new LookupError(`DNS service returned HTTP ${response.status}`);
  const body = await response.json();
  if (body.Status === NXDOMAIN) return { exists: false, records: [] };
  if (body.Status !== 0) throw new LookupError(`DNS lookup failed (status ${body.Status})`);
  const records = (body.Answer ?? []).filter((a) => a.type === TXT_TYPE).map((a) => joinTxtData(a.data));
  return { exists: true, records };
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function recordRow(label, value) {
  const row = el("div", "record");
  row.append(el("span", "record-label", label), el("code", "", value ?? "None in effect"));
  return row;
}

function findingCard(f) {
  const card = el("li", `finding sev-${f.severity}`);
  card.append(el("span", "badge", f.severity), el("p", "finding-title", f.title));
  const fix = el("div", "fix");
  fix.append(el("span", "fix-label", "Fix"), el("code", "", f.fix));
  card.append(fix);
  return card;
}

function render(domain, result) {
  const out = document.getElementById("result");
  out.replaceChildren();
  out.className = `result verdict-${result.verdict}`;
  const [headline, explanation] = HEADLINES[result.verdict];
  out.append(
    el("p", "result-domain", domain),
    el("h2", "result-headline", headline),
    el("p", "result-explainer", explanation),
    recordRow("DMARC", result.dmarcRecord),
    recordRow("SPF", result.spfRecord),
  );
  if (result.findings.length > 0) {
    const list = el("ul", "findings");
    list.append(...result.findings.map(findingCard));
    out.append(el("h3", "", "What to fix"), list);
  } else {
    out.append(el("p", "all-clear", "No problems found in SPF or DMARC."));
  }
  out.hidden = false;
}

function showError(message) {
  const out = document.getElementById("result");
  out.replaceChildren(el("p", "error", message));
  out.className = "result";
  out.hidden = false;
}

async function check(rawDomain) {
  let domain;
  try {
    domain = normaliseDomain(rawDomain);
  } catch {
    showError("Enter a domain like yourcompany.co.zw or an email address.");
    return;
  }
  const button = document.getElementById("check");
  button.disabled = true;
  button.textContent = "Checking…";
  try {
    const [spf, dmarc] = await Promise.all([lookupTxt(domain), lookupTxt(`_dmarc.${domain}`)]);
    if (!spf.exists) {
      showError(`${domain} does not exist in DNS.`);
      return;
    }
    render(domain, assess(spf.records, dmarc.records));
    history.replaceState(null, "", `?d=${encodeURIComponent(domain)}`);
  } catch (err) {
    const reason = err instanceof LookupError ? err.message : "network error";
    showError(`Couldn't complete the check (${reason}). This says nothing about the domain; try again.`);
  } finally {
    button.disabled = false;
    button.textContent = "Check";
  }
}

document.getElementById("form").addEventListener("submit", (event) => {
  event.preventDefault();
  check(document.getElementById("domain").value).catch((err) => showError(String(err)));
});

const preset = new URLSearchParams(location.search).get("d");
if (preset) {
  document.getElementById("domain").value = preset;
  check(preset).catch((err) => showError(String(err)));
}
