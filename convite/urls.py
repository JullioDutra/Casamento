from django.urls import path

from . import views

app_name = "convite"

urlpatterns = [
    path("", views.home, name="home"),
    path("rsvp/", views.rsvp_submit, name="rsvp_submit"),
    path("presentes/<int:pk>/pix/", views.presente_pix, name="presente_pix"),
    path("fotos-convidados/", views.foto_convidado_upload, name="foto_convidado_upload"),
]
