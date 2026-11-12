from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.home, name='home'),
    
    # صفحات الطلاب والأقسام
    path('register/', views.student_register, name='register'),
    path('verify/', views.verify_code_view, name='verify_code'),  # مسار صفحة إدخال كود التحقق الجديد
    path('login/', views.student_login, name='login'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('courses/', views.courses_view, name='courses'),
    
    # مسارات تفاصيل المواد والواجبات لكل مادة بشكل مستقل
    path('course/<str:course_name>/', views.course_detail_view, name='course_detail'),
    path('assignment/<str:course_name>/', views.assignment_detail_view, name='assignment_detail'),
    
    path('events/', views.events_view, name='events'),
    path('assignments/', views.assignments_view, name='assignments'),
    
    # مسار محرر أكواد بايثون أونلاين (تم إضافته هنا بنجاح)
    path('compiler/', views.python_compiler, name='python_compiler'),
    
    # مسارات المنتدى الأكاديمي 💬
    path('forum/', views.forum_view, name='forum'),
    path('forum/question/<int:question_id>/', views.question_detail_view, name='question_detail'),
    
    # لوحة التحكم الشاملة (للدكتور والمسؤول)
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
]

# تفعيل مسار ملفات الـ Media في وضع التطوير المحلي
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)