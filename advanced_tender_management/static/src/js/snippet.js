/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from '@web/legacy/js/public/public_widget';
import { renderToFragment } from "@web/core/utils/render";

export function _chunk(array,size){
    const chunk_array=[]
    for (let i=0;i<array.length;i+=size){
        chunk_array.push(array.slice(i,i+size));
    }
    return chunk_array
}
publicWidget.registry.TenderManagementSnippet=publicWidget.Widget.extend({
        selector: '.dynamic_snippet_blog',
    	willStart: async function() {
        	var self = this;
        	await rpc('/tender_management_snippet').then((data) => {
            	this.data = data;
        	});
    	},
    	start: function() {
        	var chunks = _chunk(this.data || [], 1);
        	this.$el.find("#carousel").empty().append(renderToFragment('advanced_tender_management.tender_snippet_carousel', { chunks }));
    	},
})