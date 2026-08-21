/** @odoo-module **/

import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { patch } from "@web/core/utils/patch";

patch(PivotRenderer.prototype, {
    onHeaderClick(ev, cell, isXAxis) {
        super.onHeaderClick(ev, cell, isXAxis);
        if (cell && cell.label === "Product" && cell.title) {
            let reference;
            if (cell.title.includes("[") && cell.title.includes("]")) {
                const match = cell.title.match(/\[(.*?)\]/);
                reference = match ? match[1] : cell.title;
            } else {
                reference = cell.title;
            }
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(reference);
            } else {
                const temp = document.createElement("input");
                document.body.appendChild(temp);
                temp.value = reference;
                temp.select();
                document.execCommand("copy");
                document.body.removeChild(temp);

            }
        }
    }
});
