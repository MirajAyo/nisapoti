from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main.views import views_auth  # Import your views here

urlpatterns = [
    path('', views_auth.index, name='index'),
    # path('', views_auth.root, name='root'),  
    path('post/', include('main.urls.post')),
    path('profile/', include('main.urls.profile')),
    path('search/', include('main.urls.search')),
    path('transaction/', include('main.urls.transaction')),
    path('auth/', include('main.urls.auth')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
