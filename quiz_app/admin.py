from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from .models import (
    User, Category, Tag, Question, Option, 
    Exam, ExamQuestion, RandomConfig, FeedbackConfig,
    Submission, Answer, MistakeCollection, MistakeCategory
)
from .utils.excel_utils import ExcelProcessor

# 1.1 用户管理模块
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_admin', 'date_joined', 'exam_count', 'avg_score')
    search_fields = ('username', 'email')
    list_filter = ('is_admin', 'is_staff', 'date_joined')
    fieldsets = (
        ('基本信息', {
            'fields': ('username', 'email', 'password')
        }),
        ('权限设置', {
            'fields': ('is_active', 'is_staff', 'is_admin', 'groups', 'user_permissions')
        }),
        ('重要日期', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """确保密码被正确加密保存"""
        if change:  # 如果是修改现有用户
            if 'password' in form.changed_data:
                obj.set_password(obj.password)
        else:  # 如果是创建新用户
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
    
    def exam_count(self, obj):
        return obj.submissions.count()
    exam_count.short_description = '参与测试次数'
    
    def avg_score(self, obj):
        avg = obj.submissions.aggregate(Avg('total_score'))['total_score__avg']
        return round(avg, 2) if avg else 0
    avg_score.short_description = '平均分数'

# 2. 统一题库系统
class OptionInline(admin.TabularInline):
    model = Option
    extra = 4

class QuestionImportForm(forms.Form):
    excel_file = forms.FileField()

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('content_preview', 'type', 'difficulty', 'category_list', 'tag_list', 'usage_count')
    list_filter = ('type', 'difficulty', 'categories', 'tags', 'created_at')
    search_fields = ('content', 'categories__name', 'tags__name')
    inlines = [OptionInline]
    filter_horizontal = ('categories', 'tags')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel_view), name='question-import-excel'),
            path('download-template/', self.admin_site.admin_view(self.download_template), name='question-download-template'),
        ]
        return custom_urls + urls
    
    def content_preview(self, obj):
        return format_html('<span title="{}">{}</span>', obj.content, obj.content[:50] + '...')
    content_preview.short_description = '题目内容'
    
    def category_list(self, obj):
        return ', '.join(c.name for c in obj.categories.all())
    category_list.short_description = '分类'
    
    def tag_list(self, obj):
        return ', '.join(t.name for t in obj.tags.all())
    tag_list.short_description = '标签'
    
    def usage_count(self, obj):
        return obj.examquestion_set.count()
    usage_count.short_description = '使用次数'
    
    def import_excel_view(self, request):
        if request.method == 'POST':
            if 'excel_file' not in request.FILES:
                messages.error(request, '请选择要导入的Excel文件')
                return redirect('.')
            
            file = request.FILES['excel_file']
            if not file.name.endswith(('.xls', '.xlsx')):
                messages.error(request, '请上传Excel文件(.xls或.xlsx格式)')
                return redirect('.')
            
            try:
                results = ExcelProcessor.import_questions(file, request.user)
                context = {
                    **self.admin_site.each_context(request),
                    'title': '导入题目',
                    'results': results,
                }
                if results['failed'] > 0:
                    messages.warning(
                        request, 
                        f'导入完成，成功{results["success"]}条，'
                        f'失败{results["failed"]}条，请查看详细错误信息'
                    )
                else:
                    messages.success(
                        request,
                        f'成功导入{results["success"]}条题目'
                    )
                return render(request, 'admin/quiz_app/question/import_excel.html', context)
            except Exception as e:
                messages.error(request, f'导入失败：{str(e)}')
                return redirect('.')
        
        context = {
            **self.admin_site.each_context(request),
            'title': '导入题目'
        }
        return render(request, 'admin/quiz_app/question/import_excel.html', context)
    
    def download_template(self, request):
        return ExcelProcessor.export_template()
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'question_count', 'usage_in_exams')
    search_fields = ('name',)
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = '题目数量'
    
    def usage_in_exams(self, obj):
        return Exam.objects.filter(exam_questions__question__categories=obj).distinct().count()
    usage_in_exams.short_description = '在测试中使用次数'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'question_count')
    search_fields = ('name',)
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = '题目数量'

# 1.2 & 1.3 测试/考试管理模块
class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 5
    raw_id_fields = ('question',)

class RandomConfigForm(forms.ModelForm):
    """随机配置自定义表单"""
    # 将JSONField转换为多选框
    question_types = forms.MultipleChoiceField(
        choices=RandomConfig.QUESTION_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='题目类型'
    )
    
    class Meta:
        model = RandomConfig
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是编辑现有对象，获取其中的数据
        if self.instance.pk and self.instance.question_types:
            self.initial['question_types'] = self.instance.question_types
    
    def clean_question_types(self):
        """将多选框的值转换为列表"""
        return self.cleaned_data['question_types']

class RandomConfigInline(admin.StackedInline):
    model = RandomConfig
    form = RandomConfigForm
    filter_horizontal = ('categories',)

class FeedbackConfigInline(admin.TabularInline):
    model = FeedbackConfig
    extra = 3

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam_type', 'time_limit', 'passing_score', 'question_count', 'participant_count', 'avg_score', 'pass_rate')
    list_filter = ('is_random', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    inlines = [RandomConfigInline, FeedbackConfigInline, ExamQuestionInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'created_by')
        }),
        ('测试设置', {
            'fields': ('time_limit', 'passing_score', 'is_random', 'is_active')
        }),
    )
    
    def exam_type(self, obj):
        return '随机测试' if obj.is_random else '固定测试'
    exam_type.short_description = '测试类型'
    
    def question_count(self, obj):
        return obj.exam_questions.count()
    question_count.short_description = '题目数量'
    
    def participant_count(self, obj):
        return obj.submissions.count()
    participant_count.short_description = '参与人数'
    
    def avg_score(self, obj):
        avg = obj.submissions.aggregate(Avg('total_score'))['total_score__avg']
        return round(avg, 2) if avg else 0
    avg_score.short_description = '平均分'
    
    def pass_rate(self, obj):
        total = obj.submissions.count()
        if total == 0:
            return '0%'
        passed = obj.submissions.filter(total_score__gte=obj.passing_score).count()
        return f'{round(passed/total*100, 1)}%'
    pass_rate.short_description = '通过率'

# 结果管理
class AnswerInline(admin.TabularInline):
    model = Answer
    readonly_fields = ('question', 'selected_options', 'text_answer', 'is_correct', 'score')
    extra = 0
    can_delete = False

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'total_score', 'is_passed', 'completion_time', 'created_at')
    list_filter = ('exam', 'created_at')
    search_fields = ('user__username', 'exam__title')
    inlines = [AnswerInline]
    readonly_fields = ('user', 'exam', 'start_time', 'end_time', 'total_score')
    
    def is_passed(self, obj):
        passed = obj.total_score >= obj.exam.passing_score
        return format_html(
            '<span style="color: {}">{}</span>',
            '#10B981' if passed else '#EF4444',
            '通过' if passed else '未通过'
        )
    is_passed.short_description = '是否通过'
    
    def completion_time(self, obj):
        if obj.start_time and obj.end_time:
            time_diff = obj.end_time - obj.start_time
            return f'{time_diff.seconds//60}分{time_diff.seconds%60}秒'
        return '-'
    completion_time.short_description = '完成用时'

# 错题分析
@admin.register(MistakeCollection)
class MistakeCollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'question_type', 'categories', 'created_at')
    list_filter = ('user', 'question__type', 'question__categories', 'created_at')
    search_fields = ('user__username', 'question__content')
    readonly_fields = ('user', 'question', 'answer', 'created_at')
    
    def question_type(self, obj):
        return obj.question.get_type_display()
    question_type.short_description = '题目类型'
    
    def categories(self, obj):
        return ', '.join(c.name for c in obj.question.categories.all())
    categories.short_description = '所属分类'

@admin.register(MistakeCategory)
class MistakeCategoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'mistake_count', 'total_count', 'error_rate_display')
    list_filter = ('user', 'category')
    search_fields = ('user__username', 'category__name')
    readonly_fields = ('user', 'category', 'mistake_count', 'total_count')
    
    def error_rate_display(self, obj):
        rate = obj.error_rate * 100
        return format_html(
            '<span style="color: {}">{:.1f}%</span>',
            '#EF4444' if rate > 50 else '#10B981',
            rate
        )
    error_rate_display.short_description = '错误率' 