from django.contrib import admin
from .models import ClassGroup, Submission, Comment, ActivityLog

@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'class_group', 'submitted_at', 'file_type_display', 'grade', 'comments_count', 'teacher_name']
    list_filter = ['class_group', 'submitted_at', 'grade', 'teacher']
    search_fields = ['last_name', 'first_name']
    readonly_fields = ['submitted_at']
    list_per_page = 50
    
    fieldsets = (
        ('Інформація про учня', {
            'fields': ('first_name', 'last_name', 'class_group')
        }),
        ('Здана робота', {
            'fields': ('file', 'link', 'submitted_at')
        }),
        ('Оцінювання', {
            'fields': ('grade', 'teacher')
        }),
    )
    
    def comments_count(self, obj):
        return obj.comments.count()
    comments_count.short_description = 'Коментарів'
    
    def teacher_name(self, obj):
        if obj.teacher:
            if obj.teacher.first_name:
                return f"{obj.teacher.first_name} {obj.teacher.last_name}"
            return obj.teacher.username
        return "-"
    teacher_name.short_description = 'Вчитель'
    
    def file_type_display(self, obj):
        if obj.file:
            file_type = obj.get_file_type_display()
            extension = obj.get_file_extension()
            return f"{file_type} ({extension})" if file_type else extension
        elif obj.link:
            return "Посилання"
        return "-"
    file_type_display.short_description = 'Тип файлу'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['submission', 'author', 'text_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['text', 'submission__last_name', 'submission__first_name']
    readonly_fields = ['created_at']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'actor', 'action_type', 'description', 'submission']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['description', 'actor__username']
    readonly_fields = ['timestamp']
