import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Public interaction for courier request search and group-by on portal page.
 */
export class CourierRequestGroupBySearch extends Interaction {
    static selector = ".groupby_courier";
    dynamicContent = {
        "#group_select_courier_requests": {
            "t-on-change": this.onChangeCourierRequests,
        },
        "#search_courier_requests_button": {
            "t-on-click": this.onClickCourierRequests,
        },
        "#courier_requests_search_box": {
            "t-on-keydown": this.onKeydownCourierRequestsSearch,
        },
    };

    setup() {
        this.selectEl = this.el.querySelector("#group_select_courier_requests");
        this.inputEl = this.el.querySelector("#courier_requests_search_box");
    }

    async onChangeCourierRequests() {
        const searchValue = this.selectEl ? this.selectEl.value : "0";
        const result = await this.waitFor(
            rpc("/courier/requests/group/by", {
                search_value: searchValue,
            })
        );
        const container = this.el.querySelector("#search_courier_requests_group");
        if (container) {
            container.innerHTML = result;
        }
    }

    async onClickCourierRequests() {
        const searchValue = this.inputEl ? this.inputEl.value.trim() : "";
        const result = await this.waitFor(
            rpc("/courier/requests/search", {
                search_value: searchValue,
            })
        );
        const container = this.el.querySelector("#search_courier_requests_group");
        if (container) {
            container.innerHTML = result;
        }
    }

    onKeydownCourierRequestsSearch(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onClickCourierRequests();
        }
    }
}

registry
    .category("public.interactions")
    .add("courier_management.courier_request_group_by_search", CourierRequestGroupBySearch);
