# GTE Data Dictionary

Generated from module source, 24 July 2026. One section per model;
shared mixin fields (legacy_source_id, origin_task_id, migration_incomplete,
migration_missing_fields, chatter) apply to every model inheriting gte.legacy.mixin.

## gte.project.budget — Project Budget

| Field | Type | Notes |
|---|---|---|
| name | Char | computed |
| project_id | Many2one | required |
| company_id | Many2one | related |
| currency_id | Many2one | computed |
| line_ids | One2many |  |
| amount_budget | Monetary | computed |
| amount_committed | Monetary | computed |
| amount_actual | Monetary | computed |
| amount_variance | Monetary | computed |
| state | Selection |  |

## gte.project.budget.line — Project Budget Line

| Field | Type | Notes |
|---|---|---|
| budget_id | Many2one | required |
| currency_id | Many2one | related |
| section | Selection | required |
| description | Char |  |
| amount | Monetary | required |

## gte.labour.rate — Labour Rate

| Field | Type | Notes |
|---|---|---|
| classification | Char | required |
| company_id | Many2one |  |
| currency_id | Many2one | related |
| cost_rate | Monetary |  |
| sell_rate | Monetary |  |
| active | Boolean |  |

## gte.worker.cert — Worker Certification

| Field | Type | Notes |
|---|---|---|
| worker_name | Char | required, tracked |
| user_id | Many2one | Linked User |
| cert_name | Char | Certificate — required, tracked |
| cert_number | Char | Licence / Certificate No. |
| issuer | Char |  |
| issue_date | Date |  |
| expiry_date | Date | tracked |
| responsible_id | Many2one | Reminder To |
| attachment_ids | Many2many | Certificate Copy |
| state | Selection |  |

## gte.change.order — Change Order

| Field | Type | Notes |
|---|---|---|
| name | Char | Change Number |
| title | Char | required, tracked |
| scope | Html | Complete Scope |
| project_id | Many2one | required, tracked |
| company_id | Many2one | related |
| currency_id | Many2one | computed |
| source_type | Selection |  |
| origin_rfi_id | Many2one | Originating RFI |
| origin_ref | Char | Instruction / Drawing Reference |
| partner_id | Many2one | Client — tracked, computed |
| user_id | Many2one | Project Manager — tracked |
| line_ids | One2many |  |
| amount_proposed | Monetary | tracked, computed |
| amount_submitted | Monetary | tracked |
| amount_approved | Monetary | tracked |
| exposure | Monetary | computed |
| schedule_days | Integer |  |
| date_quote | Date | tracked |
| date_submitted | Date | tracked |
| date_required | Date | Required Decision Date — tracked |
| date_decision | Date | Approved / Rejected Date — tracked |
| billing_status | Selection |  |
| date_billed | Date | tracked |
| payment_status | Selection |  |
| client_response | Html |  |
| sale_order_id | Many2one |  |
| invoice_ids | Many2many | Invoices |
| analytic_account_id | Many2one |  |
| state | Selection |  |

## gte.change.order.line — Change Order Cost Line

| Field | Type | Notes |
|---|---|---|
| order_id | Many2one | required |
| currency_id | Many2one | related |
| section | Selection |  |
| description | Char | required |
| quantity | Float |  |
| uom | Char | Unit |
| unit_cost | Monetary |  |
| markup_pct | Float | Markup % |
| tax_pct | Float | Tax % |
| subtotal_cost | Monetary | computed |
| price_sell | Monetary | computed |

## gte.rfi — Request for Information

| Field | Type | Notes |
|---|---|---|
| name | Char | RFI Number |
| subject | Char | required, tracked |
| question | Html | Full Question |
| project_id | Many2one | required, tracked |
| company_id | Many2one | related |
| currency_id | Many2one | computed |
| task_ids | Many2many | Related Tasks |
| raised_by_id | Many2one | Raised By — tracked |
| addressed_to_id | Many2one | Addressed To — tracked |
| coordinator_id | Many2one | Responsible Coordinator — tracked |
| date_raised | Date | tracked |
| date_required | Date | Required Response Date — tracked |
| date_answered | Date | tracked |
| date_distributed | Date | tracked |
| drawing_refs | Char | Drawing References |
| spec_refs | Char | Specification References |
| response | Html | Formal Response |
| distribution_ids | Many2many | Distribution Recipients |
| cost_impact | Selection |  |
| cost_amount | Monetary | tracked |
| schedule_impact | Selection |  |
| schedule_days | Integer |  |
| change_order_id | Many2one | Linked Change Order |
| priority | Selection |  |
| state | Selection |  |
| is_overdue | Boolean | computed |

## gte.submittal.spec — Standard Submittal Specification

| Field | Type | Notes |
|---|---|---|
| number | Char | Spec Section — required |
| name | Char | Title — required |
| division | Char |  |
| active | Boolean |  |
| legacy_source_id | Char |  |

## gte.submittal — Submittal

| Field | Type | Notes |
|---|---|---|
| name | Char | Submittal Number |
| title | Char | required, tracked |
| project_id | Many2one | required, tracked |
| company_id | Many2one | related |
| spec_id | Many2one | Standard Spec |
| spec_section | Char | Specification Section — tracked |
| supplier_id | Many2one | Supplier — tracked |
| contractor_id | Many2one | Responsible Contractor |
| coordinator_id | Many2one | Project Coordinator — tracked |
| reviewer_id | Many2one | Reviewer — tracked |
| revision_ids | One2many |  |
| current_revision | Integer | computed |
| date_required_onsite | Date | Required On Site — tracked |
| date_required_submit | Date | Required Submission — tracked |
| date_received | Date | tracked |
| date_submitted | Date | tracked |
| date_returned | Date | tracked |
| outcome | Selection |  |
| comments | Html | Reviewer Comments |
| drawing_ref | Char | Linked Drawing |
| rfi_id | Many2one | Linked RFI |
| task_ids | Many2many | Related Tasks |
| distribution_ids | Many2many | Distribution List |
| state | Selection |  |

## gte.submittal.revision — Submittal Revision

| Field | Type | Notes |
|---|---|---|
| submittal_id | Many2one | required |
| revision | Integer | required |
| date_submitted | Date |  |
| date_returned | Date |  |
| outcome | Selection |  |
| comments | Html |  |
| attachment_ids | Many2many | Files |

## gte.document.revision.wizard — Register Document Revision

| Field | Type | Notes |
|---|---|---|
| new_document_id | Many2one |  |
| predecessor_id | Many2one | Supersedes — required |
| revision | Char | New Revision Label |

## gte.daily.log — Daily Site Log

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| foreman_id | Many2one | Foreman — tracked |
| weather | Selection |  |
| temperature | Char | Temperature |
| labour_ids | One2many |  |
| total_hours | Float | computed |
| work_done | Text | Work Completed |
| quantities | Text | Quantities Installed |
| equipment | Text | Equipment Used |
| deliveries | Text |  |
| visitors | Text |  |
| delays | Text | Delays and Causes |
| safety_observations | Text |  |
| photo_ids | Many2many | Photos |
| signature | Binary | Foreman Signature |
| reviewed_by_id | Many2one |  |
| reviewed_date | Date |  |
| state | Selection |  |

## gte.daily.log.labour — Daily Log Labour Line

| Field | Type | Notes |
|---|---|---|
| log_id | Many2one | required |
| worker_name | Char | required |
| classification | Char | Classification |
| hours | Float | required |
| notes | Char |  |

## gte.ncr — Non-Conformance Report

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| raised_by_id | Many2one |  |
| location | Char |  |
| severity | Selection |  |
| description | Text | Non-Conformance Description |
| root_cause | Text |  |
| corrective_action | Text |  |
| assigned_to_id | Many2one | Assigned To — tracked |
| due_date | Date | Correction Due |
| photo_ids | Many2many | Photos |
| state | Selection |  |

## gte.inspection — General Inspection

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| inspector_id | Many2one |  |
| inspection_type | Char | Inspection Type |
| line_ids | One2many |  |
| overall_result | Selection |  |
| notes | Text |  |
| photo_ids | Many2many | Photos |
| state | Selection |  |

## gte.inspection.line — Inspection Checklist Item

| Field | Type | Notes |
|---|---|---|
| inspection_id | Many2one | required |
| item | Char | required |
| result | Selection |  |
| notes | Char |  |

## gte.site.attendance — Site Attendance Sheet

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| foreman_id | Many2one |  |
| line_ids | One2many |  |
| total_hours | Float | computed |
| state | Selection |  |

## gte.site.attendance.line — Attendance Line

| Field | Type | Notes |
|---|---|---|
| sheet_id | Many2one | required |
| worker_name | Char | required |
| company | Char | Employer |
| time_in | Float | In |
| time_out | Float | Out |
| hours | Float | computed |

## gte.visitor.log — Visitor Log

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| visitor_name | Char | required |
| visitor_company | Char | Company |
| host_id | Many2one | Host |
| purpose | Char |  |
| time_in | Float | In |
| time_out | Float | Out |
| badge | Char | Badge No. |
| state | Selection |  |

## gte.transmittal — Transmittal

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| partner_id | Many2one | To — tracked |
| sent_by_id | Many2one |  |
| via | Selection |  |
| description | Text | Remarks |
| line_ids | One2many |  |
| attachment_ids | Many2many | Files |
| distribution_ids | Many2many | CC |
| state | Selection |  |

## gte.transmittal.line — Transmittal Item

| Field | Type | Notes |
|---|---|---|
| transmittal_id | Many2one | required |
| description | Char | required |
| quantity | Integer |  |
| doc_format | Char | Format |
| revision | Char |  |

## gte.shop.drawing — Shop Drawing

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| title | Char | required, tracked |
| drawing_no | Char | Drawing No. |
| revision | Char | tracked |
| supplier_id | Many2one | Supplier |
| submittal_id | Many2one | Linked Submittal |
| date_received | Date | tracked |
| date_sent | Date | tracked |
| attachment_ids | Many2many | Files |
| state | Selection |  |

## gte.gate.pass — Gate Pass

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| pass_type | Selection |  |
| person | Char | Carried By — tracked |
| person_company | Char | Company |
| vehicle | Char | Vehicle / Plate |
| material_description | Text |  |
| authorized_by_id | Many2one | Authorized By |
| state | Selection |  |

## gte.flha — Field Level Hazard Assessment

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| foreman_id | Many2one | Foreman — tracked |
| location | Char | Work Location |
| site_contact | Char |  |
| task_description | Text | Task / Activity |
| overall_risk | Selection |  |
| ppe_hard_hat | Boolean |  |
| ppe_safety_glasses | Boolean |  |
| ppe_gloves | Boolean |  |
| ppe_boots | Boolean |  |
| ppe_vest | Boolean |  |
| ppe_hearing | Boolean |  |
| ppe_other | Char |  |
| hazard_ids | One2many |  |
| signoff_ids | One2many |  |
| reviewed_by_id | Many2one |  |
| reviewed_date | Date |  |
| state | Selection |  |

## gte.flha.hazard — FLHA Hazard Line

| Field | Type | Notes |
|---|---|---|
| flha_id | Many2one | required |
| description | Char | Hazard — required |
| risk | Selection |  |
| control | Char | Control Measure |

## gte.flha.signoff — FLHA Crew Sign-off

| Field | Type | Notes |
|---|---|---|
| flha_id | Many2one | required |
| worker_name | Char | required |
| signature | Binary | Signature |
| signed_on | Datetime |  |

## gte.toolbox.talk — Toolbox Talk

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| topic | Char | required, tracked |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| presenter_id | Many2one | Presenter |
| duration_minutes | Integer |  |
| notes | Html |  |
| attendee_ids | One2many |  |
| state | Selection |  |

## gte.toolbox.attendee — Toolbox Talk Attendee

| Field | Type | Notes |
|---|---|---|
| talk_id | Many2one | required |
| worker_name | Char | required |
| signature | Binary | Signature |

## gte.incident — Incident Report

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Datetime | required |
| location | Char |  |
| reported_by_id | Many2one |  |
| incident_type | Selection |  |
| severity | Selection |  |
| description | Text |  |
| people_involved | Text |  |
| injuries | Text | Injuries / First Aid Provided |
| immediate_actions | Text |  |
| root_cause | Text |  |
| corrective_actions | Text |  |
| corrective_due | Date | Corrective Actions Due |
| photo_ids | Many2many | Photos / Evidence |
| reviewed_by_id | Many2one |  |
| reviewed_date | Date |  |
| state | Selection |  |

## gte.equipment.inspection — Equipment Inspection

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| date | Date | required |
| equipment_name | Char | required |
| serial_no | Char | Serial / Asset No. |
| inspector_id | Many2one |  |
| result | Selection |  |
| defects | Text | Defects Found |
| action_taken | Text |  |
| next_due | Date | Next Inspection Due |
| photo_ids | Many2many | Photos |
| state | Selection |  |

## gte.work.permit — Work Permit

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| permit_type | Selection |  |
| description | Text | Work Description |
| valid_from | Datetime | required |
| valid_to | Datetime | required |
| issued_by_id | Many2one |  |
| issued_to | Char |  |
| conditions | Text | Conditions / Precautions |
| state | Selection |  |

## gte.risk — Risk Register Entry

| Field | Type | Notes |
|---|---|---|
| name | Char |  |
| project_id | Many2one | required |
| company_id | Many2one | related |
| title | Char | Risk — required, tracked |
| category | Selection |  |
| likelihood | Selection |  |
| impact | Selection |  |
| score | Integer | computed |
| mitigation | Text |  |
| owner_id | Many2one | Risk Owner — tracked |
| review_date | Date | Next Review |
| state | Selection |  |

## gte.mail.action.mixin — Open mail composer preloaded with the record's template

| Field | Type | Notes |
|---|---|---|
