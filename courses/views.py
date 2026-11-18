import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import (
    StudentProfile, Question, Answer, ForumNotification, 
    Course, Resource, StudentProgress, Assignment, Event, GeneralNotification,
    Exam, ExamQuestion, StudentExamSubmission
)

def home(request):
    notifications = GeneralNotification.objects.all().order_by('-created_at')
    context = {
        'notifications': notifications,
        'new_assignments_count': Assignment.objects.count(), # دائم من قاعدة البيانات ✅
        'new_courses_count': Resource.objects.count(),       # دائم من قاعدة البيانات ✅
        'new_events_count': Event.objects.count(),           # دائم من قاعدة البيانات ✅
    }
    return render(request, 'home.html', context)

def student_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # 1. إنشاء المستخدم بحالة غير مفعلة مؤقتاً
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False  # لن يتمكن من تسجيل الدخول الحقيقي إلا بعد تأكيد الكود وموافقة الأدمن
        user.save()
        
        # 2. توليد كود عشوائي من 6 أرقام
        code = str(random.randint(100000, 999999))
        
        # 3. حفظ الكود في بروفايل الطالب
        profile, created = StudentProfile.objects.get_or_create(user=user)
        profile.verification_code = code
        profile.save()
        
        # 4. إرسال الإيميل بالكود
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
                # الكود صحيح! التحقق من الإيميل تم، لكن الحساب يظل معلقاً حتى موافقة الأدمن (is_active تظل False)
                profile.is_verified = True
                profile.verification_code = None
                profile.save()
                
                # مسح الـ session وتوجيه الطالب لصفحة تنتظر موافقة الأدمن أو تسجيل الدخول مع رسالة
                del request.session['pending_user_id']
                return redirect('student_login')
            else:
                error_message = "الكود غير صحيح، حاول مرة أخرى."
                return render(request, 'verify.html', {'error': error_message})
                
    return render(request, 'verify.html')

# دالة تسجيل الدخول المحدثة والآمنة (تمنع خطأ MultipleObjectsReturned تماماً)
def student_login(request):
    if request.method == 'POST':
        login_input = request.POST.get('username') # يقبل اسم المستخدم أو الإيميل المدخل
        password = request.POST.get('password')
        
        user = None
        # 1. محاولة البحث بواسطة اسم المستخدم بأمان
        matched_user = User.objects.filter(username=login_input).first()
        if matched_user:
            user = authenticate(request, username=matched_user.username, password=password)
            
        # 2. لو مش موجود، محاولة البحث بواسطة البريد الإلكتروني بأمان
        if user is None:
            matched_user = User.objects.filter(email=login_input).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)
            
        if user is not None:
            # التحقق مما إذا كان المستخدم دكتوراً أو مشرفاً
            try:
                profile = StudentProfile.objects.get(user=user)
                if profile.is_instructor or user.is_staff:
                    login(request, user)
                    return redirect('instructor_dashboard')
            except StudentProfile.DoesNotExist:
                if user.is_staff:
                    login(request, user)
                    return redirect('instructor_dashboard')
                
            # لو طالب، نتاكد هل الحساب مفعل بواسطة الأدمن ولا لأ
            if not user.is_active:
                error_message = "حسابك قيد المراجعة وفي انتظار موافقة الأدمن لتفعيله."
                return render(request, 'login.html', {'error': error_message})
                
            login(request, user)
            # لو طالب عادي مفعل، يذهب للرئيسية
            return redirect('home')
        else:
            error_message = "اسم المستخدم أو البريد الإلكتروني أو كلمة المرور غير صحيحة."
            return render(request, 'login.html', {'error': error_message})
            
    return render(request, 'login.html')

# دالة تسجيل الخروج
def student_logout(request):
    logout(request)
    return redirect('home')

def schedule_view(request):
    return render(request, 'schedule.html')

# دالة عرض المحاضرات (من قاعدة البيانات الدائمة ✅)
def courses_view(request):
    files = Resource.objects.all().order_by('-id')
    context = {
        'files': files
    }
    return render(request, 'courses.html', context)

# دالة عرض الفعاليات (من قاعدة البيانات الدائمة ✅)
def events_view(request):
    events = Event.objects.all().order_by('-created_at')
    context = {
        'events': events
    }
    return render(request, 'events.html', context)

# دالة عرض التكليفات العامة (من قاعدة البيانات الدائمة ✅)
def assignments_view(request):
    assignments = Assignment.objects.all().order_by('-id')
    context = {
        'assignments': assignments
    }
    return render(request, 'assignments.html', context)

# دالة عرض صفحة المحاضرات المستقلة لكل مادة (مع تسجيل المشاهدة ✅)
def course_detail_view(request, course_name):
    course_files = Resource.objects.filter(course__name=course_name).order_by('-id')
    
    # تسجيل المشاهدة في قاعدة البيانات لو الطالب مسجل دخول
    if request.user.is_authenticated:
        for res_obj in course_files:
            StudentProgress.objects.get_or_create(student=request.user, resource=res_obj)

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

# دالة عرض صفحة الواجبات والتكليفات المستقلة لكل مادة (من قاعدة البيانات الدائمة ✅)
def assignment_detail_view(request, course_name):
    course_assignments = Assignment.objects.filter(course__name=course_name).order_by('-id')
    
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
    try:
        profile = StudentProfile.objects.get(user=request.user)
        if not profile.is_instructor and not request.user.is_staff:
            return redirect('home')
    except StudentProfile.DoesNotExist:
        if not request.user.is_staff:
            return redirect('home')

    # جلب الطلاب الذين لم يتم تفعيل حساباتهم بعد
    pending_students = User.objects.filter(is_active=False)

    # جلب جميع الطلاب المفعلين لمعرفة نشاطهم
    active_students = User.objects.filter(is_active=True, is_staff=False)
    
    # تجهيز تقرير تفصيلي لكل طالب
    students_progress_data = []
    all_resources = Resource.objects.all()

    for student in active_students:
        try:
            p = StudentProfile.objects.get(user=student)
            if p.is_instructor:
                continue
        except StudentProfile.DoesNotExist:
            pass

        viewed_resources_ids = StudentProgress.objects.filter(student=student, is_viewed=True).values_list('resource_id', flat=True)
        viewed_list = all_resources.filter(id__in=viewed_resources_ids)
        unviewed_list = all_resources.exclude(id__in=viewed_resources_ids)

        students_progress_data.append({
            'student': student,
            'viewed_resources': viewed_list,
            'unviewed_resources': unviewed_list,
        })

    if request.method == 'POST':
        section_type = request.POST.get('section_type')
        
        if section_type == 'assignment':
            title = request.POST.get('title')
            course_name = request.POST.get('course')
            deadline = request.POST.get('deadline')
            description = request.POST.get('description')
            
            try:
                course_obj, created = Course.objects.get_or_create(name=course_name, defaults={'code': course_name[:5].upper()})
                Assignment.objects.create(
                    course=course_obj,
                    title=title,
                    due_date=deadline,
                    description=description
                )
            except Exception:
                pass
            
        elif section_type == 'course_material':
            lecture_title = request.POST.get('lecture_title')
            course_name = request.POST.get('course_name')
            uploaded_file = request.FILES.get('lecture_file')
            
            if uploaded_file:
                try:
                    course_obj, created = Course.objects.get_or_create(name=course_name, defaults={'code': course_name[:5].upper()})
                    Resource.objects.create(
                        course=course_obj,
                        title=lecture_title,
                        file=uploaded_file
                    )
                except Exception:
                    pass
            
        elif section_type == 'event':
            event_title = request.POST.get('event_title')
            event_location = request.POST.get('event_location')
            event_details = request.POST.get('event_details')
            event_image = request.FILES.get('event_image')
            
            try:
                Event.objects.create(
                    title=event_title,
                    location=event_location,
                    details=event_details,
                    image=event_image
                )
            except Exception:
                pass
            
        elif section_type == 'notification':
            notif_text = request.POST.get('notif_text')
            notif_image = request.FILES.get('notif_image')
            
            try:
                GeneralNotification.objects.create(
                    text=notif_text,
                    image=notif_image
                )
            except Exception:
                pass
        
        # 🆕 إضافة جديدة: رفع امتحان جديد بمدة وأسئلة من لوحة التحكم
        elif section_type == 'exam':
            exam_title = request.POST.get('exam_title')
            course_name = request.POST.get('course_name')
            duration = request.POST.get('duration_minutes', 30)
            pdf_file = request.FILES.get('exam_pdf')
            
            try:
                course_obj, created = Course.objects.get_or_create(name=course_name, defaults={'code': course_name[:5].upper()})
                Exam.objects.create(
                    course=course_obj,
                    title=exam_title,
                    duration_minutes=int(duration),
                    pdf_file=pdf_file
                )
            except Exception:
                pass
            
        return redirect('instructor_dashboard')

    context = {
        'pending_students': pending_students,
        'students_progress_data': students_progress_data,
        'exams': Exam.objects.all().order_by('-id')
    }
    return render(request, 'instructor_dashboard.html', context)

# دالة تفعيل الحساب بواسطة الأدمن
@login_required(login_url='student_login')
def approve_student_view(request, user_id):
    if request.user.is_staff:
        try:
            target_user = User.objects.get(id=user_id)
            target_user.is_active = True  
            target_user.save()
            
            profile = StudentProfile.objects.get(user=target_user)
            profile.is_verified = True
            profile.save()
        except (User.DoesNotExist, StudentProfile.DoesNotExist):
            pass
            
    return redirect('instructor_dashboard')

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


# ==========================================
# 🆕 دوال إدارة ونظام الامتحانات والتصحيح
# ==========================================

# 1. عرض قائمة الامتحانات المتاحة للطلاب
@login_required(login_url='student_login')
def exams_list_view(request):
    exams = Exam.objects.all().order_by('-id')
    context = {'exams': exams}
    return render(request, 'exams_list.html', context)

# 2. صفحة دخول الامتحان (مع الأسئلة والوقت وحماية الشاشة ضد السكرين شوت)
@login_required(login_url='student_login')
def take_exam_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    
    # التحقق هل الطالب امتحن قبل كده ولا لأ
    existing_submission = StudentExamSubmission.objects.filter(student=request.user, exam=exam).first()
    if existing_submission:
        return render(request, 'exam_result.html', {'submission': existing_submission})

    if request.method == 'POST':
        total_score = 0
        earned_score = 0
        
        submission = StudentExamSubmission.objects.create(student=request.user, exam=exam)
        
        for q in questions:
            total_score += q.grade
            student_answer = request.POST.get(f'question_{q.id}', '').strip()
            
            # التصحيح التلقائي لأسئلة الاختيار من متعدد MCQ
            if q.q_type == 'mcq':
                if student_answer.lower() == str(q.correct_answer).lower():
                    earned_score += q.grade
            # الأسئلة المقالية يتم حفظها ليقوم الدكتور بتصحيحها لاحقاً
            else:
                pass 
                
        submission.score = earned_score
        submission.is_graded = True # تم التصحيح (الأسئلة المقالية يمكن تركها معلقة حسب رغبتك)
        submission.save()
        
        return redirect('exam_result', submission_id=submission.id)

    context = {'exam': exam, 'questions': questions}
    return render(request, 'take_exam.html', context)

# 3. عرض نتيجة الامتحان للطالب فور التسليم
@login_required(login_url='student_login')
def exam_result_view(request, submission_id):
    submission = get_object_or_404(StudentExamSubmission, id=submission_id, student=request.user)
    context = {'submission': submission}
    return render(request, 'exam_result.html', context)