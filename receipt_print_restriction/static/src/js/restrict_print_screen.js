/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { useExternalListener } from "@odoo/owl";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        useExternalListener(document, 'keydown', this.keydownCtrl);
        useExternalListener(document, 'contextmenu', this.contextMenuHandler);
        
        const order = this.currentOrder || (this.pos && (this.pos.getOrder ? this.pos.getOrder() : null));
        if (order) {
            const printKey = order.uuid || order.uid;
            if (printKey) {
                const order_data = localStorage.getItem(printKey);
                if (!order_data) {
                    order.receipt_print_count = 0;
                    localStorage.setItem(printKey, "0");
                } else {
                    order.receipt_print_count = parseInt(order_data, 10);
                }
            }
        }
    },
    contextMenuHandler(event) {
        if (this.pos && this.pos.config && this.pos.config.receipt_restriction) {
            event.preventDefault();
        }
    },
    keydownCtrl(event) {
        if (this.pos && this.pos.config && this.pos.config.receipt_restriction && (event.ctrlKey || event.metaKey) && (event.key === 'p' || event.key === 'P')) {
            event.preventDefault();
        }
    },
});