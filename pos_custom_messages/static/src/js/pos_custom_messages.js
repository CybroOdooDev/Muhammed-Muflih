import { Component , useRef} from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';
import { Chrome } from "@point_of_sale/app/pos_app";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

export class CustomMessagePopup extends Component {
    static components = { Dialog };
    static template = "CustomMessagePopup";
    static defaultProps = {
        confirmText: _t("Ok"),
        cancelKey: false,   
        body: "Ok",
    };

    setup() {
        super.setup();
        this.message_icon = useRef("message_icon");
        this.modal_header = useRef("modalHeader");

        setTimeout(() => {
            const messageInfo = this.props ? this.props.message_info : false;
            const messageIcon = this.message_icon.el; // Access the actual DOM element
            const modalHeader = this.modal_header.el; // Access the actual DOM element

            if (messageInfo && messageIcon && modalHeader) {
                messageIcon.classList.remove("fa-info-circle", "fa-exclamation-triangle", "fa-clock-o");
                modalHeader.classList.remove("warning", "info", "alert");

                if (messageInfo.message_type === "warning") {
                    messageIcon.classList.add("fa", "fa-exclamation-triangle");
                    modalHeader.classList.add("warning");
                } else if (messageInfo.message_type === 'inform') {
                    messageIcon.classList.add("fa", "fa-info-circle");
                    modalHeader.classList.add("info");
                } else {
                    messageIcon.classList.add("fa", "fa-clock-o");
                    modalHeader.classList.add("alert");
                }
            }
        }, 200);
    }
}


patch(PosStore.prototype, {
    async processServerData() {
        await super.processServerData(...arguments);
        this.custom_messages = this.models['pos.custom.message']?.getAll() || [];
        let current_time = new Date().getTime(); // Get current timestamp

        this.custom_messages.forEach((message) => {
            try {
                let message_time = new Date(new Date().toDateString() + ' ' + message.input_time).getTime();
                message.execution_time = message_time - current_time;

            } catch (error) {
                console.error("Error processing message time:", message.input_time, error);
            }
        });
        return this.custom_messages; // Return the processed messages
    },
});

patch(Chrome.prototype,{
    setup() {
        super.setup();
        (this.pos.custom_messages || []).forEach(message => {
            if (message.execution_time >= 0) {
                setTimeout(() => {
                    this.env.services.dialog.add(CustomMessagePopup, {
                         title: _t(message.title),
                         body: _t(message.message),
                         cancelLabel: _t('Cancel'),
                         message_info: message,
                    })
                }, message.execution_time);
            }
        });
    },
})
