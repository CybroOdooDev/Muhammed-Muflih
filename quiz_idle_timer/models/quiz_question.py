from odoo import api, fields, models


class QuizQuestion(models.Model):
    _name = 'quiz.question'
    _description = 'Quiz Question'

    name=fields.Char(string='Question Name',required=True)
    sequence=fields.Integer(string='Question Sequence',required=True)
    quiz_answer_ids=fields.One2many(comodel_name='quiz.answer',inverse_name='question_id',string='Answers')




