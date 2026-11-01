from odoo import models


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Odoo task status values that mean "finished" / "open".
    _DONE_STATE = "1_done"
    _OPEN_STATE = "01_in_progress"
    _DONE_STAGE_NAMES = ("done", "complete", "completed", "closed")

    def _cs_stage_is_done(self, stage):
        """A stage counts as 'done' when it is folded or named like one."""
        if not stage:
            return False
        if stage.fold:
            return True
        return (stage.name or "").strip().lower() in self._DONE_STAGE_NAMES

    def _cs_find_done_stage(self):
        """The done-like stage to use for this task's project (folded first)."""
        self.ensure_one()
        if not self.project_id:
            return self.env["project.task.type"]
        stages = self.env["project.task.type"].search(
            [("project_ids", "in", self.project_id.id)], order="sequence, id")
        done = stages.filtered(lambda s: self._cs_stage_is_done(s))
        return (done.filtered("fold")[:1] or done[:1])

    def _cs_find_open_stage(self):
        """The first non-done stage for this task's project (to reopen into)."""
        self.ensure_one()
        if not self.project_id:
            return self.env["project.task.type"]
        stages = self.env["project.task.type"].search(
            [("project_ids", "in", self.project_id.id)], order="sequence, id")
        open_stages = stages.filtered(lambda s: not self._cs_stage_is_done(s))
        # Prefer an active "In Progress"-style stage when the project has one,
        # so reopening a task lands somewhere sensible rather than the backlog.
        preferred = open_stages.filtered(
            lambda s: (s.name or "").strip().lower()
            in ("in progress", "in-progress", "doing", "started", "active"))
        return (preferred[:1] or open_stages[:1])

    def write(self, vals):
        # Re-entrancy guard: our own sync writes skip the logic below.
        if self.env.context.get("cs_task_sync"):
            return super().write(vals)

        res = super().write(vals)

        # Stage drove the change -> bring status into line.
        if "stage_id" in vals and "state" not in vals:
            for task in self:
                in_done = task._cs_stage_is_done(task.stage_id)
                if in_done and task.state != self._DONE_STATE:
                    task.with_context(cs_task_sync=True).state = self._DONE_STATE
                elif not in_done and task.state == self._DONE_STATE:
                    task.with_context(cs_task_sync=True).state = self._OPEN_STATE

        # Status drove the change -> bring stage into line.
        elif "state" in vals and "stage_id" not in vals:
            for task in self:
                if task.state == self._DONE_STATE:
                    stage = task._cs_find_done_stage()
                    if stage and task.stage_id != stage:
                        task.with_context(cs_task_sync=True).stage_id = stage.id
                elif (task.state == self._OPEN_STATE
                      and task._cs_stage_is_done(task.stage_id)):
                    stage = task._cs_find_open_stage()
                    if stage and task.stage_id != stage:
                        task.with_context(cs_task_sync=True).stage_id = stage.id

        return res
