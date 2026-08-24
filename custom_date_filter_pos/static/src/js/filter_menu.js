/** @odoo-module **/
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { Domain } from "@web/core/domain";
import { useState } from "@odoo/owl";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
const { DateTime } = luxon;

patch(SearchBarMenu.prototype, {
    setup() {
        this.currentModel = this.env.searchModel.resModel;
        this.models = {
            'stock.report': 'creation_date',
            'report.pos.order': 'date',
            'account.invoice.report': 'invoice_date',
            'purchase.report': 'date_order'
        };
        this.DateFilter = useState({
            from_date: "",
            to_date: "",
            error_note: "",
        });
        super.setup();
    },

    getSearchFieldAndType() {
        const searchField = this.currentModel in this.models ? this.models[this.currentModel] : 'create_date';
        const fieldMeta = this.env.searchModel.searchItems ?
            Object.values(this.env.searchModel.searchItems).find(item => item.fieldName === searchField) : null;
        const isDateOnly = fieldMeta && fieldMeta.fieldType === 'date';
        return { searchField, isDateOnly };
    },

    formatBounds(startLuxon, endLuxon, isDateOnly) {
        const serializeFn = isDateOnly ? serializeDate : serializeDateTime;
        return {
            start: serializeFn(startLuxon),
            end: serializeFn(endLuxon)
        };
    },

    onClickToday() {
        const { searchField, isDateOnly } = this.getSearchFieldAndType();
        const now = DateTime.now();
        const { start, end } = this.formatBounds(now.startOf("day"), now.endOf("day"), isDateOnly);

        const domainArray = [
            [searchField, '>=', start],
            [searchField, '<=', end]
        ];
        const preFilters = {
            description: "Today",
            domain: new Domain(domainArray).toString(),
            type: "filter",
        };
        this.env.searchModel.createNewFilters([preFilters]);
    },

    onClickYesterday() {
        const { searchField, isDateOnly } = this.getSearchFieldAndType();
        const yesterday = DateTime.now().minus({ days: 1 });
        const { start, end } = this.formatBounds(yesterday.startOf("day"), yesterday.endOf("day"), isDateOnly);

        const domainArray = [
            [searchField, '>=', start],
            [searchField, '<=', end]
        ];
        const preFilters = {
            description: "Yesterday",
            domain: new Domain(domainArray).toString(),
            type: "filter",
        };
        this.env.searchModel.createNewFilters([preFilters]);
    },

    onClickCustomDate() {
        if (this.DateFilter.from_date && this.DateFilter.to_date) {
            const { searchField, isDateOnly } = this.getSearchFieldAndType();
            this.DateFilter.error_note = "";

            const fromDT = DateTime.fromISO(this.DateFilter.from_date).startOf("day");
            const toDT = DateTime.fromISO(this.DateFilter.to_date).endOf("day");

            if (!fromDT.isValid || !toDT.isValid || fromDT > toDT) {
                this.DateFilter.error_note = "Invalid date range!";
                return;
            }

            const { start, end } = this.formatBounds(fromDT, toDT, isDateOnly);

            const domainArray = [
                [searchField, '>=', start],
                [searchField, '<=', end]
            ];
            const preFilters = {
                description: `${this.DateFilter.from_date} to ${this.DateFilter.to_date}`,
                domain: new Domain(domainArray).toString(),
                type: "filter",
            };
            this.env.searchModel.createNewFilters([preFilters]);
        } else {
            this.DateFilter.error_note = "Invalid date!";
        }
    }
});
