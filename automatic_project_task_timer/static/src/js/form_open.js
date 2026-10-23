/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormRenderer } from '@web/views/form/form_renderer';
import { useService } from "@web/core/utils/hooks";
patch(FormRenderer.prototype, {
     // Patched the form render to show the notification for already existing task.
        setup() {
            super.setup();
            this.notification = useService("notification");
            if (this.props.record?.data?.is_status_stage) {
                this.notification.add(
                    "The timer will not work properly for existing tasks until the stage is updated. Please change the stage once to activate the timer.",
                    { title: "Warning", type: "warning" }
                );
            }
        },
});
