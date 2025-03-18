from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
import logging

# 设置日志
logger = logging.getLogger(__name__)

def login_view(request):
    # 获取next参数，用于登录后重定向
    next_url = request.GET.get('next', '/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"LOGIN DEBUG: 尝试登录用户: {username}")
        
        # 获取POST请求中的next参数
        next_url = request.POST.get('next', next_url)
        
        # 直接验证
        user = authenticate(username=username, password=password)
        print(f"LOGIN DEBUG: 认证结果: {user}")
        if user is not None:
            print(f"LOGIN DEBUG: 用户权限: is_active={user.is_active}, 组={list(user.groups.all().values_list('name', flat=True))}, 权限数={user.user_permissions.count()}")
            login(request, user)
            messages.success(request, f"欢迎回来，{username}！")
            return redirect(next_url)
        else:
            print(f"LOGIN DEBUG: 认证失败，用户名:{username}")
            messages.error(request, "用户名或密码错误。请确保输入的信息正确，并区分大小写。")
            
        # 表单验证（用于显示更具体的错误）
        form = AuthenticationForm(request, data=request.POST)
        if not form.is_valid():
            print(f"LOGIN DEBUG: 表单无效")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"LOGIN DEBUG: 表单错误 - {field}: {error}")
                    messages.error(request, f"{field}: {error}")
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)
    messages.success(request, "您已成功退出系统。")
    return redirect('login') 