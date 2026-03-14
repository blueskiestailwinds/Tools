Definitions:

X: X-day (off day, the only day PCS can move)
R: Reserve (day of work)
CQ: Training (canoot be moved by PCS)
A: Absensce (cannot be moved by PCS)
CI: Carry-In (cannot be moved by PCS)
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
  - User cannot add CI or CQ in desired schedule. Those days can only be added to Current schedule and should be mirrored into the Desired Schedule.
    - fails when: User selects CI and then paints a date on the desired schedule with CI.
    - passes when: User selects CQ and then attempts to paint on the desired schedule and nothing changes.
- Rule D8:
  -  If the analysis results in an error and that individual error contains dates in the same months, drop the month name on the second date.
  - example: "March 2–March 3: 2 days on call is below the minimum on-call duration (4)" should be "March 2-3: 2 days on call is below the minimum on-call duration (4)."

Pathfinding rules:

- Rule P1: CQ does not count as work days and cannot be used to create a work block by PCS.
  - valid example: PCS analyzer can create this pattern: [X-X-X-R-R-R-R-CQ-CQ]
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
    - P3.E2: if a short block touches CQ in the current schedule, that block can remain short as long as it still touches CQ.
      - valid example:
        - current schedule: [X-X-R-CQ-CQ-X-X] (per Rule P1, CQ does not count as work days; work block length = 1)
        - desired schedule: [X-R-R-CQ-CQ-X-X] (CQ does not coun as work days; work block length =2. Because work block length was already short, it can remain short)
        - CQ-touching block can grow to any length within the confines of other rules.
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
    -  current month begins with [CI-CI-R-X-X...]
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
