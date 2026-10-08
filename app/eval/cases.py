"""Week 6 eval set: 31 HR-policy cases, each tagged with ONE Week-5 taxonomy mode.

Modes (analysis/taxonomy.md):
  M1  quotes a figure from the superseded 2023 policy as current, or puts the 2023 label on it
  M2  picks an office/policy the employee never named (or one Northwind policy does not cover)
  M3  right headline, plus a reassurance or reason the policy text does not contain
  M4  dead-end refusal: topic not in the policies, no next step or person to ask
  M5  says "I cannot answer" although the policies hold a usable or per-office answer

A case's mode is the failure it PROBES, not a prediction that it fails. `source_trace` marks a
regression case: its question is the trace's stored query copied verbatim (run_eval checks this
against traces/traces.jsonl), from a trace that was hand-coded as a failure in Week 5.

`reference` is what the current policy says, written from data/corpus/ before any answer was
generated. The human labeller and the judge both grade against it, on the same single criterion.

Assertion switches (deterministic, see app/eval/assertions.py):
  cite              answer must carry resolvable citations with the cited policy's own version
  allow_superseded  the employee explicitly asked about the 2023 policy, so citing it is fine
  notice_numeric    a notice-period figure must be stated in digits with a unit
  expect_refusal    out-of-jurisdiction: the answer must take the refusal path
  forbidden         figures that exist only in a superseded 2023 file
"""
from dataclasses import dataclass
from typing import Optional, Tuple

MODES = {
    "M1": "superseded 2023 figure",
    "M2": "office never named / not covered",
    "M3": "unsupported reassurance",
    "M4": "dead-end refusal",
    "M5": "refuses though answer exists",
}


@dataclass(frozen=True)
class EvalCase:
    cid: str
    mode: str
    question: str
    reference: str
    source_trace: Optional[str] = None
    cite: bool = True
    allow_superseded: bool = False
    notice_numeric: bool = False
    expect_refusal: bool = False
    forbidden: Tuple[str, ...] = ()


NOT_COVERED = ("The provided Northwind policies do not cover this. A correct answer says so plainly and gives a "
               "next step: raise a ticket with People Ops or speak to your People Ops partner "
               "(HR-FAQ-002, 'Who do I ask about something not covered here?').")

CASES = (
    # ---------------- M1: superseded 2023 policy ----------------
    EvalCase("C01", "M1",
             "Hi team, I hope you are doing well. I wanted to understand the process for applying for maternity leave, including how much advance notice I should give and what documents are required. I am based in London. Thank you so much for your help.",
             "London employee -> UK Parental Leave Policy HR-LEAVE-011-UK (2025). §5: notify your reporting manager and "
             "the People Ops partner no later than the 15th week before the expected week of childbirth; provide the "
             "MATB1 certificate; People Ops confirms leave dates, pay pattern and return date in writing within 28 days; "
             "give at least 8 weeks' notice to change the return date. Enhanced pay needs 26 weeks' continuous service at "
             "the 15th week (§2). The India figures (10 or 8 weeks' notice, 80 days worked, Form MAT-IN / PL-IN) do NOT "
             "apply to a London employee.",
             source_trace="tr_5bedf7521bc9", forbidden=("10 weeks", "80 days", "MAT-IN")),
    EvalCase("C02", "M1",
             "Reimbursement for internet and home office setup, is there a monthly allowance?",
             "Hybrid Working Policy HR-WORK-007 (2025) §4: internet allowance INR 1,500 / GBP 25 / USD 35 per month for "
             "all employees; one-time home office setup INR 25,000 / GBP 350 / USD 450, once per employment, after "
             "confirmation. The 2023 Remote Working Policy figures (internet INR 1,000 / GBP 15 / USD 20 for fully remote "
             "only; setup INR 15,000 / GBP 200 / USD 250) are superseded.",
             source_trace="tr_6eb9c787ea49",
             forbidden=("INR 1,000", "GBP 15", "USD 20", "INR 15,000", "GBP 200", "USD 250")),
    EvalCase("C03", "M1",
             "How many days of annual leave can I carry forward into next year? I'm an L2 engineer in Chennai.",
             "Annual Leave Policy HR-LEAVE-002 (2025): L1-L3 may carry over up to 10 days (§3); carried leave must be "
             "used by 30 September or it lapses (§4). The 2023 policy's 5 days / 30 June are superseded.",
             forbidden=("30 June",)),
    EvalCase("C04", "M1",
             "What's the cap on leave encashment when I resign?",
             "Annual Leave Policy HR-LEAVE-002 (2025) §4: encashment only at separation, capped at 15 days regardless "
             "of grade band. The 2023 cap of 10 days is superseded.",
             forbidden=("capped at 10 days", "cap of 10 days", "maximum of 10 days", "up to 10 days")),
    EvalCase("C05", "M1",
             "Paternity leave in the Chennai office - how many days do I get and can I split it?",
             "India Parental Leave Policy HR-LEAVE-011-IN (2025) §2: 15 working days, no service requirement, 4 weeks' "
             "notice; must be taken within 6 months of the birth and may be split into at most two blocks. The 2023 "
             "policy (5 working days, single block, within 3 months) is superseded.",
             forbidden=("5 working days", "single block", "within 3 months")),
    EvalCase("C06", "M1",
             "What is the creche reimbursement for Chennai employees?",
             "India Parental Leave Policy HR-LEAVE-011-IN (2025) §4: INR 8,000 per month per child until the child turns "
             "6, claimed through the monthly expense process. The 2023 figure (INR 5,000 until age 4) is superseded.",
             forbidden=("INR 5,000", "turns 4")),
    EvalCase("C07", "M1",
             "how many days a week do engineers need to be in office",
             "Hybrid Working Policy HR-WORK-007 (2025) §2: Engineering and QA - minimum 3 office days a week, anchor "
             "days set by the team lead; fully remote by exception only. The 2023 figure of 2 days is superseded, and "
             "the FAQ's 'two to three days' is not authoritative where it differs from the policy.",
             forbidden=("minimum of 2", "minimum 2 office", "2 days a week", "2 days per week", "two days a week")),
    EvalCase("C08", "M1",
             "carry forward limit as per the leave policy 2023?",
             "The employee asked about the 2023 policy itself. 2023 Annual Leave Policy HR-LEAVE-001 (superseded) §3: "
             "carry-over cap 5 days (L1-L3), 7 (L4-L5), 7 (L6+), 0 (fixed-term); §4: carried leave used by 30 June. "
             "A correct answer gives these AND says the 2023 policy has been replaced by HR-LEAVE-002 from FY2025-26 "
             "(now 10 / 12 / 12 / 0, used by 30 September). Attributing the FAQ's '10 days' to the 2023 policy is wrong.",
             source_trace="tr_ff64ec880989", allow_superseded=True),

    # ---------------- M2: office never named / not covered ----------------
    EvalCase("C09", "M2",
             "can i extend maternity leave unpaid after the paid part ends",
             "Depends on the office, which the employee did not give; a correct answer asks, or answers per office "
             "and names each. London (HR-LEAVE-011-UK §2): 18 weeks full pay, 8 weeks half pay, then 26 weeks "
             "statutory or unpaid, 52 weeks total. Chennai (HR-LEAVE-011-IN): 26 weeks paid (first two children); "
             "an extension is requested against unused annual leave (§5). Austin (HR-LEAVE-011-US): 12 company-paid "
             "weeks, running concurrently with unpaid job-protected leave under law; no further company extension is "
             "described. Presenting one office's answer as universal is wrong.",
             source_trace="tr_c8c4d8bc166a"),
    EvalCase("C10", "M2",
             "What notice period do I have to serve if I resign? I'm an L3 developer.",
             "Depends on the office, which was not given; a correct answer asks or answers per office. Chennai "
             "(HR-SEP-005-IN §3): 90 days after confirmation. London (HR-SEP-005-UK §3): 2 months. Austin "
             "(HR-SEP-005-US §3): employment is at will; requested notice is 3 weeks.",
             notice_numeric=True),
    EvalCase("C11", "M2",
             "I'm in the London office, grade L4. What notice do I have to give when I resign?",
             "UK policy HR-SEP-005-UK §3: 2 months for L3-L4, running in calendar months from the date the resignation "
             "is received in writing; a longer contractual notice prevails (§1). Written notice goes to the reporting "
             "manager (§5). India figures (90 / 60 days) do not apply.",
             notice_numeric=True, forbidden=("90 days", "60 days")),
    EvalCase("C12", "M2",
             "Austin office, L5. how much notice am I supposed to give before leaving?",
             "US policy HR-SEP-005-US: employment is at will and no notice period is guaranteed (§1); the requested "
             "notice for L5 and above is 4 weeks, and giving it keeps you eligible for rehire (§3).",
             notice_numeric=True),
    EvalCase("C13", "M2",
             "I'm on the Singapore payroll. How many paid sick days do I get a year?",
             "Out of jurisdiction: Northwind's policies cover only the India (Chennai), UK (London) and US (Austin) "
             "payrolls. A correct answer does not apply any of those figures, says the policies do not cover the "
             "Singapore payroll, and points the employee to People Ops.",
             cite=False, expect_refusal=True),
    EvalCase("C14", "M2",
             "I work out of our Berlin office on a German contract. What is my notice period if I resign?",
             "Out of jurisdiction: Northwind's policies cover only the India, UK and US payrolls. A correct answer "
             "does not apply their notice periods, says a German contract is not covered, and points the employee to "
             "People Ops or their contract.",
             cite=False, expect_refusal=True),
    EvalCase("C15", "M2",
             "How many paid sick days do I get per year?",
             "Depends on the office, which was not given; a correct answer asks or answers per office. Sick Leave "
             "Policy HR-LEAVE-004 §2: Chennai 12, London 10, Austin 8 paid sick days per leave year."),
    EvalCase("C16", "M2",
             "Kindly advise the procedure for availing adoption leave.",
             "Depends on the office, which was not given; a correct answer asks or names the office per procedure. "
             "London (HR-LEAVE-011-UK §5): notify the reporting manager and People Ops partner, provide the adoption "
             "matching certificate, written confirmation within 28 days. Chennai (HR-LEAVE-011-IN §5): notify in "
             "writing, submit Form PL-IN with supporting documents, confirmation within 10 working days. Austin "
             "(HR-LEAVE-011-US §5): notify at least 30 days before, request in Workday, provide placement "
             "documentation. Presenting one office's procedure as the company procedure is wrong.",
             source_trace="tr_c33486812828"),

    # ---------------- M3: unsupported reassurance ----------------
    EvalCase("C17", "M3",
             "I got married last month. How do I add my spouse to the medical policy and is there a window for that?",
             "Handbook HR-HB-001 'Health insurance': mid-year additions are allowed on marriage but must be notified "
             "within 30 days of the event. 'Last month' may already be more than 30 days ago, so the answer must not "
             "reassure the employee that they still have time. The handbook gives no enrolment steps or named "
             "recipient. Spouse cover: included in Chennai; opt-in in London and Austin.",
             source_trace="tr_7bae0296d4ee"),
    EvalCase("C18", "M3",
             "My manager hasn't responded to my leave request for a week, so it counts as approved, right?",
             "No. HR-LEAVE-002 §5: the reporting manager approves or rejects within 3 working days, and there is no "
             "auto-approval rule; leave taken without an approved request is unauthorised absence handled under the "
             "Disciplinary Policy. Saying it is approved, or inventing an escalation route, is wrong."),
    EvalCase("C19", "M3",
             "I'm resigning from the Chennai office. Can I use my leave balance to shorten my notice period?",
             "Not by default. HR-SEP-005-IN §3: annual leave may not be used to offset notice except with the written "
             "approval of the business unit head. A notice buy-out may be possible (max 30 days for L1-L2, 45 for "
             "L3-L4, not permitted for L5+). Saying yes without the BU head condition is wrong."),
    EvalCase("C20", "M3",
             "I'm an Austin employee leaving next month. Will my unused PTO be paid out?",
             "No. HR-SEP-005-US §3 table note: unused PTO is paid out only where the work state requires it; Texas "
             "does not, so Austin-based employees get no payout unless a written agreement says otherwise."),
    EvalCase("C21", "M3",
             "If I fall sick during my annual leave, do I get those annual leave days back?",
             "No. HR-LEAVE-004 §6: sick leave taken during an approved annual leave period is not converted back to "
             "annual leave. Adding a condition under which it would be (e.g. with a certificate) is wrong."),

    # ---------------- M4: dead-end refusal ----------------
    EvalCase("C22", "M4",
             "Is there any provision for bereavement leave? My grandfather passed away and I need a few days.",
             NOT_COVERED + " There is no bereavement policy in the corpus; mentioning that annual leave can be "
             "requested under HR-LEAVE-002 is acceptable. The bare fixed refusal sentence alone is a FAIL.",
             source_trace="tr_70e480dfca88", cite=False),
    EvalCase("C23", "M4",
             "How do relocation allowances work if I transfer from Chennai to London?",
             "Several policies say transfers fall under the Relocation Policy, which is not in the provided documents. "
             "A correct answer names the Relocation Policy and points the employee to People Ops / the People Ops "
             "partner. The bare fixed refusal sentence alone is a FAIL.",
             cite=False),
    EvalCase("C24", "M4",
             "is there a gym reimbursement or any wellness allowance", NOT_COVERED, cite=False),
    EvalCase("C25", "M4",
             "I've been called for jury duty. Is that paid leave?", NOT_COVERED, cite=False),
    EvalCase("C26", "M4",
             "I got an offer from another company. Can HR help me negotiate a counter-offer?", NOT_COVERED, cite=False),

    # ---------------- M5: refuses although an answer exists ----------------
    EvalCase("C27", "M5",
             "I am relocating my working hours slightly to overlap with the US team. Does that need a formal flexible working request?",
             "The policies describe no formal flexible working request process, but they do answer the constraint: "
             "core hours are 11:00-16:00 local time and cross-office meetings should fall in the 14:00-17:00 UK window "
             "(HR-WORK-007 §7). A correct answer says this; a bare refusal is a FAIL.",
             source_trace="tr_68e7240fd2bc"),
    EvalCase("C28", "M5",
             "Kindly confirm the notice period applicable during the probation period.",
             "Answerable per office (the office was not given; a correct answer asks or answers per office). Chennai "
             "(HR-SEP-005-IN §2): 30 days either side, all grades. London (HR-SEP-005-UK §2): 1 week (L1-L2), 2 weeks "
             "(L3-L4), 4 weeks (L5+). Austin (HR-SEP-005-US §2): requested notice 1 week (L1-L2), 2 weeks (L3+), "
             "employment at will. A bare refusal is a FAIL.",
             source_trace="tr_0f87b193b804", notice_numeric=True),
    EvalCase("C29", "M5",
             "What is the hotel limit per night in London for business travel?",
             "Handbook HR-HB-001 'Travel and expense reimbursement': GBP 190 per night in London; business travel "
             "needs pre-approval from the reporting manager."),
    EvalCase("C30", "M5",
             "When is salary credited for Austin employees, and what is the payroll cut-off?",
             "Handbook HR-HB-001 'Payroll and payslips': Austin is paid on the 15th and the last working day; payroll "
             "cut-offs for changes are the 8th and the 22nd; payslips are available on the pay date."),
    EvalCase("C31", "M5",
             "How many keeping in touch days can I work during maternity leave? I'm in London.",
             "UK policy HR-LEAVE-011-UK §3: up to 10 keeping in touch days without ending the leave, paid at the normal "
             "daily rate, agreed with the reporting manager in advance, voluntary on both sides."),
)

CASES_BY_ID = {c.cid: c for c in CASES}
