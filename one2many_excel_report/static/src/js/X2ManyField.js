/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

// Dynamically resolve parent field definition (sol_o2m -> section_and_note_one2many -> x2ManyField)
const baseFieldDef = registry.category("fields").get("sol_o2m")
    || registry.category("fields").get("section_and_note_one2many")
    || x2ManyField;

const BaseComponent = baseFieldDef.component || X2ManyField;

export class ExcelX2ManyField extends BaseComponent {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    async Print_excel_report() {
        if (this.props.record && this.props.record.isDirty) {
            await this.props.record.save();
        }
        var order = this.props.record ? this.props.record.resId : false;
        var fieldObj = this.field || (this.props.record && this.props.record.fields && this.props.record.fields[this.props.name]);
        var relation = fieldObj ? fieldObj.relation : false;
        var related_field = fieldObj ? (fieldObj.relation_field || fieldObj.inverse_fname) : false;
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
    ...baseFieldDef,
    component: ExcelX2ManyField,
};

registry.category("fields").add("one2many_excel", excelX2ManyField);



