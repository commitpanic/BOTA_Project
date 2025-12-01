"""
Admin site customization
Hide unused default Django admin models from sidebar
"""
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

# Unregister unused models to clean up admin interface
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Site)
except admin.sites.NotRegistered:
    pass

# Customize admin site headers
admin.site.site_header = "BOTA Project Administration"
admin.site.site_title = "BOTA Admin"
admin.site.index_title = "Welcome to BOTA Administration"
