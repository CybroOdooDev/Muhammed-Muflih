/** @odoo-module **/
import { registry } from "@web/core/registry";
import {Component, useState,onWillDestroy} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
import { rpc } from "@web/core/network/rpc";
import {AnswerOptions} from "./answer_options";

 class QuizDashboard extends Component {

   static components={AnswerOptions}
     setup() {
        super.setup();
        // this.orm = useService('orm');
        // this.action=useService('action');
        this.timer=0
         this.inctime=0
        this.seconds=0
         this.answer=''
         this.points=0
         this.checked_value=false

         console.log(123213123)


       this.interval=setInterval(()=>this.timercheck(),1000)
        this.FetchData();
        this.state=useState({
            questions:{},
            index:0
        })

            onWillDestroy(() => {
                 clearInterval(this.interval)
                document.querySelector('.idle_time').textContent='0'

    });

         window.onkeyup =()=>this.detect();
		 window.onclick =()=>this.detect();
         window.onmouseup =()=>this.detect();
         window.onmouseover=()=>this.detect();
    }



    detect(){
        this.seconds=0
    }
   //fetching all
   async FetchData(){

        var result=await rpc('/quiz_values/',{})
         this.state.questions=result.question_answer
        var timer=result.timer
       this.timer=Number(timer)
    }

   timercheck(ev){
         this.seconds+=1
       console.log('time',this.seconds)
        document.querySelector('.idle_time').textContent=this.seconds
       if(this.seconds==this.timer){
           this.seconds=0
           console.log('answer checking',this.state.questions[this.state.index].id)
           if(this.state.index!=this.state.questions.length-1) {
               this.state.index++
           }else{
               clearInterval(this.interval)
               window.location.replace('/quiz/over/page/point='+this.points);
           }

       }
   }

   get  CurrentQuestion(){

      return this.state.questions[this.state.index]
    }

    async NextQuestion(ev){
         if(this.state.index!=this.state.questions.length-1){
             this.state.index++
             this.seconds=0
             if(this.answer){
                  var question_id =ev.target.parentElement.parentElement.children[0].children[0].innerHTML
              var points= await rpc('/quiz/point/',{'question_id':question_id,'answer_option':this.answer})
                 this.points+=points
                 console.log('point',this.points)
             }

         }else{
             window.location.replace('/quiz/over/page/point='+this.points);
         }

    }


    PrevQuestion(){
         if(this.state.index>0){
             this.state.index--

         }

    }

    CheckingAnswer(ev){
             this.answer= ev.target.parentElement.parentElement.children[0].children[0].innerHTML
             this.checked_value=ev.target.checked
             console.log('answer_vals',this.checked_value)
        }




}
QuizDashboard.template = "quiz_idle_timer.QuizDashboard";
actionRegistry.add("quiz_dashboard_tag", QuizDashboard);
registry.category("public_components").add("quiz_dashboard_tag", QuizDashboard);
