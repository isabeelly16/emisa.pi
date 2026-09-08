from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from app import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),

    path('cadastro/', views.cadastro_view, name='cadastro'),

    path('explorar/', views.explorar, name='explorar'),

    path(
        'pet/<int:pet_id>/',
        views.perfil_pet,
        name='perfil_pet'
    ),

    path(
        'pet/<int:pet_id>/adotar/',
        views.solicitar_adocao,
        name='solicitar_adocao'
    ),

    path('sair/', views.logout_view, name='logout'),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)