SEED_TEMPLATE_XMLIDS = [
    "tpl_daily_inspection",
    "tpl_toolbox",
    "tpl_field_insp",
    "tpl_site_insp",
    "tpl_hazard",
    "tpl_equipment",
]


def _publish_seed_templates(env):
    """Publish the seeded starter templates if they are still draft.

    The XML seeds create each template as draft and publish it with a second
    same-id record. That publish only takes effect on a fresh install (init
    mode); on a module upgrade the second record is skipped because the record
    already carries a noupdate ir.model.data entry. This hook (run on install
    and by the 0.2.1 migration) makes publishing reliable in both cases.
    """
    for xmlid in SEED_TEMPLATE_XMLIDS:
        tpl = env.ref("cs_hse_templates.%s" % xmlid, raise_if_not_found=False)
        if tpl and tpl.state == "draft" and tpl.question_count:
            tpl.action_publish()


def post_init_hook(env):
    _publish_seed_templates(env)
