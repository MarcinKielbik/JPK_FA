"""
URL configuration for jpk_fa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from jpk_fa_app.views import process_file
# , download_processed_file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('process-file/', process_file, name='process_file'),
    # path('download-processed-file/', download_processed_file, name='download_processed_file')
]
