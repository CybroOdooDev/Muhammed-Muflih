/** @odoo-module **/
import { SaleOrderLineOne2Many, saleOrderLineOne2Many } from "@sale/js/sale_order_line_field/sale_order_line_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Extends SaleOrderLineOne2Many to create widget for sale order line & one2many fields
export class ExcelX2ManyField extends SaleOrderLineOne2Many {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    async Print_excel_report() {
        if (this.props.record && this.props.record.isDirty) {
            await this.props.record.save();
        }
        var order = this.props.record ? this.props.record.resId : false;
        var fieldObj = this.field || (this.props.record && this.props.record.fields[this.props.name]);
        var relation = fieldObj ? fieldObj.relation : false;
        var related_field = fieldObj ? fieldObj.relation_field : false;
        var action = {
            type: "ir.actions.report",
            report_type: "xlsx",
            report_name: 'Excel',
            report_file: "report.excel",
            context: { 'model': relation, 'id': order || false, 'field': related_field },
        };
        return this.actionService.doAction(action);
    }
}

ExcelX2ManyField.template = "one2many_excel_report.One2manyExcel";

export const excelX2ManyField = {
    ...saleOrderLineOne2Many,
    component: ExcelX2ManyField,
};

registry.category("fields").add("one2many_excel", excelX2ManyField);

