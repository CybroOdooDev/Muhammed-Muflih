from odoo import http
from odoo.http import request

class QiuzController(http.Controller):

  @http.route('/quiz/over/page/<string:point>', type='http', auth="user", website=True)
  def quiz_over_page(self, point):
      """score display page"""
      new_point=point.split('=')
      if int(new_point[1])>1:
          message=f"Congrats You passed this quiz score: {new_point[1]}"
      else:
          message=f"oops! your are failed  score: {new_point[1]}"

      return request.render("quiz_idle_timer.quiz_over_page",{'message':message})



  @http.route('/quiz/user/page/', type='http', auth="public", website=True)
  def quiz_user_page(self):
      """score display page"""

      print('yeee')
      return request.render("quiz_idle_timer.quiz_user_page")


  @http.route('/quiz_values/', type='jsonrpc', auth="user")
  def get_quiz_values(self):
      """quiz question answer"""
      question_answer=[]
      param = self.env['ir.config_parameter'].sudo()
      timer = param.get_param('quiz_idle_timer.time_limit_for_quiz')
      questions=request.env['quiz.question'].sudo().search([])
      for ques in questions:
          question_answer.append({'id': ques.id, 'question': ques.name,'answer':[i.option_name for i in ques.quiz_answer_ids],'timer':timer})

      return {'question_answer':question_answer,'timer':timer}


  @http.route('/quiz/point/', type='jsonrpc', auth="user")
  def checking_answer(self,question_id,answer_option):
      """checking correct answer"""
      point=0
      print('question_id',question_id,answer_option)
      answer_check=request.env['quiz.question'].sudo().browse(int(question_id))
      for option in answer_check.quiz_answer_ids:
          if option.option_name==answer_option:
              if option.correct_answer==True:
                  point+=1

      print(answer_check)
      return point




