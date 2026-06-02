/** @odoo-module **/
import { registry } from "@web/core/registry";
import {Component} from "@odoo/owl";
const actionRegistry = registry.category("actions");
export class AnswerOptions extends Component {

    static template="quiz_idle_timer.Answer";

    setup() {
        super.setup();

    }


   static props = {
       answer:{},
       checkingAnswer:Function,

   };







}

