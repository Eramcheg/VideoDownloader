"""
URL configuration for VideoDownloader project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from downloaderApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name="homepage"),
    path('audio-download/', views.audio_homepage, name="audio_homepage"),
    path('video-download/', views.video_homepage, name="video_homepage"),
    path('download-video/', views.download_video, name="download_video"),
    path('download-video-with-format/', views.download_video_with_format, name="download_video_with_format"),
    path('get-video-formats/', views.show_formats, name="get_video_formats"),
]
