from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .forms import DressUploadForm
from .utils import recommend_jewelry
import os
from django.conf import settings

def recommend_view(request):
    recommendations = None

    if request.method == 'POST':
        form = DressUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dress_image = form.cleaned_data['dress_image']

            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save dress image temporarily
            dress_image_path = os.path.join(upload_dir, dress_image.name)
            with open(dress_image_path, 'wb+') as destination:
                for chunk in dress_image.chunks():
                    destination.write(chunk)

            # Get jewelry recommendations
            recommendations = recommend_jewelry(dress_image_path)

    else:
        form = DressUploadForm()

    return render(request, 'recommendation/recommend.html', {
        'form': form,
        'recommendations': recommendations
    })
