# Publicly Undocumented Blackboard Endpoints

This file records endpoints absent from the available public Blackboard API
reference.

## `GET /learn/api/public/v1/institutionalHierarchy/nodes/{nodeId}/courses`

### Purpose

Returns associations between an institutional-hierarchy node and its courses.
`{nodeId}` accepts the node identifier, including `externalId:<value>` when the
instance supports it.

### Response shape

The response is a paginated collection of associations. An item can include:

```json
{
  "nodeId": "_9_1",
  "courseId": "_8_1",
  "isPrimary": true
}
```

- `nodeId`: primary ID of the associated node.
- `courseId`: primary ID of the associated course.
- `isPrimary`: whether the node is the course's primary association.

## `GET /learn/api/public/v1/institutionalHierarchy/nodes/{nodeId}/users`

### Purpose

Returns users associated with an institutional-hierarchy node.

### Response shape

The response is a paginated collection of users associated with the node. Each
item normally contains the user's primary identifier, external identifier, and
username.

```json
{
  "userId": "_8907_1",
  "externalId": "user-external-id",
  "userName": "user"
}
```
