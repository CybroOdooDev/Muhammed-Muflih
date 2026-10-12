/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { onMounted } from "@odoo/owl";

const ChatterPatch = {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        // Once the chatter component is mounted, check user preferences
        onMounted(async () => {
            try {
                const userData = await this.orm.call(
                    "role.management",
                    "get_role_restrictions",
                );
                const el = typeof this.rootRef === "function" ? this.rootRef() : this.rootRef?.el;
                if (userData.is_chatter === true) {
                    const hide = () => {
                        const targetEl = typeof this.rootRef === "function" ? this.rootRef() : this.rootRef?.el;
                        if (targetEl) {
                            targetEl.classList.add("d-none");
                            const container = targetEl.closest(".o-mail-ChatterContainer, .o-mail-Form-chatter");
                            if (container) {
                                container.classList.add("d-none");
                            }
                        } else {
                            document.querySelectorAll(".o-mail-ChatterContainer, .o-mail-Form-chatter").forEach((c) => c.classList.add("d-none"));
                        }
                    };
                    hide();
                    setTimeout(hide, 0);
                }
            } catch (error) {
                console.error("Failed to check chatter visibility preference:", error);
            }
        });
    },
};
patch(Chatter.prototype, ChatterPatch);