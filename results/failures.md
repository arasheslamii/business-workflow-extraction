# Failure analysis

Machine-found candidates from 40 eval records across 3 arms. Judge: `gemini-3.5-flash-lite`.

Three categories, because they have different causes and different fixes: **regressions** (fine-tuning made it worse), **absolute** (worst tuned outputs regardless of baseline), and **patterns** (systematic weakness on a slice).


## 1. Structural failures

| Arm | id | difficulty | vertical | gen tokens | parse error |
|---|---|---|---|---|---|
| Tuned | `eval_syn_012` | vague | private tutoring | 717 | `braces: Expecting ',' delimiter: line 21 column 5 (char 766)` |

## 2. Regressions - tuned worse than the better baseline (16)

`det_delta` = tuned minus best-baseline on the deterministic composite (`schema_valid`, `step_coverage_vs_reference`, `ai_steps_grounded_recall`, `current_process_grounded`, `systems_grounded`). `rub_delta` = same on the judge's mean rubric score. Pairwise losses are items where a baseline won in BOTH orders.

| id | difficulty | source | det_delta | rub_delta | tuned rubric | base rubric | pairwise losses |
|---|---|---|---|---|---|---|---|
| `eval_syn_012` | vague | synthetic | -0.386 | -2.60 | 1.00 | 3.60 | base_fewshot, base_zeroshot |
| `eval_pet_009` | standard | pet_real | -0.050 | -1.30 | 2.80 | 4.10 | base_zeroshot |
| `eval_syn_005` | standard | synthetic | -0.002 | -0.90 | 2.90 | 3.80 | - |
| `eval_pet_007` | standard | pet_real | +0.116 | -0.30 | 3.20 | 3.50 | - |
| `eval_syn_017` | contradictory | synthetic | +0.213 | -0.30 | 4.00 | 4.30 | - |
| `eval_syn_010` | standard | synthetic | +0.052 | -0.20 | 3.50 | 3.70 | base_zeroshot |
| `eval_pet_001` | standard | pet_real | +0.111 | -0.20 | 3.30 | 3.50 | base_fewshot |
| `eval_syn_028` | standard | synthetic | +0.089 | -0.20 | 2.70 | 2.90 | - |
| `eval_pet_005` | standard | pet_real | +0.024 | -0.10 | 3.40 | 3.50 | base_fewshot |
| `eval_syn_011` | contradictory | synthetic | +0.060 | -0.10 | 3.10 | 3.20 | - |
| `eval_syn_025` | contradictory | synthetic | +0.160 | -0.10 | 3.00 | 3.10 | - |
| `eval_syn_003` | contradictory | synthetic | +0.331 | -0.10 | 3.60 | 3.70 | - |
| `eval_syn_023` | vague | synthetic | -0.038 | +0.10 | 3.70 | 3.60 | - |
| `eval_syn_015` | standard | synthetic | -0.015 | +0.20 | 3.50 | 3.30 | - |
| `eval_pet_011` | standard | pet_real | -0.067 | +0.60 | 3.80 | 3.20 | - |
| `eval_pet_008` | standard | pet_real | -0.075 | +0.70 | 3.60 | 2.90 | - |

## 3. Patterns by slice axis

Tuned minus best-baseline on the deterministic composite, per group. Negative = fine-tuning hurt this slice.


**`source`**

| Group | n | tuned | best baseline | delta | rubric delta |
|---|---|---|---|---|---|
| `pet_real` | 12 | 0.756 | 0.701 | +0.055 | +0.35 |
| `synthetic` | 28 | 0.708 | 0.584 | +0.124 | +0.12 |

**`ood_vertical`**

| Group | n | tuned | best baseline | delta | rubric delta |
|---|---|---|---|---|---|
| `False` | 24 | 0.716 | 0.645 | +0.072 | +0.12 |
| `True` | 16 | 0.732 | 0.581 | +0.152 | +0.29 |

**`vertical_unseen_in_train`**

| Group | n | tuned | best baseline | delta | rubric delta |
|---|---|---|---|---|---|
| `False` | 12 | 0.676 | 0.588 | +0.088 | -0.10 |
| `True` | 28 | 0.743 | 0.632 | +0.110 | +0.32 |

**`difficulty`**

| Group | n | tuned | best baseline | delta | rubric delta |
|---|---|---|---|---|---|
| `contradictory` | 7 | 0.714 | 0.547 | +0.167 | +0.14 |
| `standard` | 20 | 0.751 | 0.688 | +0.063 | +0.01 |
| `vague` | 13 | 0.683 | 0.551 | +0.131 | +0.50 |

## 4. Side-by-side detail


### `eval_syn_012` - private tutoring / refunds/returns (vague, synthetic)

Tuned rubric 1.00 | det composite 0.200 vs best baseline 0.586

- **Judge preferred base_fewshot**: unparseable output
- **Judge preferred base_zeroshot**: unparseable output

<details><summary>Input description</summary>

```
REFUNDS OF PREPAID LESSON BLOCKS
Note held in the business's shared drive

Families may purchase lessons in blocks, typically of ten, paid in advance at a discount against the single-session rate. Requests arise for refunds of unused sessions where a student stops, moves school, or the family's circumstances change.

Current handling, as far as it could be established:

A request is made, usually by message. It is dealt with by whoever receives it. The basis on which a refund is calculated was not stated consistently: descriptions given included refunding the unused sessions at the discounted rate, refunding at the discounted rate less an administration amount, refunding the unused sessions at the full single-session rate having recalculated the used sessions at the discount, and refunding nothing where the block was bought more than a term ago.

No written terms covering block purchases were produced. The website was said to mention blocks but the wording was not located during the session.

It was not established who authorises a refund, whether any threshold applies, how refunds are paid, or where they are recorded. Nobody was able to say how many were made in the last year or their total value.

Sessions used against a block are tracked, but the record of this could not be identified with certainty.

Where a refund is declined, what the family is told, and whether the decis ...[truncated]
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - A request for a refund is received via various channels
  - The request is handled by the receiver of the request
  - Refund calculations vary based on different methods described inconsistently
  - Refunds are processed without clear documentation of terms or procedures
  - No written terms covering block purchases exist
  - _(+4 more)_

**`ai_agent_steps`**
  - An AI agent can generate standardized refund forms based on pre-defined templates
  - An AI agent can calculate refunds using agreed-upon methods and provide clear instructions
  - An AI agent can review and validate refund calculations and decisions
  - An AI agent can communicate with families regarding declined refunds and provide appeals mechanisms
  - An AI agent can maintain and update records of refunds and usage across multiple platforms

**`bottlenecks_and_risks`**
  - Variability in refund calculation methods makes it difficult to track consistent processes
  - Lack of written terms complicates understanding of refund policies
  - Unclear roles and responsibilities for authorizing refunds lead to inconsistent decisions
  - No documentation of refund amounts or thresholds increases risk of errors
  - Difficulty in identifying usage records linking to specific blocks reduces transparency
  - _(+2 more)_

**Tuned**

_(unparseable)_

**Reference**

**`current_process`**
  - A family buys a block of lessons, typically ten, paid in advance at a discount against the single-session rate
  - The family stops and requests a refund, usually by message
  - The request is dealt with by whoever receives it
  - Sessions used against a block are tracked, though the record of this could not be identified with certainty

**`ai_agent_steps`**
  - An AI agent can calculate the refund from the tracked sessions used against the published terms
  - An AI agent can produce the written explanation of the calculation for the family
  - An AI agent can route the request to the correct approver against the threshold
  - An AI agent can report on refund volume, value and reason

**`bottlenecks_and_risks`**
  - Four different calculation bases were described for the same situation - refunding unused sessions at the discounted rate, at the discounted rate less an administration amount, recalculating used sessions at full rate first, or refunding nothing after a term - so families receive materially different amounts for identical circumstances
  - No written terms covering block purchases were produced; the website was said to mention blocks but the wording could not be located during the session
  - It was not established who authorises a refund, whether any threshold applies, how refunds are paid, or where they are recorded
  - Nobody could say how many refunds were made in the last year or their total value
  - The record of sessions used against a block could not be identified with certainty, so the basic input to any calculation is uncertain
  - _(+1 more)_

### `eval_pet_009` - corporate finance / expense report approval (standard, pet_real)

Tuned rubric 2.80 | det composite 0.747 vs best baseline 0.797

- **Judge preferred base_zeroshot**: Analysis 2 correctly identifies the trigger, participants, and flow of the as-is process, whereas Analysis 1 introduces hallucinations and factual errors about the process steps.

<details><summary>Input description</summary>

```
An employee purchases a product or service he requires. For instance, a sales person on a trip rents a car. The employee submits an expense report with a list of items, along with the receipts for each item. A supervisor reviews the expense report and approves or rejects the report. Since the company has expense rules, there are circumstances where the supervisor can accept or reject the report upon first inspection. These rules could be automated, to reduce the workload on the supervisor. If the supervisor rejects the report, the employee, who submitted it, is given a chance to edit it, for example to correct errors or better describe an expense. If the supervisor approves the report, it goes to the treasurer. The treasurer checks that all the receipts have been submitted and match the items on the list. If all is in order, the treasurer accepts the expenses for processing (including, e.g., payment or refund, and accounting). If receipts are missing or do not match the report, he sends it back to the employee. If a report returns to the employee for corrections, it must again go to a supervisor, even if the supervisor previously approved the report. If the treasurer accepts the expenses for processing, the report moves to an automatic activity that links to a payment system. The process waits for the payment confirmation. After the payment is confirmed, the process ends.
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - Employee submits an expense report
  - Supervisor reviews the report and either approves or rejects it
  - If rejected, employee edits the report
  - If approved, report goes to Treasurer
  - Treasurer verifies receipts and matches them to the report
  - _(+4 more)_

**`ai_agent_steps`**
  - AI agents scan and verify receipts in real-time
  - AI agents provide immediate rejection or correction suggestions
  - AI agents use machine learning to detect patterns and suggest corrective actions
  - AI agents centralize the entire expense process within a single system
  - AI agents automate the payment confirmation step

**`bottlenecks_and_risks`**
  - Manual review by Supervisor increases workload and potential for error
  - Complexity in verifying receipts and matching them to the report increases risk of discrepancies
  - Rejection rate varies based on individual supervisor discretion, leading to inconsistent outcomes
  - Supervisor needs to manually check receipts and report completeness, increasing turnaround time
  - Multiple rounds of editing required due to initial rejection, adding complexity and delay
  - _(+1 more)_

**Tuned**

**`current_process`**
  - An employee submits an expense report listing items and their receipts
  - A supervisor reviews the report and either approves or rejects it
  - If rejected, the employee is given a chance to edit the report and resubmit
  - If approved, the report goes to the treasurer for checking
  - The treasurer verifies that all receipts have been submitted and match the items on the list
  - _(+3 more)_

**`ai_agent_steps`**
  - An AI agent can flag receipts that do not match the report items during the first inspection stage
  - An AI agent can reconcile receipts against the report items and flag unmatched or incomplete entries
  - An AI agent can produce the weekly discrepancy report and escalate recurring patterns
  - An AI agent can draft the payment instruction from the approved report and send it to the payment system

**`bottlenecks_and_risks`**
  - Approval depends entirely on one person, so the same error can recur repeatedly without being caught until someone else notices
  - Rejection at first inspection means the report cannot be corrected once submitted, so the error persists
  - Receipts missing or mismatched stop the report from moving to acceptance, requiring re-submission
  - Reports returning to the employee for corrections restart the whole cycle, with no feedback loop
  - Payment confirmation is required but does not complete the process, so the transaction remains unrecorded
  - _(+1 more)_

**Reference**

**`current_process`**
  - An employee purchases a product or service and submits an expense report with a list of items and the receipts
  - A supervisor reviews the report and approves or rejects it, with company expense rules meaning some reports can be accepted or rejected on first inspection
  - If the supervisor rejects, the employee is given a chance to edit it, for example to correct errors or better describe an expense
  - If the supervisor approves, it goes to the treasurer, who checks that all receipts have been submitted and match the items on the list
  - If all is in order the treasurer accepts the expenses for processing, including payment or refund and accounting
  - _(+3 more)_

**`ai_agent_steps`**
  - An AI agent can validate the report against the company expense rules at submission and accept or flag it, reducing the supervisor's workload as the description anticipates
  - An AI agent can match receipts to line items at submission and flag missing or mismatched receipts before the report reaches the supervisor
  - An AI agent can monitor payment confirmations and chase those that do not arrive
  - An AI agent can report on cycle time, rejection reasons and policy exceptions

**`bottlenecks_and_risks`**
  - A report sent back by the treasurer must go through the supervisor again even where the supervisor already approved it, so a receipt mismatch costs a full second approval cycle
  - The company's expense rules are applied manually by the supervisor on first inspection, and the description itself notes these rules could be automated to reduce the supervisor's workload
  - Receipt checking sits entirely with the treasurer at the end of the chain, so a missing receipt is discovered only after supervisor approval
  - There are two rejection loops back to the employee - from the supervisor and from the treasurer - with no described limit or escalation
  - The process waits for payment confirmation with no described action where confirmation does not arrive
  - _(+1 more)_

_Reference is `model_generated_unverified` (PET slice): treat as a comparison point, not ground truth._

### `eval_syn_005` - gym / customer support (standard, synthetic)

Tuned rubric 2.90 | det composite 0.734 vs best baseline 0.736

<details><summary>Input description</summary>

```
Call notes - health and fitness club, member communications

- The club has a members' Facebook group with roughly 1,400 members. It was set up during a period of closure and was never wound down.
- Members post questions in it constantly: class timetable changes, is the pool open, is the sauna fixed, lost property, is anyone selling a spare place at the spin bike.
- Also complaints, sometimes at length and with photographs.
- Nobody is assigned to monitor or answer it. Three staff are admins - the fitness manager, a class instructor and a former duty manager who left last year and has not been removed.
- Answers are given by whichever member of staff happens to see a post on their own phone, in their own time. Instructors answer questions about the timetable that turn out to be wrong.
- Members answer each other, often incorrectly. A member told twenty others the pool was shut for a fortnight when it was two days.
- Nothing posted there reaches the club's actual systems. Lost property reports, maintenance issues and complaints raised in the group are not logged anywhere.
- The club also has an email address and a phone; posts in the group are not redirected to either.
- Response time, volume and themes are not measured.
- The owner reads it "occasionally, and it puts me in a bad mood".
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - Members post questions or complaints in the Facebook group
  - Fitness Manager, Class Instructor, and Former Duty Manager respond individually
  - Responses are given by whichever staff member sees the post on their own phone
  - Incorrect answers occur frequently due to lack of monitoring
  - Lost property reports, maintenance issues, and complaints remain unlogged
  - _(+1 more)_

**`ai_agent_steps`**
  - An AI agent can monitor the Facebook group and forward relevant messages to designated staff
  - An AI agent can analyze the frequency and content of group messages to identify trends and escalate critical issues
  - An AI agent can automate logging of lost property reports, maintenance issues, and complaints
  - An AI agent can generate summary reports on group activity metrics

**`bottlenecks_and_risks`**
  - Lack of monitoring leads to inconsistent and incorrect responses
  - Volume of queries exceeds staff capacity
  - Member-to-member communication results in misinformation spread
  - Unlogged issues lead to unresolved problems
  - Owner's infrequent readings do not provide actionable insights
  - _(+1 more)_

**Tuned**

**`current_process`**
  - Members post questions and complaints in the club's Facebook members' group
  - Nobody monitors or answers it; three admin staff handle them on their own phones in their own time
  - Instructors answer questions about the timetable that turn out to be wrong
  - Lost property reports, maintenance issues and complaints raised in the group are not logged anywhere
  - Nothing posted there reaches the club's actual systems such as lost property, maintenance or complaint logs

**`ai_agent_steps`**
  - An AI agent can flag posts by theme and reporter before they reach a member
  - An AI agent can draft responses from recorded FAQs and recent enquiries
  - An AI agent can escalate recurring or serious complaints to a named person
  - An AI agent can report on volume, themes and resolution rate

**`bottlenecks_and_risks`**
  - No one owns the group so nobody takes responsibility for its content or quality
  - Instructors answer questions about the timetable that turn out to be wrong, which means the group becomes unreliable
  - Members answer each other, often incorrectly, so the group propagates misinformation
  - Nothing posted there reaches the club's actual systems, so lost property, maintenance and complaint records remain unrecorded
  - Response time, volume and themes are not measured, so nothing can be improved
  - _(+1 more)_

**Reference**

**`current_process`**
  - A member posts a question or complaint in the Facebook group
  - Nobody is assigned to monitor or answer it
  - Answers are given by whichever member of staff happens to see the post on their own phone, in their own time
  - Members also answer each other
  - Nothing posted reaches the club's actual systems - lost property, maintenance issues and complaints raised in the group are not logged anywhere

**`ai_agent_steps`**
  - An AI agent can monitor the group and alert the named owner to posts requiring a response, particularly complaints and facility questions
  - An AI agent can create logged records in the club's systems from group posts about lost property or maintenance
  - An AI agent can draft responses for the named owner to review and post
  - An AI agent can classify posts by theme and report volume and response times

**`bottlenecks_and_risks`**
  - A group of 1,400 members set up during a closure period was never wound down and now carries live operational questions with nobody assigned to it
  - A former duty manager who left last year remains an admin, so someone outside the business holds administrative control of a member-facing channel
  - Staff answer on their own phones in their own time, and instructors have given wrong answers about the timetable
  - Members answer each other incorrectly - one told twenty others the pool was shut for a fortnight when it was two days
  - Lost property, maintenance issues and complaints raised in the group never reach the club's systems, so they are simply lost
  - _(+2 more)_

### `eval_pet_007` - mental health care / patient intake (standard, pet_real)

Tuned rubric 3.20 | det composite 0.779 vs best baseline 0.662

<details><summary>Input description</summary>

```
The intake workflow starts with a notice by telephone at the secretarial office of the mental health care institute. This notice is done by the family doctor of somebody who is in need of mental treatment. The secretarial worker inquires after the name and residence of the patient. On the basis of this information, the doctor is put through to the nursing officer responsible for the part of the region that the patient lives in. The nursing officer makes a full inquiry into the mental, health, and social state of the patient in question. This information is recorded on a registration form. At the end of the conversation, this form is handed in at the secretarial office of the institute. Here, the information on the form is stored in the information system and subsequently printed. For new patients, a patient file is created. The registration form as well as the print from the information system are stored in the patient file. Patient files are kept at the secretarial office and may not leave the building. At the secretarial office, two registration cards are produced for respectively the future first and second intaker of the patient. The registration card contains a set of basic patient data. The new patient is added on the list of new notices. Halfway the week, at Wednesday, a staff meeting of the entire medical team takes place. The medical team consists of social-medical wor ...[truncated]
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - The family doctor calls the secretarial office with a patient needing mental treatment.
  - The secretarial worker inquires about the patient's name and residence.
  - The nurse interviews the patient and fills out a registration form.
  - The registration form is sent to the secretarial office.
  - The secretarial office prints the form and stores it in the information system.
  - _(+4 more)_

**`ai_agent_steps`**
  - An AI agent can automate the call center process and streamline communication.
  - An AI agent can generate standardized interview questions and forms.
  - An AI agent can monitor and alert on bottlenecks in the current process.
  - An AI agent can analyze patterns in patient behavior and suggest improvement areas.
  - An AI agent can create automated reports for treatment planning.

**`bottlenecks_and_risks`**
  - Manual processes slow down the intake process.
  - Lack of standardized procedures leads to inconsistent patient handling.
  - Incomplete documentation increases risk of errors.
  - Communication breakdowns among team members lead to inefficiencies.

**Tuned**

**`current_process`**
  - A family doctor telephones the secretarial office of the mental health care institute to register a new patient
  - The secretarial worker inquires after the name and residence of the patient
  - On the basis of this information, the doctor is put through to the nursing officer responsible for the part of the region that the patient lives in
  - The nursing officer makes a full inquiry into the mental, health, and social state of the patient and records this on a registration form
  - At the end of the conversation, the form is handed in at the secretarial office of the institute
  - _(+12 more)_

**`ai_agent_steps`**
  - An AI agent can generate the assignment list from the intake decision and the team leader's roster
  - An AI agent can issue the first and second intaker cards and send the confirmation messages
  - An AI agent can flag patients whose intake was incomplete because the file was not received
  - An AI agent can produce the monthly intake report by region and role showing completion rate and average wait time

**`bottlenecks_and_risks`**
  - Assigning intakers without taking into account expertise, region responsibility, earlier contacts, and case load means some patients receive no intake at all while others get more than one
  - Printing the registration form and then storing it in the information system creates duplicate records and slows down access
  - The first intaker keeps the registration with him at times when visiting the patient and in his close proximity when he is at the office, so there is no centralised record of the intake
  - The second intaker does not meet until the medical information of the physician has arrived, so the intake is incomplete before the treatment plan is written
  - Sending letters to family doctors requesting copies of medical files requires the secretary to contact them twice, once to request and once to confirm receipt
  - _(+2 more)_

**Reference**

**`current_process`**
  - The family doctor telephones the secretarial office; the secretarial worker takes the patient's name and residence and puts the doctor through to the nursing officer for that region
  - The nursing officer makes a full inquiry into the patient's mental, health and social state, recorded on a registration form handed in at the secretarial office
  - The information is stored in the information system and printed; for new patients a patient file is created holding the registration form and the print, and two registration cards are produced for the future first and second intakers
  - The new patient is added to the list of new notices
  - At the Wednesday staff meeting the team-leader assigns each new patient to a social-medical worker as first intaker and a physician as second intaker, taking into account expertise, region, earlier contacts and case load, and determines whether the medical file is required
  - _(+3 more)_

**`ai_agent_steps`**
  - An AI agent can request the copy of the medical file from the family doctor and chase it against a deadline, unblocking the second intaker
  - An AI agent can propose intaker assignments against the team-leader's criteria - expertise, region, earlier contacts and case load - for approval
  - An AI agent can transcribe physicians' dictated observations into the patient record for review
  - An AI agent can track each patient's intake stage and report elapsed time from notice to treatment plan

**`bottlenecks_and_risks`**
  - Assignment happens only at the Wednesday staff meeting, so a notice received on a Thursday waits nearly a week before an intaker is allocated
  - Where the medical file is required, the second intaker cannot plan a first meeting until a copy arrives from the family doctor by post, and the process contains no chasing step or deadline for that copy
  - Patient files are paper and may not leave the building, so an intaker visiting a patient carries only a registration card and cannot consult the file
  - Physicians record observations on dictaphone tapes that the secretarial office must type out before they reach the patient file, adding a transcription delay to the second intaker's contribution
  - The first intaker's additional observations are kept in a personal notebook and only a copy is later placed in the file, so the primary record sits outside the institute's system
  - _(+2 more)_

_Reference is `model_generated_unverified` (PET slice): treat as a comparison point, not ground truth._

### `eval_syn_007` - plumbing/trades / supplier orders (contradictory, synthetic)

Tuned rubric 2.70 | det composite 0.610 vs best baseline 0.522

<details><summary>Input description</summary>

```
[WhatsApp - "Office" group, plumbing firm]

Kirsty: whose is the £412 at Plumbase yesterday
Deano: not mine
Baz: might be mine, was that the Whitmore Road boiler
Kirsty: there's no job on it, just an account number
Deano: there never is
Kirsty: Dean you told me last week that everyone rings the job number through before they buy
Deano: they're supposed to
Kirsty: you said it was happening
Deano: I said I'd told them. I didn't say they did it
Kirsty: right. so for the statement I've got 61 lines and I can allocate about 20
Baz: just split it over the jobs that week
Kirsty: that's what I did in March and then we underbilled the Whitmore job by £300
Deano: how do you know
Kirsty: because I don't, that's the point
Baz: the merchant can email the tickets
Kirsty: they do email the tickets. the tickets say who collected and what. they don't say what job
Deano: write it on the ticket lads
Baz: 👍
Kirsty: you said that in January too
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - Customers purchase goods from Plumbase without providing a job number
  - Baz receives the purchase orders and collects the goods
  - Baz writes down the details of the transaction in the internal database
  - The merchant emails the ticket information to Baz
  - Baz matches the ticket information with the internal database entries
  - _(+2 more)_

**`ai_agent_steps`**
  - An AI agent can remind customers to provide job numbers during the purchasing process
  - An AI agent can automatically generate and send job numbers via the merchants' email system
  - An AI agent can check the accuracy of job numbers collected by the billing clerk
  - An AI agent can alert employees to handle missing job numbers promptly
  - An AI agent can suggest updates to the job number collection policy based on historical data

**`bottlenecks_and_risks`**
  - Customers often forget to provide job numbers, leading to incorrect allocations
  - Baz relies on memory to recall job numbers, increasing the risk of errors
  - The merchant's email system occasionally fails to deliver tickets, causing delays
  - The internal database lacks comprehensive job tracking, making it difficult to trace transactions
  - The lack of job numbers leads to underbilling or overbilling issues
  - _(+1 more)_

**Tuned**

**`current_process`**
  - An invoice arrives from Plumbase showing a customer has been charged £412
  - Kirsty asks Deano whether he owns the job, and Baz says it might have been his
  - Kirsty checks the Plumbase job list and finds nothing on the account number
  - Kirsty allocates about 20 lines of the 61 line statement
  - Baz proposes splitting the allocation over the jobs that week
  - _(+1 more)_

**`ai_agent_steps`**
  - An AI agent can match invoices to jobs based on the recorded collection details and flag mismatches
  - An AI agent can produce the weekly allocation report and flag customers with high discrepancy rates
  - An AI agent can chase unpaid invoices and escalate those flagged as likely due to a known error
  - An AI agent can analyse historical allocation patterns to identify customers with consistently incorrect billing

**`bottlenecks_and_risks`**
  - Invoices arrive without a job reference, so allocating between jobs requires guesswork
  - Allocations are made manually against a paper list, so the same mistake repeats month after month
  - There is no way to confirm who collected the payment, so the allocation cannot be verified
  - The merchant emails the tickets but does not record who collected or what job, so the allocation relies on memory
  - The same error happened in March when the Whitmore job was underbilled by £300, and the cause remains unknown
  - _(+1 more)_

**Reference**

**`current_process`**
  - Engineers buy parts on the merchant account
  - Engineers are supposed to ring the job number through before buying, but do not
  - The merchant emails tickets showing who collected and what, but not which job
  - The monthly statement arrives with lines carrying an account number and no job reference
  - Kirsty attempts to allocate the lines; of 61 she can allocate about 20
  - _(+1 more)_

**`ai_agent_steps`**
  - An AI agent can match merchant statement lines and emailed tickets to jobs by job reference, date, engineer and part type
  - An AI agent can produce the exception list of unallocated lines for Kirsty rather than her working all 61
  - An AI agent can flag jobs about to be invoiced with unallocated parts spend, preventing underbilling
  - An AI agent can report unallocated spend by engineer to evidence whether the control is operating

**`bottlenecks_and_risks`**
  - Deano's position is contradictory - he told Kirsty last week that everyone rings the job number through before buying, and now says he only said he had told them, not that they did it - so the control was reported as operating when it was not
  - Of 61 statement lines, about 20 can be allocated, so roughly two thirds of parts spend cannot be attributed to a job
  - Splitting unallocated spend across the week's jobs produced an underbilling of £300 on the Whitmore job in March, and Kirsty's point is that she cannot even know when it happens
  - The merchant tickets record who collected and what but not the job, so the available data cannot close the gap
  - The instruction to write the job on the ticket was given in January and again now, with no change in behaviour and no enforcement
  - _(+1 more)_

### `eval_syn_028` - car repair garage / customer support (standard, synthetic)

Tuned rubric 2.70 | det composite 0.761 vs best baseline 0.672

<details><summary>Input description</summary>

```
Call notes - independent garage, customer communication and courtesy cars

- The garage has three courtesy cars. Demand exceeds supply in most weeks.
- Booking: a customer asks for one when they book the job in. The receptionist writes the registration and the date in a diary. There is no check that the car is back from the previous customer.
- Cars are returned with varying fuel levels and are not always cleaned or checked between users. Damage found is often not attributable because no condition check is done at handover.
- Insurance: drivers are added to the trade policy by phone. The receptionist said this "usually" happens before the customer drives away.
- Job progress: a customer rings to ask how their car is doing. The receptionist puts them on hold, walks into the workshop and shouts to the technician over the noise, then comes back with an answer.
- Where the technician is under a car or out on a road test, the customer is told someone will ring back. The callback is written on a sticky note.
- Completion: the customer is rung when the car is ready. Whoever is on reception does this from the job cards in the "done" pile. Cars have been finished for a day before the customer was told.
- Nothing is recorded about what the customer was told or when.
- No text or email updates are sent. The garage's management system can send them; nobody has set it up.
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - A customer books a service and receives a registration number and booking date.
  - The receptionist writes the registration and booking date in the diary.
  - There is no verification that the car is available or has been returned.
  - Cars are returned with varying fuel levels and lack of cleaning/checks.
  - Drivers are added to the trade policy via phone call.
  - _(+4 more)_

**`ai_agent_steps`**
  - An AI agent can verify the availability of courtesy cars based on reservations.
  - An AI agent can monitor and log inspection results of returned cars.
  - An AI agent can alert staff when a customer inquiry needs attention.
  - An AI agent can generate automated updates in the management system.
  - An AI agent can provide real-time feedback on customer inquiries through communication channels.

**`bottlenecks_and_risks`**
  - Demand exceeds supply due to insufficient courtesy cars.
  - Varying fuel levels and lack of cleaning/checks indicate potential damage.
  - Damage attributed to no condition checks at handover.
  - Insurance drivers are added without confirmation.
  - Incomplete documentation of customer inquiries and statuses.
  - _(+2 more)_

**Tuned**

**`current_process`**
  - A customer books a job and requests a courtesy car
  - The receptionist writes the registration and the date in a diary without checking that the car is back from the previous customer
  - Cars are returned with varying fuel levels and are not always cleaned or checked between users
  - Drivers are added to the trade policy by phone 'usually' before the customer drives away
  - Job progress is asked for by ringing the reception desk
  - _(+3 more)_

**`ai_agent_steps`**
  - An AI agent can chase overdue cars and flag those past the due date
  - An AI agent can issue the confirmation message and schedule the pre-handover inspection
  - An AI agent can route job progress queries to the correct person and escalate unsolvable ones
  - An AI agent can log completion and produce the promised-to-be-received report

**`bottlenecks_and_risks`**
  - Demand exceeds supply in most weeks, so the diary entry cannot catch every request
  - No check is made that the car is back from the previous customer, so damage found after use is unattributable
  - Fuel level, cleanliness and condition checks are never done at handover, so damage discovered later is invisible
  - Drivers are added to the trade policy by phone usually before the customer drives away, so insurance cover is incomplete
  - Job progress is asked for by holding the line and shouting to the technician, which means the customer hears nothing until completion
  - _(+2 more)_

**Reference**

**`current_process`**
  - A customer asks for a courtesy car when booking the job in and the receptionist writes the registration and date in a diary
  - Drivers are added to the trade policy by phone, which 'usually' happens before the customer drives away
  - A customer rings to ask how their vehicle is doing; the receptionist puts them on hold, walks into the workshop and shouts to the technician over the noise, then returns with an answer
  - Where the technician is under a car or on a road test, the customer is told someone will ring back and this is written on a sticky note
  - When the vehicle is ready the receptionist rings the customer from the job cards in the 'done' pile

**`ai_agent_steps`**
  - An AI agent can answer progress enquiries from the job status in the system, removing the need to interrupt technicians
  - An AI agent can send automated status updates and the vehicle-ready notification
  - An AI agent can flag courtesy cars booked out where the previous customer has not returned the vehicle, or where the driver is not yet on the policy
  - An AI agent can track promised callbacks and escalate them, replacing sticky notes

**`bottlenecks_and_risks`**
  - Adding drivers to the trade policy 'usually' happens before the customer drives away, which means sometimes it does not - a customer may be driving an uninsured vehicle
  - There is no check that a courtesy car is back from the previous customer before it is booked out again, so demand exceeding supply is managed by hope
  - No condition check is done at handover, so damage found afterwards cannot be attributed and fuel levels vary
  - Every progress enquiry requires the receptionist to physically interrupt a technician, so both the customer and the workshop lose time
  - Callbacks are written on sticky notes, so a promised call depends on a note not being lost
  - _(+3 more)_

### `eval_pet_012` - financial services / account defaulter reporting (vague, pet_real)

Tuned rubric 2.80 | det composite 0.753 vs best baseline 0.689

<details><summary>Input description</summary>

```
Every weekday morning, the database is backed up and then it is checked to see whether the Account Defaulter table has new records. If no new records are found, then the process should check the CRM system to see whether new returns have been filed. If new returns exist, then register all defaulting accounts and customers. If the defaulting client codes have not been previously advised, produce another table of defaulting accounts and send to account management. All of this must be completed by 2:30 pm, if it is not, then an alert should be sent to the supervisor. Once the new defaulting account report has been completed, check the CRM system to see whether new returns have been filed. If new returns have been filed, reconcile with the existing account defaulters table. This must be completed by 4:0 pm otherwise a supervisor should be sent a message.
```

</details>

| | |
|---|---|


**Base 2-shot**

**`current_process`**
  - Back up the database
  - Check the Account Defaulter table for new records
  - If no new records are found, check the CRM system for new returns
  - If new returns exist, register all defaulting accounts and customers
  - If defaulting client codes have not been previously advised, produce another table of defaulting accounts and send to account management
  - _(+5 more)_

**`ai_agent_steps`**
  _(empty)_

**`bottlenecks_and_risks`**
  - Manual checks take longer than automated processes, leading to potential delays in completing tasks by the required deadlines
  - Failure to complete tasks within the set timeframe results in alerts and messages being sent to the supervisor
  - Potential oversight in verifying new returns in the CRM system due to lack of automation
  - Risk of missing key information during manual registration of defaulting accounts and customers
  - Lack of clear communication channels between different departments regarding task priorities and deadlines

**Tuned**

**`current_process`**
  - Back up the database at 8 am each day
  - Check the Account Defaulter table for new records
  - If no new records are found, check the CRM system for new returns
  - Where new returns exist, register all defaulting accounts and customers
  - Where defaulting client codes have not been previously advised, produce another table of defaulting accounts and send to account management
  - _(+3 more)_

**`ai_agent_steps`**
  - An AI agent can capture returns from the CRM system during the nightly backup run and build the reconciled defaulters view
  - An AI agent can identify exceptions between the two lists and flag them for review
  - An AI agent can generate the weekly false positive and missed recovery reports
  - An AI agent can draft the client notification messages for approval before sending

**`bottlenecks_and_risks`**
  - There is no trigger other than finding no new records in the Account Defaulter table, so the work starts when nothing needs doing, which wastes time on unactionable tasks
  - Checking the CRM system for new returns requires looking through files that were not captured during the daily backup, so the risk is missing actual returns
  - Producing another table of defaulting accounts without first checking the existing list means double-counting, which can cause duplicate debt recovery efforts
  - Reconciliation depends on the existing defaulters table being complete, but there is no control over its completeness beyond the date limit
  - A supervisor is sent a message only when the reconciliation fails, so the person responsible does not know they failed until it is too late
  - _(+1 more)_

**Reference**

**`current_process`**
  - Every weekday morning the database is backed up
  - It is then checked to see whether the Account Defaulter table has new records
  - If no new records are found, the CRM system is checked to see whether new returns have been filed
  - If new returns exist, all defaulting accounts and customers are registered
  - If the defaulting client codes have not been previously advised, another table of defaulting accounts is produced and sent to account management
  - _(+2 more)_

**`ai_agent_steps`**
  - An AI agent can run the daily checks of the Account Defaulter table and the CRM system for newly filed returns and produce the draft table of defaulting accounts
  - An AI agent can monitor progress against the 2:30 pm and 4:00 pm deadlines and escalate to the supervisor before they are breached rather than after
  - An AI agent can reconcile newly filed returns against the existing account defaulters table and flag mismatches
  - An AI agent can report on cycle completion times, deadline breaches and defaulter volumes

**`bottlenecks_and_risks`**
  - No owner is identified for any step, so it cannot be established who performs the checks or who is accountable when a deadline is missed
  - The CRM system is checked for newly filed returns twice in the same day, before 2:30 pm and again before 4:00 pm, duplicating the same check within a few hours
  - Missing either deadline produces only an alert or a message to the supervisor, with no described action or remedy, so the control detects lateness without correcting it
  - The path through the process depends on whether new records are found in the Account Defaulter table, and the description does not state what happens on the alternative branch, leaving the flow ambiguous
  - Whether defaulting client codes have been previously advised gates the production of the report, but how that is determined is not described
  - _(+1 more)_

_Reference is `model_generated_unverified` (PET slice): treat as a comparison point, not ground truth._

---

# Written analysis

Hand-written interpretation of the machine-found candidates above. Kept in a
separate file (`analysis_notes.md`) and appended by
`scripts/09_failure_analysis.py`, so regenerating the report never destroys it.

## The one catastrophic failure: `eval_syn_012`

The only unparseable output in 120 generations, and the single worst regression
(tuned rubric 1.00 vs base 3.60; lost pairwise to *both* baselines). It is worth
reading the actual break:

```
"The basis on which a refund is calculated was not stated consistently: "
    + "refunding the unused sessions at the discounted rate",
    + "refunding at the discounted rate less an administration amount",
```

The model emitted **Python-style string concatenation inside JSON**. It was not
truncated — it generated 717 tokens of a 2048 budget and closed the object
cleanly at the end.

Why here? This record is `vague`, and the input describes a refund policy stated
three inconsistent ways. The model tried to enumerate the competing alternatives
inside a single list item, and reached for a code idiom to join them. Nothing in
120 training examples demonstrates "the input contradicts itself, enumerate the
options", so under that pressure it fell back on a pretraining habit.

The lesson is about the *depth* of what LoRA learned. Strict-JSON compliance went
0% → 98%, but that discipline is shallow: it survives ordinary inputs and breaks
when the content pushes the model toward a structure it never saw supervised.
A schema-constrained decoder would eliminate this entire failure mode and is the
cheapest robustness win available (see SUMMARY v0.2).

## The field-level regressions: `bottlenecks_and_risks` and `human_approvals_controls`

These are the only two fields where tuned scores *below* a baseline:

| Field | Base 0-shot | Base 2-shot | Tuned |
|---|---|---|---|
| `bottlenecks_and_risks` | 3.32 | 3.19 | **2.77** |
| `human_approvals_controls` | 2.34 | 2.53 | **2.35** |

The obvious hypothesis — that tuned under-generates here — is **wrong**, and the
measurements say so. On `bottlenecks_and_risks` tuned produces 6.0 items of 19.4
words against a reference of 6.3 items of 23.9 words; the 2-shot baseline manages
5.5 items of 10.8 words. Tuned is *closer* to reference shape on both axes.

Reading an actual regressed record (`eval_syn_005`) shows what is really
happening:

- **Base 2-shot:** "Lack of monitoring leads to inconsistent and incorrect
  responses" — terse, generic, but safely hedged.
- **Tuned:** "No one owns the group so nobody takes responsibility for its
  content or quality" — fluent, longer, causal, confident.
- **Reference:** "A group of 1,400 members set up during a closure period was
  never wound down and now carries live operational questions with nobody
  assigned to it" / "A former duty manager who left last year remains an admin,
  so someone outside the business holds administrative control".

The reference's value is **evidential specificity**: the 1,400 members, the
ex-employee still holding admin rights. Tuned has learned the reference's
*rhetorical form* — the long "X, so Y" causal construction — without its
*anchoring in named facts from the input*. It writes confident analysis-shaped
prose that is less tied to evidence than it sounds.

That is a coherent story for why a judge instructed to reward grounding marks it
down relative to a terse baseline: confident-but-unanchored claims are penalised
harder than vague-but-safe ones. **Stated as the most plausible reading, not a
demonstrated one** — it rests on one inspected record against a 40-record
aggregate, and the two regressions are small (-0.42 and -0.18 on a 1-5 scale).

It is also the expected failure mode for 120 examples: style is cheap to learn
and specificity is not. These two fields are the most open-ended reasoning
targets in the schema, so they are exactly where form-without-substance shows up
first.

## Where fine-tuning helped least: seen verticals

The derived `vertical_unseen_in_train` axis produces the only negative rubric
slice in the whole analysis:

| Slice | n | det delta | rubric delta |
|---|---|---|---|
| vertical **seen** in train | 12 | +0.088 | **-0.10** |
| vertical **unseen** in train | 28 | +0.110 | +0.32 |

Fine-tuning helped *least* on the verticals it actually trained on. That is
counter-intuitive and worth stating plainly rather than smoothing over.

The likely explanation is a ceiling effect rather than damage: the 12 seen-vertical
records are the in-domain synthetic ones, where the baselines already performed
best (base composite 0.588 vs 0.632 on unseen), so there was less headroom. The
gains concentrate where the baseline was weakest — vague inputs (+0.50 rubric)
and contradictory inputs (+0.14 det composite from a much lower base).

Note this slice is **invisible** under the delivered `ood_vertical` flag, which
marks all 12 PET records `False` despite every PET vertical being unseen in
training. Under that flag alone the analysis would have shown a uniformly
positive picture. This is the concrete payoff of carrying three independent axes
instead of trusting one delivered label.

## Real text vs synthetic

PET (real, human-written) shows a *smaller* deterministic gain than synthetic
(+0.055 vs +0.124) but a *larger* rubric gain (+0.35 vs +0.12). The two signals
disagree, and neither should be suppressed.

The most likely reason is the reference asymmetry: PET references are
`model_generated_unverified`, so `step_coverage_vs_reference` measures agreement
with an unverified target rather than correctness. That is exactly why pairwise
judging was designated the primary signal for the PET slice — and on pairwise,
tuned wins there too.

The honest summary is that the tuned model transfers to real text, and the
transfer is real but measured less precisely than on synthetic data.


---
_Machine-found sections generated by `scripts/09_failure_analysis.py`; written analysis from `analysis_notes.md`._
