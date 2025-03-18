from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..models import Question, Option, Category, Tag
from ..forms import QuestionForm, OptionFormSet
from ..utils.excel_import import process_excel_import
import pandas as pd

@login_required
def question_list(request):
    """题目列表页面"""
    questions = Question.objects.all()
    categories = Category.objects.all()
    
    # 过滤逻辑
    category_id = request.GET.get('category')
    q_type = request.GET.get('type')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('search')
    
    if category_id:
        questions = questions.filter(categories__id=category_id)
    if q_type:
        questions = questions.filter(type=q_type)
    if difficulty:
        questions = questions.filter(difficulty=difficulty)
    if search:
        questions = questions.filter(content__icontains=search)
    
    return render(request, 'quiz_app/questions/list.html', {
        'questions': questions,
        'categories': categories,
    })

@login_required
def question_create(request):
    """创建题目"""
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = OptionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.created_by = request.user
            question.save()
            form.save_m2m()  # 保存多对多关系
            
            # 保存选项
            options = formset.save(commit=False)
            for option in options:
                option.question = question
                option.save()
            
            # 处理判断题选项
            if question.type == 'truefalse' and 'truefalse_answer' in request.POST:
                # 删除已有选项
                Option.objects.filter(question=question).delete()
                
                # 创建是/否选项
                Option.objects.create(
                    question=question,
                    content='是',
                    is_correct=request.POST['truefalse_answer'] == 'true'
                )
                Option.objects.create(
                    question=question,
                    content='否',
                    is_correct=request.POST['truefalse_answer'] == 'false'
                )
            
            return redirect('question_list')
    else:
        form = QuestionForm()
        formset = OptionFormSet()
    
    return render(request, 'quiz_app/questions/create.html', {
        'form': form,
        'formset': formset,
    })

@login_required
def import_questions(request):
    """批量导入题目"""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            # 处理Excel导入
            result = process_excel_import(excel_file, request.user)
            return render(request, 'quiz_app/questions/import.html', {'result': result})
        except Exception as e:
            return render(request, 'quiz_app/questions/import.html', {'error': str(e)})
    
    return render(request, 'quiz_app/questions/import.html') 