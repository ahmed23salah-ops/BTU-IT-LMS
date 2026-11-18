"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from courses import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # مسارات الحسابات والتسجيل والدخول والخروج بالأسماء المضبوطة تماماً
    path('login/', views.student_login, name='student_login'),
    path('register/', views.student_register, name='student_register'),
    path('verify/', views.verify_code_view, name='verify_code'),
    path('logout/', views.student_logout, name='student_logout'),
    
    # مسار موافقة الأدمن على حساب الطالب الجديد
    path('approve-student/<int:user_id>/', views.approve_student_view, name='approve_student'),
    
    path('', include('courses.urls')),  # ربط بقية مسارات التطبيق
]