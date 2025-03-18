from django import forms

class DressUploadForm(forms.Form):
    dress_image = forms.ImageField(label='Upload your dress image')
