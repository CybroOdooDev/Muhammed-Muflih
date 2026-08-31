/** @odoo-module **/

import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";

patch(OrderReceipt.prototype, {
    get isBranchSpecificReceipt() {
        return Boolean(this.env.services.pos?.config?.branch_specific_receipt);
    },

    get IsWhiteLabelReceipt() {
        return Boolean(this.env.services.pos?.config?.white_label_receipt);
    },

    get branchLogoSrc() {
        const logo = this.env.services.pos?.config?.branch_logo;
        if (!logo) return null;
        return logo.startsWith('data:') ? logo : `data:image/png;base64,${logo}`;
    },

    get branchDetails() {
        const cfg = this.env.services.pos?.config || {};
        return {
            tel:     cfg.branch_tel     || null,
            email:   cfg.branch_email   || null,
            website: cfg.branch_website || null,
            address: cfg.branch_address || null,
        };
    },

    get customerLogoSrc() {
        const order = this.props.order;
        const partner = order?.partner_id || (order?.getPartner ? order.getPartner() : null);
        if (partner?.pos_show_logo_on_receipt && partner?.image_1920) {
            const img = partner.image_1920;
            return img.startsWith('data:') ? img : `data:image/png;base64,${img}`;
        }
        return null;
    },
});