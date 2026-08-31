/** @odoo-module **/

import { StockReportSearchModel } from '@stock/views/search/stock_report_search_model';
import { patch } from "@web/core/utils/patch";

patch(StockReportSearchModel.prototype, {
    async _loadWarehouses() {
        this.warehouses = await this.orm.call(
            'stock.warehouse',
            'get_current_warehouses',
            [[]],
            { context: this.context },
        );
    },

    clearWarehouseContext() {
        this.orm.call('stock.warehouse','action_remove_context',[false]).then(()=>{
            delete this.globalContext.warehouse;
            this._notify();
        })
    },

    applyWarehouseContext(warehouse_id) {
        this.orm.call('stock.warehouse', 'action_update_context',[warehouse_id]).then(()=>{
             this.globalContext['warehouse'] = warehouse_id;
             this._notify();
        })
    }

})