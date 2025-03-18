from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, F, Q, Sum, Avg
from django.db import transaction
from django.contrib import messages
from ..models import (
    Exam, Submission, Answer, Question, Option, FeedbackConfig,
    MistakeCollection, MistakeCategory, Category
)
import json
from collections import defaultdict

@login_required
def start_exam(request, exam_id):
    """开始测试"""
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    
    # 如果是随机考试，检查是否有题目，如果没有则生成
    if exam.is_random and exam.exam_questions.count() == 0:
        from ..views.exam_views import generate_random_questions
        questions_count = generate_random_questions(exam)
        if questions_count == 0:
            messages.error(request, "无法生成随机题目，请联系管理员")
            return redirect('exam_list')
    
    # 创建答题记录
    submission = Submission.objects.create(
        user=request.user,
        exam=exam,
        start_time=timezone.now()
    )
    
    return redirect('take_exam', submission_id=submission.id)

@login_required
def take_exam(request, submission_id):
    """答题界面"""
    submission = get_object_or_404(Submission, id=submission_id, user=request.user)
    exam = submission.exam
    
    # 检查是否已完成
    if submission.end_time:
        return redirect('exam_result', submission_id=submission.id)
    
    # 获取题目
    exam_questions = exam.exam_questions.all().select_related('question')
    
    return render(request, 'quiz_app/exams/take_exam.html', {
        'submission': submission,
        'exam': exam,
        'exam_questions': exam_questions,
    })

@login_required
@transaction.atomic
def submit_exam(request, submission_id):
    """提交测试答案"""
    if request.method != 'POST':
        return JsonResponse({'error': '方法不允许'}, status=405)
    
    submission = get_object_or_404(Submission, id=submission_id, user=request.user)
    
    # 检查是否已完成
    if submission.end_time:
        return JsonResponse({'error': '此测试已完成'}, status=400)
    
    # 获取答案数据
    try:
        print(f"收到提交请求，用户: {request.user.username}, 提交ID: {submission_id}")
        print(f"原始请求体: {request.body.decode('utf-8')}")
        answers_data = json.loads(request.body)
        print(f"解析后的答案数据: {answers_data}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {str(e)}")
        return JsonResponse({'error': 'JSON解析错误'}, status=400)
    
    total_score = 0
    total_possible = 0
    
    # 用于记录错题分类统计
    category_stats = defaultdict(lambda: {'total': 0, 'mistakes': 0})
    
    # 处理每个题目的答案
    for answer_data in answers_data:
        question_id = answer_data.get('question_id')
        print(f"处理题目: {question_id}")
        question = get_object_or_404(Question, id=question_id)
        
        # 获取此题在考试中的分值
        try:
            exam_question = submission.exam.exam_questions.get(question=question)
            question_score = exam_question.score
            total_possible += question_score
            print(f"题目分值: {question_score}")
        except Exception as e:
            print(f"获取题目分值出错: {str(e)}")
            question_score = 0
        
        # 创建答案记录
        answer = Answer(
            submission=submission,
            question=question,
            score=0
        )
        
        # 更新分类统计
        for category in question.categories.all():
            category_stats[category.id]['total'] += 1
        
        # 根据题型处理答案
        if question.type in ['single', 'multiple']:
            selected_option_ids = answer_data.get('selected_options', [])
            print(f"题目 {question_id} 用户选择的选项: {selected_option_ids}")
            correct_options = question.options.filter(is_correct=True)
            print(f"题目 {question_id} 正确的选项: {list(correct_options.values_list('id', flat=True))}")
            
            # 保存答案
            answer.save()
            for option_id in selected_option_ids:
                option = get_object_or_404(Option, id=option_id)
                answer.selected_options.add(option)
            
            # 评分
            if question.type == 'single':
                # 单选题: 选择正确选项得满分
                if len(selected_option_ids) == 1:
                    option = get_object_or_404(Option, id=selected_option_ids[0])
                    if option.is_correct:
                        answer.is_correct = True
                        answer.score = question_score
                        print(f"单选题 {question_id} 回答正确")
                    else:
                        print(f"单选题 {question_id} 回答错误")
            else:
                # 多选题: 完全正确得满分
                selected_options = set(selected_option_ids)
                correct_option_ids = set(correct_options.values_list('id', flat=True))
                if selected_options == correct_option_ids:
                    answer.is_correct = True
                    answer.score = question_score
                    print(f"多选题 {question_id} 回答正确")
                else:
                    print(f"多选题 {question_id} 回答错误, 用户选择: {selected_options}, 正确选项: {correct_option_ids}")
        
        elif question.type == 'truefalse':
            # 判断题处理
            selected = answer_data.get('selected', False)
            print(f"判断题 {question_id} 用户选择: {selected}")
            answer.text_answer = str(selected)
            
            # 评分
            correct_answer = question.options.filter(is_correct=True).exists()
            print(f"判断题 {question_id} 正确答案: {correct_answer}")
            if selected == correct_answer:
                answer.is_correct = True
                answer.score = question_score
                print(f"判断题 {question_id} 回答正确")
            else:
                print(f"判断题 {question_id} 回答错误")
            
            answer.save()
        
        elif question.type == 'essay':
            # 问答题处理 (需要人工评分)
            answer.text_answer = answer_data.get('text_answer', '')
            print(f"问答题 {question_id} 用户回答: {answer.text_answer[:50]}...")
            answer.save()
        
        # 累加分数
        total_score += answer.score
        
        # 如果答错了，添加到错题集
        if not answer.is_correct:
            # 更新错题统计
            for category in question.categories.all():
                category_stats[category.id]['mistakes'] += 1
            
            # 添加到错题集
            MistakeCollection.objects.update_or_create(
                user=request.user,
                question=question,
                defaults={'answer': answer}
            )
        
        answer.save()
    
    # 更新错题分类统计
    for category_id, stats in category_stats.items():
        category = Category.objects.get(id=category_id)
        try:
            # 先尝试获取现有记录进行更新
            mistake_category = MistakeCategory.objects.get(user=request.user, category=category)
            mistake_category.mistake_count += stats['mistakes']
            mistake_category.total_count += stats['total']
            mistake_category.save()
        except MistakeCategory.DoesNotExist:
            # 如果不存在，则创建新记录
            MistakeCategory.objects.create(
                user=request.user,
                category=category,
                mistake_count=stats['mistakes'],
                total_count=stats['total']
            )
    
    # 更新提交记录
    submission.end_time = timezone.now()
    submission.total_score = total_score
    
    # 获取对应分数段的反馈
    feedback = None
    for fb_config in submission.exam.feedback_configs.all():
        if fb_config.min_score <= total_score <= fb_config.max_score:
            feedback = fb_config
            break
    
    submission.save()
    
    response_data = {
        'success': True,
        'score': total_score,
        'total': total_possible,
        'percentage': (total_score / total_possible * 100) if total_possible > 0 else 0,
        'feedback': {
            'message': feedback.message if feedback else "测试已完成",
            'image_url': feedback.image.url if feedback and feedback.image else None
        }
    }
    print(f"返回响应: {response_data}")
    return JsonResponse(response_data)

@login_required
def exam_result(request, submission_id):
    """查看测试结果"""
    submission = get_object_or_404(Submission, id=submission_id, user=request.user)
    
    # 确保测试已完成
    if not submission.end_time:
        return redirect('take_exam', submission_id=submission.id)
    
    # 获取答案和反馈
    answers = submission.answers.all().select_related('question')
    
    # 获取对应分数段的反馈
    feedback = None
    for fb_config in submission.exam.feedback_configs.all():
        if fb_config.min_score <= submission.total_score <= fb_config.max_score:
            feedback = fb_config
            break
    
    # 计算错题统计
    wrong_answers = answers.filter(is_correct=False)
    wrong_count = wrong_answers.count()
    total_count = answers.count()
    
    # 按题型统计错题
    wrong_by_type = {}
    for q_type, q_type_display in Question.QUESTION_TYPES:
        type_total = answers.filter(question__type=q_type).count()
        type_wrong = wrong_answers.filter(question__type=q_type).count()
        if type_total > 0:
            wrong_by_type[q_type_display] = {
                'total': type_total,
                'wrong': type_wrong,
                'percentage': type_wrong / type_total * 100
            }
    
    # 按分类统计错题
    wrong_by_category = {}
    for answer in wrong_answers:
        for category in answer.question.categories.all():
            if category.name not in wrong_by_category:
                wrong_by_category[category.name] = 0
            wrong_by_category[category.name] += 1
    
    return render(request, 'quiz_app/exams/result.html', {
        'submission': submission,
        'answers': answers,
        'feedback': feedback,
        'wrong_count': wrong_count,
        'total_count': total_count,
        'wrong_percentage': (wrong_count / total_count * 100) if total_count > 0 else 0,
        'wrong_by_type': wrong_by_type,
        'wrong_by_category': wrong_by_category
    })

@login_required
def mistake_collection(request):
    """错题集"""
    mistakes = MistakeCollection.objects.filter(user=request.user).select_related(
        'question', 'answer'
    )
    
    # 过滤条件
    category_id = request.GET.get('category')
    q_type = request.GET.get('type')
    
    if category_id:
        mistakes = mistakes.filter(question__categories__id=category_id)
    if q_type:
        mistakes = mistakes.filter(question__type=q_type)
    
    # 分类统计
    categories = MistakeCategory.objects.filter(
        user=request.user
    ).select_related('category').order_by('-mistake_count')
    
    # 题型统计
    type_stats = []
    for q_type, q_type_display in Question.QUESTION_TYPES:
        type_count = mistakes.filter(question__type=q_type).count()
        if type_count > 0:
            type_stats.append({
                'type': q_type_display,
                'count': type_count
            })
    
    return render(request, 'quiz_app/mistakes/collection.html', {
        'mistakes': mistakes,
        'categories': categories,
        'type_stats': type_stats
    })

@login_required
def mistake_analysis(request):
    """错题分析"""
    # 获取用户的错题分类统计
    category_stats = MistakeCategory.objects.filter(
        user=request.user, total_count__gt=0
    ).select_related('category').order_by('-mistake_count')
    
    # 计算总体错误率
    total_mistakes = sum(stat.mistake_count for stat in category_stats)
    total_questions = sum(stat.total_count for stat in category_stats)
    overall_error_rate = total_mistakes / total_questions if total_questions > 0 else 0
    
    # 按题型统计错误率
    type_stats = []
    for q_type, q_type_display in Question.QUESTION_TYPES:
        # 获取该题型的所有答题记录
        type_answers = Answer.objects.filter(
            submission__user=request.user,
            question__type=q_type
        )
        
        type_total = type_answers.count()
        type_wrong = type_answers.filter(is_correct=False).count()
        
        if type_total > 0:
            type_stats.append({
                'type': q_type_display,
                'total': type_total,
                'wrong': type_wrong,
                'error_rate': type_wrong / type_total * 100
            })
    
    # 获取最近的错题
    recent_mistakes = MistakeCollection.objects.filter(
        user=request.user
    ).select_related('question').order_by('-created_at')[:10]
    
    return render(request, 'quiz_app/mistakes/analysis.html', {
        'category_stats': category_stats,
        'overall_error_rate': overall_error_rate * 100,
        'type_stats': type_stats,
        'recent_mistakes': recent_mistakes
    })

@login_required
def remove_from_mistakes(request, mistake_id):
    """从错题集中移除"""
    if request.method != 'POST':
        return JsonResponse({'error': '方法不允许'}, status=405)
    
    mistake = get_object_or_404(MistakeCollection, id=mistake_id, user=request.user)
    mistake.delete()
    
    return JsonResponse({'success': True}) 