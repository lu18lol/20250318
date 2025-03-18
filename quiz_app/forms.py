from django import forms
from django.forms import inlineformset_factory
from .models import (
    Question, Option, Category, Tag, 
    Exam, ExamQuestion, RandomConfig, FeedbackConfig
)

class QuestionForm(forms.ModelForm):
    """题目表单"""
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Question
        fields = ['type', 'content', 'explanation', 'difficulty', 'categories', 'tags']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'explanation': forms.Textarea(attrs={'rows': 3}),
        }

class OptionForm(forms.ModelForm):
    """选项表单"""
    class Meta:
        model = Option
        fields = ['content', 'is_correct']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2}),
        }

# 创建选项的内联表单集
OptionFormSet = inlineformset_factory(
    Question, Option,
    form=OptionForm,
    extra=4,
    can_delete=True
)

class ExamForm(forms.ModelForm):
    """测试表单"""
    class Meta:
        model = Exam
        fields = ['title', 'description', 'time_limit', 'passing_score', 'is_random', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class RandomConfigForm(forms.ModelForm):
    """随机出题配置表单"""
    class Meta:
        model = RandomConfig
        fields = ['total_questions', 'categories', 'difficulty', 'question_types']
        widgets = {
            'total_questions': forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-multiselect mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'difficulty': forms.Select(attrs={'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'question_types': forms.SelectMultiple(attrs={
                'class': 'form-multiselect mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'choices': RandomConfig.QUESTION_TYPE_CHOICES
            })
        }

class FeedbackConfigForm(forms.ModelForm):
    """分数段反馈配置表单"""
    class Meta:
        model = FeedbackConfig
        fields = ['min_score', 'max_score', 'message', 'image']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2}),
        }

# 创建反馈配置的内联表单集
FeedbackConfigFormSet = inlineformset_factory(
    Exam, FeedbackConfig,
    form=FeedbackConfigForm,
    extra=3,
    can_delete=True
)

class ExamQuestionForm(forms.ModelForm):
    """测试题目关联表单"""
    question = forms.ModelChoiceField(
        queryset=Question.objects.all(),
        widget=forms.Select(attrs={'class': 'select2'})
    )
    
    class Meta:
        model = ExamQuestion
        fields = ['question', 'score', 'order']

# 创建测试题目关联的内联表单集
ExamQuestionFormSet = inlineformset_factory(
    Exam, ExamQuestion,
    form=ExamQuestionForm,
    extra=5,
    can_delete=True
) 