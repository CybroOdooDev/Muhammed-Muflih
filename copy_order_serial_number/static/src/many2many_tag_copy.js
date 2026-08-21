/** @odoo-module */
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(Many2ManyTagsField.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
    },
    getTagProps(record) {
        const props = super.getTagProps(record);
        props.showCopy = record.resModel === 'pos.pack.operation.lot';
        props.onCopy = (text) => this.onTagCopy(text);
        return props;
    },
    onTagCopy(tag_text) {
        var temp = document.createElement("input");
        document.body.appendChild(temp);
        temp.value = tag_text;
        temp.select();
        document.execCommand("copy");
        document.body.removeChild(temp);
        return this.action.doAction({
            name: _t('Stock Moves'),
            type: 'ir.actions.act_window',
            res_model: 'stock.move.line',
            view_mode: 'list',
            views: [[false, "list"], [false, "form"]],
            domain: [['lot_id.name', '=', tag_text]],
        });
    }
});

