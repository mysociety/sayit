from django import forms

from .models import Instance

class InstanceForm(forms.ModelForm):
    class Meta:
        model = Instance
        exclude = ( 'label', 'users', 'created_by' )

