from django.contrib import admin
from .models import StudentProfile, Course, Schedule, Resource, Assignment

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'is_approved')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'department')

admin.site.register(Course)
admin.site.register(Schedule)
admin.site.register(Resource)
admin.site.register(Assignment)