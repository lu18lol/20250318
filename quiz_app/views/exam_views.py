from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count
from ..models import Exam, ExamQuestion, Question, RandomConfig, FeedbackConfig, Category, MistakeCollection
from ..forms import ExamForm, RandomConfigForm, FeedbackConfigFormSet, ExamQuestionFormSet
import random

def index(request):
    """首页"""
    return render(request, 'quiz_app/index.html')

@login_required
def exam_list(request):
    """测试列表页面"""
    exams = Exam.objects.filter(is_active=True)
    return render(request, 'quiz_app/exams/list.html', {
        'exams': exams
    })

@login_required
def exam_create(request):
    """创建测试"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            
            # 处理随机出题配置
            if exam.is_random:
                random_config_form = RandomConfigForm(request.POST)
                if random_config_form.is_valid():
                    random_config = random_config_form.save(commit=False)
                    random_config.exam = exam
                    random_config.save()
                    random_config_form.save_m2m()
                    
                    # 自动生成随机题目
                    generate_random_questions(exam)
                    messages.success(request, f"测试「{exam.title}」已创建，并已自动生成{random_config.total_questions}道随机题目")
            else:
                messages.success(request, f"测试「{exam.title}」已创建")
            
            # 处理分数段反馈配置
            feedback_formset = FeedbackConfigFormSet(request.POST, request.FILES)
            if feedback_formset.is_valid():
                feedbacks = feedback_formset.save(commit=False)
                for feedback in feedbacks:
                    feedback.exam = exam
                    feedback.save()
            
            return redirect('exam_list')
    else:
        form = ExamForm()
        random_config_form = RandomConfigForm()
        feedback_formset = FeedbackConfigFormSet()
    
    return render(request, 'quiz_app/exams/create.html', {
        'form': form,
        'random_config_form': random_config_form,
        'feedback_formset': feedback_formset,
    })

@login_required
def generate_random_exam(request, exam_id):
    """生成随机测试题目"""
    exam = get_object_or_404(Exam, id=exam_id)
    if not exam.is_random:
        messages.error(request, "此测试不支持随机出题")
        return redirect('exam_list')
    
    # 清除现有题目
    ExamQuestion.objects.filter(exam=exam).delete()
    
    # 生成新题目
    questions_count = generate_random_questions(exam)
    
    if questions_count > 0:
        messages.success(request, f"已为测试「{exam.title}」随机生成{questions_count}道题目")
    else:
        messages.warning(request, "未能生成题目，请检查随机配置或确保题库中有符合条件的题目")
    
    return redirect('exam_list')

def generate_random_questions(exam):
    """根据配置生成随机题目"""
    try:
        # 获取随机配置
        config = RandomConfig.objects.get(exam=exam)
        
        # 构建查询条件
        query = Q()
        
        # 按分类筛选
        if config.categories.exists():
            category_ids = config.categories.values_list('id', flat=True)
            query &= Q(categories__id__in=category_ids)
        
        # 按难度筛选
        if config.difficulty and config.difficulty != 'mixed':
            query &= Q(difficulty=config.difficulty)
        
        # 按题型筛选
        if config.question_types:
            query &= Q(type__in=config.question_types)
        
        # 查询符合条件的题目
        available_questions = Question.objects.filter(query).distinct()
        
        print(f"随机出题查询: {query}")
        print(f"分类: {list(config.categories.values_list('name', flat=True))}")
        print(f"难度: {config.difficulty}")
        print(f"题型: {config.question_types}")
        print(f"可用题目数量: {available_questions.count()}")
        
        # 如果可用题目数量小于需要的数量，调整需要的数量
        total_questions = min(config.total_questions, available_questions.count())
        
        if total_questions == 0:
            print("未找到符合条件的题目")
            return 0
        
        # 随机选择题目
        selected_questions = random.sample(list(available_questions), total_questions)
        
        # 创建ExamQuestion记录
        for i, question in enumerate(selected_questions):
            ExamQuestion.objects.create(
                exam=exam,
                question=question,
                order=i+1
            )
        
        return total_questions
    except RandomConfig.DoesNotExist:
        print("未找到随机配置")
        return 0
    except Exception as e:
        print(f"生成随机题目时发生错误: {str(e)}")
        return 0

@login_required
def exam_detail(request, exam_id):
    """考试详情页面"""
    exam = get_object_or_404(Exam, id=exam_id)
    return render(request, 'quiz_app/exams/detail.html', {
        'exam': exam
    })

@login_required
def mistake_collection(request):
    """错题集页面"""
    mistakes = MistakeCollection.objects.filter(user=request.user)
    return render(request, 'quiz_app/mistakes/collection.html', {
        'mistakes': mistakes
    })

@login_required
def mistake_analysis(request):
    """错题分析页面"""
    # 获取用户的错题分类统计
    mistake_stats = MistakeCollection.objects.filter(user=request.user).values('question__categories__name').annotate(count=Count('id'))
    
    # 获取用户的错题难度分布
    difficulty_stats = MistakeCollection.objects.filter(user=request.user).values('question__difficulty').annotate(count=Count('id'))
    
    # 获取用户的错题类型分布
    type_stats = MistakeCollection.objects.filter(user=request.user).values('question__type').annotate(count=Count('id'))
    
    return render(request, 'quiz_app/mistakes/analysis.html', {
        'mistake_stats': mistake_stats,
        'difficulty_stats': difficulty_stats,
        'type_stats': type_stats,
    }) 