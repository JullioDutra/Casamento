from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "painel"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="painel/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="painel:login"), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_planilha, name="upload_planilha"),
    path("modelo-planilha/", views.baixar_modelo_planilha, name="modelo_planilha"),
    path("convidado/adicionar/", views.adicionar_convidado, name="adicionar_convidado"),
    path("convidado/<int:pk>/alternar/", views.alternar_confirmado, name="alternar_confirmado"),
    path("convidado/<int:pk>/excluir/", views.excluir_convidado, name="excluir_convidado"),
    path("adicionar-presente/", views.adicionar_presente, name="adicionar_presente"),
]
