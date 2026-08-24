import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("xlsx_handler", async (action) => {
    if (action.report_type === 'xlsx') {
        await download({
            url: '/xlsx_reports',
            data: action.data,
            error: (error) => console.error("XLSX Report Download Error:", error),
        });
        return true;
    }
});
