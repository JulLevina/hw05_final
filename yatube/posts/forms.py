import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        text = self.cleaned_data['text']
        if re.search(r'[~#$%^&]', text):
            raise ValidationError(
                'Текст не должен содержать специальных символов.')
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
