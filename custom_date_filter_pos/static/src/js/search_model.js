/** @odoo-module **/
import { SearchModel } from "@web/search/search_model";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";


patch(SearchModel.prototype,{
    setup(){
        super.setup(...arguments);
        this.action = useService("action");
    },
    createNewFilters(prefilters) {
        if (!prefilters.length) {
            return [];
        }
        prefilters.forEach((preFilter) => {
            const filter = Object.assign(preFilter, {
                groupId: this.nextGroupId,
                groupNumber: this.nextGroupNumber,
                id: this.nextId,
                type: "filter",
            });
            let searchItem = null;
            if(filter.description == 'Today'){
                 for (let item in this.searchItems){
                    if (this.searchItems[item].description == 'Today'){
                        searchItem = this.searchItems[item]
                        break
                    }
                 }
            }
            else if(filter.description == 'Yesterday'){
               for (let item in this.searchItems){
                    if (this.searchItems[item].description == 'Yesterday'){
                        searchItem = this.searchItems[item]
                        break
                    }
               }
            }

            if(!searchItem){
                this.searchItems[this.nextId] = filter;
                this.query.push({ searchItemId: this.nextId });
                this.nextId++;
            }
            else{
                 this.action.doAction({
                    type: 'ir.actions.client',
                    tag: 'display_notification',
                    params: {
                        message: 'Already registered',
                        type: 'warning',
                        sticky: false,
                    }
                 })
            }
        });
        this.nextGroupId++;
        this.nextGroupNumber++;
        this._notify();
    }
})