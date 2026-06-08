from rest_framework.routers import DefaultRouter

from .views import ElectronicDocumentViewSet

router = DefaultRouter()
router.register("", ElectronicDocumentViewSet, basename="documents")

urlpatterns = router.urls
