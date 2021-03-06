from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from .models import User
from django.contrib.auth import login
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection
from django.contrib.auth import authenticate


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 接收
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        mobile = request.POST.get('phone')
        sms_code = request.POST.get('msg_code')
        allow = request.POST.get('allow')

        # 验证
        # 1.非空
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.HttpResponseForbidden('填写数据不完整')
        # 2.用户名
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名为5-20个字符')
        if User.objects.filter(username=username).count() > 0:
            return http.HttpResponseForbidden('用户名已经存在')
        # 密码
        if not re.match('^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码为8-20个字符')
        # 确认密码
        if password != password2:
            return http.HttpResponseForbidden('两个密码不一致')
        # 手机号
        if not re.match('^1[3456789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号错误')
        if User.objects.filter(mobile=mobile).count() > 0:
            return http.HttpResponseForbidden('手机号存在')
        # 短信验证码
        # 1.读取redis中的短信验证码
        redis_cli = get_redis_connection('sms_code')
        sms_code_redis = redis_cli.get(mobile)
        # 2.判断是否过期
        if sms_code_redis is None:
            return http.HttpResponseForbidden('短信验证码已经过期')
        # 3.删除短信验证码，不可以使用第二次
        redis_cli.delete(mobile)
        redis_cli.delete(mobile + '_flag')
        # 4.判断是否正确
        if sms_code_redis.decode() != sms_code:
            return http.HttpResponseForbidden('短信验证码错误')

        # 处理
        # 1.创建用户对象
        user = User.objects.create_user(
            username=username,
            password=password,
            mobile=mobile
        )
        # 2.状态保持
        login(request, user)

        # 响应
        return redirect('/')


class UsernameCountView(View):
    def get(self, request, username):
        # 接收：通过路由在路径中提取
        # 验证：路由的正则表达式
        # 处理：判断用户名是否存在
        count = User.objects.filter(username=username).count()
        # 响应：提示是否存在
        return http.JsonResponse({
            'count': count,
            'code': RETCODE.OK,
            'errmsg': 'OK'
        })


class MobileCountView(View):
    def get(self, request, mobile):
        # 接收
        # 验证
        # 处理：判断手机号是否存在
        count = User.objects.filter(mobile=mobile).count()
        # 响应：提示是否存在
        return http.JsonResponse({
            'count': count,
            'code': RETCODE.OK,
            'errmsg': "OK"
        })


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 接收
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')

        # 验证：根据用户名查询，找到对象后再对比密码
        '''
        user=User.objects.get(username=username)
        user.password==加密(pwd)===>user.check_password(pwd)
        '''
        user = authenticate(request, username=username, password=pwd)
        if user is None:
            # 用户名或密码错误
            return http.HttpResponseForbidden('用户名或密码错误')
        else:
            # 用户名和密码正确
            login(request, user)
            return redirect('/')
