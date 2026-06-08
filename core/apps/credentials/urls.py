from rest_framework.routers import DefaultRouter

from .views import SunatCredentialViewSet

router = DefaultRouter()
router.register("", SunatCredentialViewSet, basename="credentials")

urlpatterns = router.urls
