from rest_framework.routers import DefaultRouter

from .views import RequestLogViewSet

router = DefaultRouter()
router.register("", RequestLogViewSet, basename="request-logs")

urlpatterns = router.urls
