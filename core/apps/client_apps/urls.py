from rest_framework.routers import DefaultRouter

from .views import ClientAppViewSet

router = DefaultRouter()
router.register("", ClientAppViewSet, basename="client-apps")

urlpatterns = router.urls
