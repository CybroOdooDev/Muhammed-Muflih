{
    'name': 'Quiz Idle Timer',
    'application':True,
    'installable':True,
    'depends':['base', 'web','mail'],
    'license': 'LGPL-3',
    'data':{
        'security/quiz_idle_timer_groups.xml',
        'security/ir.model.access.csv',
        'views/quiz_question_view.xml',
        'views/quiz_question_template.xml',
        'views/res_config_settings.xml',
        'views/quiz_over_page.xml',
        'views/quize_user_template.xml',
        'wizard/sending_quiz_to_users.xml',
        'data/quiz_email_template.xml',
        'views/quiz_idle_timer_menus.xml',

    },


'assets': {
   'web.assets_backend': [
       'quiz_idle_timer/static/src/js/quiz.js',
       'quiz_idle_timer/static/src/xml/quiz_template.xml',
       'quiz_idle_timer/static/src/js/answer_options.js',
       'quiz_idle_timer/static/src/xml/answer_template.xml',
   ],
'web.assets_frontend': [
       'quiz_idle_timer/static/src/js/quiz.js',
       'quiz_idle_timer/static/src/xml/quiz_template.xml',
       'quiz_idle_timer/static/src/js/answer_options.js',
       'quiz_idle_timer/static/src/xml/answer_template.xml',
   ],
},

}