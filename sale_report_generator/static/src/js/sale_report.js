/** @odoo-module */
import { Component, proxy, signal } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

class SaleReport extends Component {
    setup() {
        super.setup(...arguments);
        this.uiService = useService('ui');
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');

        this.date_from = signal.ref();
        this.date_to = signal.ref();
        this.order_by = signal.ref();
        this.date_error = signal.ref();

        this.state = proxy({
            order_line: [],
            data: null,
            order: 'Report By Sale Order',
            order_by: 'report_by_order',
            wizard_id: []
        });
        this.load_data();
    }

    _validateDates() {
        const fromEl = this.date_from() || this.date_from.el;
        const toEl   = this.date_to() || this.date_to.el;
        const errorEl = this.date_error() || this.date_error.el;
        const fromVal = fromEl?.value;
        const toVal   = toEl?.value;

        if (fromEl) fromEl.classList.remove('is-invalid');
        if (toEl) toEl.classList.remove('is-invalid');
        if (errorEl) errorEl.style.display = 'none';

        if (!fromVal || !toVal) {
            return true;
        }

        if (new Date(toVal) <= new Date(fromVal)) {
            if (toEl) toEl.classList.add('is-invalid');
            if (errorEl) errorEl.style.display = 'block';
            return false;
        }

        return true;
    }

    async load_data(wizard_id = null) {
        try {
            if (wizard_id == null) {
                this.state.wizard_id = await this.orm.create("sales.report", [{}]);
            }
            this.state.data = await this.orm.call("sales.report", "sale_report", [this.state.wizard_id]);
            this.state.order_line = this.state.data.report_lines;
        } catch (el) {
            console.error(el);
        }
    }

    async apply_filter(ev) {
        if (!this._validateDates()) return;

        let filter_data = {};
        const orderByEl = this.order_by() || this.order_by.el;
        const fromEl = this.date_from() || this.date_from.el;
        const toEl = this.date_to() || this.date_to.el;

        this.state.order_by = orderByEl ? orderByEl.value : 'report_by_order';
        this.state.order    = orderByEl && orderByEl.selectedOptions[0] ? orderByEl.selectedOptions[0].outerText : '';
        filter_data.date_from    = fromEl ? fromEl.value : false;
        filter_data.date_to      = toEl ? toEl.value : false;
        filter_data.report_type  = orderByEl ? orderByEl.value : 'report_by_order';
        let data = await this.orm.write("sales.report", this.state.wizard_id, filter_data);
        this.load_data(this.state.wizard_id);
    }

    async PrintPdf(ev) {
        ev.preventDefault();
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'sale_report_generator.sale_order_report',
            'report_file': 'sale_report_generator.sale_order_report',
            'data': { 'report_data': this.state.data },
            'context': {
                'active_model': 'sales.report',
                'landscape': 1,
                'sale_order_report': true
            },
            'display_name': 'sale Order',
        });
    }

    async PrintXlsx() {
        var data = this.state.data;
        var action = {
            'data': {
                'model': 'sales.report',
                'options': JSON.stringify(data['orders']),
                'output_format': 'xlsx',
                'report_data': JSON.stringify(data['report_lines']),
                'report_name': 'Sales Report',
                'dfr_data': JSON.stringify(data),
            },
        };
        this.uiService.block();
        try {
            await download({
                url: '/sale_dynamic_xlsx_reports',
                data: action.data,
            });
        } finally {
            this.uiService.unblock();
        }
    }

    async viewSaleOrder(ev) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'sale.order',
            res_id: parseInt(ev.target.id),
            views: [[false, "form"]],
            target: "current",
        });
    }
}

SaleReport.template = 'SaleReport';
actionRegistry.add("sales_report", SaleReport);