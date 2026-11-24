/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

var CustomForm = publicWidget.Widget.extend({
    selector: '.form-container',
    start: function (ev) {
        var self = this;
        var $select = self.$('select.js-example-basic-multiple');

        if (typeof $select.select2 === 'function') {
            $select.select2({
                allowClear: true,
                placeholder: "Select categories",
                width: '100%'
            });
        }

        var updateHiddenInput = function () {
            var selectedValues = $select.val() || [];
            if (!Array.isArray(selectedValues)) {
                selectedValues = [selectedValues];
            }
            $('.hidden_categories').remove();
            $('.vendor-registration-form').append(
                `<input type="hidden" class="hidden_categories" name="many2many_field" value='${JSON.stringify(selectedValues)}'>`
            );
        };

        $select.on('change', updateHiddenInput);
        updateHiddenInput();
        return this._super.apply(this, arguments);
    }
});

publicWidget.registry.Many2many_tag = CustomForm;
export default CustomForm;