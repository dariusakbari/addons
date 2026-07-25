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
        this.state = useState({ kpis: [], loading: true });
        onWillStart(async () => {
            this.state.kpis = await this.orm.call("cs.dashboard", "get_kpis", []);
            this.state.loading = false;
        });
    }

    get groups() {
        const g = {};
        for (const k of this.state.kpis) {
            (g[k.group] = g[k.group] || []).push(k);
        }
        return Object.entries(g).map(([name, items]) => ({ name, items }));
    }

    openKpi(kpi) {
        if (kpi.action) {
            this.action.doAction(kpi.action);
        }
    }
}

registry.category("actions").add("cs_construction_dashboard", ConstructionDashboard);
