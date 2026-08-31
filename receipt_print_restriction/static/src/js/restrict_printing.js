/** @odoo-module */

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";


patch(PosStore.prototype, {
    async printReceipt({ basic = false, order = this.getOrder(), printBillActionTriggered = false } = {}) {
        if (this.config && this.config.receipt_restriction) {
            const printOrder = order || (this.getOrder ? this.getOrder() : null);
            if (printOrder) {
                const printKey = printOrder.uuid || printOrder.uid;
                if (printKey) {
                    let receipt_print_count = parseInt(localStorage.getItem(printKey) || "0", 10);
                    if (receipt_print_count >= this.config.restriction_limit) {
                        this.dialog.add(AlertDialog, {
                            title: _t("Error"),
                            body: _t('Print limit Reached : ' + this.config.restriction_limit),
                        });
                        return false;
                    }
                    receipt_print_count += 1;
                    printOrder.receipt_print_count = receipt_print_count;
                    localStorage.setItem(printKey, receipt_print_count.toString());
                }
            }
        }
        return super.printReceipt(...arguments);
    }
});