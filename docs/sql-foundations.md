---
layout: default
title: "Learn SQL Basics — A Beginner's Guide to SQL with Examples and Exercises"
description: "Free SQL tutorial for beginners. Learn SELECT, WHERE, JOIN, GROUP BY, ORDER BY, SUM, COUNT with real examples and practice exercises. Plain English, no jargon."
---

# Learn SQL Basics — A Beginner's Guide to SQL with Examples and Exercises

**A free, plain-English SQL reference for beginners.**
Covers SELECT, WHERE, JOIN, GROUP BY, ORDER BY, SUM, COUNT, and more —
with real examples, practice exercises, and zero jargon.

> Part of the [NEXUS](https://github.com/michaelnocito/nexus-sql-mystery) project —
> a free game where you learn SQL by solving a corporate fraud mystery.
> This guide covers every SQL concept taught in Season 1 and works as a
> standalone reference even if you don't play the game.

This isn't a textbook. It's the cheat sheet your future self will want
when you sit down at a job and someone says, "Can you pull that data?"

**What's covered:** SELECT, FROM, WHERE, COUNT, SUM, GROUP BY, ORDER BY,
JOIN, IN, HAVING, primary keys, foreign keys, aliases, subqueries,
NULL handling, and the SQL order of operations.

---

## How SQL Works (30-Second Version)

SQL (Structured Query Language) is how you talk to databases. A database
stores information in **tables** — think spreadsheet tabs. Each table has
**columns** (fields) and **rows** (records). You write queries to ask
questions about the data, and the database answers.

Every query follows the same basic shape:

```sql
SELECT what_you_want
FROM which_table
WHERE some_condition;
```

That's it. Everything else is a variation on that pattern.

---

## The Concepts

### 1. Tables

**What it is:**
A table stores data in rows and columns — like one tab in a spreadsheet.
A database is just a collection of related tables.

**Why it matters:**
Before you can analyze anything, you need to know what tables exist
and what data lives in each one.

**Syntax:**
```sql
-- List all tables in the database
SELECT name FROM sqlite_master WHERE type='table';
```

**Real-world analogy:**
A database is a filing cabinet. Each table is a labeled drawer —
"Employees," "Transactions," "Vendors."

**Common mistake:**
Table names are case-sensitive in some databases.
Always check the exact name before querying.

**In the investigation:**
You logged into the Nexus database and found 5 tables: employees,
vendors, transactions, departments, and projects. This was your map.

---

### 2. SELECT * FROM

**What it is:**
`SELECT` retrieves data. The asterisk `*` means "every column."
`FROM` names the table you're pulling from.

**Why it matters:**
The first thing you do with any new dataset: look at it.
`SELECT *` is your starting point.

**Syntax:**
```sql
SELECT * FROM employees;
SELECT * FROM transactions;
```

**Real-world analogy:**
Opening a spreadsheet and scrolling through all the rows before
you decide what to focus on.

**Common mistake:**
`SELECT *` on a huge table can be slow. Add `LIMIT 10` to preview
without loading millions of rows:
```sql
SELECT * FROM transactions LIMIT 10;
```

**In the investigation:**
You pulled the full employee roster — 10 people including yourself,
Alex Chen. This told you who works here and in which departments.

---

### 3. COUNT(*)

**What it is:**
`COUNT(*)` is an **aggregate function**. Instead of returning every
matching row, it collapses them into a single number: the count.

**Why it matters:**
"How many customers do we have?" "How many transactions happened
this month?" COUNT answers those instantly.

**Syntax:**
```sql
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM transactions WHERE vendor_id = 4;
```

**Real-world analogy:**
Asking someone to count the people in a room vs. listing every
person's name. You just want the number.

**Common mistake:**
`COUNT(*)` counts all rows, including ones with NULL values.
`COUNT(column_name)` skips rows where that column is NULL.
They give different numbers if your data has gaps.

**In the investigation:**
Sam asked for a headcount. You ran `COUNT(*)` on employees and
got 10. Quick, clean, useful.

---

### 4. WHERE

**What it is:**
`WHERE` limits your results to only rows that match a condition.
Everything that doesn't match gets filtered out.

**Why it matters:**
Real datasets have thousands or millions of rows. WHERE is how
you zoom in on just what matters.

**Syntax:**
```sql
SELECT * FROM vendors WHERE verified = 0;
SELECT * FROM employees WHERE department = 'Finance';
```

**Comparison operators:**
| Operator | Meaning |
|----------|---------|
| `=` | Equal to |
| `!=` or `<>` | Not equal to |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal to |
| `<=` | Less than or equal to |

**Real-world analogy:**
Ctrl+F in a spreadsheet — but instead of highlighting matches,
it hides everything that doesn't match.

**Common mistake:**
Strings need quotes: `WHERE name = 'Alex'`.
Numbers don't: `WHERE id = 4`.
Mix them up and you'll get errors.

**In the investigation:**
You filtered vendors where `verified = 0` and found two unverified
companies: Apex Solutions LLC and Pinnacle Strategy Group.
No address. No phone. Red flags everywhere.

---

### 5. SUM()

**What it is:**
`SUM()` adds up all the values in a column. Like COUNT, it's an
aggregate function — it collapses rows into a single number.

**Why it matters:**
"How much did we spend on this vendor?" "What's our total revenue?"
SUM is the answer.

**Syntax:**
```sql
SELECT SUM(amount) FROM transactions;
SELECT SUM(amount) FROM transactions WHERE vendor_id = 4;
```

**Real-world analogy:**
Adding up all the receipts in a folder to get a total.

**Common mistake:**
`SUM()` returns NULL if no rows match your WHERE clause.
Wrap it in `COALESCE` to get 0 instead:
```sql
SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE vendor_id = 99;
-- Returns 0 instead of NULL when nothing matches
```

**In the investigation:**
You totalled all payments to Apex Solutions — over $1.2 million
to a company with no verified address.

---

### 6. GROUP BY

**What it is:**
`GROUP BY` bundles rows that share a value into groups, then lets
you run aggregates (SUM, COUNT, AVG) on each group separately.

**Why it matters:**
"How much did we spend **per vendor**?" "How many orders
**per customer**?" GROUP BY splits the data into piles and lets
you summarize each pile.

**Syntax:**
```sql
SELECT vendor_id, SUM(amount) AS total
FROM transactions
GROUP BY vendor_id
ORDER BY total DESC;
```

**Real-world analogy:**
Sorting receipts by category — groceries, utilities, restaurants —
and totalling each pile.

**Common mistake:**
Every column in your SELECT must either appear in GROUP BY or be
inside an aggregate function (SUM, COUNT, AVG, etc.). If you select
a column without grouping or aggregating it, the database won't
know which value to show.

```sql
-- ✅ Correct
SELECT vendor_id, SUM(amount) FROM transactions GROUP BY vendor_id;

-- ❌ Wrong — 'date' isn't grouped or aggregated
SELECT vendor_id, date, SUM(amount) FROM transactions GROUP BY vendor_id;
```

**In the investigation:**
You ranked vendors by total spend. Two vendor IDs — 4 and 7 — were
dramatically higher than everything else. That's the pattern that
cracked the case open.

---

### 7. ORDER BY

**What it is:**
`ORDER BY` sorts your results. `ASC` = smallest first (default).
`DESC` = largest first.

**Why it matters:**
"Who are our top 10 customers?" "What's our biggest expense?"
Sorting reveals the outliers immediately.

**Syntax:**
```sql
SELECT * FROM departments ORDER BY budget DESC;
SELECT * FROM employees ORDER BY name ASC;
```

**Sorting by multiple columns:**
```sql
SELECT * FROM transactions ORDER BY vendor_id ASC, amount DESC;
-- First sort by vendor, then within each vendor sort by amount
```

**Real-world analogy:**
Clicking a column header in a spreadsheet to flip between A→Z and Z→A.

**Common mistake:**
ORDER BY runs **after** WHERE and GROUP BY. You're sorting the final
result, not the raw table. The order of operations matters:

```
FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

**In the investigation:**
You sorted Apex transactions by date and watched the amounts escalate:
$87K → $243K in 9 months. He was getting bolder. ORDER BY made the
pattern undeniable.

---

### 8. JOIN

**What it is:**
`JOIN` combines rows from two tables where a column matches.
Think of it as a VLOOKUP that actually works properly.

**Why it matters:**
Data is intentionally split across tables to avoid duplication.
JOINs let you reassemble the pieces for analysis.

**Syntax:**
```sql
SELECT t.date, t.amount, v.name
FROM transactions t
JOIN vendors v ON t.vendor_id = v.id;
```

**Table aliases:**
The `t` and `v` after table names are aliases — shortcuts so you
don't have to type `transactions.date` every time.

**Types of JOINs:**
| Type | What it keeps |
|------|---------------|
| `JOIN` (or `INNER JOIN`) | Only rows that match in **both** tables |
| `LEFT JOIN` | All rows from the left table, matched or not |
| `RIGHT JOIN` | All rows from the right table |
| `FULL OUTER JOIN` | Everything from both tables |

**Real-world analogy:**
You have a list of order IDs and a separate list of customer names.
JOIN links them by the shared ID so you can see which customer made
which order.

**Common mistake:**
If the join column has NULLs, those rows get dropped with a regular
JOIN. Use `LEFT JOIN` if you need to keep unmatched rows.

**In the investigation:**
You linked transactions to vendor names and confirmed — every large
unverified payment went to Apex or Pinnacle. Without the JOIN, you
only had vendor IDs. With it, you had names.

---

### 9. Primary Keys & Foreign Keys

**What it is:**
A **primary key** is a unique ID column — no two rows share the same
value. A **foreign key** is a column in one table that points to the
primary key of another table. Together, they're how tables connect.

**Why it matters:**
When you see `approved_by` in the transactions table with a value of
`4`, that's a foreign key pointing to `id = 4` in the employees table.
Understanding this link is how you follow the trail.

**Syntax:**
```sql
-- employees.id is a primary key (unique per employee)
SELECT * FROM employees WHERE id = 4;

-- transactions.approved_by is a foreign key → employees.id
SELECT * FROM transactions WHERE approved_by = 4;
```

**Real-world analogy:**
A social security number — unique per person, used to link records
across different systems (tax records, bank accounts, medical files).

**Common mistake:**
Primary keys usually auto-increment (1, 2, 3...) but don't assume
they start at 1 or have no gaps. Deleted rows can leave holes.

**In the investigation:**
Every suspicious transaction had `approved_by = 4`. You looked up
employee #4 — Marcus Webb, the CFO. The foreign key led you straight
to the person signing off on the fraud.

---

### 10. IN

**What it is:**
`IN` lets you match a column against multiple values at once.
It replaces a stack of `OR` conditions.

**Why it matters:**
"Show me transactions from vendors 4 and 7." IN is cleaner, faster,
and easier to read than chaining ORs.

**Syntax:**
```sql
SELECT * FROM transactions
WHERE vendor_id IN (4, 7);

-- Equivalent to:
SELECT * FROM transactions
WHERE vendor_id = 4 OR vendor_id = 7;
```

**Advanced — subqueries with IN:**
```sql
SELECT * FROM transactions
WHERE vendor_id IN (
    SELECT id FROM vendors WHERE verified = 0
);
-- Finds all transactions from unverified vendors
```

**Real-world analogy:**
A guest list check — is this name on the list? If yes, include them.

**Common mistake:**
`NOT IN` is powerful but dangerous with NULLs. If any value in the
list is NULL, `NOT IN` returns no results. Filter NULLs out first.

**In the investigation:**
You queried both shell companies at once — `WHERE vendor_id IN (4, 7)`.
Same approver, same pattern, thirteen months of payments.

---

### 11. HAVING

**What it is:**
`HAVING` is like `WHERE`, but it filters **after** aggregation.
Use it when you need to filter on aggregated values (SUM, COUNT, AVG).

**Why it matters:**
"Show me vendors where total spend exceeds $100,000." You can't use
WHERE here because the total doesn't exist until GROUP BY runs.

**Syntax:**
```sql
SELECT vendor_id, SUM(amount) AS total
FROM transactions
GROUP BY vendor_id
HAVING total > 100000;
```

**WHERE vs. HAVING:**
```sql
-- WHERE filters individual rows BEFORE grouping
SELECT vendor_id, SUM(amount) FROM transactions
WHERE amount > 1000
GROUP BY vendor_id;

-- HAVING filters groups AFTER aggregation
SELECT vendor_id, SUM(amount) AS total FROM transactions
GROUP BY vendor_id
HAVING total > 100000;
```

**Common mistake:**
Using WHERE when you mean HAVING (or vice versa). Rule of thumb:
if you're filtering on a SUM, COUNT, or AVG, use HAVING.

**In the investigation:**
You combined aggregates to calculate the total fraud amount across
both shell companies: $1,869,500.

---

## SQL Order of Operations

This is the order SQL actually processes your query, regardless of
how you write it:

```
1. FROM      — Which table(s)?
2. JOIN      — Combine tables
3. WHERE     — Filter individual rows
4. GROUP BY  — Bundle rows into groups
5. HAVING    — Filter groups
6. SELECT    — Choose which columns to show
7. ORDER BY  — Sort the results
8. LIMIT     — Cap the number of rows returned
```

You write `SELECT` first, but the database processes `FROM` and
`WHERE` before it even looks at what you're selecting.

---

## Quick Reference Card

| When you need to... | Use this |
|---|---|
| See what tables exist | `SELECT name FROM sqlite_master WHERE type='table';` |
| Look at all data in a table | `SELECT * FROM table_name;` |
| Preview a big table | `SELECT * FROM table_name LIMIT 10;` |
| Count rows | `SELECT COUNT(*) FROM table_name;` |
| Filter rows | `SELECT * FROM table_name WHERE condition;` |
| Add up a column | `SELECT SUM(column) FROM table_name;` |
| Group and summarize | `SELECT col, SUM(val) FROM table GROUP BY col;` |
| Sort results | `SELECT * FROM table_name ORDER BY column DESC;` |
| Connect two tables | `SELECT * FROM a JOIN b ON a.id = b.a_id;` |
| Match a list of values | `WHERE column IN (1, 2, 3)` |
| Filter after grouping | `HAVING SUM(amount) > 1000` |
| Rename a column in output | `SELECT SUM(amount) AS total` |

---

## Practice Exercises

You finished the investigation. Now build the muscle memory.
These exercises use the same NEXUS database — open the game
and try them. No objectives required, just you and the SQL editor.

### Warm-Up (SELECT, WHERE, COUNT)

1. **List all departments.** Just the names.
2. **Find all employees in the Finance department.**
3. **Count how many transactions exist in the database.**
4. **Find all transactions over $100,000.**
5. **List vendors that ARE verified** (the opposite of what you did in the game).

### Intermediate (GROUP BY, ORDER BY, SUM)

6. **Count how many employees are in each department.**
   _Hint: GROUP BY department, COUNT(*)_
7. **Find the average transaction amount per vendor.**
   _Hint: Use AVG(amount) instead of SUM(amount)_
8. **List all departments sorted by budget, smallest to largest.**
9. **Find the total transaction amount per month.**
   _Hint: You can GROUP BY a partial date using substr(date, 1, 7)_
10. **Which employee approved the most transactions?**
    _Hint: GROUP BY approved_by, COUNT(*), ORDER BY ... DESC_

### Advanced (JOIN, IN, Subqueries)

11. **Show every transaction with the approver's full name** (not just their ID).
    _Hint: JOIN transactions with employees ON approved_by = employees.id_
12. **Find all transactions approved by someone in the Finance department.**
    _Hint: You'll need a JOIN or a subquery with IN_
13. **List vendors who have never had a transaction.**
    _Hint: LEFT JOIN vendors to transactions, look for NULLs_
14. **Calculate the average transaction amount for verified vs. unverified vendors.**
    _Hint: JOIN, GROUP BY verified, AVG(amount)_
15. **Find the month with the highest total spending.**
    _Hint: GROUP BY substr(date, 1, 7), SUM, ORDER BY ... DESC, LIMIT 1_

### Challenge (Combine Everything)

16. **Build the fraud summary yourself.** Write a single query that shows:
    vendor name, total amount paid, number of transactions, and whether
    they're verified — for every vendor — sorted by total amount descending.

    When you nail this one, you've got real analyst skills.

---

## Glossary

| Term | Definition |
|---|---|
| **Query** | A question you ask the database, written in SQL |
| **Table** | A structured set of data organized in rows and columns |
| **Row** (record) | One entry in a table (one employee, one transaction) |
| **Column** (field) | One attribute (name, amount, date) |
| **Primary key** | A unique identifier for each row in a table |
| **Foreign key** | A column that references the primary key of another table |
| **Aggregate function** | A function that combines multiple rows into one value (COUNT, SUM, AVG, MIN, MAX) |
| **NULL** | A missing or unknown value — not zero, not empty string, just absent |
| **Alias** | A temporary name for a column or table (`AS total`, `FROM transactions t`) |
| **Subquery** | A query nested inside another query |
| **Schema** | The structure of a database — what tables exist and what columns they have |
| **SQLite** | The lightweight database engine NEXUS uses. No server required — the whole database is one file |
| **CRUD** | Create, Read, Update, Delete — the four basic operations on data |

---

## What's Next

Season 1 covered SQL fundamentals — the tools you need for 80% of
real-world data analysis work. Season 2 introduces Python alongside SQL,
which is where things get interesting (and a little... strange).

Until then, the best thing you can do is practice. Open the game,
run queries, break things, fix them. Every analyst you'll ever meet
got good the same way: by writing queries until the syntax stopped
feeling foreign and started feeling like thinking.

---

_Part of the [NEXUS](https://github.com/michaelnocito/nexus-sql-mystery) project
by [Michael Nocito](https://github.com/michaelnocito)._
