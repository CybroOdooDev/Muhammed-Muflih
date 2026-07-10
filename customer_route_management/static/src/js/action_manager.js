/** @odoo-module*/
import {registry} from "@web/core/registry";
import {download} from "@web/core/network/download";

// Action handler for xlsx reports.
registry.category("ir.actions.report handlers").add("xlsx", async (action, options, env) => {
    if (action.report_type === "xlsx") {
        env.services.ui.block();
        try {
            await download({
                url: "/xlsx_report",
                data: action.data,
            });
        } finally {
            env.services.ui.unblock();
        }
        return true;
    }
});
