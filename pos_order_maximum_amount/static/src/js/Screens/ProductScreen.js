/** @odoo-module **/
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async pay() {
        let order_limit = this.config.pos_order_limit;
        let currency_symbol = this.currency.symbol;
        let order_total = this.getOrder().priceIncl;
        if (order_limit > 0 && order_total > order_limit) {
            this.dialog.add(AlertDialog, {
                title: _t('Limit exceeded'),
                body: _t(`You are not allowed to create an order that is greater than "${order_limit}${currency_symbol}"`),
            });
        }
        else {
            super.pay(...arguments);
        }
    }
});