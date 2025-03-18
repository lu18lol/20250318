from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from quiz_app.models import User, Exam, Submission, MistakeCollection

class Command(BaseCommand):
    help = '修复所有用户的权限和密码'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='指定要修复的用户名')

    def handle(self, *args, **options):
        # 创建普通用户组并设置权限
        user_group, created = Group.objects.get_or_create(name='普通用户')
        
        # 清除现有权限
        user_group.permissions.clear()
        
        # 添加考试相关权限
        exam_content_type = ContentType.objects.get_for_model(Exam)
        for perm in Permission.objects.filter(content_type=exam_content_type):
            user_group.permissions.add(perm)
        
        # 添加提交相关权限
        submission_content_type = ContentType.objects.get_for_model(Submission)
        for perm in Permission.objects.filter(content_type=submission_content_type):
            user_group.permissions.add(perm)
        
        # 添加错题集相关权限
        mistake_content_type = ContentType.objects.get_for_model(MistakeCollection)
        for perm in Permission.objects.filter(content_type=mistake_content_type):
            user_group.permissions.add(perm)
        
        self.stdout.write(self.style.SUCCESS(f'成功设置普通用户组权限，共 {user_group.permissions.count()} 个权限'))
        
        # 修复指定用户或所有非管理员用户
        if options['username']:
            users = User.objects.filter(username=options['username'])
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'用户 {options["username"]} 不存在'))
                return
        else:
            # 排除管理员用户
            users = User.objects.filter(is_superuser=False, is_staff=False)
        
        for user in users:
            # 添加到普通用户组
            user.groups.add(user_group)
            
            # 确保用户是激活状态
            user.is_active = True
            
            # 如果是非管理员用户，重置密码为用户名
            if not user.is_superuser and not user.is_staff:
                password = f"{user.username}123"
                user.set_password(password)
                self.stdout.write(f'用户 {user.username} 的密码已重置为: {password}')
            
            user.save()
            self.stdout.write(self.style.SUCCESS(f'已修复用户 {user.username} 的权限和状态')) 