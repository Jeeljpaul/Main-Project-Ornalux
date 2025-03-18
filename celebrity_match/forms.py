from django import forms

class CelebrityUploadForm(forms.Form):
    image = forms.ImageField(
        label='Upload Celebrity Image',
        help_text='Upload an image to find matching jewelry'
    )
