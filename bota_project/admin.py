"""
Admin site customization
Hide unused default Django admin models from sidebar
"""
from django.contrib import admin
from django.contrib.auth.models import Group

# Unregister unused models to clean up admin interface
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# Note: Site model removed - django.contrib.sites not in INSTALLED_APPS

# Customize admin site headers
admin.site.site_header = "BOTA Project Administration"
admin.site.site_title = "BOTA Admin"
admin.site.index_title = "Welcome to BOTA Administration"
