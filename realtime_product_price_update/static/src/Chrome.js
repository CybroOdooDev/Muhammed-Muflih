import { Chrome } from "@point_of_sale/app/pos_app";
import { patch } from "@web/core/utils/patch";

patch(Chrome.prototype, {
    setup(){
        this.busService = this.env.services.bus_service
        this.busService.addChannel('POS_PRODUCT_PRICE_UPDATE')
        this.busService.subscribe('notification_pos_realtime_price', this.onMessage.bind(this))
        super.setup()
    },
    onMessage(res) {
       let product = this.pos.models["product.product"].getBy('id', res.value.charge_id);
       if (product) {
           this.pos.models["product.product"].update(product, { lst_price: res.value.lst_price });
       }
    }
})
