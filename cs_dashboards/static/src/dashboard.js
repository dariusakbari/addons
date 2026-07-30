/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ConstructionDashboard extends Component {
    static template = "cs_dashboards.ConstructionDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ projects: [], loading: true });
        onWillStart(async () => {
            this.state.projects = await this.orm.call(
                "cs.dashboard", "get_project_kpis", []);
            this.state.loading = false;
        });
    }

    open(action) {
        if (action) {
            this.action.doAction(action);
        }
    }

    openProject(projectId) {
        if (!projectId) { return; }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project.project",
            res_id: projectId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("cs_construction_dashboard", ConstructionDashboard);
