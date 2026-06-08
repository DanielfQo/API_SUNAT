from django.urls import path

from .views import SunatCheckTicketView, SunatSendDocumentView, SunatStatusView

urlpatterns = [
    path("send/", SunatSendDocumentView.as_view(), name="sunat-send"),
    path("ticket/<str:ticket_number>/", SunatCheckTicketView.as_view(), name="sunat-ticket"),
    path("status/", SunatStatusView.as_view(), name="sunat-status"),
]
