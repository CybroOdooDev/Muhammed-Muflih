/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("xlsx_handler", async function (action, options, env) {
    if (action.report_type === 'xlsx') {
        env.services.ui.block();
        try {
            await download({
                url: '/account_xlsx',
                data: action.data,
            });
        } finally {
            env.services.ui.unblock();
        }
        return true;
    }
});
