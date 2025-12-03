from django.db import models
import os
from datetime import datetime

class ClassGroup(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Клас")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Клас"
        verbose_name_plural = "Класи"
        ordering = ['name']

def submission_upload_path(instance, filename):
    # Format: YYYY-MM-DD/Class/Name/File
    today = datetime.now().strftime('%Y-%m-%d')
    class_name = instance.class_group.name
    student_name = f"{instance.last_name}_{instance.first_name}"
    return os.path.join(today, class_name, student_name, filename)

class Submission(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE)
    file = models.FileField(upload_to=submission_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    comment = models.TextField(blank=True, null=True, verbose_name="Коментар вчителя")
    teacher = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Вчитель")
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.class_group.name} ({self.submitted_at.strftime('%Y-%m-%d')})"
    
    def get_file_extension(self):
        """Повертає розширення файлу"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None
    
    def get_file_type_display(self):
        """Повертає людино-читабельне ім'я типу файлу"""
        from .utils import get_file_type_info
        ext = self.get_file_extension()
        if ext:
            return get_file_type_info(ext)['name']
        return None
    
    def get_file_icon(self):
        """Повертає іконку для типу файлу"""
        from .utils import get_file_type_info
        ext = self.get_file_extension()
        if ext:
            return get_file_type_info(ext)['icon']
        return '📎'
    
    def get_file_info(self):
        """Повертає повну інформацію про файл"""
        from .utils import get_file_type_info
        ext = self.get_file_extension()
        if ext:
            info = get_file_type_info(ext)
            info['extension'] = ext
            return info
        return None
    
    class Meta:
        verbose_name = "Здана робота"
        verbose_name_plural = "Здані роботи"
        ordering = ['-submitted_at']

class Comment(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='comments', verbose_name="Робота")
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    text = models.TextField(verbose_name="Текст коментаря")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    
    def __str__(self):
        return f"Коментар від {self.author} до {self.submission}"
    
    class Meta:
        verbose_name = "Коментар"
        verbose_name_plural = "Коментарі"
        ordering = ['created_at']

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('submission', 'Здача роботи'),
        ('grading', 'Оцінювання'),
        ('comment', 'Коментар'),
        ('login', 'Вхід в систему'),
    ]
    
    actor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Користувач")
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Тип дії")
    description = models.TextField(verbose_name="Опис")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Час")
    submission = models.ForeignKey(Submission, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs', verbose_name="Робота")
    
    def __str__(self):
        return f"{self.timestamp} - {self.actor} - {self.action_type}"
    
    class Meta:
        verbose_name = "Журнал дій"
        verbose_name_plural = "Журнал дій"
        ordering = ['-timestamp']

def log_activity(actor, action_type, description, submission=None):
    """Створює запис в журналі дій"""
    ActivityLog.objects.create(
        actor=actor if actor and actor.is_authenticated else None,
        action_type=action_type,
        description=description,
        submission=submission
    )
