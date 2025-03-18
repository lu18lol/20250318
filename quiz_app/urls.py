from django.urls import path
from .views import question_views, exam_views, submission_views, auth_views

urlpatterns = [
    # 首页
    path('', exam_views.index, name='index'),
    
    # 题目管理
    path('questions/', question_views.question_list, name='question_list'),
    path('questions/create/', question_views.question_create, name='question_create'),
    path('questions/import/', question_views.import_questions, name='import_questions'),
    
    # 测试管理
    path('exams/', exam_views.exam_list, name='exam_list'),
    path('exams/create/', exam_views.exam_create, name='exam_create'),
    path('exams/<uuid:exam_id>/generate-random/', exam_views.generate_random_exam, name='generate_random_exam'),
    path('exams/<uuid:exam_id>/', exam_views.exam_detail, name='exam_detail'),
    
    # 答题流程
    path('exams/<uuid:exam_id>/start/', submission_views.start_exam, name='start_exam'),
    path('submissions/<uuid:submission_id>/take/', submission_views.take_exam, name='take_exam'),
    path('submissions/<uuid:submission_id>/submit/', submission_views.submit_exam, name='submit_exam'),
    path('submissions/<uuid:submission_id>/result/', submission_views.exam_result, name='exam_result'),
    
    # 错题分析
    path('mistakes/', exam_views.mistake_collection, name='mistake_collection'),
    path('mistakes/analysis/', exam_views.mistake_analysis, name='mistake_analysis'),
    path('mistakes/<int:mistake_id>/remove/', submission_views.remove_from_mistakes, name='remove_from_mistakes'),
    
    # 登录视图
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
] 