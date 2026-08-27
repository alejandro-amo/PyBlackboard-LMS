# Integration test plan

## Purpose

Validate the public `BlackboardAPI` facades against the dedicated Blackboard
test tenant. The suite uses a single generated resource graph, avoids global
collection scans, and performs all mutations only on resources it created.

## Execution contract

- Run explicitly with `python -m tests.integration.run`.
- Require a valid repository-local `.env.test.local` file.
- Use the test tenant only; never production credentials or production data.
- The runner writes logs to standard output and to ignored
  `data/test-artifacts/logs/`. It must not log credentials, tokens, passwords,
  or full sensitive payloads.
- Blackboard consistency is eventual. Every verification after a mutation
  waits two seconds before its first read.
- The final cleanup test is always last. The `atexit` cleanup is only a
  fallback for interrupted runs.

## Ordered test sequence

1. **Connectivity and API quota**
   - Authenticate with the test configuration.
   - Read API quota information and warn when fewer than 1,000 requests remain.
   - Do not export resource data in this group.

2. **Base fixtures**
   - Create two terms, two nodes, five users, and two courses.
   - All fixtures use a unique, generated run prefix.

3. **Identifier compatibility**
   - After two seconds, read every fixture through its primary ID and every
     additional identifier actually returned by Blackboard.
   - Users: `externalId`, `userName`, and `uuid` when present.
   - Courses: `externalId`, `courseId`, and `uuid` when present.
   - Nodes and terms: `externalId` when present.

4. **Comprehensive updates**
   - Update all currently supported mutable fields of one term, node, user,
     and course.
   - Change the selected user's `userName` through `users.change_username()`.
   - Wait two seconds and read each object to verify all changed values.

5. **Availability transitions**
   - For one user and one course, set availability to `No`, `Disabled`, and
     finally `Yes`.
   - Wait two seconds and verify after every transition.

6. **Course-one enrollments**
   - Create one enrollment for each of the five users in course one.
   - Wait two seconds and use `enrollments.list_by_course()` to verify them.

7. **Course-two enrollments**
   - Create one enrollment for each of the five users in course two.
   - Wait two seconds and use `enrollments.list_by_course()` to verify them.

8. **Per-user enrollment lists**
   - Wait two seconds and use `enrollments.list_by_user()` for every user.
   - Verify each contains the two fixture courses.

9. **Exports**
   - After two seconds, export the fixture terms, nodes, users, courses,
     enrollments, and enrollment roles to temporary CSV, Excel, and JSON files.
   - Validate CSV and JSON again through standard output.
   - Excel without an output file must be rejected because binary Excel data is
     intentionally not written to standard output.

10. **Enrollment removal**
   - Delete every fixture enrollment from both courses.
   - Wait two seconds and verify via the two bounded course enrollment lists.

11. **Primary node membership**
    - Associate every user with node one using `primary=True`.
    - Wait two seconds and verify through `users.list_by_node()`.

12. **Secondary node membership**
    - Associate every user with node two using `primary=False`.
    - Wait two seconds and verify through `users.list_by_node()`.

13. **Node membership removal**
    - Remove every user from both nodes.
    - Wait two seconds and verify both bounded node user lists no longer
      include any fixture user.

14. **Course-term association and reassignment**
    - Assign both courses to term one; wait two seconds and verify each course
      resolves to term one through `terms.get_by_course()`.
    - Reassign both courses to term two; wait two seconds and verify each now
      resolves to term two. A course therefore has only its current term.
    - Wait two seconds and verify `courses.list_by_term(term_identifier=...)`
      returns both fixture courses for term two.

15. **Cleanup**
    - Delete remaining relationships and every fixture resource in dependency
      order.
    - Wait two seconds and verify every fixture primary ID returns
      `NotFoundError`.

## Data and privacy rules

- Use only generated synthetic data in the Blackboard test tenant.
- Do not commit credentials, test exports, tokens, or passwords.
- Assertions must use the generated fixture IDs, never unrelated tenant data.
