"""Replay pool of realistic HR questions for Northwind Systems.

This is NOT a gold test set. There are no reference answers here, and the pool
was not curated to break the assistant. It is meant to look like roughly one
week of real inbound traffic from employees across the Chennai, London and
Austin offices, arriving over Slack, the HR portal and email.

Phrasing is deliberately uneven: terse one-liners, typos, lowercase with no
punctuation, long polite preambles, follow-up-shaped fragments, and the
slightly formal register common in HR tickets. Some questions happen to be
region-ambiguous, time/version ambiguous, outside the policy corpus, or carry
pasted personal identifiers, because real traffic does. Those properties are
recorded only in the short `note` field for provenance; they are not labels of
expected behaviour and they never appear inside the question text.

A replay script sends QUESTION_POOL through the RAG app to produce a trace log.
A human then samples that log at random and hand-codes failure modes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PoolQuestion:
    qid: str
    question: str
    channel: str  # "slack" | "portal" | "email"
    note: str


QUESTION_POOL = (
    # --- ordinary answerable traffic ---
    PoolQuestion(
        qid="P001",
        question="How many earned leave days do I get per year in the Chennai office?",
        channel="portal",
        note="plain annual leave, region named",
    ),
    PoolQuestion(
        qid="P002",
        question="sick leave how many days",
        channel="slack",
        note="terse, lowercase, no punctuation",
    ),
    PoolQuestion(
        qid="P003",
        question="Hi team, I hope you are doing well. I wanted to understand the process for applying for maternity leave, including how much advance notice I should give and what documents are required. I am based in London. Thank you so much for your help.",
        channel="email",
        note="long polite, UK maternity",
    ),
    PoolQuestion(
        qid="P004",
        question="Kindly confirm whether paternity leave can be availed in parts or must it be taken in one stretch. I am in the Chennai office.",
        channel="portal",
        note="formal Indian-English register",
    ),
    PoolQuestion(
        qid="P005",
        question="Do I need a doctors note for 2 days of sick leave?",
        channel="slack",
        note="sick leave documentation",
    ),
    PoolQuestion(
        qid="P006",
        question="whats the notice period for someone in austin",
        channel="slack",
        note="US notice period, lowercase",
    ),
    PoolQuestion(
        qid="P007",
        question="I am planning to resign next month. What is the correct resignation process and who do I submit the letter to?",
        channel="email",
        note="resignation process",
    ),
    PoolQuestion(
        qid="P008",
        question="how long is probation for new joiners in india",
        channel="portal",
        note="probation, India",
    ),
    PoolQuestion(
        qid="P009",
        question="When does confirmation happen after probation ends? Is there a formal letter?",
        channel="portal",
        note="confirmation process",
    ),
    PoolQuestion(
        qid="P010",
        question="How many days a week do I have to come to office under the hybrid policy?",
        channel="slack",
        note="hybrid, no region named but policy may be global",
    ),
    PoolQuestion(
        qid="P011",
        question="Can I work from home full time if my manager approves it?",
        channel="portal",
        note="WFH exception",
    ),
    PoolQuestion(
        qid="P012",
        question="travel expense claim deadline? i travelled in september and still havent filed",
        channel="slack",
        note="expense claim window, typo-ish casual",
    ),
    PoolQuestion(
        qid="P013",
        question="What is the per diem for domestic travel and do I need to keep meal receipts?",
        channel="portal",
        note="travel per diem",
    ),
    PoolQuestion(
        qid="P014",
        question="Kindly let me know the maximum hotel tariff permissible for a two night client visit to London.",
        channel="email",
        note="formal register, travel limits",
    ),
    PoolQuestion(
        qid="P015",
        question="when is the next performance review cycle",
        channel="slack",
        note="review cycle timing",
    ),
    PoolQuestion(
        qid="P016",
        question="What are the rating levels used in the performance review and what does a mid rating mean for my increment?",
        channel="portal",
        note="ratings",
    ),
    PoolQuestion(
        qid="P017",
        question="I disagree with my review rating. Is there an appeal process?",
        channel="email",
        note="review appeal, borders on grievance",
    ),
    PoolQuestion(
        qid="P018",
        question="How do I raise a grievance against my reporting manager without it going to him first?",
        channel="email",
        note="grievance escalation",
    ),
    PoolQuestion(
        qid="P019",
        question="is there an anonymous way to report something",
        channel="slack",
        note="whistleblower / code of conduct",
    ),
    PoolQuestion(
        qid="P020",
        question="Kindly clarify the escalation matrix if my grievance is not resolved within the stated timeline.",
        channel="portal",
        note="grievance timeline",
    ),
    PoolQuestion(
        qid="P021",
        question="What counts as a conflict of interest under the code of conduct? I have been asked to do some weekend consulting.",
        channel="email",
        note="code of conduct, moonlighting",
    ),
    PoolQuestion(
        qid="P022",
        question="can i accept a gift from a vendor",
        channel="slack",
        note="gifts policy",
    ),
    PoolQuestion(
        qid="P023",
        question="What are the disciplinary steps for repeated late attendance?",
        channel="portal",
        note="disciplinary ladder",
    ),
    PoolQuestion(
        qid="P024",
        question="payslip not showing for last month, where do i download it",
        channel="slack",
        note="payslip access",
    ),
    PoolQuestion(
        qid="P025",
        question="Which date of the month is salary credited?",
        channel="portal",
        note="payroll date",
    ),
    PoolQuestion(
        qid="P026",
        question="I think there is an error in my payslip deductions. Who should I write to and what is the turnaround time for a payroll correction?",
        channel="email",
        note="payroll dispute",
    ),
    PoolQuestion(
        qid="P027",
        question="Does the health insurance cover my parents or only spouse and kids?",
        channel="portal",
        note="insurance dependants",
    ),
    PoolQuestion(
        qid="P028",
        question="health insurance sum insured amount?",
        channel="slack",
        note="terse insurance",
    ),
    PoolQuestion(
        qid="P029",
        question="I got married last month. How do I add my spouse to the medical policy and is there a window for that?",
        channel="email",
        note="insurance mid-year addition",
    ),
    PoolQuestion(
        qid="P030",
        question="how much is the referral bonus",
        channel="slack",
        note="referral bonus amount",
    ),
    PoolQuestion(
        qid="P031",
        question="If I refer a candidate and they join but leave in 3 months, do I still get the referral payout?",
        channel="portal",
        note="referral clawback",
    ),
    PoolQuestion(
        qid="P032",
        question="Kindly confirm whether referral bonus is applicable for contract to hire positions as well.",
        channel="portal",
        note="referral scope",
    ),
    PoolQuestion(
        qid="P033",
        question="Can I take earned leave and sick leave together for a surgery and recovery?",
        channel="email",
        note="combining leave types",
    ),
    PoolQuestion(
        qid="P034",
        question="is casual leave different from earned leave here",
        channel="slack",
        note="leave type distinction",
    ),
    PoolQuestion(
        qid="P035",
        question="what happens to my leave balance when i resign, do i get paid out",
        channel="portal",
        note="leave encashment on exit",
    ),
    PoolQuestion(
        qid="P036",
        question="During notice period am I allowed to take leave? My manager says no but I have 9 days pending.",
        channel="email",
        note="leave during notice",
    ),
    PoolQuestion(
        qid="P037",
        question="Do public holidays differ between the Chennai, London and Austin offices or is there one common list?",
        channel="portal",
        note="holiday calendar",
    ),
    PoolQuestion(
        qid="P038",
        question="how many optional holidays can i pick",
        channel="slack",
        note="floating holidays",
    ),
    PoolQuestion(
        qid="P039",
        question="I am relocating my working hours slightly to overlap with the US team. Does that need a formal flexible working request?",
        channel="email",
        note="flexible hours",
    ),
    PoolQuestion(
        qid="P040",
        question="Can I work from another city for a month while visiting family? Is that covered by the remote work policy?",
        channel="portal",
        note="work from anywhere",
    ),
    PoolQuestion(
        qid="P041",
        question="does working from abroad need approval",
        channel="slack",
        note="remote work abroad",
    ),
    PoolQuestion(
        qid="P042",
        question="Reimbursement for internet and home office setup, is there a monthly allowance?",
        channel="portal",
        note="WFH allowance",
    ),
    PoolQuestion(
        qid="P043",
        question="I used my own car for a client visit. How is mileage reimbursed and at what rate?",
        channel="email",
        note="mileage",
    ),
    PoolQuestion(
        qid="P044",
        question="expense report rejected saying missing approval. what approval do i need before booking flights",
        channel="slack",
        note="pre-approval for travel",
    ),
    PoolQuestion(
        qid="P045",
        question="Kindly advise the procedure for availing adoption leave.",
        channel="portal",
        note="adoption leave",
    ),
    PoolQuestion(
        qid="P046",
        question="Is there any provision for bereavement leave? My grandfather passed away and I need a few days.",
        channel="email",
        note="bereavement leave",
    ),
    PoolQuestion(
        qid="P047",
        question="can i extend maternity leave unpaid after the paid part ends",
        channel="portal",
        note="unpaid extension",
    ),
    PoolQuestion(
        qid="P048",
        question="What is the shared parental leave arrangement if my partner also works here?",
        channel="email",
        note="both parents employed",
    ),
    PoolQuestion(
        qid="P049",
        question="Do I keep accruing annual leave while I am on maternity leave?",
        channel="portal",
        note="accrual during leave",
    ),
    PoolQuestion(
        qid="P050",
        question="notice period if i am terminated vs if i resign, is it the same",
        channel="slack",
        note="notice symmetry",
    ),
    PoolQuestion(
        qid="P051",
        question="Can the company waive part of my notice period if I have a joining date pressure from the new employer?",
        channel="email",
        note="notice buyout",
    ),
    PoolQuestion(
        qid="P052",
        question="what does the exit process involve, clearance etc",
        channel="portal",
        note="exit formalities",
    ),
    PoolQuestion(
        qid="P053",
        question="Is my probation period counted towards gratuity or any service based benefit?",
        channel="portal",
        note="probation and service",
    ),
    PoolQuestion(
        qid="P054",
        question="my manager wants to extend my probation, can they do that and for how long",
        channel="slack",
        note="probation extension",
    ),
    PoolQuestion(
        qid="P055",
        question="Hello, apologies for the long message. I joined four months ago and I am not clear whether I am eligible for the full performance review this cycle or only a shorter check in, since I joined partway through the year. Could you please clarify how new joiners are handled in the review process? Many thanks.",
        channel="email",
        note="rambling, new joiner review eligibility",
    ),
    # --- region ambiguous (no India/UK/US named) ---
    PoolQuestion(
        qid="P056",
        question="notice period?",
        channel="slack",
        note="no region named",
    ),
    PoolQuestion(
        qid="P057",
        question="How long is the notice period for a senior engineer?",
        channel="portal",
        note="no region named",
    ),
    PoolQuestion(
        qid="P058",
        question="and if I'm still on probation?",
        channel="slack",
        note="follow-up shaped, no region named",
    ),
    PoolQuestion(
        qid="P059",
        question="Kindly confirm the notice period applicable during the probation period.",
        channel="portal",
        note="no region named",
    ),
    PoolQuestion(
        qid="P060",
        question="how much parental leave do i get",
        channel="slack",
        note="no region named",
    ),
    PoolQuestion(
        qid="P061",
        question="We are expecting a baby in March. What parental leave am I entitled to and is it fully paid?",
        channel="email",
        note="no region named",
    ),
    PoolQuestion(
        qid="P062",
        question="Is parental leave the same for fathers and mothers?",
        channel="portal",
        note="no region named",
    ),
    PoolQuestion(
        qid="P063",
        question="probation length for a lateral hire",
        channel="portal",
        note="no region named",
    ),
    PoolQuestion(
        qid="P064",
        question="when does probation end exactly, is it 3 months or 6",
        channel="slack",
        note="no region named",
    ),
    PoolQuestion(
        qid="P065",
        question="Could you please tell me the notice period I need to serve if I have been with the company for over five years?",
        channel="email",
        note="no region named, tenure based",
    ),
    PoolQuestion(
        qid="P066",
        question="is parental leave available from day one or is there a service requirement",
        channel="portal",
        note="no region named",
    ),
    PoolQuestion(
        qid="P067",
        question="Kindly clarify whether notice period is calculated in calendar days or working days.",
        channel="portal",
        note="no region named",
    ),
    # --- time / version ambiguous ---
    PoolQuestion(
        qid="P068",
        question="How many annual leave days am I entitled to?",
        channel="portal",
        note="no year given, policy was revised",
    ),
    PoolQuestion(
        qid="P069",
        question="how many leaves can i carry over to next year",
        channel="slack",
        note="carry-over, no year given",
    ),
    PoolQuestion(
        qid="P070",
        question="Last year I was told I could carry forward 10 days. Is that still correct?",
        channel="email",
        note="references last year, version ambiguous",
    ),
    PoolQuestion(
        qid="P071",
        question="Under the 2023 leave policy my entitlement was different. Which one applies to me now?",
        channel="portal",
        note="explicitly names 2023 policy",
    ),
    PoolQuestion(
        qid="P072",
        question="carry forward limit as per the leave policy 2023?",
        channel="slack",
        note="explicitly names 2023 policy",
    ),
    PoolQuestion(
        qid="P073",
        question="I had some leave left over from last year that I never used. Did it lapse or is it still in my balance?",
        channel="email",
        note="last year balance, version ambiguous",
    ),
    PoolQuestion(
        qid="P074",
        question="Kindly confirm the current earned leave entitlement as the figure I have on record appears to be outdated.",
        channel="portal",
        note="asks for current vs old entitlement",
    ),
    PoolQuestion(
        qid="P075",
        question="did the leave policy change recently, my balance looks different from last year",
        channel="slack",
        note="policy change comparison",
    ),
    # --- out of corpus, should be refused ---
    PoolQuestion(
        qid="P076",
        question="What is the relocation allowance if I move from Chennai to Austin?",
        channel="portal",
        note="out of corpus, relocation",
    ),
    PoolQuestion(
        qid="P077",
        question="how many stock options do engineers at my level get",
        channel="slack",
        note="out of corpus, equity",
    ),
    PoolQuestion(
        qid="P078",
        question="Does Northwind Systems sponsor an H1B or any work visa for the Austin office?",
        channel="email",
        note="out of corpus, visa sponsorship",
    ),
    PoolQuestion(
        qid="P079",
        question="is there a gym in the office or a gym reimbursement",
        channel="slack",
        note="out of corpus, facilities",
    ),
    PoolQuestion(
        qid="P080",
        question="I have an offer from another company. How should I approach negotiating a counter offer with my manager?",
        channel="email",
        note="out of corpus, salary negotiation advice",
    ),
    PoolQuestion(
        qid="P081",
        question="Kindly share details of the ESPP enrolment window and the discount percentage.",
        channel="portal",
        note="out of corpus, ESPP",
    ),
    PoolQuestion(
        qid="P082",
        question="what is my vesting cliff",
        channel="slack",
        note="out of corpus, equity vesting",
    ),
    PoolQuestion(
        qid="P083",
        question="Can HR help with a rental agreement or broker for accommodation near the Chennai office?",
        channel="portal",
        note="out of corpus, housing assistance",
    ),
    # --- contains personal identifiers (fake placeholders only) ---
    PoolQuestion(
        qid="P084",
        question="My employee ID is EMP-48213. Can you check how many earned leave days I have left this year?",
        channel="portal",
        note="contains employee id",
    ),
    PoolQuestion(
        qid="P085",
        question="emp id EMP-48213, payslip for last month not downloading",
        channel="slack",
        note="contains employee id",
    ),
    PoolQuestion(
        qid="P086",
        question="Please send the insurance e-card to my personal address priya.k@example.com as I will be on leave.",
        channel="email",
        note="contains email",
    ),
    PoolQuestion(
        qid="P087",
        question="Kindly reach me on 555-0137 regarding my notice period query, as I am travelling and may not see email.",
        channel="portal",
        note="contains phone",
    ),
    PoolQuestion(
        qid="P088",
        question="Hi, this is Priya. I want to know the maternity leave duration applicable to me.",
        channel="slack",
        note="contains first name",
    ),
    PoolQuestion(
        qid="P089",
        question="Alex here, my manager asked me to confirm the probation confirmation date. My employee ID is EMP-48213 if that helps.",
        channel="email",
        note="contains first name and employee id",
    ),
    PoolQuestion(
        qid="P090",
        question="referral candidate applied with alex.m@example.com and phone 555-0164, how do i track the referral bonus status",
        channel="portal",
        note="contains email and phone",
    ),
)
