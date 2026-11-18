from django.db import models
from django.contrib.auth.models import User

# ملف تعريف الطالب المرتبط بنظام الموافقة (محدث لتمييز الدكتور عن الطالب)
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    department = models.CharField(max_length=100, default="IT")
    verification_code = models.CharField(max_length=6, blank=True, null=True)  # كود التحقق
    is_verified = models.BooleanField(default=False)                            # حالة تفعيل الإيميل
    is_instructor = models.BooleanField(default=False)                        # حقل تحديد هل هو دكتور أم طالب

    def __str__(self):
        return f"{self.user.username} ({'دكتور' if self.is_instructor else 'طالب'})"

# جدول المواد الدراسية
class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# جدول المحاضرات والمواعيد
class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day = models.CharField(max_length=50)
    time = models.CharField(max_length=50)
    room = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.course.name} - {self.day}"

# جدول المصادر والملفات أو فيديوهات اليوتيوب
class Resource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

# جدول التكليفات والواجبات
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField()
    description = models.TextField()

    def __str__(self):
        return self.title

# جدول الأسئلة للمنتدى الأكاديمي (محدث لدعم رفع الصور)
class Question(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان السؤال")
    content = models.TextField(verbose_name="تفاصيل السؤال")
    image = models.ImageField(upload_to='forum_images/', blank=True, null=True, verbose_name="صورة مرفقة")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="صاحب السؤال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت النشر")

    def __str__(self):
        return self.title

# جدول الردود على الأسئلة في المنتدى
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name="السؤال المرتبط")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="الكاتب (طالب/دكتور)")
    content = models.TextField(verbose_name="نص الرد")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الرد")

    def __str__(self):
        return f"رد بواسطة {self.author.username} على {self.question.title}"

# جدول إشعارات المنتدى الجديد 🔔
class ForumNotification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_notifications', verbose_name="المستقبل")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المرسل")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="السؤال المرتبط")
    message = models.CharField(max_length=255, verbose_name="نص الإشعار")
    is_read = models.BooleanField(default=False, verbose_name="هل تم القراءة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإشعار")

    def __str__(self):
        return f"إشعار إلى {self.recipient.username}"


# ==========================================
# الجداول الجديدة لتتبع نشاط وتقدم الطلاب 📊
# ==========================================

# جدول تتبع المحاضرات والمصادر التي شاهدها الطالب
class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="الطالب")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name="المحاضرة / المصدر")
    is_viewed = models.BooleanField(default=True, verbose_name="تمت المشاهدة")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت المشاهدة")

    def __str__(self):
        return f"{self.student.username} شاف -> {self.resource.title}"

# جدول تتبع تسليم التكليفات والواجبات للطلاب
class StudentAssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="التكليف")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="الطالب")
    submitted_file = models.FileField(upload_to='submissions/', verbose_name="ملف الحل")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت التسليم")
    is_graded = models.BooleanField(default=False, verbose_name="تم التقييم")

    def __str__(self):
        return f"حل {self.student.username} لتكليف {self.assignment.title}"


# ==========================================
# جداول الفعاليات والإشعارات العامة الدائمة 📢
# ==========================================

# جدول الأنشطة والفعاليات الدائم
class Event(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان الفعالية")
    location = models.CharField(max_length=200, verbose_name="المكان")
    details = models.TextField(verbose_name="التفاصيل")
    image = models.ImageField(upload_to='events/', blank=True, null=True, verbose_name="صورة الفعالية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإضافة")

    def __str__(self):
        return self.title

# جدول التنبيهات والإشعارات العامة الدائم
class GeneralNotification(models.Model):
    text = models.TextField(verbose_name="نص الإشعار")
    image = models.ImageField(upload_to='notifications/', blank=True, null=True, verbose_name="صورة مرفقة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت النشر")

    def __str__(self):
        return self.text[:50]


# ==========================================
# 🆕 جداول نظام الامتحانات والاختبارات 📝
# ==========================================

# جدول الامتحان الرئيسي
class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="المادة الدراسية")
    title = models.CharField(max_length=200, verbose_name="عنوان الامتحان")
    duration_minutes = models.IntegerField(default=30, verbose_name="مدة الامتحان (بالدقائق)")
    pdf_file = models.FileField(upload_to='exams_pdf/', blank=True, null=True, verbose_name="ملف الامتحان PDF")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإضافة")

    def __str__(self):
        return self.title

# جدول أسئلة الامتحان (تدعم اختر ومقالي)
class ExamQuestion(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'اختيار من متعدد (MCQ)'),
        ('essay', 'سؤال مقالي'),
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', verbose_name="الامتحان")
    text = models.TextField(verbose_name="نص السؤال")
    q_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq', verbose_name="نوع السؤال")
    
    option_a = models.CharField(max_length=255, blank=True, null=True, verbose_name="الخيار أ")
    option_b = models.CharField(max_length=255, blank=True, null=True, verbose_name="الخيار ب")
    option_c = models.CharField(max_length=255, blank=True, null=True, verbose_name="الخيار ج")
    option_d = models.CharField(max_length=255, blank=True, null=True, verbose_name="الخيار د")
    
    correct_answer = models.CharField(max_length=255, blank=True, null=True, verbose_name="الإجابة الصحيحة (للاختر)")
    grade = models.IntegerField(default=5, verbose_name="درجة السؤال")

    def __str__(self):
        return f"{self.text[:50]} ({self.exam.title})"

# جدول إجابات ونتيجة الطالب في الامتحان
class StudentExamSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="الطالب")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="الامتحان")
    score = models.FloatField(default=0, verbose_name="الدرجة الكلية الحاصل عليها")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت التسليم")
    is_graded = models.BooleanField(default=False, verbose_name="تم التقييم")

    def __str__(self):
        return f"نتيجة {self.student.username} في {self.exam.title}"