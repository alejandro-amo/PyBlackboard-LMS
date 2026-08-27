# API Reference

`BlackboardAPI` and its facades are the public API. `resources`, `services`,
and the facade implementation are internal details.

## Initialization

```python
from blackboard_api import BlackboardAPI

client = BlackboardAPI(
    url="https://blackboard.example.com",
    client_id="...",
    client_secret="...",
    enable_write=False,
)
```

```python
BlackboardAPI(
    url=None,
    client_id=None,
    client_secret=None,
    env_file="path/to/config.env",
    enable_write=False,
    max_retries=None,
    results_per_page=100,
)
```

When credentials are omitted, `env_file` is required and credentials are loaded
from that file. The API never selects a default ENV file.
`enable_write` always defaults to `False`; the ENV file cannot enable writes.
Pass `enable_write=True` explicitly to allow mutations. With writes disabled,
`POST`, `PUT`, `PATCH`, and `DELETE` are blocked before transmission.

`BB_REQUEST_CONNECT_TIMEOUT` and `BB_REQUEST_READ_TIMEOUT` are optional ENV
settings expressed as positive integer seconds. They default to `10` seconds
for connection and `60` seconds for reads. They are deliberately omitted from
`.env.example`; set them only when the target environment needs different
timeouts.

`results_per_page` is optional and defaults to `100`, the maximum accepted by
the verified Blackboard instance. Do not change it without verifying that the
target instance accepts another value. Continuation URLs (`paging.nextPage`)
are followed exactly as Blackboard returns them.

## Client state

- `token`: current token, or `None` before authentication.
- `api_quota_remaining`: known remaining API requests, or `None`.
- `max_requests_per_day`: known daily request maximum, or `None`.

Authentication, headers, API quota refresh, HTTP requests, and pagination are
internal implementation details.

## Identifiers

Identifier parameters are keyword-only and validated before building a route.
An unprefixed value is a primary ID.

- Courses: primary ID, `externalId`, `courseId`, and `uuid`.
- Users: primary ID, `externalId`, `userName`, and `uuid`.
- Nodes: primary ID and `externalId`.
- Terms: primary ID and `externalId`.

Examples: `courseId:COURSE-1`, `externalId:USER-1`,
`userName:user@example.com`, `uuid:...`, and `_1234_1`.

These forms locate existing resources. Blackboard generates the primary `id`
for every resource and `uuid` for courses and users. `create()` therefore
rejects top-level `id` and `uuid`. Nodes and terms do not document a `uuid`.

| Resource | Required creation fields | Optional client-controlled identifier |
|---|---|---|
| Course | `courseId`, `name` | `externalId` (defaults to `courseId`) |
| User | `userName`, `password`, `name` | `externalId` (defaults to `userName`) |
| Term | `externalId`, `name` | — |
| Node | `title` | `externalId` |

`courseId` is the visible course code, not the primary `id`. Blackboard's web
UI calls a term's `externalId` **Source ID**.

## Availability

Courses, users, and enrollments provide:

- `set_available(...)`: sets `availability.available` to `Yes`.
- `set_unavailable(...)`: sets it to `No`.
- `set_disabled(...)`: sets it to `Disabled`.

They use `PATCH` and accept the same identifier types as `update`. `No` makes
the resource unavailable; `Disabled` retains a disabled record, usually under
SIS or administrative data-state control. Course availability may also inherit
from its term.

## Public facades

### `client.courses`

`list()`, `iter()`, `get(*, course_identifier)`, `create(data)`,
`update(*, course_identifier, data)`, `delete(*, course_identifier)`,
`set_available`, `set_unavailable`, and `set_disabled` implement course CRUD.
Course CRUD uses public v2 endpoints. `assign_node`, `unassign_node`,
`list_by_node`, and `iter_by_node` use documented v1 node associations.
`assign_term(*, course_identifier, term_identifier)` resolves the term and
updates `termId`; `unassign_term(*, course_identifier)` removes it.
`list_by_term(*, term_identifier)` returns the courses assigned to a term,
using Blackboard's filtered v2 course collection endpoint.
`get_copy_history(*, course_identifier)` returns the copy history of a given
course.

### `client.users`

`list()`, `iter()`, `get(*, user_identifier)`, `create(data)`,
`update(*, user_identifier, data)`, `delete(*, user_identifier)`,
`set_available`, `set_unavailable`, and `set_disabled` implement user CRUD.
`assign_node`, `unassign_node`, `list_by_node`, and `iter_by_node` manage node
membership. `change_username(*, current_username, new_username)` updates a
user through the typed `userName:...` identifier.

`assign_node(..., primary=False)` was accepted by the test tenant even when the
user had no remaining primary-node association. The node-membership list
response confirms the association but does not expose an `isPrimary` field, so
the persisted primary flag cannot currently be read back through this facade.
The test tenant also rejects `GET` on the node-user association route with 405,
returns 404 for a user-node association route, and omits `isPrimary` even when
it is requested through `fields`. The `PUT` association response likewise only
contains `nodeId` and `userId`.

### `client.nodes`

`list()`, `iter()`, `get(*, node_identifier)`, `create(data)`,
`update(*, node_identifier, data)`, and `delete(*, node_identifier)` implement
node CRUD. `list_by_course(*, course_identifier)` and
`list_by_user(*, user_identifier)` return a resource's node memberships.

### `client.terms`

Terms represent academic periods and use public v1 endpoints. `list()`,
`iter()`, `get(*, term_identifier)`, `create(data)`,
`update(*, term_identifier, data)`, and `delete(*, term_identifier)` implement
term CRUD. `get_by_course(*, course_identifier)` returns the assigned term or
`None`.

### `client.enrollments`

Atomic methods are `list_by_course`, `iter_by_course`, `list_by_user`,
`iter_by_user`, `get`, `create`, `update`, `delete`, and the three availability
convenience methods. They require keyword-only course and user identifiers.

Composite methods are `find`, `upsert`, `ensure_enrolled`, `change_role`,
`set_availability`, `activate`, `deactivate`, `delete_if_exists`,
`validate_course_role`, `list_for_courses`, `list_for_users`,
`enroll_user_in_courses`, and `enroll_users_in_course`. `upsert` creates or
updates only differing fields and validates course roles through an in-memory,
lazily loaded role cache. Bulk list methods preserve input order and remove
duplicate identifiers.

### `client.enrollment_roles`

`list()` returns all course roles and `iter()` yields them lazily. Roles have
no mutating operations.

### `client.api_quota`

`get()` returns `remaining` and `max_requests_per_day`. API quota is distinct
from the HTTP `limit` pagination parameter and `results_per_page`.

## Internal layers

`Transport.request(..., max_retries=3)` means three additional retries after
the initial attempt: up to four total attempts.

| Layer | Classes | Responsibility |
|---|---|---|
| Public facades | `CourseFacade`, `UserFacade`, `NodeFacade`, `TermFacade`, `EnrollmentFacade`, `EnrollmentRoleFacade`, `ApiQuotaFacade` | Stable public API |
| Facade base | `ResourceFacade` | Shared internal facade base |
| Services | `EnrollmentService`, `CourseService`, `TermService`, `UserService` | Composite coordination |
| Resources | `CourseResource`, `UserResource`, `NodeResource`, `TermResource`, `EnrollmentResource`, `EnrollmentRoleResource` | Atomic HTTP operations |
| Client | `BlackboardAPI` | Authentication, URLs, validation, pagination |
| Transport | `Transport` | Timeout, retries, jitter, API quota |

Services call resources; they never build URLs or invoke `requests` directly.
All requests end in `Transport`.

## Public errors

- `AuthenticationError`: OAuth authentication failed or was invalid.
- `QuotaExhaustedError`: Blackboard reported zero remaining requests.
- `WriteNotEnabledError`: a mutating operation was attempted while writes were
  disabled.
- `NotFoundError`: the resource does not exist.
- `ResponseFormatError`: JSON or collection structure was invalid.
- `TransportError`: a non-recoverable network error occurred.
