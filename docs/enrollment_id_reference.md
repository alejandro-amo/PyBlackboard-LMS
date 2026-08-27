# Identifiers Accepted by Enrollment Methods

This table documents validation applied before each request is built. The types
come from Blackboard's public reference and read-only verification.

Confirmed `GET` identifier types are also accepted for `PUT`, `PATCH`, and
`DELETE` on the same endpoint unless Blackboard documents a restriction.

| API method | Endpoint | Parameter | Accepted types |
|---|---|---|---|
| `enrollments.create` | `PUT /courses/{courseId}/users/{userId}` | `course_identifier` | primary, `externalId`, `courseId`, UUID |
| `enrollments.create` | `PUT /courses/{courseId}/users/{userId}` | `user_identifier` | primary, `externalId`, `userName`, UUID |
| `enrollments.get` | `GET /courses/{courseId}/users/{userId}` | both | same types as above |
| `enrollments.update` | `PATCH /courses/{courseId}/users/{userId}` | both | same types as above |
| `enrollments.delete` | `DELETE /courses/{courseId}/users/{userId}` | both | same types as above |
| `enrollments.list_by_course` | `GET /courses/{courseId}/users` | `course_identifier` | primary, `externalId`, `courseId`, UUID |
| `enrollments.list_by_user` | `GET /users/{userId}/courses` | `user_identifier` | primary, `externalId`, `userName`, UUID |
| `enrollments.list_course_roles` | `GET /courseRoles` | none | not applicable |

## Read-only verification results

- A course UUID worked with `GET /courses/{courseId}` and `GET /courses/{courseId}/nodes`.
- Enrollment listing by course worked with primary ID, `courseId`, `externalId`, and UUID.
- Enrollment listing by user worked with primary ID, `externalId`, `userName`, and UUID.
- Nodes do not expose `uuid`; their confirmed types are primary ID and `externalId`.

## Input convention

Methods receive typed identifiers such as `externalId:MAT-001`,
`courseId:MAT-001`, `userName:user@example.com`, `uuid:...`, or `_1234_1`.
Common validation rejects unsupported types before making a request.

## Sources

- [Blackboard Create Membership](https://www.postman.com/insead-apis/higher-ed-rest-apis/request/rvd27pg/blackboard-create-membership)
- [Blackboard Get Course Memberships](https://www.postman.com/insead-apis/higher-ed-rest-apis/request/q8mqgg8/blackboard-get-course-memberships)
- [Blackboard SOAP-to-REST](https://docs.blackboard.com/docs/blackboard/rest-apis/advanced/soap-to-rest)
