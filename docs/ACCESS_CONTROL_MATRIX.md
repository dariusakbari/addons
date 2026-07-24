# GTE Access-Control Matrix

Groups (Green Tech Construction category): Field Employee < Foreman /
Estimator / Safety Lead / Coordinator (imply Field) < Project Manager
(implies Coordinator) < Construction Administrator (implies PM +
Accounting + Safety). Accounting is separate from the field chain.

R=read W=write C=create U=unlink. Record rules additionally restrict
non-manager groups to projects where the user is a follower (member).

| Model | Group | R | W | C | U |
|---|---|---|---|---|---|
| gte.project.budget | pm | 1 | 1 | 1 | 0 |
| gte.project.budget | accounting | 1 | 1 | 1 | 0 |
| gte.project.budget | admin | 1 | 1 | 1 | 1 |
| gte.project.budget.line | pm | 1 | 1 | 1 | 1 |
| gte.project.budget.line | accounting | 1 | 1 | 1 | 1 |
| gte.labour.rate | accounting | 1 | 1 | 1 | 0 |
| gte.labour.rate | pm | 1 | 0 | 0 | 0 |
| gte.labour.rate | admin | 1 | 1 | 1 | 1 |
| gte.worker.cert | field | 1 | 0 | 0 | 0 |
| gte.worker.cert | safety | 1 | 1 | 1 | 0 |
| gte.worker.cert | pm | 1 | 1 | 1 | 0 |
| gte.worker.cert | admin | 1 | 1 | 1 | 1 |
| gte.rfi | field | 1 | 0 | 0 | 0 |
| gte.rfi | foreman | 1 | 1 | 1 | 0 |
| gte.rfi | coordinator | 1 | 1 | 1 | 0 |
| gte.rfi | admin | 1 | 1 | 1 | 1 |
| gte.change.order | field | 1 | 0 | 0 | 0 |
| gte.change.order | estimator | 1 | 1 | 1 | 0 |
| gte.change.order | coordinator | 1 | 1 | 1 | 0 |
| gte.change.order | accounting | 1 | 1 | 0 | 0 |
| gte.change.order | admin | 1 | 1 | 1 | 1 |
| gte.change.order.line | field | 1 | 0 | 0 | 0 |
| gte.change.order.line | estimator | 1 | 1 | 1 | 1 |
| gte.change.order.line | coordinator | 1 | 1 | 1 | 1 |
| gte.change.order.line | accounting | 1 | 1 | 0 | 0 |
| gte.submittal | field | 1 | 0 | 0 | 0 |
| gte.submittal | coordinator | 1 | 1 | 1 | 0 |
| gte.submittal | admin | 1 | 1 | 1 | 1 |
| gte.submittal.revision | field | 1 | 0 | 0 | 0 |
| gte.submittal.revision | coordinator | 1 | 1 | 1 | 0 |
| gte.submittal.spec | field | 1 | 0 | 0 | 0 |
| gte.submittal.spec | coordinator | 1 | 1 | 1 | 0 |
| gte.document.revision.wizard | field | 1 | 1 | 1 | 1 |
| gte.daily.log | field | 1 | 1 | 1 | 0 |
| gte.daily.log | admin | 1 | 1 | 1 | 1 |
| gte.daily.log.labour | field | 1 | 1 | 1 | 1 |
| gte.ncr | field | 1 | 1 | 1 | 0 |
| gte.ncr | admin | 1 | 1 | 1 | 1 |
| gte.inspection | field | 1 | 1 | 1 | 0 |
| gte.inspection | admin | 1 | 1 | 1 | 1 |
| gte.inspection.line | field | 1 | 1 | 1 | 1 |
| gte.site.attendance | field | 1 | 1 | 1 | 0 |
| gte.site.attendance | admin | 1 | 1 | 1 | 1 |
| gte.site.attendance.line | field | 1 | 1 | 1 | 1 |
| gte.visitor.log | field | 1 | 1 | 1 | 0 |
| gte.visitor.log | admin | 1 | 1 | 1 | 1 |
| gte.transmittal | field | 1 | 1 | 1 | 0 |
| gte.transmittal | admin | 1 | 1 | 1 | 1 |
| gte.transmittal.line | field | 1 | 1 | 1 | 1 |
| gte.shop.drawing | field | 1 | 1 | 1 | 0 |
| gte.shop.drawing | admin | 1 | 1 | 1 | 1 |
| gte.gate.pass | field | 1 | 1 | 1 | 0 |
| gte.gate.pass | admin | 1 | 1 | 1 | 1 |
| gte.flha | field | 1 | 1 | 1 | 0 |
| gte.flha | admin | 1 | 1 | 1 | 1 |
| gte.flha.hazard | field | 1 | 1 | 1 | 1 |
| gte.flha.signoff | field | 1 | 1 | 1 | 1 |
| gte.toolbox.talk | field | 1 | 1 | 1 | 0 |
| gte.toolbox.talk | admin | 1 | 1 | 1 | 1 |
| gte.toolbox.attendee | field | 1 | 1 | 1 | 1 |
| gte.incident | field | 1 | 1 | 1 | 0 |
| gte.incident | admin | 1 | 1 | 1 | 1 |
| gte.equipment.inspection | field | 1 | 1 | 1 | 0 |
| gte.equipment.inspection | admin | 1 | 1 | 1 | 1 |
| gte.work.permit | field | 1 | 1 | 1 | 0 |
| gte.work.permit | admin | 1 | 1 | 1 | 1 |
| gte.risk | field | 1 | 1 | 1 | 0 |
| gte.risk | admin | 1 | 1 | 1 | 1 |
| gte.migration.wizard | system | 1 | 1 | 1 | 1 |

Field-level: gte.labour.rate has NO ACL rows for field/foreman groups;
cost_rate column visible only to accounting/admin. Commercial menu
restricted to PM/Accounting. Legacy migration menu: system admins only.