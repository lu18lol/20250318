from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    """扩展用户模型"""
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Category(models.Model):
    """题目分类"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    """题目标签"""
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Question(models.Model):
    """题目模型"""
    QUESTION_TYPES = (
        ('single', '单选题'),
        ('multiple', '多选题'),
        ('truefalse', '判断题'),
        ('essay', '问答题'),
    )
    
    DIFFICULTY_LEVELS = (
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    content = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    categories = models.ManyToManyField(Category, related_name='questions')
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.content[:50]}..."

class Option(models.Model):
    """选项模型"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    content = models.TextField()
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.content[:30]}... ({'正确' if self.is_correct else '错误'})"

class Exam(models.Model):
    """测试/考试模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit = models.IntegerField(help_text="时间限制(分钟)", null=True, blank=True)
    passing_score = models.FloatField(default=60.0)
    is_random = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class ExamQuestion(models.Model):
    """考试题目关联模型"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    score = models.FloatField(default=1.0)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']

class RandomConfig(models.Model):
    """随机出题配置"""
    DIFFICULTY_CHOICES = [
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
        ('mixed', '混合'),
    ]

    QUESTION_TYPE_CHOICES = [
        ('single', '单选题'),
        ('multiple', '多选题'),
        ('truefalse', '判断题'),
        ('essay', '问答题'),
    ]

    exam = models.OneToOneField('Exam', on_delete=models.CASCADE, related_name='random_config')
    total_questions = models.PositiveIntegerField(verbose_name='题目总数')
    categories = models.ManyToManyField('Category', verbose_name='题目分类')
    difficulty = models.CharField(
        max_length=10, 
        choices=DIFFICULTY_CHOICES,
        default='mixed',
        verbose_name='难度级别'
    )
    question_types = models.JSONField(
        default=list,
        verbose_name='题目类型',
        help_text='可选择多个题目类型'
    )

    class Meta:
        verbose_name = '随机出题配置'
        verbose_name_plural = '随机出题配置'

    def __str__(self):
        return f"{self.exam.title}的随机出题配置"

    def get_questions(self):
        """根据配置获取随机题目"""
        from django.db.models import Q
        
        # 基础查询：根据分类筛选
        questions = Question.objects.filter(categories__in=self.categories.all()).distinct()
        
        # 根据难度筛选
        if self.difficulty != 'mixed':
            questions = questions.filter(difficulty=self.difficulty)
        
        # 根据题目类型筛选
        if self.question_types:
            questions = questions.filter(type__in=self.question_types)
        
        # 随机选择指定数量的题目
        return questions.order_by('?')[:self.total_questions]

class FeedbackConfig(models.Model):
    """分数段反馈配置"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='feedback_configs')
    min_score = models.FloatField()
    max_score = models.FloatField()
    message = models.TextField()
    image = models.ImageField(upload_to='feedback_images/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.min_score}-{self.max_score}: {self.message[:30]}..."

class Submission(models.Model):
    """答题记录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.total_score}"

class Answer(models.Model):
    """用户答案"""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    score = models.FloatField(default=0)

class MistakeCollection(models.Model):
    """错题收集"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mistake_collections')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='mistake_records')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'question')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.question.content[:30]}..."

class MistakeCategory(models.Model):
    """错题分类统计"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mistake_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    mistake_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'category')
    
    @property
    def error_rate(self):
        """错误率"""
        if self.total_count == 0:
            return 0
        return self.mistake_count / self.total_count
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.error_rate:.2%}"


# 信号处理
from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver

@receiver(post_save, sender=User)
def add_user_to_normal_group(sender, instance, created, **kwargs):
    """当创建新用户时，自动将其添加到普通用户组"""
    if created and not instance.is_superuser and not instance.is_staff:
        # 获取或创建普通用户组
        user_group, _ = Group.objects.get_or_create(name='普通用户')
        
        # 将用户添加到普通用户组
        instance.groups.add(user_group)
        
        # 确保用户是激活状态
        if not instance.is_active:
            instance.is_active = True
            instance.save(update_fields=['is_active']) 