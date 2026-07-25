from . import models


def _cs_automation_post_init(env):
    """Retire the per-model activity crons now that the escalation engine
    handles them, so nothing double-fires. Idempotent and safe if any is
    already absent."""
    for xmlid in ("cs_controls.cron_rfi_overdue",
                  "cs_hse.cron_permit_expiry",
                  "cs_commercial.cron_cert_expiry"):
        cron = env.ref(xmlid, raise_if_not_found=False)
        if cron and cron.active:
            cron.active = False
