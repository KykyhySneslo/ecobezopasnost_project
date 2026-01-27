from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    """Форма для отправки сообщения"""
    class Meta:
        model = Message
        fields = ['text', 'file']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите сообщение...',
                'id': 'message-input'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'file-input',
                'accept': 'image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Ограничение размера файла (10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError(f"Размер файла не должен превышать 10MB")
            
            # Проверка типа файла
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 
                'video/mp4', 'video/avi', 'video/mov',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            
            if file.content_type not in allowed_types:
                raise forms.ValidationError("Недопустимый тип файла")
        
        return file