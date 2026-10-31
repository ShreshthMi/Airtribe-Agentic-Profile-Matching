# Resume grading: instructions

Thank you for helping. You are grading resumes against real job postings, so that a
resume-screening tool can be checked against human judgement. Your grades are only useful
if they are your own, so please work alone and don't look at what the tool concluded.

## What is in this pack

- `job_descriptions/` - the job postings, one file each (`real_frontend.txt`, ...)
- `resumes/` - 100 short resumes (`.md`, `.txt`, `.pdf`, `.docx`); every person is fictional
- `sheets/` - one spreadsheet per posting, named after it (`real_frontend_A.csv` is the
  frontend posting, for grader A)

## What to do

For each sheet:

1. Read its posting in `job_descriptions/`, carefully, once.
2. For each row, open the resume named in `resume_path` and fill in **human_grade**:
   - **2** - I would invite this person to interview for this posting.
   - **1** - Borderline: close, but I would want more information first.
   - **0** - I would not interview this person for this posting.
3. Optionally, write a one-line reason in **notes** ("no Snowflake", "strong React, junior").

Three sheets list 11 to 17 people; two list all 100. On the long ones most people are
clearly a 0 for that role, and a glance at their skills and job titles is enough.

Postings often ask for things a resume can't show, such as "excellent communication".
Grade on what a resume *can* show; you'd check the rest in the interview anyway.

## Rules

1. Judge only against the posting's requirements. Ignore names, schools, nationality and
   locations.
2. Grade every row with 0, 1 or 2. Don't add, remove or rename columns or rows.
3. Don't discuss grades with the other grader until you have both finished.
4. Save as CSV with the same file name. In Google Sheets: File -> Download -> CSV. In Excel:
   File -> Save As -> "CSV UTF-8". In Numbers: File -> Export To -> CSV.
5. Send the `sheets/` files back when you're done.

## Time

About 1-2 minutes per resume on the short sheets (40 people, roughly an hour), much less on
the 100-row ones (1-1.5 hours each): roughly 3-4 hours in all. It doesn't have to be done in
one sitting.
