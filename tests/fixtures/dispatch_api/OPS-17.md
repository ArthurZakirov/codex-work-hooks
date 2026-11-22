# OPS-17 · Delete a dispatch manifest

Requested by Morgan, Dispatch Operations.

- DELETE /manifests/{id} removes the existing manifest and returns HTTP 204 with an empty body.
- GET for the deleted manifest returns 404. DELETE for an unknown ID returns 404.
