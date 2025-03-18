from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from quiz_app.models import User, Exam, Submission, MistakeCollection

class Command(BaseCommand):
    help = '设置用户组权限'

    def handle(self, *args, **options):
        # 创建普通用户组
        user_group, created = Group.objects.get_or_create(name='普通用户')
        
        # 清除现有权限
        user_group.permissions.clear()
        
        # 添加考试相关权限
        exam_content_type = ContentType.objects.get_for_model(Exam)
        view_exam = Permission.objects.get(content_type=exam_content_type, codename='view_exam')
        user_group.permissions.add(view_exam)
        
        # 添加提交相关权限
        submission_content_type = ContentType.objects.get_for_model(Submission)
        add_submission = Permission.objects.get(content_type=submission_content_type, codename='add_submission')
        change_submission = Permission.objects.get(content_type=submission_content_type, codename='change_submission')
        view_submission = Permission.objects.get(content_type=submission_content_type, codename='view_submission')
        user_group.permissions.add(add_submission, change_submission, view_submission)
        
        # 添加错题集相关权限
        mistake_content_type = ContentType.objects.get_for_model(MistakeCollection)
        add_mistake = Permission.objects.get(content_type=mistake_content_type, codename='add_mistakecollection')
        change_mistake = Permission.objects.get(content_type=mistake_content_type, codename='change_mistakecollection')
        view_mistake = Permission.objects.get(content_type=mistake_content_type, codename='view_mistakecollection')
        delete_mistake = Permission.objects.get(content_type=mistake_content_type, codename='delete_mistakecollection')
        user_group.permissions.add(add_mistake, change_mistake, view_mistake, delete_mistake)
        
        # 确保所有test2用户都在普通用户组中
        test2_user = User.objects.get(username='test2')
        test2_user.groups.add(user_group)
        
        # 加入权限设置
        test2_user.is_active = True
        test2_user.save()
        
        self.stdout.write(self.style.SUCCESS(f'成功设置普通用户组权限，包含 {user_group.permissions.count()} 个权限'))
        self.stdout.write(self.style.SUCCESS(f'用户 test2 已添加到普通用户组')) 