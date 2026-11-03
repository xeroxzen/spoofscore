# Move a domain to `p=reject` safely

Publishing `p=reject` straight away can block your own legitimate mail: invoices from your accounting system, newsletters from a marketing platform, or alerts from a website form. This guide shows you how to get to `p=reject` in stages, using DMARC reports to find every legitimate sender first.

Plan for four to eight weeks. Most of that is waiting for reports.

## Before you begin

- Access to edit your domain's DNS.
- A mailbox to receive DMARC aggregate reports. Reports are XML attachments, and a busy domain receives dozens a day. A dedicated address such as `dmarc-reports@yourcompany.co.zw` keeps them out of personal inboxes. A DMARC report-reading service makes them much easier to read.

## Stage 1: Publish a monitoring record

1. Publish this TXT record at `_dmarc.yourcompany.co.zw`. If a DMARC record already exists, replace it; never publish two.

   ```text
   v=DMARC1; p=none; rua=mailto:dmarc-reports@yourcompany.co.zw
   ```

2. Confirm it:

   ```bash
   spoofscore yourcompany.co.zw
   ```

   Expect `DMARC_MONITOR_ONLY`. That's correct for this stage.

3. Wait at least two weeks. Include a month-end if you send invoices or statements monthly.

## Stage 2: Find and fix every legitimate sender

1. In the reports, list every source that sends mail as your domain.

2. For each one, decide whether it's yours:

   | Source | Action |
   |---|---|
   | Your mail provider (Microsoft 365, Google Workspace) | Make sure DKIM signing is turned on for your domain. |
   | A service you use (CRM, ticketing, marketing, payroll) | Follow its guide to add its SPF `include:` or, better, set up DKIM for your domain. |
   | Your own servers or website | Add their IP addresses to SPF, or send through your mail provider. |
   | Something you don't recognise | Probably spoofing. This is what you're about to block. |

3. Fix SPF while you're here. It should end with `-all` and have at most 10 lookups:

   ```bash
   spoofscore yourcompany.co.zw
   ```

   Expect no `SPF_*` findings.

4. Wait for a week of reports in which every legitimate source passes DMARC.

## Stage 3: Quarantine

1. Change the record:

   ```text
   v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@yourcompany.co.zw
   ```

2. Tell your help desk. If a legitimate sender was missed, its mail now goes to recipients' spam folders. That's recoverable, which is why this stage comes before reject.

3. Watch reports for one to two weeks.

> [!NOTE]
> You can use `pct=` to apply the policy to part of your mail, for example `pct=25`, and raise it in steps. spoofscore reports any `pct` below 100 as `partial`, because the rest of the forged mail is still delivered.

## Stage 4: Reject

1. Change the record:

   ```text
   v=DMARC1; p=reject; rua=mailto:dmarc-reports@yourcompany.co.zw
   ```

2. Confirm:

   ```bash
   spoofscore yourcompany.co.zw
   ```

   Expect `PROTECTED` with no high or critical findings.

3. Keep reading the reports. Every new service your organisation adopts that sends as your domain needs SPF or DKIM before it goes live.

## Domains that never send mail

Parked domains and domains used only for websites are easy targets because nobody watches them. Lock them down in one step:

```text
yourcompany-parked.co.zw          TXT  "v=spf1 -all"
_dmarc.yourcompany-parked.co.zw   TXT  "v=DMARC1; p=reject"
```

## Rollback

If legitimate mail is being blocked, change `p=reject` back to `p=quarantine` or `p=none`. DNS changes take effect as caches expire, which depends on the record's TTL. Fix the sender, then move forward again.
