# Review sample

Generated 2026-08-07. 15 stratified examples: 5 train, 5 synthetic eval (hard cases first), 5 PET real-text.

## `train_001` — dental/GP clinic / invoicing/billing

- **split**: train · **style**: chat_transcript · **difficulty**: standard · **ood**: False · **reference**: authored_gold

### Input

```text
[Transcript - practice manager call, Tues 14:10]

CONSULTANT: Talk me through what happens when a patient has private treatment.
DEBORAH (practice manager): So the dentist writes the treatment on the paper chart while the patient's in the chair. Codes, materials, whether it was a composite or an onlay, all of it goes on the chart.
CONSULTANT: And then?
DEBORAH: The charts come to the front desk in a tray at the end of the session. I sit down about half five, six o'clock and type them into SOE - that's our practice management system - and raise the invoice.
CONSULTANT: Same day?
DEBORAH: Supposed to be. If we've had a busy list it slips to the next morning, sometimes Friday if it's been a bad week.
CONSULTANT: What triggers it, the chart arriving?
DEBORAH: Yes, the tray. If a chart doesn't make it into the tray I don't know it exists.
CONSULTANT: Does that happen?
DEBORAH: More than I'd like. Mr Achebe does a lot of implant work and he'll take a chart into his office to write up his notes and I'll find it a fortnight later. That treatment's just not been billed.
CONSULTANT: Who chases payment?
DEBORAH: Me. I run an aged debt report out of SOE on the last Friday of the month and phone anyone over 30 days.
CONSULTANT: Card payments at the desk?
DEBORAH: Most people pay on the day at reception, we've got a Worldpay terminal. It's the plans and the bigger treatments that get invoiced.
CONSULTANT: And the write-up handwriting?
DEBORAH: Honestly some of it I have to go and ask about. That's another delay.
```

### Gold

```json
{
  "objective": "Turn private dental treatment recorded on paper charts into invoices raised in the practice management system, and recover payment on the resulting debt.",
  "trigger": "A completed paper treatment chart arrives in the tray at the front desk at the end of a clinical session.",
  "owner_and_participants": {
    "owner": "Deborah, the practice manager",
    "participants": [
      "Treating dentists including Mr Achebe",
      "Reception (card payments at the desk)",
      "Patients"
    ]
  },
  "inputs_data_required": [
    "Handwritten paper treatment chart (codes, materials, whether composite or onlay)",
    "Aged debt report from SOE",
    "Patient contact details for payment chasing"
  ],
  "systems_involved": [
    "SOE (practice management system)",
    "Worldpay card terminal"
  ],
  "current_process": [
    "Dentist writes treatment, codes and materials onto the paper chart while the patient is in the chair",
    "Charts are placed in a tray at the front desk at the end of the session",
    "Deborah types the charts into SOE at around 17:30-18:00 and raises the invoice",
    "Where the list has been busy, typing slips to the next morning or to Friday",
    "Most patients pay at reception on the day by Worldpay terminal; plans and larger treatments are invoiced",
    "Deborah runs an aged debt report from SOE on the last Friday of the month and phones anyone over 30 days"
  ],
  "bottlenecks_and_risks": [
    "Charts that never reach the tray are invisible to billing - Mr Achebe takes implant charts to his office and they surface a fortnight later, by which time the treatment is unbilled",
    "The tray is the only trigger, so there is no check that every treated patient has been billed",
    "Illegible handwriting forces Deborah to go back and ask the clinician, adding further delay",
    "Billing depends entirely on one person; a busy list pushes invoicing into the following week",
    "Debt chasing happens only once a month, so a slipped invoice plus monthly chasing can leave treatment unpaid for 60+ days"
  ],
  "recommended_improved_process": [
    "Dentist records treatment directly into SOE chairside, or dictates it, so the clinical record is the billing record",
    "SOE automatically raises a draft invoice for every completed private treatment item at the end of each session",
    "A daily exception report lists patients seen with no invoice raised, sent to Deborah each morning",
    "Deborah reviews and releases the day's draft invoices rather than keying them",
    "Invoices are issued the same day with a payment link; card payments at the desk continue to settle in SOE",
    "Automated payment reminders are sent at 7, 14 and 28 days before any human chase",
    "Deborah works a weekly exceptions-and-escalations list instead of a monthly aged debt sweep"
  ],
  "ai_agent_steps": [
    "An AI agent can generate the daily 'seen but not invoiced' exception report by reconciling the SOE appointment list against raised invoices",
    "An AI agent can draft the invoice narrative from the structured treatment items before Deborah reviews and releases it",
    "An AI agent can send and escalate the automated payment reminders at 7, 14 and 28 days and flag non-responders",
    "An AI agent can summarise the weekly exceptions-and-escalations list, ranking debts by age and value"
  ],
  "human_approvals_controls": [
    "Deborah reviews and releases every draft invoice before it is issued",
    "The treating clinician confirms the treatment items recorded in SOE at the end of the session",
    "Write-offs and disputed charges require the practice manager's approval, outside the automated reminder cycle",
    "A human makes contact before any account is referred to formal recovery"
  ]
}
```

---

## `train_013` — gym / customer onboarding

- **split**: train · **style**: chat_transcript · **difficulty**: contradictory · **ood**: False · **reference**: authored_gold

### Input

```text
[WhatsApp thread - "Front Desk" group]

Katie: hiya, quick one - who's actually meant to be booking the new joiner inductions now?
Ryan: front desk does it, always has. we take the name on the clipboard when they sign up and give them a slot with whichever PT is on the floor
Katie: right but Marcus told me last week that inductions are his responsibility as fitness manager and we shouldn't be putting people in without checking with him
Ryan: he says that but he's not here evenings and half our signups are after 6
Katie: so what do i do with the two from Saturday
Ryan: put them on the clipboard, someone will pick them up
Katie: the clipboard by the till? there's like 15 names on it going back to before Christmas
Ryan: yeah nobody's crossed them off. some of those will have been done
Katie: how do we know
Ryan: we don't really. if they come back and complain we rebook them
Katie: do we put anything in Legend? [membership system]
Ryan: no, Legend's just the membership and the direct debit. induction isn't in there
Katie: and the PAR-Q health form?
Ryan: paper, they fill it in at the desk when they sign up, goes in the folder in the office
Katie: does the PT see it before the induction
Ryan: supposed to. usually they just ask them again
Katie: ok. i'll add them to the clipboard and message Marcus too i guess
```

### Gold

```json
{
  "objective": "Book and complete gym inductions for newly joined members so that new joiners receive a supervised introduction before using the equipment.",
  "trigger": "A new member signs up at the front desk and their name is added to the induction clipboard.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "Front desk staff (Katie, Ryan)",
      "Marcus, the fitness manager",
      "Personal trainers on the gym floor",
      "New members"
    ]
  },
  "inputs_data_required": [
    "New member's name",
    "Completed paper PAR-Q health questionnaire",
    "Availability of a PT on the floor"
  ],
  "systems_involved": [
    "Legend (membership and direct debit system)"
  ],
  "current_process": [
    "Member signs up at the front desk and completes a paper PAR-Q health form, which is filed in the office folder",
    "Front desk writes the member's name on the induction clipboard kept by the till",
    "The member is given a slot with whichever personal trainer is on the floor",
    "The PT is expected to read the PAR-Q before the induction, but usually re-asks the questions instead",
    "Nothing is recorded in Legend; Legend holds only membership and direct debit",
    "Names are not crossed off the clipboard, and members who complain are rebooked"
  ],
  "bottlenecks_and_risks": [
    "Ownership is contradictory: Ryan states inductions have always been front desk's responsibility, while Marcus states they are his as fitness manager and should not be booked without him - both descriptions are current and unreconciled",
    "Marcus is not present in the evenings, when roughly half of signups occur, so the stated approval route cannot function",
    "The clipboard holds about 15 names dating back to before Christmas with no completions marked, so it is impossible to tell who has been inducted",
    "Completion is discovered only when a member complains, meaning new joiners may use equipment with no supervised induction",
    "The paper PAR-Q sits in an office folder disconnected from the booking, so health screening information is not reliably seen by the PT delivering the induction"
  ],
  "recommended_improved_process": [
    "Name a single accountable owner for inductions in writing and define a deputy for evenings and weekends",
    "Capture the PAR-Q digitally at signup so it is attached to the member record in Legend",
    "Create induction as a bookable appointment type in Legend against a named trainer and time slot",
    "Auto-invite the member to book their induction at the point of joining, with a reminder if unbooked after 72 hours",
    "Require the trainer to mark the induction complete in Legend, which closes the task",
    "Escalate members still uninducted after 14 days to the fitness manager",
    "Reconcile the historic clipboard backlog once, contacting all 15 names to confirm or rebook"
  ],
  "ai_agent_steps": [
    "An AI agent can send the automated invitation to book an induction at signup and the 72-hour reminder if unbooked",
    "An AI agent can produce the daily list of members uninducted after 14 days for escalation to the fitness manager",
    "An AI agent can flag PAR-Q responses containing health conditions so the trainer is alerted before the session",
    "An AI agent can draft the outreach messages for the historic clipboard backlog reconciliation"
  ],
  "human_approvals_controls": [
    "The fitness manager signs off the written ownership and deputy arrangement",
    "A trainer must review the member's PAR-Q and confirm they have read it before delivering the induction",
    "Any member flagged with a health condition requires the fitness manager's clearance before an unsupervised gym-floor induction",
    "Only the delivering trainer may mark an induction complete in Legend"
  ]
}
```

---

## `train_028` — property management / inventory/stock

- **split**: train · **style**: formal_process_doc · **difficulty**: vague · **ood**: False · **reference**: authored_gold

### Input

```text
INVENTORY AND CHECK-IN
Departmental note, residential lettings

At the start of a tenancy an inventory and schedule of condition is prepared for the property, and the incoming tenant is checked in.

As currently carried out:

The inventory is written by hand onto a pre-printed pad, room by room, describing items and their condition. Meter readings are noted at the back. Photographs are taken on a mobile phone.

The tenant signs the pad at check-in where they are present. Where the tenant is not present, the pad is posted or the tenant is asked to sign later.

The pad copy is brought back to the office. It is understood to be filed, though it was not established where, or by whom, or whether photographs are transferred off the phone at any point.

At the end of the tenancy a check-out is carried out and compared against the inventory in order to justify any deduction from the deposit.

Points noted: it was not possible to establish which phone the photographs from recent check-ins are held on, or whether that phone belongs to the firm. The handwriting on several pads reviewed was not legible. Some pads have no meter readings. There is no standard wording for describing condition, so "good", "fair" and "some marks" are used interchangeably by different staff. No date is recorded on some pads. It is unclear what triggers the check-in being scheduled or who arranges it.
```

### Gold

```json
{
  "objective": "Prepare an inventory and schedule of condition at the start of a tenancy and check the tenant in, so that condition can be compared at check-out.",
  "trigger": "A tenancy is due to start; the input does not establish what triggers the check-in being scheduled or who arranges it.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "Staff who prepare inventories",
      "Incoming tenants"
    ]
  },
  "inputs_data_required": [
    "Pre-printed inventory pad completed room by room",
    "Meter readings noted at the back of the pad",
    "Photographs taken on a mobile phone",
    "The tenant's signature"
  ],
  "systems_involved": [],
  "current_process": [
    "The inventory is written by hand onto a pre-printed pad, room by room, describing items and their condition, with meter readings at the back",
    "Photographs are taken on a mobile phone",
    "The tenant signs the pad at check-in where present; where not present the pad is posted or the tenant is asked to sign later",
    "The pad copy is brought back to the office and is understood to be filed, though where, by whom, and whether photographs are transferred off the phone was not established",
    "At the end of the tenancy a check-out is carried out and compared against the inventory to justify any deposit deduction"
  ],
  "bottlenecks_and_risks": [
    "It could not be established which phone holds recent check-in photographs or whether that phone belongs to the firm, so the primary evidence for deposit deductions may sit on a personal device",
    "Handwriting on several pads reviewed was not legible, which makes the evidence unusable in a deposit dispute",
    "Some pads carry no meter readings and some no date, so utility liability and the timing of the record cannot be proven",
    "There is no standard wording for condition, so 'good', 'fair' and 'some marks' are used interchangeably by different staff and cannot be compared at check-out",
    "Tenants who are not present sign later or not at all, weakening agreement to the record",
    "Nobody could say where pads are filed or by whom, so retrieval at check-out depends on chance"
  ],
  "recommended_improved_process": [
    "Move inventories to a digital app capturing typed condition notes, timestamped and geotagged photographs and meter readings",
    "Use a controlled condition vocabulary with defined terms rather than free text",
    "Store photographs and the report against the property record on firm-owned systems, not personal phones",
    "Capture the tenant's signature digitally at check-in, with a defined process where the tenant cannot attend",
    "Make the check-in a scheduled task with a named owner triggered by the tenancy start date",
    "Generate the check-out report directly against the check-in record, item by item"
  ],
  "ai_agent_steps": [
    "An AI agent can transcribe legacy handwritten pads into the structured digital format for human verification",
    "An AI agent can flag inventories missing meter readings, dates, photographs or a tenant signature before the tenancy starts",
    "An AI agent can compare check-in and check-out photographs and notes item by item and propose a schedule of differences",
    "An AI agent can schedule the check-in task against the tenancy start date and chase the named owner"
  ],
  "human_approvals_controls": [
    "The inventory clerk confirms the digital record is complete and accurate before the tenant signs",
    "The tenant signs the inventory; the record is not deemed agreed without it, or without the defined alternative process",
    "A property manager reviews and approves any proposed deposit deduction before it is put to the tenant",
    "AI-proposed check-in/check-out differences are verified by a person before being used as evidence"
  ]
}
```

---

## `train_031` — independent retail / appointment scheduling

- **split**: train · **style**: chat_transcript · **difficulty**: vague · **ood**: False · **reference**: authored_gold

### Input

```text
[Shop floor chat, lingerie and swimwear boutique]

CONSULTANT: You do fitting appointments. How do people book?
ASSISTANT: They ring, or they come in and ask.
CONSULTANT: And where does it go?
ASSISTANT: The diary. It's behind the counter, the big blue one.
CONSULTANT: Is it online at all?
ASSISTANT: No.
CONSULTANT: How long is a fitting?
ASSISTANT: Depends. Bridal's longer. Post-surgery ones are longer as well.
CONSULTANT: Do you block different lengths in the diary?
ASSISTANT: We just write the name on the line.
CONSULTANT: How many lines per hour?
ASSISTANT: Two, I think. Or three on a Saturday.
CONSULTANT: Who decides who does the fitting?
ASSISTANT: Whoever's in.
CONSULTANT: Are they all trained?
ASSISTANT: Most of us.
CONSULTANT: Does anything remind the customer?
ASSISTANT: No. Well, we might ring them. I don't, I don't think anyone does really.
CONSULTANT: Do people not turn up?
ASSISTANT: Sometimes, yeah.
CONSULTANT: How often?
ASSISTANT: Couldn't say.
CONSULTANT: When the shop's shut and someone wants to book?
ASSISTANT: They'd have to ring back.
CONSULTANT: Is there an owner of the diary - someone who checks it?
ASSISTANT: It's just the diary.
CONSULTANT: What if two people write in the same slot?
ASSISTANT: That's happened. You just squeeze them in or ask one to wait.
```

### Gold

```json
{
  "objective": "Book and run in-store fitting appointments at a lingerie and swimwear boutique.",
  "trigger": "A customer rings or comes into the shop and asks for a fitting appointment.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "Shop assistants",
      "Customers, including bridal and post-surgery fittings"
    ]
  },
  "inputs_data_required": [
    "The customer's requested time",
    "The type of fitting (bridal and post-surgery take longer)"
  ],
  "systems_involved": [
    "A paper diary kept behind the counter"
  ],
  "current_process": [
    "A customer rings or comes in and asks for a fitting",
    "The booking is written on a line in the large paper diary behind the counter",
    "Roughly two lines are allowed per hour, or three on a Saturday, regardless of the type of fitting",
    "The fitting is done by whoever is in on the day",
    "No confirmation or reminder is sent to the customer"
  ],
  "bottlenecks_and_risks": [
    "Bridal and post-surgery fittings take longer but every booking is written on one line, so the diary systematically under-allocates time for the most sensitive and highest-value appointments",
    "The diary exists only behind the counter, so a customer who wants to book when the shop is shut has to ring back and may not",
    "No reminders are sent at all, and no-shows happen but the frequency is not known",
    "Two people writing in the same slot has happened, and is resolved by squeezing customers in or asking one to wait",
    "Nobody owns the diary - 'it's just the diary' - so no one is accountable for its accuracy",
    "Only 'most' staff are trained to fit, but allocation is to whoever is in, so an untrained assistant may take a fitting",
    "None of the volume, no-show rate or fitting type mix is measured"
  ],
  "recommended_improved_process": [
    "Move bookings to an online system with appointment types of differing lengths for standard, bridal and post-surgery fittings",
    "Allow customers to book online outside opening hours",
    "Send automated confirmations and reminders before the appointment",
    "Allocate fittings to staff recorded as trained for that fitting type",
    "Name an owner for the appointment diary",
    "Measure bookings, no-show rate and fitting type mix"
  ],
  "ai_agent_steps": [
    "An AI agent can take booking enquiries outside opening hours and offer available slots of the correct length for the fitting type",
    "An AI agent can send confirmations and reminders and flag likely no-shows",
    "An AI agent can check that the allocated fitter is recorded as trained for that fitting type and flag exceptions",
    "An AI agent can report on booking volume, no-show rate and fitting type mix"
  ],
  "human_approvals_controls": [
    "The named diary owner confirms bookings that fall outside standard availability",
    "A person confirms staff training records; the system checks against them but does not certify",
    "Bridal and post-surgery appointments are confirmed by a trained fitter before being accepted",
    "The owner approves the appointment type lengths and any change to them"
  ]
}
```

---

## `train_043` — restaurant / customer support

- **split**: train · **style**: chat_transcript · **difficulty**: contradictory · **ood**: False · **reference**: authored_gold

### Input

```text
[Kitchen pass, mid-afternoon - two conversations, transcribed]

INTERVIEWER: If someone rings up about allergies, what happens?
LIV (front of house): Whoever picks up the phone deals with it. We know the menu.
INTERVIEWER: Is there something you read from?
LIV: There's the allergen matrix in the folder by the till. It's a printout.
INTERVIEWER: When was it last updated?
LIV: I don't know, chef does it.
[Later, with the head chef]
INTERVIEWER: The allergen matrix - who maintains it?
CHEF (Marek): Front of house do it. They print it off from the supplier data. It's their document, they own it, I don't touch it.
INTERVIEWER: Liv said you do it.
MAREK: No. I tell them if a dish changes. What they do with that is up to them.
INTERVIEWER: Do you tell them every time a dish changes?
MAREK: If I remember. We change the specials daily.
INTERVIEWER: Are the specials on the matrix?
MAREK: No, the specials aren't on it. You'd have to ask the kitchen.
INTERVIEWER: And if someone rings at 3pm and asks about a special?
MAREK: Front of house would come and ask us.
INTERVIEWER: Liv, would you?
LIV: If someone's in the kitchen, yeah. Between two and four there might not be.
INTERVIEWER: What do you say then?
LIV: I'd say I'll ring them back. I might forget.
INTERVIEWER: Is anything written down when a guest tells you their allergy?
LIV: On the booking, as a note. If they booked online there's a box.
MAREK: We don't see the booking notes in the kitchen. We get told on the night by the waiter.
INTERVIEWER: Always?
MAREK: Should be. Not always.
```

### Gold

```json
{
  "objective": "Answer customers' allergy queries by telephone and get allergen information to the kitchen and to the table.",
  "trigger": "A customer telephones to ask about allergens, or tells front of house their allergy on the night.",
  "owner_and_participants": {
    "owner": "Contradictory in input: Liv says the chef maintains the allergen matrix, while Marek says front of house own it and he does not touch it - each attributes ownership of the same document to the other",
    "participants": [
      "Liv and other front of house staff",
      "Marek, the head chef",
      "Kitchen staff",
      "Customers"
    ]
  },
  "inputs_data_required": [
    "The printed allergen matrix in the folder by the till, derived from supplier data",
    "Booking notes where a customer recorded an allergy online",
    "Verbal information from the kitchen about specials"
  ],
  "systems_involved": [
    "An online booking system with an allergy notes box",
    "A printed allergen matrix in a folder by the till"
  ],
  "current_process": [
    "A customer telephones about allergens and whoever picks up the phone deals with it",
    "The member of staff reads from the printed allergen matrix in the folder by the till",
    "Specials, which change daily, are not on the matrix, so front of house go and ask the kitchen",
    "Between two and four there may be nobody in the kitchen, in which case the customer is told they will be rung back",
    "Where a customer states an allergy on a booking it is recorded as a note, including via a box on the online booking form",
    "The kitchen does not see booking notes and is told on the night by the waiter"
  ],
  "bottlenecks_and_risks": [
    "Ownership of the allergen matrix is contradictory and unresolved - front of house believe the chef maintains it, the chef believes front of house own it - so a life-safety document has no actual owner and its update date is unknown",
    "The chef tells front of house when a dish changes only 'if I remember', while specials change daily, so the matrix is knowingly incomplete",
    "Specials are not on the matrix at all, so the highest-churn menu items have no documented allergen information",
    "Between two and four nobody may be in the kitchen, so the customer is promised a call back that Liv acknowledges she might forget",
    "The kitchen does not see booking allergy notes and relies on the waiter telling them on the night, which the chef says should always happen but does not",
    "Any member of staff answers allergy calls with no training requirement or script"
  ],
  "recommended_improved_process": [
    "Assign a single named owner - the head chef - for the allergen matrix, with a required update whenever a dish or special changes",
    "Include specials on the matrix as part of writing the special",
    "Hold allergen information in a system accessible to both front of house and the kitchen rather than a printed folder",
    "Flow booking allergy notes through to the kitchen ticket automatically",
    "Define who may answer allergy calls and give them a script, including what to do when the kitchen is unavailable",
    "Require the kitchen to acknowledge each allergy on a table before service",
    "Audit the matrix against the live menu on a set cycle"
  ],
  "ai_agent_steps": [
    "An AI agent can flag menu or specials changes that have not been reflected in the allergen matrix",
    "An AI agent can route a booking's recorded allergy note to the kitchen ticket and confirm it has been acknowledged",
    "An AI agent can log allergy call-backs and chase them so a promised call is not forgotten",
    "An AI agent can audit the matrix against the live menu on the set cycle and report gaps"
  ],
  "human_approvals_controls": [
    "The head chef verifies and signs off the allergen matrix; no allergen information is published without that sign-off",
    "A trained member of staff answers every allergy query; the AI does not give allergen advice to customers",
    "The kitchen acknowledges each table allergy before the dish is served",
    "Any uncertainty about an allergen is escalated to the chef before an answer is given"
  ]
}
```

---

## `eval_syn_013` — vet clinic / appointment scheduling

- **split**: eval_synthetic · **style**: formal_process_doc · **difficulty**: standard · **ood**: True · **reference**: authored_gold

### Input

```text
OUT OF HOURS TELEPHONE TRIAGE
Practice policy note, mixed small animal veterinary practice

The practice provides its own first-line out of hours cover between 19:00 and 08:00 and at weekends, with surgical and inpatient work referred to a dedicated emergency provider twelve miles away.

Arrangements as currently operated:

The practice answerphone message gives a mobile number. The mobile is held by the duty veterinary surgeon, who takes it home. The rota for who holds the phone is drawn up monthly by the practice manager and pinned in the staff room.

An owner calls and describes the animal's condition. The duty vet triages by telephone: advises, asks the owner to attend the practice, or directs them to the emergency provider. Where the owner is asked to attend, the duty vet drives in and a nurse is called in separately by the vet.

Records: the call is written in the duty vet's own notebook, or not written at all. Where the animal is seen, the consultation is entered on the practice management system the following working day, reconstructed from memory. Calls that do not result in a visit are generally not recorded anywhere.

Points noted: the mobile number is a personal handset, not a practice line, and its call log is the only record of contact volume. Owners have kept the number and called it during working hours and on the vet's days off. There is no script or triage protocol, so advice for the same presentation differs between vets. Fees for out of hours attendance are quoted verbally and inconsistently. No handover to the day team is documented.
```

### Gold

```json
{
  "objective": "Provide first-line out of hours telephone triage for animal owners between 19:00 and 08:00 and at weekends, referring surgical and inpatient work to a dedicated emergency provider.",
  "trigger": "An owner telephones out of hours and reaches the duty veterinary surgeon on the mobile given by the answerphone message.",
  "owner_and_participants": {
    "owner": "The duty veterinary surgeon holding the mobile (rota drawn up by the practice manager)",
    "participants": [
      "The practice manager, who draws up the rota",
      "Nurses called in by the duty vet",
      "The dedicated emergency provider twelve miles away",
      "Animal owners"
    ]
  },
  "inputs_data_required": [
    "The owner's description of the animal's condition",
    "The duty rota pinned in the staff room",
    "The duty vet's own notebook, where the call is written if at all"
  ],
  "systems_involved": [
    "A practice answerphone giving a mobile number",
    "A personal mobile handset held by the duty vet",
    "A practice management system, updated the following working day",
    "A paper rota pinned in the staff room"
  ],
  "current_process": [
    "The answerphone gives a mobile number held by the duty vet, who takes it home",
    "An owner calls and describes the animal's condition",
    "The duty vet triages by telephone - advises, asks the owner to attend the practice, or directs them to the emergency provider",
    "Where the owner is asked to attend, the duty vet drives in and separately calls in a nurse",
    "The call is written in the duty vet's own notebook, or not written at all",
    "Where the animal is seen, the consultation is entered on the practice management system the following working day, reconstructed from memory"
  ],
  "bottlenecks_and_risks": [
    "Triage calls that do not result in a visit are generally not recorded anywhere, so clinical advice given out of hours leaves no record - a significant clinical governance and medico-legal exposure",
    "Consultations are reconstructed from memory the following working day, so the clinical record is written up hours later by recollection",
    "The number is a personal handset, not a practice line, so the only record of contact volume is a private call log, and owners have kept the number and called it during working hours and on the vet's days off",
    "There is no script or triage protocol, so advice for the same presentation differs between vets",
    "Fees for out of hours attendance are quoted verbally and inconsistently",
    "No handover to the day team is documented, so an animal advised overnight may not be followed up"
  ],
  "recommended_improved_process": [
    "Move out of hours calls to a practice number that diverts to the duty vet, so the number stays with the practice",
    "Adopt a written triage protocol covering common presentations, so advice is consistent between vets",
    "Record every triage call at the time - caller, animal, presentation, advice given and outcome - directly into the practice management system",
    "Publish an out of hours fee schedule and quote from it",
    "Require a documented handover to the day team for every out of hours contact",
    "Review out of hours call volume, outcomes and referrals to the emergency provider"
  ],
  "ai_agent_steps": [
    "An AI agent can capture the call record - caller, animal, presentation and advice - into the practice management system at the time of the call",
    "An AI agent can generate the handover note to the day team from the recorded out of hours contact",
    "An AI agent can quote the published out of hours fee schedule to the owner",
    "An AI agent can report out of hours call volume, outcomes and referral patterns"
  ],
  "human_approvals_controls": [
    "The duty veterinary surgeon makes every triage decision; the AI records but does not triage or give clinical advice",
    "The duty vet reviews and confirms the captured call record",
    "The day team confirms receipt of the handover for each out of hours contact",
    "The practice manager approves the triage protocol and the out of hours fee schedule"
  ]
}
```

---

## `eval_syn_001` — independent retail / invoicing/billing

- **split**: eval_synthetic · **style**: rambling_owner_email · **difficulty**: vague · **ood**: False · **reference**: authored_gold

### Input

```text
Subject: school accounts

Hello,

Someone suggested I get in touch. We're an art and stationery shop and we supply a few local schools on account - they send a teacher or a TA in with a list, we make it up, and they take it away.

The way it's billed is the person at the till rings it through as a normal sale, prints the receipt, writes the school's name on it and staples it to a docket book page. The dockets build up.

Then at some point somebody types them into an invoice and emails it to the school office.

I say "somebody" and "at some point" because I'm not sure who does it or how often. It's not me. It might be my sister when she's in on Thursdays.

Schools take ages to pay anyway and some of them need a purchase order number on the invoice which we don't have because nobody asks for one at the till.

I don't know what's owed. I know it's a fair bit because one of the primaries asked us for a statement and we couldn't produce one.

Not sure what else to tell you. Happy to answer questions.
```

### Gold

```json
{
  "objective": "Invoice local schools that buy art and stationery supplies on account, and collect what they owe.",
  "trigger": "A school sends a teacher or teaching assistant in with a list; the sale is rung through the till and the receipt stapled to a docket book page.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "Whoever is on the till",
      "The writer's sister, who is in on Thursdays and may do the invoicing",
      "Local schools and their school offices"
    ]
  },
  "inputs_data_required": [
    "Till receipt with the school's name written on it, stapled to a docket book page",
    "Purchase order number required by some schools, which is not captured at the till"
  ],
  "systems_involved": [
    "A till",
    "A docket book",
    "Email (invoices sent to the school office)"
  ],
  "current_process": [
    "A school sends someone in with a list and the order is made up",
    "The person at the till rings it through as a normal sale, prints the receipt, writes the school's name on it and staples it to a docket book page",
    "The dockets build up",
    "At some point somebody types them into an invoice and emails it to the school office"
  ],
  "bottlenecks_and_risks": [
    "Who does the invoicing and how often could not be established - 'somebody' and 'at some point', possibly the writer's sister on Thursdays - so nobody is accountable for billing",
    "Some schools require a purchase order number on the invoice and nobody asks for one at the till, so invoices are rejected or delayed at the school's end",
    "The amount owed is not known, and when a primary school asked for a statement the shop could not produce one",
    "Charges are recorded on stapled paper receipts rather than against an account, so there is no ledger to produce a statement from",
    "Schools are slow payers by nature and there is no chasing process at all",
    "The trigger for invoicing is dockets accumulating rather than a defined cycle"
  ],
  "recommended_improved_process": [
    "Set up each school as an account customer with a billing contact and any purchase order requirement recorded",
    "Capture the school account and purchase order number on the till at the point of sale",
    "Name an owner for school account invoicing and set a fixed monthly invoice date",
    "Generate invoices from the till account transactions rather than from stapled dockets",
    "Produce statements on demand and send them periodically",
    "Run aged debt reporting and chase on defined terms"
  ],
  "ai_agent_steps": [
    "An AI agent can generate the monthly invoices from till account transactions, including the purchase order reference",
    "An AI agent can produce statements on request and send them periodically to each school office",
    "An AI agent can issue payment reminders on the agreed terms and flag overdue accounts",
    "An AI agent can flag account sales rung through without a purchase order number where the school requires one"
  ],
  "human_approvals_controls": [
    "The named invoicing owner reviews and releases the monthly invoice run",
    "A person confirms the school account and any purchase order requirement when the account is opened",
    "Escalation of an overdue school account is decided by the owner",
    "Credit limits or trading terms for a school account are approved by the owner"
  ]
}
```

---

## `eval_syn_003` — restaurant / inventory/stock

- **split**: eval_synthetic · **style**: formal_process_doc · **difficulty**: contradictory · **ood**: False · **reference**: authored_gold

### Input

```text
CELLAR STOCKTAKE
Bar procedures, gastro pub

A stocktake of the cellar and back bar is performed weekly, on Sunday after close, to calculate gross profit on wet sales and identify losses.

The procedure states that the stocktake is carried out by the general manager alone, counting each line and entering the figures directly into the stock module, and that the assistant manager is not involved because the count must be done by the person accountable for the result.

Staff described a different arrangement, which they said has been in place all year: the general manager and the assistant manager count together, splitting the cellar between them - kegs and casks to one, bottles, wines and spirits to the other - and combining their sheets afterwards.

Both descriptions were given during the review as the current method.

Recorded difficulties: the two counters routinely disagree on part-used kegs, which are estimated by weight by one and by a dip stick by the other, and on spirits, which one counts by tenths of a bottle and the other to the nearest half. Combined sheets have shown the same line counted twice and other lines not counted at all. Where the resulting gross profit figure looks wrong, the figure is adjusted before it is reported to the owner rather than investigated. Wastage, staff drinks and promotional pours are not separately recorded, so any shortfall is attributed to theft or to "the count being out". No stocktake sheet from a previous week is retained for comparison.
```

### Gold

```json
{
  "objective": "Perform the weekly cellar and back bar stocktake to calculate gross profit on wet sales and identify losses.",
  "trigger": "Sunday after close, weekly.",
  "owner_and_participants": {
    "owner": "Contradictory in input: the written procedure states the stocktake is carried out by the general manager alone, precisely because it must be done by the person accountable for the result, while staff describe the general manager and assistant manager counting together and splitting the cellar, and say this has been the arrangement all year - both were given as current",
    "participants": [
      "The general manager",
      "The assistant manager",
      "The owner, to whom the gross profit figure is reported"
    ]
  },
  "inputs_data_required": [
    "Counted quantities for kegs, casks, bottles, wines and spirits",
    "Part-used kegs, estimated by weight by one counter and by dip stick by the other",
    "Spirits, counted to tenths of a bottle by one and to the nearest half by the other"
  ],
  "systems_involved": [
    "A stock module into which figures are entered"
  ],
  "current_process": [
    "A stocktake of the cellar and back bar is performed weekly on Sunday after close",
    "The cellar is split between two counters - kegs and casks to one, bottles, wines and spirits to the other",
    "Each counts their section and the sheets are combined afterwards",
    "Figures are entered into the stock module and a gross profit figure is produced",
    "Where the resulting gross profit figure looks wrong, it is adjusted before being reported to the owner",
    "No stocktake sheet from a previous week is retained"
  ],
  "bottlenecks_and_risks": [
    "Who performs the count is contradictory and both accounts are current - the procedure specifies the general manager alone so the accountable person does the count, while in practice the person being measured counts alongside the person he manages",
    "Adjusting the gross profit figure when it looks wrong rather than investigating means the control is defeated by the person it is meant to measure",
    "The two counters use incompatible methods on the same categories - part-used kegs by weight versus dip stick, spirits to tenths versus nearest half - so combining their sheets produces a figure with no consistent basis",
    "Combined sheets have shown the same line counted twice and other lines not counted at all",
    "Wastage, staff drinks and promotional pours are not separately recorded, so any shortfall is attributed to theft or a bad count - meaning genuine losses and legitimate usage are indistinguishable",
    "No previous week's sheet is retained, so trends cannot be examined and the adjusted figures cannot be audited"
  ],
  "recommended_improved_process": [
    "Resolve and document who counts, ensuring the count is not performed solely by the person accountable for the result",
    "Define a single counting method per category - weight for part-used kegs, a consistent fraction for spirits - and train both counters on it",
    "Use a structured count sheet listing every line so nothing is double-counted or missed",
    "Record wastage, staff drinks and promotional pours separately so they can be excluded from loss",
    "Prohibit adjustment of the gross profit figure; require investigation of variances instead",
    "Retain every stocktake sheet and review trends over time",
    "Have the owner review the unadjusted figure and the variance investigation"
  ],
  "ai_agent_steps": [
    "An AI agent can calculate expected stock from opening stock, deliveries and till sales, and compare it against the count to produce the variance",
    "An AI agent can flag lines counted twice, lines not counted, and counts inconsistent with the defined method",
    "An AI agent can trend variance by line and by week to distinguish recurring loss from count error",
    "An AI agent can reconcile recorded wastage, staff drinks and promotional pours against the variance"
  ],
  "human_approvals_controls": [
    "The owner receives the unadjusted gross profit figure; adjustments by the person being measured are prohibited",
    "Counters sign their own count sheets and the combined sheet is verified by a second person",
    "Variances above a threshold are investigated by a person and the investigation recorded",
    "The owner approves the counting method and any change to it"
  ]
}
```

---

## `eval_syn_002` — dental/GP clinic / customer onboarding

- **split**: eval_synthetic · **style**: rambling_owner_email · **difficulty**: standard · **ood**: False · **reference**: authored_gold

### Input

```text
Subject: registering new patients

Hi,

You asked how a new patient gets onto our books.

They ring or come in. Reception hands them a clipboard with the registration form and the medical history questionnaire, and they fill it in sitting in the waiting room. It's four sides. Name, address, GP, medications, allergies, medical conditions, consent for us to hold their data, and the section about who's paying - NHS exempt, NHS paying, or private.

They hand it back, reception photocopies their exemption evidence if they've claimed exemption, and puts the form in a tray.

Later - same day if it's quiet, next day usually - reception types the details into SOE and creates the patient record. The paper goes in the filing cabinet.

Then they get an examination appointment, and the dentist reads the medical history off the screen.

Things that go wrong. People leave sections blank, especially the medications one, and nobody checks before they've gone. The handwriting on medications is often unreadable and the nurse ends up asking again in the surgery. Exemption evidence gets photocopied but nobody checks it's the right kind, and we've had claims rejected. And the form doesn't get typed up before the appointment sometimes, so the dentist is reading a paper form in the surgery.

Emma (Practice Manager)
```

### Gold

```json
{
  "objective": "Register new dental patients, capturing their details, medical history and payment status, and create the patient record.",
  "trigger": "A new patient rings or comes in and is given a clipboard with the registration form and medical history questionnaire.",
  "owner_and_participants": {
    "owner": "Emma, the practice manager (reception carries out the process)",
    "participants": [
      "Reception staff",
      "Nurses, who chase unreadable medications entries in surgery",
      "Dentists, who read the medical history at the examination",
      "New patients"
    ]
  },
  "inputs_data_required": [
    "Four-side paper registration and medical history form - name, address, GP, medications, allergies, medical conditions, data consent, and payment status (NHS exempt, NHS paying, or private)",
    "Photocopied exemption evidence"
  ],
  "systems_involved": [
    "SOE (patient records)",
    "Paper forms on a clipboard",
    "A photocopier",
    "A filing cabinet"
  ],
  "current_process": [
    "The patient rings or comes in and reception hands them a clipboard with the four-side registration and medical history form",
    "The patient completes it sitting in the waiting room",
    "They hand it back and reception photocopies exemption evidence where exemption is claimed, placing the form in a tray",
    "Reception types the details into SOE and creates the patient record - the same day if quiet, usually the next day",
    "The paper goes in the filing cabinet",
    "The patient is given an examination appointment and the dentist reads the medical history off the screen"
  ],
  "bottlenecks_and_risks": [
    "Patients leave sections blank, especially medications, and nobody checks before they have gone, so the clinical record is incomplete at the point it matters",
    "Handwriting on the medications section is often unreadable and the nurse ends up asking again in the surgery, duplicating the work and delaying the appointment",
    "Exemption evidence is photocopied without anyone checking it is the right kind, and claims have been rejected as a result - a direct financial loss",
    "The form is not always typed into SOE before the appointment, so the dentist reads a paper form in the surgery rather than the screen the process assumes",
    "A four-side form completed in a public waiting room is a poor setting for medical and personal information",
    "There is a delay of up to a day between capture and the record existing, during which the information is only on paper"
  ],
  "recommended_improved_process": [
    "Send the registration and medical history form digitally before the appointment, completed by the patient at home",
    "Use required fields and validation so medications and allergies cannot be left blank",
    "Capture exemption category with guidance on acceptable evidence and validate it at the point of claim",
    "Populate SOE directly from the submitted form rather than re-keying",
    "Flag any incomplete registration before the examination appointment",
    "Offer an assisted route in a private area for patients who cannot complete it digitally",
    "Report on rejected exemption claims and incomplete registrations"
  ],
  "ai_agent_steps": [
    "An AI agent can send the digital registration form on booking and chase completion before the appointment",
    "An AI agent can validate exemption category against the acceptable evidence rules and flag likely rejections before the claim is made",
    "An AI agent can flag registrations with missing medications, allergy or medical history fields for reception to follow up",
    "An AI agent can report on rejected claims and incomplete registrations by cause"
  ],
  "human_approvals_controls": [
    "A clinician reviews the medical history before treatment; the AI does not assess clinical information",
    "Reception verifies exemption evidence against the flagged category before the claim is submitted",
    "A person completes the assisted route for patients who cannot use the digital form",
    "The practice manager approves any change to the registration form and its required fields"
  ]
}
```

---

## `eval_syn_005` — gym / customer support

- **split**: eval_synthetic · **style**: consultant_call_notes · **difficulty**: standard · **ood**: False · **reference**: authored_gold

### Input

```text
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

### Gold

```json
{
  "objective": "Handle member questions and complaints posted in the club's Facebook group.",
  "trigger": "A member posts a question or complaint in the Facebook group.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "Three group admins - the fitness manager, a class instructor, and a former duty manager who left last year and has not been removed",
      "Whichever member of staff sees a post on their own phone",
      "Members, who answer each other",
      "The owner, who reads it occasionally"
    ]
  },
  "inputs_data_required": [
    "The content of members' posts - timetable changes, pool and sauna status, lost property, spare class places, complaints with photographs"
  ],
  "systems_involved": [
    "A members' Facebook group with roughly 1,400 members",
    "The club's email address and telephone, to which group posts are not redirected"
  ],
  "current_process": [
    "A member posts a question or complaint in the Facebook group",
    "Nobody is assigned to monitor or answer it",
    "Answers are given by whichever member of staff happens to see the post on their own phone, in their own time",
    "Members also answer each other",
    "Nothing posted reaches the club's actual systems - lost property, maintenance issues and complaints raised in the group are not logged anywhere"
  ],
  "bottlenecks_and_risks": [
    "A group of 1,400 members set up during a closure period was never wound down and now carries live operational questions with nobody assigned to it",
    "A former duty manager who left last year remains an admin, so someone outside the business holds administrative control of a member-facing channel",
    "Staff answer on their own phones in their own time, and instructors have given wrong answers about the timetable",
    "Members answer each other incorrectly - one told twenty others the pool was shut for a fortnight when it was two days",
    "Lost property, maintenance issues and complaints raised in the group never reach the club's systems, so they are simply lost",
    "Posts are not redirected to the club's email or telephone, so the channel is a dead end",
    "Response time, volume and themes are not measured, and the owner reads it occasionally and finds it demoralising"
  ],
  "recommended_improved_process": [
    "Decide whether the group remains an official channel or is wound down in favour of the club's own channels",
    "If retained, name an owner and a monitoring schedule with defined response times",
    "Remove admins who no longer work for the business",
    "Route operational items - lost property, maintenance, complaints - from the group into the club's own systems",
    "Publish authoritative information such as the timetable and facility status in one place members can rely on",
    "Correct significant member misinformation promptly",
    "Measure volume, response time and themes"
  ],
  "ai_agent_steps": [
    "An AI agent can monitor the group and alert the named owner to posts requiring a response, particularly complaints and facility questions",
    "An AI agent can create logged records in the club's systems from group posts about lost property or maintenance",
    "An AI agent can draft responses for the named owner to review and post",
    "An AI agent can classify posts by theme and report volume and response times"
  ],
  "human_approvals_controls": [
    "The named owner reviews and posts every response; nothing is published to the group automatically",
    "The club manager decides whether the group is retained as an official channel and who holds admin rights",
    "A person handles any complaint raised in the group rather than an automated reply",
    "Corrections of member misinformation are approved by a manager before posting"
  ]
}
```

---

## `eval_pet_001` — hotel / room service order fulfilment

- **split**: eval_pet · **style**: formal_process_doc · **difficulty**: standard · **ood**: False · **reference**: model_generated_unverified · **PET doc**: doc-1.3

### Input

```text
The Evanstonian is an upscale independent hotel. When a guest calls room service at The Evanstonian, the room-service manager takes down the order. She then submits an order ticket to the kitchen to begin preparing the food. She also gives an order to the sommelier (i.e., the wine waiter) to fetch wine from the cellar and to prepare any other alcoholic beverages. Eighty percent of room-service orders include wine or some other alcoholic beverage. Finally, she assigns the order to the waiter. While the kitchen and the sommelier are doing their tasks, the waiter readies a cart (i.e., puts a tablecloth on the cart and gathers silverware). The waiter is also responsible for nonalcoholic drinks. Once the food, wine, and cart are ready, the waiter delivers it to the guest's room. After returning to the room-service station, the waiter debits the guest's account. The waiter may wait to do the billing if he has another order to prepare or deliver.
```

### Gold

```json
{
  "objective": "Take, prepare and deliver a room service order at an upscale independent hotel, and bill it to the guest's account.",
  "trigger": "A guest calls room service.",
  "owner_and_participants": {
    "owner": "The room-service manager",
    "participants": [
      "The kitchen",
      "The sommelier (wine waiter)",
      "The waiter",
      "The guest"
    ]
  },
  "inputs_data_required": [
    "The guest's order",
    "The order ticket sent to the kitchen",
    "The order given to the sommelier",
    "The guest's account details for billing"
  ],
  "systems_involved": [],
  "current_process": [
    "The guest calls room service and the room-service manager takes down the order",
    "She submits an order ticket to the kitchen to begin preparing the food",
    "She gives an order to the sommelier to fetch wine from the cellar and prepare any other alcoholic beverages",
    "She assigns the order to the waiter",
    "While the kitchen and the sommelier work, the waiter readies a cart - putting a tablecloth on it and gathering silverware - and is also responsible for nonalcoholic drinks",
    "Once the food, wine and cart are ready, the waiter delivers the order to the guest's room",
    "After returning to the room-service station the waiter debits the guest's account, though he may wait to do the billing if he has another order to prepare or deliver"
  ],
  "bottlenecks_and_risks": [
    "Billing is deferred at the waiter's discretion when he has another order, so revenue capture depends on him remembering after a busy period",
    "The room-service manager is a single point of intake for every order, so she is a bottleneck at peak times",
    "Eighty percent of orders involve the sommelier, so cellar availability and the sommelier's capacity gate most orders",
    "Food, wine and cart are prepared in parallel by three parties with no stated coordination point, so the whole order waits on the slowest and nothing signals a delay",
    "The waiter both prepares the cart and delivers, so a delivery in progress delays preparation of the next order",
    "No mechanism is described for confirming the order back to the guest or for handling an item that cannot be supplied"
  ],
  "recommended_improved_process": [
    "Capture the order directly into a point-of-sale system that simultaneously issues tickets to the kitchen, the sommelier and the waiter",
    "Post the charge to the guest's account at the point of order, adjusting only if the order changes",
    "Display order status to all three preparers so the coordination point is visible",
    "Allow guests to order through an in-room or mobile channel as well as by telephone, easing the manager bottleneck",
    "Alert the manager when any component of an order exceeds its expected preparation time",
    "Separate cart preparation from delivery at peak times so the waiter is not the constraint",
    "Report on order volume, preparation and delivery times and billing exceptions"
  ],
  "ai_agent_steps": [
    "An AI agent can take orders placed through the in-room or mobile channel and issue the kitchen, sommelier and waiter tickets",
    "An AI agent can post the charge to the guest's account at the point of order, removing the deferred billing step",
    "An AI agent can monitor component preparation times and alert the manager when an order is at risk",
    "An AI agent can report on order volume, delivery times and billing exceptions"
  ],
  "human_approvals_controls": [
    "The room-service manager confirms any order taken by telephone before tickets are issued",
    "The waiter confirms delivery to the room before the charge is finalised",
    "Adjustments or removals of a charge on a guest's account require staff authorisation",
    "The sommelier confirms availability where a requested wine cannot be supplied"
  ]
}
```

---

## `eval_pet_002` — investment banking / securities underwriting

- **split**: eval_pet · **style**: formal_process_doc · **difficulty**: standard · **ood**: False · **reference**: model_generated_unverified · **PET doc**: doc-1.4

### Input

```text
Whenever a company makes the decision to go public, its first task is to select the underwriters. Underwriters act as financial midwives to a new issue. Usually they play a triple role: First they provide the company with procedural and financial advice, then they buy the issue, and finally they resell it to the public. Established underwriters are careful of their reputation and will not handle a new issue unless they believe the facts have been presented fairly. Thus, in addition to handling the sale of a company's issue, the underwriters in effect give their seal of approval to it. They prepare a registration statement for the approval of the Securities and Exchange Commission (SEC). In addition to registering the issue with the SEC, they need to check that the issue complies with the so-called blue-sky laws of each state that regulate sales of securities within the state. While the registration statement is awaiting approval, underwriters begin to firm up the issue price. They arrange a road show to talk to potential investors. Immediately after they receive clearance from the SEC, underwriters fix the issue price. After that they enter into a firm commitment to buy the stock and then offer it to the public, when they haven't still found any reason not to do it.
```

### Gold

```json
{
  "objective": "Take a company public, from selecting underwriters through registration and pricing to offering the stock to the public.",
  "trigger": "A company makes the decision to go public.",
  "owner_and_participants": {
    "owner": "The underwriters",
    "participants": [
      "The company going public",
      "The Securities and Exchange Commission (SEC)",
      "State regulators administering blue-sky laws",
      "Potential investors met on the road show",
      "The public"
    ]
  },
  "inputs_data_required": [
    "The facts about the company, which established underwriters check have been presented fairly",
    "The registration statement prepared for SEC approval",
    "Blue-sky law requirements of each state",
    "Feedback from potential investors on the road show"
  ],
  "systems_involved": [],
  "current_process": [
    "The company selects the underwriters",
    "The underwriters provide the company with procedural and financial advice",
    "Established underwriters satisfy themselves that the facts have been presented fairly before handling the issue, in effect giving their seal of approval",
    "They prepare a registration statement for the approval of the SEC",
    "They check that the issue complies with the blue-sky laws of each state regulating sales of securities within that state",
    "While the registration statement awaits approval, they begin to firm up the issue price and arrange a road show to talk to potential investors",
    "Immediately after clearance from the SEC they fix the issue price",
    "They enter into a firm commitment to buy the stock and then offer it to the public, provided they have not found any reason not to proceed"
  ],
  "bottlenecks_and_risks": [
    "The underwriters buy the issue under a firm commitment, so once the price is fixed they carry the risk that the stock does not sell at that price",
    "The issue price is only firmed up while approval is pending and fixed immediately on clearance, compressing the most consequential decision into the narrowest window",
    "Blue-sky compliance must be checked state by state, so a single non-compliant state can hold up the offering",
    "The underwriters' verification that the facts have been presented fairly rests on their concern for their own reputation rather than on any described procedure",
    "The road show gathers investor sentiment in parallel with an approval process whose timing the underwriters do not control",
    "The final decision to proceed is conditioned on not having 'still found any reason not to do it', which is an undefined and late-breaking exit point"
  ],
  "recommended_improved_process": [
    "Run due diligence to a documented checklist so the fairness verification is evidenced rather than reputational",
    "Track blue-sky compliance per state on a single register with status and owner",
    "Maintain a version-controlled registration statement with an audit trail of SEC comments and responses",
    "Capture road show investor feedback in a structured book-building record that feeds the pricing decision",
    "Model pricing scenarios continuously through the approval period rather than fixing price in the final window",
    "Define and document the criteria that would cause the underwriters not to proceed",
    "Report on timetable, approval status and demand coverage throughout"
  ],
  "ai_agent_steps": [
    "An AI agent can track blue-sky compliance status across every state and flag outstanding requirements",
    "An AI agent can maintain the registration statement version history and match SEC comments to responses",
    "An AI agent can aggregate structured road show feedback into the book-building record to support the pricing decision",
    "An AI agent can report timetable status, approval progress and demand coverage"
  ],
  "human_approvals_controls": [
    "The underwriters approve the registration statement before it is filed with the SEC",
    "The issue price is fixed by the underwriters, not by an automated model",
    "The firm commitment to buy the stock is a human decision, taken against the documented go/no-go criteria",
    "Counsel confirms blue-sky compliance in each state before the offering proceeds"
  ]
}
```

---

## `eval_pet_003` — energy metering / meter operator registration

- **split**: eval_pet · **style**: formal_process_doc · **difficulty**: vague · **ood**: False · **reference**: model_generated_unverified · **PET doc**: doc-10.2

### Input

```text
The MPON reports the meter operation to the GO. The GO examines the application of the MPON. The GO rejects the application of the MPON or the GO confirmes the application of the MPON. The GO informs the MPOO about the registration confirmation of the MPON. The GO informs the MSPO about the registration confirmation of the MPON. The MPON and the MPOO perform the equipment acquisition and / or equipment changes. The MPON informs the GO about the failure of the entire process or the MPON informs the GO about the successful completion of the entire process. The GO informs the MPON about the failure of the overall transaction by deadline if after a maximum time limit no message of the MPON is present at the GO. If the MPON informs the GO about the failure of the entire process, the GO confirms the failure of the assignment to the MPON. If the MPON informs the GO about the successful completion of the overall process, the GO assigns the MPON. The GO confirms the assignment to the MPON. The GO informs the MPOO about the failure of the assignment of the MPON or the GO informs the MPOO about the assignment of the MPON. The GO informs the MSPO about the failure of the assignment of the MPON or the GO informs the MSPO about the assignment of the MPON. The GO informs the SP about the assignment of the MPON.
```

### Gold

```json
{
  "objective": "Register a new meter point operator with the grid operator and complete the assignment, including the associated equipment acquisition or changes.",
  "trigger": "The new meter point operator (MPON) reports the meter operation to the grid operator (GO).",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "The new meter point operator (MPON)",
      "The grid operator (GO)",
      "The old meter point operator (MPOO)",
      "The metering service point operator (MSPO)",
      "The service provider (SP)"
    ]
  },
  "inputs_data_required": [
    "The MPON's application",
    "Notification from the MPON of the failure or successful completion of the entire process",
    "A maximum time limit after which the GO treats the transaction as failed"
  ],
  "systems_involved": [],
  "current_process": [
    "The MPON reports the meter operation to the GO",
    "The GO examines the application and either rejects or confirms it",
    "The GO informs the MPOO and the MSPO of the registration confirmation",
    "The MPON and the MPOO perform the equipment acquisition and any equipment changes",
    "The MPON informs the GO of either the failure or the successful completion of the entire process",
    "Where no message is received from the MPON within a maximum time limit, the GO informs the MPON of the failure of the overall transaction by deadline",
    "On failure the GO confirms the failure of the assignment to the MPON; on success the GO assigns the MPON and confirms the assignment",
    "The GO informs the MPOO and the MSPO of either the failure or the assignment, and informs the SP of the assignment"
  ],
  "bottlenecks_and_risks": [
    "The whole outcome depends on the MPON sending a completion message, and silence is resolved only by a timeout that fails the entire transaction",
    "Failure by deadline is treated identically to reported failure, so a lost or delayed message produces the same outcome as a genuine failure",
    "The equipment acquisition and change step is performed jointly by the incoming and outgoing operators with no described coordination, checkpoint or dispute route",
    "The GO must fan out notifications to the MPOO, MSPO and SP at multiple points, so any missed notification leaves a party working from a stale position",
    "No owner is identified for the process and no supporting system is described, so accountability for progressing a stalled application cannot be established",
    "The SP is informed only of the assignment and not of failure, so it has no visibility of unsuccessful transactions"
  ],
  "recommended_improved_process": [
    "Exchange application, confirmation and completion messages through a standardised market messaging platform with delivery acknowledgement",
    "Track each registration as a case with a status, an owner and a due date rather than relying on a single timeout",
    "Warn the MPON before the maximum time limit expires rather than only notifying failure afterwards",
    "Distinguish failure by deadline from reported failure so the causes can be analysed separately",
    "Define checkpoints and a dispute route for the joint equipment acquisition and change step",
    "Notify all affected parties, including the SP, of both success and failure",
    "Report on registration volumes, timeouts and failure reasons"
  ],
  "ai_agent_steps": [
    "An AI agent can monitor open registrations against the maximum time limit and issue warnings to the MPON before expiry",
    "An AI agent can distribute the status notifications to the MPOO, MSPO and SP at each defined point and confirm delivery",
    "An AI agent can classify failures as reported or by deadline and report on volumes and reasons",
    "An AI agent can chase the MPON and MPOO for progress on the equipment acquisition and change step"
  ],
  "human_approvals_controls": [
    "The grid operator examines and decides every application; the AI does not confirm or reject registrations",
    "A person authorises the assignment of the MPON",
    "Failure of a transaction by deadline is confirmed by a person before it is treated as final",
    "Disputes arising during the equipment acquisition step are resolved by people, not automatically"
  ]
}
```

---

## `eval_pet_004` — telecommunications / service problem resolution

- **split**: eval_pet · **style**: formal_process_doc · **difficulty**: standard · **ood**: False · **reference**: model_generated_unverified · **PET doc**: doc-2.1

### Input

```text
At the beginning the customer perceives that her subscribed service has degraded. A list with all the problem parameters is then sent to the Customer Service department of TELECO. At the customer service an employee enters (based on the received data) a problem report into system T.. Then the problem report is compared to the customer SLA to identify what the extent and the details of the service degradation are. Based on this, the necessary counter measures are determined including their respective priorities. An electronic service then determines the significance of the customer based on information that has been collected during the history of the contractual relationship. In case the customer is premium, the process will link to an extra problem fix process (this process will not be detailed here). In case the customer is of certain significance which would affect the counter measures previously decided upon, the process goes back to re-prioritize these measures otherwise the process continues. Taking together the information (i.e. contract commitment data + prioritized actions) a detailed problem report is created. The detailed problem report is then sent to Service Management. Service Management deals on a first level with violations of quality in services that are provided to customers. After receiving the detailed problem report, Service management investigates whether the problem is analyzable at the level of their department or whether the problem may be located at Resource Provisioning. In case Service Management assesses the problem to be not analyzable by themselves, the detailed problem report is sent out to Resource Provisioning. If Service Management is sure they can analyze it, they perform the analysis and based on the outcome they create a trouble report that indicates the type of problem. After Resource Provisioning receives the detailed problem report, it is checked whether there are any possible problems. If no problems are detected, a notification about the normal service execution is created. If a problem is detected this will be analyzed by Resource Provisioning and a trouble report is created. Either trouble report or the normal execution notification will be included in a status report and sent back to Service Management. Service Management then prepares the final status report based on the received information. Subsequently it has to be determined what counter measures should be taken depending on the information in the final status report. Three alternative process paths may be taken. For the case that no problem was detected at all, the actual service performance is sent back to the Customer Service. For the case that minor corrective actions are required, Service Management will undertake corrective actions by themselves. Subsequently, the problem resolution report is created and then sent out to Customer Service. After sending, this process path of Service Management ends. For the case that automatic resource restoration from Resource Provisioning is required, Service Management must create a request for automatic resource restoration. This message is then sent to Resource Provisioning. Resource Provisioning has been on-hold and waiting for a restoration request but this must happen within 2 days after the status report was sent out, otherwise Resource Provisioning terminates the process. After the restoration request is received, all possible errors are tracked. Based on the tracked errors, all necessary corrective actions are undertaken by Resource Provisioning. Then a trouble-shooting report is created. This report is sent out to Service Management; then the process ends. The trouble-shooting report is received by Service Management and this information goes then into the creation of the problem resolution report just as described for ii). Customer Service either receives the actual service performance (if there was no problem) or the problem resolution report. Then, two concurrent activities are triggered, i.e. i) a report is created for the customer which details the current service performance and the resolution of the problem, and ii) an SLA violation rebate is reported to Billing & Collections who will adjust the billing. The report for the customer is sent out to her. After all three activities are completed the process ends within Customer Service. After the customer then receives the report about service performance and problem resolution from Customer Service, the process flow at the customer also ends.
```

### Gold

```json
{
  "objective": "Resolve a customer's reported degradation of a subscribed telecommunications service, from the customer's problem report through analysis and corrective action to a report back to the customer and any billing rebate.",
  "trigger": "The customer perceives that her subscribed service has degraded and a list of all the problem parameters is sent to the Customer Service department.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "The customer",
      "Customer Service at TELECO",
      "Service Management",
      "Resource Provisioning",
      "Billing & Collections",
      "An electronic service that determines customer significance"
    ]
  },
  "inputs_data_required": [
    "The list of problem parameters received from the customer",
    "The customer SLA, used to identify the extent and details of the degradation",
    "Information collected during the history of the contractual relationship, used to determine customer significance",
    "Contract commitment data and prioritized actions, combined into the detailed problem report",
    "Status and trouble reports"
  ],
  "systems_involved": [
    "System T (into which the problem report is entered)",
    "An electronic service determining customer significance"
  ],
  "current_process": [
    "A Customer Service employee enters a problem report into System T from the received data",
    "The report is compared to the customer SLA to identify the extent and details of the degradation, and counter measures and their priorities are determined",
    "An electronic service determines the customer's significance; premium customers link to a separate problem fix process, and where significance would affect the counter measures the process returns to re-prioritize them",
    "A detailed problem report combining contract commitment data and prioritized actions is created and sent to Service Management",
    "Service Management investigates whether the problem is analyzable at their level or may sit with Resource Provisioning, and either analyses it and creates a trouble report or sends the detailed report to Resource Provisioning",
    "Resource Provisioning checks for possible problems and creates either a trouble report or a normal service execution notification, returning it in a status report to Service Management",
    "Service Management prepares the final status report and takes one of three paths - no problem, minor corrective actions by themselves, or a request for automatic resource restoration from Resource Provisioning, which must be sent within 2 days or Resource Provisioning terminates the process",
    "Customer Service receives either the actual service performance or the problem resolution report, then concurrently creates and sends a report to the customer and reports an SLA violation rebate to Billing & Collections"
  ],
  "bottlenecks_and_risks": [
    "Resource Provisioning waits on hold for a restoration request and terminates the process if it does not arrive within 2 days, so a delay at Service Management silently ends the resolution path",
    "The problem report can loop back to re-prioritize counter measures after customer significance is determined, so prioritisation is done twice and the first pass may be wasted",
    "The customer's report crosses three departments - Customer Service, Service Management and Resource Provisioning - before any corrective action, with a handover and a report created at each boundary",
    "Service Management decides whether it can analyse the problem itself, so a wrong judgement at that point sends the case down the longer path or holds it at the wrong level",
    "The SLA violation rebate is reported to Billing & Collections concurrently with the customer report, with no described check that the rebate matches what the customer was told",
    "No single owner is identified for the customer's problem end to end, so nobody is accountable for the elapsed time across the three departments"
  ],
  "recommended_improved_process": [
    "Assign a single case owner accountable for the customer's problem from report to resolution across all three departments",
    "Determine customer significance at the point the problem report is created, so counter measures are prioritised once",
    "Replace the 2-day on-hold termination with an escalation to the case owner before the deadline",
    "Give all three departments a shared case record rather than passing reports between them",
    "Set and monitor elapsed-time targets at each stage against the customer SLA",
    "Reconcile the SLA violation rebate against the report sent to the customer before Billing & Collections adjusts the billing",
    "Report on resolution times, path taken and rebate value by cause"
  ],
  "ai_agent_steps": [
    "An AI agent can create the initial problem report in System T from the received problem parameters and compare it against the customer SLA",
    "An AI agent can determine customer significance from contractual history at the point of report creation",
    "An AI agent can monitor cases approaching the restoration request deadline and escalate to the case owner before Resource Provisioning terminates",
    "An AI agent can reconcile the SLA violation rebate against the customer report before it reaches Billing & Collections",
    "An AI agent can report resolution times, path taken and rebate value by cause"
  ],
  "human_approvals_controls": [
    "The case owner approves the prioritised counter measures before the detailed problem report is issued",
    "Service Management decides whether a problem is analyzable at their level or belongs to Resource Provisioning",
    "Corrective actions on network resources are authorised by Resource Provisioning, not applied automatically",
    "The SLA violation rebate is approved by a person before Billing & Collections adjusts the customer's billing"
  ]
}
```

---

## `eval_pet_005` — energy retail / customer switch-over onboarding

- **split**: eval_pet · **style**: formal_process_doc · **difficulty**: standard · **ood**: False · **reference**: model_generated_unverified · **PET doc**: doc-2.2

### Input

```text
The process is initiated by a switch-over request. In doing so, the customer transmits his data to the customer service department of the company. Customer service is a shared service center between the departments Sales and Distribution. The customer data is received by customer service and based on this data a customer data object is entered into the CRM system. After customer data has been entered it should then be compared with the internal customer data base and checked for completeness and plausibility. In case of any errors these should be corrected on the basis of a simple error list. The comparison of data is done to prevent individual customer data being stored multiple times. In case the customer does not exist in the customer data base, a new customer object is being created which will remain the data object of interest during the rest of the process flow. This object consists of data elements such as the customer's name and address and the assigned power gauge. The generated customer object is then used, in combination with other customer data to prepare the contract documents for the power supplier switch (including data such as bank connection, information on the selected rate, requested date of switch-over). In the following an automated check of the contract documents is carried out within the CIS (customer information system) in order to confirm their successful generation. In case of a negative response, i.e. the contract documents are not (or incorrectly) generated, the causing issues are being analyzed and resolved. Subsequently the contract documents are generated once again. In case of a positive response a confirmation document is sent out to the customer stating that the switch-over to the new supplier can be executed. A request to the grid operator is automatically sent out by the CIS. It puts the question whether the customer may be supplied by the selected supplier in the future. The switch-over request is checked by the grid operator for supplier concurrence, and the grid operator transmits a response comment. In the case of supplier concurrence the grid operator would inform all involved suppliers and demand the resolution of the conflict. The grid operator communicates with the old supplier and carries out the termination of the sales agreement between the customer and the old supplier (i.e. the customer service (of the new supplier) does not have to interact with the old supplier regarding termination). If there are not any objections by the grid operator (i.e. no supplier concurrence), customer service creates a CIS contract. The customer then has the chance to check the contract details and based on this check may decide to either withdraw from the switch contract or confirm it. Depending on the customer's acceptance / rejection the process flow at customer service either ends (in case of withdrawal) or continues (in case of a confirmation). An additional constraint is that the customer can only withdraw from the offered contract within 7 days after the 7th day the contract will be regarded as accepted and the process continues. The confirmation message by the customer is therefore not absolutely necessary (as it will count as accepted after 7 days in any way) but it can speed up the switch process. On the switch-date, but no later than 10 days after power supply has begun, the grid operator transmits the power meter data to the customer service and the old supplier via messages containing a services consumption report. At the same time, the grid operator computes the final billing based on the meter data and sends it to the old supplier. Likewise the old supplier creates and sends the final billing to the customer. For the customer as well as the grid operator the process ends then. After receiving the meter data customer service imports the meter data to systems that require the information. The process of winning a new customer ends here.
```

### Gold

```json
{
  "objective": "Switch a customer to a new power supplier, from the switch-over request through contract generation and grid operator clearance to importing the final meter data.",
  "trigger": "The customer transmits his data to the customer service department as a switch-over request.",
  "owner_and_participants": {
    "owner": "Not specified in input",
    "participants": [
      "The customer",
      "Customer service, a shared service centre between Sales and Distribution",
      "The grid operator",
      "The old supplier"
    ]
  },
  "inputs_data_required": [
    "The customer's transmitted data",
    "The internal customer data base, against which data is compared for completeness and plausibility",
    "A simple error list used to correct errors",
    "The customer object - name, address and assigned power gauge",
    "Bank connection, selected rate and requested date of switch-over",
    "The grid operator's response comment",
    "Power meter data and the services consumption report"
  ],
  "systems_involved": [
    "The CRM system (customer data object)",
    "The CIS (customer information system) - contract document checks, automated request to the grid operator, CIS contract"
  ],
  "current_process": [
    "Customer service receives the customer's data and enters a customer data object into the CRM system",
    "The data is compared against the internal customer data base and checked for completeness and plausibility, with errors corrected from a simple error list; where the customer does not exist a new customer object is created",
    "The customer object and other data are used to prepare the contract documents for the switch, including bank connection, selected rate and requested switch date",
    "The CIS carries out an automated check confirming the documents were generated successfully; on a negative response the issues are analysed, resolved and the documents generated again",
    "On a positive response a confirmation document is sent to the customer and the CIS automatically sends a request to the grid operator asking whether the customer may be supplied by the selected supplier",
    "The grid operator checks for supplier concurrence and responds; where there is concurrence it informs all involved suppliers and demands resolution, and it handles termination with the old supplier",
    "Where there are no objections, customer service creates a CIS contract; the customer may withdraw within 7 days, after which it counts as accepted",
    "On the switch date, and no later than 10 days after supply begins, the grid operator transmits meter data to customer service and the old supplier and computes the final billing; customer service imports the meter data into the systems that require it"
  ],
  "bottlenecks_and_risks": [
    "The customer's confirmation is not necessary because the contract counts as accepted after 7 days, so the process relies on silence as consent within a fixed withdrawal window",
    "Meter data may arrive up to 10 days after supply has begun, so the customer is being supplied before the data underpinning billing is available",
    "Contract document generation is checked only for successful generation by the CIS, and a negative response sends the process back to analyse and regenerate with no described limit on repetition",
    "Supplier concurrence is detected only after the request reaches the grid operator, at which point the customer has already been sent a confirmation that the switch can be executed",
    "Duplicate customer records are prevented by a comparison against the internal data base, but errors are corrected from a simple error list with no described validation of the correction",
    "No owner is identified for the switch case, and customer service is a shared service centre between two departments, so accountability for a stalled switch is unclear"
  ],
  "recommended_improved_process": [
    "Assign a case owner accountable for each switch from request to meter data import",
    "Validate customer data at the point of capture rather than correcting from an error list afterwards",
    "Check supplier concurrence with the grid operator before sending the customer a confirmation that the switch can be executed",
    "Limit and escalate repeated contract document generation failures rather than looping indefinitely",
    "Track the 7-day withdrawal window and the 10-day meter data deadline as monitored milestones",
    "Reconcile received meter data against the switch date and chase the grid operator where it is late",
    "Report on switch cycle time, failure causes and withdrawal rates"
  ],
  "ai_agent_steps": [
    "An AI agent can validate customer data against the internal data base at capture and propose corrections for confirmation",
    "An AI agent can monitor the 7-day withdrawal window and the 10-day meter data deadline and escalate breaches to the case owner",
    "An AI agent can chase the grid operator for a response comment or for late meter data",
    "An AI agent can classify contract generation failures and report recurring causes",
    "An AI agent can report switch cycle time, failure causes and withdrawal rates"
  ],
  "human_approvals_controls": [
    "Customer service confirms the customer object and any proposed data correction before the contract documents are prepared",
    "A person reviews and resolves contract generation failures rather than allowing unlimited automated regeneration",
    "The customer's withdrawal or confirmation decision is theirs alone and is recorded, not inferred beyond the stated 7-day rule",
    "A person authorises the CIS contract creation once the grid operator has raised no objection"
  ]
}
```

---
