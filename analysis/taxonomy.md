# HR assistant failure taxonomy (Week 5, 2026-10-08)

Random sample of 20 of 90 traces (seed 424242). Each trace is counted once, under its main failure.
Ranked by severity, then count.

| Rank | Failure mode | Count | % of 20 | Severity | Example trace_id |
|---|---|---|---|---|---|
| 1 | Quotes a figure from the superseded 2023 policy as current, or puts the 2023 label on a current figure | 3 | 15% | Legal exposure | `tr_6eb9c787ea49` |
| 2 | Picks an office or policy the employee never named (usually London) and answers as if it applied to them, without saying so or asking | 3 | 15% | Legal exposure | `tr_c8c4d8bc166a` |
| 3 | Gets the headline right but adds a reassurance or a reason the policy text does not contain | 2 | 10% | Legal exposure | `tr_7bae0296d4ee` |
| 4 | Dead-end refusal: the topic is not in the policies, and the employee gets the one fixed "I cannot answer" sentence with no next step or person to ask | 6 | 30% | Annoys the employee | `tr_70e480dfca88` |
| 5 | Says "I cannot answer" although the retrieved extracts held a usable or per-office answer | 2 | 10% | Annoys the employee | `tr_0f87b193b804` |
| – | No failure seen | 4 | 20% | – | `tr_30b5aa50d18e` |
| | **Total** | **20** | **100%** | | |

- **Legal exposure:** modes 1–3 are 8 of 20 (40%). Each one tells an employee a wrong or unsupported entitlement,
  deadline or approval rule, in the company's voice.
- **Also seen as a second failure:** `tr_5bedf7521bc9` (mode 1) gave India numbers to a London employee (mode 2),
  then ended with a refusal that contradicts its own answer.
- **Seen outside the sample:** 4 of 90 traces hit the 700-token limit, and 3 of those returned an empty answer.
- Sentences per trace: [notes.md](notes.md) §4. Next week's target and prediction: [prediction.md](prediction.md).
