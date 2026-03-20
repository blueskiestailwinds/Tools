Definitions:

X: X-day (off day, the only day PCS can move)
R: Reserve (day of work)
CQ: Training (canoot be moved by PCS and cannot be painted on desired calendar)
A: Absensce (cannot be moved by PCS and cannot be painted on desired calendar)
CI: Carry-In (cannot be moved by PCS and cannot be painted on desired calendar)
IVD: Individual Vacation Day (can be painted on current or desired)
Short Work Block: A contiguous block of work days < minWork (default: 4)
work block: A group of days that are not X or A. CI and R are work days.
maxXblocks: The highest permissible quantity of separate contiguous groupings of X days. [R-R-X-X-X-R-R-R-X-X-X-R-R-R-X-X-X-R-R] is three "X-day blocks". [R-R-R-R-X-X-R-R-R-R-X-X-R-R-R-R-X-X-R-R-R-R-X-X-R-R-R-R-X-X] would be illegal if maxXblocks = 4.
minWork: The fewest number of work days that are allowed to make up a work block. minwork = 4 would be legal with [X-X-X-R-R-R-R-X-X-X]. minwork = 4 would be illegal with [X-X-X-R-R-R-X-X-X].  
maxWork: Will always be 99. It is only a UI element because the user expects to input it. No role in pathfinding.
All examples below assuming minWork = 4 unless explicitly stated.

Display rules:

- Rule D1: day index 0 corresponds to bid-month start date, not calendar day 1
  - fails when: displayed labels use raw index positions instead of real dates
  - passes when: displayed dates are computed as bidMonthStart + dayIndex
  - all date references should reflect real calendar dates
  - applies to: all user visible date text
  - valid example: dayIndex 15 in March bid month -> March 17
  - invalid example: dayIndex 15 -> March 16
- Rule D2: analyzer reports mismatch when current and desired X counts differ
  - passes when: warning appears if counts differ, absent if equal
  - fails when: mismatch is not reported
  - UI message: X-day count mismatch: Current has {currX}, Desired has {desX}.
  - Prevents PCS analyzer from running
- Rule D3:
  - Block of CI days must touch first day of bid period.
    - fails when: CI days are present anywhere in the month but not on the first day of the bid period.
    - passes when: bid period begins with any number of CI days but there are no more separate instances of CI days in the month.
    - valid example: March 2-4 are CI. March 5 is X
    - invalid example: March 2 is X. March 3-5 are CI.
    - Prevents PCS analyzer from running
    - Displays error "Check CI day placement in current month"
- Rule D4:
  - Results for a valid schedule should:
    - pair removed X days with added X days chronologically 1:1
    - merge consecutive pairs where both source and destination are consecutive days so the user sees "X Day Moves: June 2-4 -> June 7-9.
- Rule D5:
  - In the PCS Analysis display window, replace the variable "minWork" with "minimum on-call duration"
    - example: "work block length 1 is below minWork (4)" becomes "1 day on call is below the minimum on-call duration (4)."
- Rule D6:
  - If the start and end date are the same, only display one date.
    - example: "March 26–March 26" becomes "March 26"
- Rule D7:
  - User cannot add A, CI, or CQ in desired schedule. Those days can only be added to Current schedule and should be mirrored into the Desired Schedule.
    - fails when: User selects CI and then paints a date on the desired schedule with CI.
    - fails when: User selects A and then paints a date on the desired schedule with A.
    - passes when: User selects CQ and then attempts to paint on the desired schedule and nothing changes.
    - passes when: User selects A and then attempts to paint on the desired schedule and nothing changes.
- Rule D8:
  - If the analysis results in an error and that individual error contains dates in the same months, drop the month name on the second date.
  - example: "March 2–March 3: 2 days on call is below the minimum on-call duration (4)" should be "March 2-3: 2 days on call is below the minimum on-call duration (4)."
- Rule D9: Frozen-day mismatch blocks analysis entirely.
  - The earliest movable day is D+2 (two calendar days from today). Days before that index are frozen.
  - If any frozen day differs between current and desired, raise a blocked failure immediately — do not run any pathfinding or validation checks.
  - Prevents analyzer from running
  - fails when: desired differs from current on any day before D+2
  - passes when: all days before D+2 are identical between current and desired
  - UI message: "{date} cannot be changed — it is within the 2-day submission window."
- Rule D10: If the pathfinder solution requires adding or removing an X day in the current bid period and the current date is the 11th through the 17th, add a caution warning in yellow with the pathfinder result.
  - example: Today is March 12. The pathfinder solution requires moving an X day from March 29 to March 27. Assume the move is legal for all other rules. Because today is between the 11th and 17th and the current bid period is March 2 - March 31, any moves between March 26 and March 31 may not be allowed immediately. Do not stop the pathfinder. This is cautionary only.

Pathfinding rules:

- Rule P1: CQ does not count as work days and cannot be used to create a work block by PCS.
  - valid example: PCS analyzer can create this pattern: [X-X-X-R-R-R-R-CQ-CQ]
  - See exception P3.E2 for exceptions
- Rule P1.1: IVD does not count as work days and cannot be used to create a work block by PCS.
  - valid example: PCS analyzer can create this pattern: [X-X-X-R-R-R-R-IVD-IVD]
  - See exception P3.E2 for exceptions
- Rule P2: Only X day can be moved and only onto R days.
  - fails when: X day moved onto A, CI, or CQ day
  - passes when: All X days in desired calendar were R or X days in current calendar
  - fails when: Any X day in desired calendar was A, CI, or CQ day in current calendar
  - valid example: March 1 is an R day on current calendar. March 1 is X day on desired calendar.
- Rule P3: Unless excepted, work block must meet or exceed minWork
  - fails when: length of work block < minWork
  - passes when: length of work block => minWork
  - valid example: minWork = 4; [X-X-X-R-R-R-R-X-X-X]
  - invalid example: minWork = 5; [X-X-X-R-R-X-X-X]
  - exceptions:
    - P3.E1: a work block touching the last day of the bid period is always legal, regardless of length
      - valid example:
        - March 31 is the last day of March bid period.
        - March 29, 30, and 31 can be R and March 28 can be X.
      - invalid example:
        - March 31 is the last day of the bid period.
        - March 29 and 30 cannot be R if March 31 is X because the March 29-30 work block is short but does not touch the end of the month.
    - P3.E2: if a short block touches CQ OR IVD in the current schedule, the corresponding short block in desired can remain short as long as it still touches CQ or IVD.
      - valid example:
        - current schedule: [X-X-R-CQ-CQ-X-X] (per Rule P1, CQ does not count as work days; work block length = 1)
        - desired schedule: [X-R-R-CQ-CQ-X-X] (CQ does not coun as work days; work block length =2. Because work block length was already short, it can remain short)
      - valid example:
        - current schedule: [X-R-R-IVD-R-R-X] (per Rule P1, IVD does not count as work days; work block length = 1)
        - desired schedule: [X-X-R-IVD-R-X-X] (CQ does not coun as work days; work block length =2. Because work block length was already short, it can remain short)
      - CQ-touching block can grow to any length within the confines of other rules.
      - IVD-touching block can grow to any length within the confines of other rules.

- Rule P4: CI counts as R days and satisfies all requirements for contiguous work blocks.
  - Any number of R days may follow a block of CI.
- Rule P5: If a bid period begins with a short work block, that work block can remain short as long as one day in the group remains.
  - valid example:
    - current month starts with [R-R-R-X-X]. That is a short work block (length of work block = 2).
    - desired month starts with [X-R-R-X-X]. That is a short work block and is allowed because the block was already short and Day 2 is in both groups.
  - invalid example:
    - current month starts with [R-R-R-X-X]. That is a short work block (length of work block = 2).
    - desired month starts with [X-X-X-X-R]. That is a short work block but is disallowed because the R day in position 4 does not overlap in any way with the original short work block in positions 0-2.
- Rule P6: If a bid period begins with X days, a new short block can be built starting with the first day of the month.
  - valid example:
    - current month begins with [X-X-X-X-R...]
    - desired month begins with [R-R-X-X-X...]
- Rule P7: If a bid period begins with CI, any number of R days can be added to the end of the CI-block provided they touch the CI block and all R days touching a CI can be removed.
  - vaild example:
    - current month begins with [CI-CI-X-X-X]
    - desired month begins with [CI-CI-R-X-X...]
  - invalid example:
    - current month begins with [CI-CI-X-X-X]
    - desired month begins with [CI-CI-X-R-X...]. This does not touch the CI so it must comply with minWork.
  - valid example:
    - current month begins with [CI-CI-R-X-X...]
    - desired month begins with [CI-CI-X-X-X...]
- Rule P8: The first day of the bid period is always the start of the bid period. CI does not change that.
  - fails when: March 2 is the start of the bid period per function generateBidMonths(), but any other day is seen as the start of the month within these rules.
  - passes when: March 2 is the start of the bid period per function generateBidMonths(), and March 2 is used as the "start" of the March bid period for the purpose of judging any rule.
  - valid example:
    - March 2 is X and March 2 is used as the start of the bid period.
    - March 2 is CI and March 2 is used as the start of the bid period.
    - March 2 is R and March 2 is used as the start of the bid period.
  - invalid examples:
    - March 2 is CI and March 3 is used as the start of the bid period.
- Rule P9:
  - IVDs can be placed on ANY R day.
    - valid example:
      - current: X-R-R-R-R-R-X
      - desired: X-R-R-IVD-R-R-X
        Analyzer should return "Place IVD on {date of added IVD}" in the results.
- Rule P10: X days moved from a block must be contiguous and must include the block's first or last day (implements contract section 8.a).
  - The "moved" X days from any single X-day block must be either:
    1. The entire block
    2. A contiguous prefix (starting at the block's first day)
    3. A contiguous suffix (ending at the block's last day)
  - fails when: X days removed from a block are non-contiguous
  - fails when: X days removed from a block are contiguous but don't touch the first or last day of the block
  - passes when: removed X days start at the block's first day
  - passes when: removed X days end at the block's last day
  - valid example: block [X-X-X-X], remove first 3 → [R-R-R-X]: prefix including first day ✓
  - valid example: block [X-X-X-X], remove last 3 → [X-R-R-R]: suffix including last day ✓
  - invalid example: block [X-X-X-X], remove middle 2 → [X-R-R-X]: touches neither first nor last ✗
- Rule P11: If a direct X-day move is blocked by P10, the desired schedule may still be reachable via two separate PCS runs, each independently satisfying all rules (including P10).
  - The app will identify and display valid two-run sequences when found.
  - Each run is submitted as a separate PCS change request.
  - valid two-run example: to move days from the middle of block [S..E]:
    - Run 1: move suffix [A+1..E] to desired positions (valid: touches last day E of block)
    - Run 2: move [A] — now the last day of the shortened block [S..A] — to its final position (valid: touches last day A)
- Rule P12: Certain dates may be marked as staffing-blocked, meaning the company has determined that minimum on-call headcount would be violated if any additional employee took that day off.
  - A staffing-blocked date forbids R→X transitions on that date only. It does not affect X→R or X→X.
  - fails when: desired has X on a staffing-blocked date that was R in current (new day-off placed on a blocked date)
  - passes when: current already has X on a staffing-blocked date and desired keeps it X (no move, no violation)
  - passes when: current has X on a staffing-blocked date and desired moves it away to an unblocked date (removing a day off from a blocked date is always allowed)
  - Blocked date set is external to the employee's schedule — it comes from company-wide headcount data and must be supplied as input to the analyzer.
  - If all valid destinations for a required X-day move are staffing-blocked, the analyzer must report the move as impossible.
  - Staffing-blocked dates apply equally to intermediate states in two-run plans (P11): neither Run 1 nor Run 2 may place a new X on a blocked date.
