from odoo import api, fields, models

class QuizAnswer(models.Model):
    _name = 'quiz.answer'
    _description = 'Quiz Answer'

    question_id = fields.Many2one( comodel_name='quiz.question',string='Quiz question')
    option_name=fields.Char(string='Name')
    correct_answer=fields.Boolean(string='Currect Answer',default=False)