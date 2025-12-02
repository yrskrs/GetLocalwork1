from django import forms
from .models import Submission, ClassGroup

class SubmissionForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Прізвище Ім\'я',
        }),
        label='Прізвище та ім\'я'
    )
    
    class Meta:
        model = Submission
        fields = ['class_group', 'file', 'link']
        widgets = {
            'class_group': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'file-input'
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': "https://..."
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        link = cleaned_data.get('link')

        if not file and not link:
            raise forms.ValidationError("Будь ласка, прикріпіть файл або вставте посилання.")
        return cleaned_data
