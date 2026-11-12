import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import StudentProfile, Question, Answer, ForumNotification

# قوائم مؤقتة لتخزين البيانات، الإشعارات، والملفات
NOTIFICATIONS_LIST = [
    {"text": "مرحباً بكم في المنصة الأكاديمية الذكية لقسم تكنولوجيا المعلومات - جامعة بني سويف التكنولوجية.", "image": None},
]
ASSIGNMENTS_LIST = []
EVENTS_LIST = []
FILES_LIST = []  # قائمة لتخزين الملفات والمحاضرات المرفوعة

def home(request):
    context = {
        'notifications': NOTIFICATIONS_LIST,
    }
    return render(request, 'home.html', context)

def student_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # 1. إنشاء المستخدم بحالة غير مفعلة مؤقتاً
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False  # لن يتمكن من تسجيل الدخول الحقيقي إلا بعد تأكيد الكود
        user.save()
        
        # 2. توليد كود عشوائي من 6 أرقام
        code = str(random.randint(100000, 999999))
        
        # 3. حفظ الكود في بروفايل الطالب
        profile, created = StudentProfile.objects.get_or_create(user=user)
        profile.verification_code = code
        profile.save()
        
        # 4. إرسال الإيميل بالكود (تم تصحيح الإيميل المرسل هنا ليطابق إيميل السيرفر)
        send_mail(
            subject='كود التأكيد الخاص بك - منصة جامعة بني سويف التكنولوجية',
            message=f'مرحباً بك يا أحمد، كود التحقق الخاص بك هو: {code}',
            from_email='btu.it.verify@gmail.com',
            recipient_list=[email],
            fail_silently=False,
        )
        
        # تخزين الـ user_id في الـ session للانتقال لصفحة التحقق
        request.session['pending_user_id'] = user.id
        return redirect('verify_code')
        
    return render(request, 'register.html')

def verify_code_view(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        user_id = request.session.get('pending_user_id')
        
        if user_id:
            user = User.objects.get(id=user_id)
            profile = StudentProfile.objects.get(user=user)
            
            if profile.verification_code == entered_code:
                # الكود صحيح! تفعيل الحساب
                profile.is_verified = True
                profile.verification_code = None
                profile.save()
                
                user.is_active = True
                user.save()
                
                # مسح الـ session وتوجيه الطالب لتسجيل الدخول
                del request.session['pending_user_id']
                return redirect('student_login')
            else:
                error_message = "الكود غير صحيح، حاول مرة أخرى."
                return render(request, 'verify.html', {'error': error_message})
                
    return render(request, 'verify.html')

# دالة تسجيل الدخول (محدثة لدعم الدخول برقم التليفون والفصل بين الدكتور والطالب)
def student_login(request):
    if request.method == 'POST':
        phone = request.POST.get('username') # الـ input في الـ html قد يكون اسمه username ولكنه يرسل رقم التليفون
        password = request.POST.get('password')
        
        # البحث عن المستخدم الذي لديه اسم مستخدم مطابقة لرقم التليفون أو من خلال الـ profile
        user = None
        try:
            # محاولة البحث المباشر لو كان الـ username مسجلاً برقم التليفون
            matched_user = User.objects.get(username=phone)
            user = authenticate(request, username=matched_user.username, password=password)
        except User.DoesNotExist:
            pass
            
        if user is not None:
            login(request, user)
            
            # التحقق مما إذا كان المستخدم دكتوراً أو مسؤولاً
            try:
                profile = StudentProfile.objects.get(user=user)
                if profile.is_instructor or user.is_staff:
                    return redirect('instructor_dashboard')
            except StudentProfile.DoesNotExist:
                if user.is_staff:
                    return redirect('instructor_dashboard')
                
            # لو طالب عادي، يذهب للرئيسية
            return redirect('home')
        else:
            error_message = "رقم الهاتف أو كلمة المرور غير صحيحة."
            return render(request, 'login.html', {'error': error_message})
            
    return render(request, 'login.html')

def schedule_view(request):
    return render(request, 'schedule.html')

def courses_view(request):
    # تمرير الملفات والمحاضرات لصفحة المقررات
    context = {
        'files': FILES_LIST
    }
    return render(request, 'courses.html', context)

def events_view(request):
    # تمرير الأنشطة والفعاليات (مع صور إن وجدت)
    context = {
        'events': EVENTS_LIST
    }
    return render(request, 'events.html', context)

def assignments_view(request):
    context = {
        'assignments': ASSIGNMENTS_LIST
    }
    return render(request, 'assignments.html', context)


# دالة عرض صفحة المحاضرات المستقلة لكل مادة
def course_detail_view(request, course_name):
    course_files = [f for f in FILES_LIST if f.get('course') == course_name]
    
    course_titles_ar = {
        'Python': 'أساسيات البرمجة (Python)',
        'Cyber Security': 'مقدمة الأمن السيبراني',
        'IT Essentials': 'أساسيات تكنولوجيا المعلومات',
        'Math': 'الرياضيات الهندسية (Math)',
        'Physics': 'الفيزياء العامة (Physics)',
        'English': 'اللغة الإنجليزية'
    }
    
    context = {
        'course_code': course_name,
        'course_title': course_titles_ar.get(course_name, course_name),
        'files': course_files
    }
    return render(request, 'course_detail.html', context)


# دالة عرض صفحة الواجبات والتكليفات المستقلة لكل مادة
def assignment_detail_view(request, course_name):
    course_assignments = [a for a in ASSIGNMENTS_LIST if a.get('course') == course_name]
    
    course_titles_ar = {
        'Python': 'أساسيات البرمجة (Python)',
        'Cyber Security': 'مقدمة الأمن السيبراني',
        'IT Essentials': 'أساسيات تكنولوجيا المعلومات',
        'Math': 'الرياضيات الهندسية (Math)',
        'Physics': 'الفيزياء العامة (Physics)',
        'English': 'اللغة الإنجليزية'
    }
    
    context = {
        'course_code': course_name,
        'course_title': course_titles_ar.get(course_name, course_name),
        'assignments': course_assignments
    }
    return render(request, 'assignment_detail.html', context)


# دالة عرض صفحة محرر أكواد بايثون أونلاين
def python_compiler(request):
    return render(request, 'python_compiler.html')


@login_required(login_url='student_login')
def instructor_dashboard(request):
    # التحقق من أن المستخدم الحالي دكتور أو مشرف
    try:
        profile = StudentProfile.objects.get(user=request.user)
        if not profile.is_instructor and not request.user.is_staff:
            return redirect('home')
    except StudentProfile.DoesNotExist:
        if not request.user.is_staff:
            return redirect('home')

    if request.method == 'POST':
        section_type = request.POST.get('section_type')
        
        # استقبال الواجبات وتكليفات الـ PDF
        if section_type == 'assignment':
            title = request.POST.get('title')
            course = request.POST.get('course')
            deadline = request.POST.get('deadline')
            description = request.POST.get('description')
            
            uploaded_file = request.FILES.get('assignment_file')
            filename = None
            file_url = None
            
            if uploaded_file:
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_url = fs.url(filename)
            
            ASSIGNMENTS_LIST.append({
                "title": title, 
                "course": course, 
                "deadline": deadline, 
                "description": description,
                "filename": filename,
                "file_url": file_url
            })
            
        # 2. استقبال المحاضرات وملفات الشرح (PDF / Zip / PPT)
        elif section_type == 'course_material':
            lecture_title = request.POST.get('lecture_title')
            course_name = request.POST.get('course_name')
            uploaded_file = request.FILES.get('lecture_file')
            
            if uploaded_file:
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_url = fs.url(filename)
                
                FILES_LIST.append({
                    "title": lecture_title,
                    "course": course_name,
                    "filename": filename,
                    "file_url": file_url
                })
            
        # 3. استقبال الأنشطة والفعاليات (مع دعم رفع صورة)
        elif section_type == 'event':
            event_title = request.POST.get('event_title')
            event_location = request.POST.get('event_location')
            event_details = request.POST.get('event_details')
            
            event_image = request.FILES.get('event_image')
            img_name = None
            img_url = None
            
            if event_image:
                fs = FileSystemStorage()
                img_name = fs.save(event_image.name, event_image)
                img_url = fs.url(img_name)
            
            EVENTS_LIST.append({
                "title": event_title, 
                "location": event_location, 
                "details": event_details,
                "image": img_name,
                "image_url": img_url
            })
            
        # 4. استقبال الإشعارات (مع دعم رفع صورة)
        elif section_type == 'notification':
            notif_text = request.POST.get('notif_text')
            notif_image = request.FILES.get('notif_image')
            img_name = None
            img_url = None
            
            if notif_image:
                fs = FileSystemStorage()
                img_name = fs.save(notif_image.name, notif_image)
                img_url = fs.url(img_name)
            
            NOTIFICATIONS_LIST.insert(0, {
                "text": notif_text,
                "image": img_name,
                "image_url": img_url
            })
            
        return redirect('instructor_dashboard')

    return render(request, 'instructor_dashboard.html')


# دالة المنتدى الأكاديمي
def forum_view(request):
    questions = Question.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')  
        
        if title and content and request.user.is_authenticated:
            Question.objects.create(
                title=title, 
                content=content, 
                image=image, 
                author=request.user
            )
            return redirect('forum')
            
    context = {'questions': questions}
    return render(request, 'forum.html', context)


# دالة تفاصيل السؤال والردود
def question_detail_view(request, question_id):
    question = Question.objects.get(id=question_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content and request.user.is_authenticated:
            Answer.objects.create(question=question, author=request.user, content=content)
            
            if question.author != request.user:
                ForumNotification.objects.create(
                    recipient=question.author,
                    sender=request.user,
                    question=question,
                    message=f"قام {request.user.username} بالرد على سؤالك: {question.title}"
                )
                
            return redirect('question_detail', question_id=question.id)
            
    context = {'question': question}
    return render(request, 'question_detail.html', context)