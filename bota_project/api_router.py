"""
Main API router configuration.
Registers all viewsets and configures URL routing.
"""
from rest_framework.routers import DefaultRouter
from accounts.views import (
    UserViewSet, UserStatisticsViewSet, UserRoleViewSet, UserRoleAssignmentViewSet
)
from bunkers.views import (
    BunkerCategoryViewSet, BunkerViewSet, BunkerPhotoViewSet,
    BunkerResourceViewSet, BunkerInspectionViewSet
)
from cluster.views import (
    ClusterViewSet, ClusterMemberViewSet, ClusterAlertViewSet, SpotViewSet
)
from activations.views import (
    ActivationKeyViewSet, ActivationLogViewSet, LicenseViewSet
)
from diplomas.views import (
    DiplomaTypeViewSet, DiplomaViewSet, DiplomaProgressViewSet, DiplomaVerificationViewSet
)

# Create router
router = DefaultRouter()

# Register accounts viewsets
router.register(r'users', UserViewSet, basename='user')
router.register(r'statistics', UserStatisticsViewSet, basename='userstatistics')
router.register(r'roles', UserRoleViewSet, basename='userrole')
router.register(r'role-assignments', UserRoleAssignmentViewSet, basename='userroleassignment')

# Register bunkers viewsets
router.register(r'bunker-categories', BunkerCategoryViewSet, basename='bunkercategory')
router.register(r'bunkers', BunkerViewSet, basename='bunker')
router.register(r'bunker-photos', BunkerPhotoViewSet, basename='bunkerphoto')
router.register(r'bunker-resources', BunkerResourceViewSet, basename='bunkerresource')
router.register(r'bunker-inspections', BunkerInspectionViewSet, basename='bunkerinspection')

# Register cluster viewsets
router.register(r'clusters', ClusterViewSet, basename='cluster')
router.register(r'cluster-members', ClusterMemberViewSet, basename='clustermember')
router.register(r'cluster-alerts', ClusterAlertViewSet, basename='clusteralert')
router.register(r'spots', SpotViewSet, basename='spot')

# Register activations viewsets
router.register(r'activation-keys', ActivationKeyViewSet, basename='activationkey')
router.register(r'activation-logs', ActivationLogViewSet, basename='activationlog')
router.register(r'licenses', LicenseViewSet, basename='license')

# Register diplomas viewsets
router.register(r'diploma-types', DiplomaTypeViewSet, basename='diplomatype')
router.register(r'diplomas', DiplomaViewSet, basename='diploma')
router.register(r'diploma-progress', DiplomaProgressViewSet, basename='diplomaprogress')
router.register(r'diploma-verifications', DiplomaVerificationViewSet, basename='diplomaverification')

urlpatterns = router.urls
