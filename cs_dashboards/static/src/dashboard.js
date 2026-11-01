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
        this.state = useState({
            projects: [],
            loading: true,
            hideValues: this._loadHideValues(),
        });
        onWillStart(async () => {
            this.state.projects = await this.orm.call(
                "cs.dashboard", "get_project_kpis", []);
            this.state.loading = false;
        });
    }

    // Any commercial figures on the board? (only money-trusted roles get them)
    get hasMoney() {
        return this.state.projects.some(
            (p) => p.money && p.money.length);
    }

    _loadHideValues() {
        try {
            return localStorage.getItem("cs_dashboard_hide_values") === "1";
        } catch (e) {
            return false;
        }
    }

    toggleValues() {
        this.state.hideValues = !this.state.hideValues;
        try {
            localStorage.setItem(
                "cs_dashboard_hide_values", this.state.hideValues ? "1" : "0");
        } catch (e) {
            // storage unavailable — toggle still works for this session
        }
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
