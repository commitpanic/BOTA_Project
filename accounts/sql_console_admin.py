"""
Admin SQL Console
Safe SQL query interface for superusers only
"""
from django.contrib import admin
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import connection
from django.utils.html import format_html
from django.contrib import messages
import json
import re


class SQLConsoleAdmin(admin.ModelAdmin):
    """
    SQL Console for superusers only.
    Provides safe interface for running SELECT queries.
    """
    
    def has_module_permission(self, request):
        """Only superusers can see this in admin"""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


def sql_console_view(request):
    """
    SQL Console view for executing safe queries
    """
    # Security: Only superusers
    if not request.user.is_superuser:
        return HttpResponse("Access Denied: Superuser only", status=403)
    
    results = None
    error = None
    query = ""
    execution_time = None
    
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        
        if query:
            # Security: Block dangerous operations
            dangerous_patterns = [
                r'\bDROP\b',
                r'\bDELETE\b',
                r'\bUPDATE\b',
                r'\bINSERT\b',
                r'\bALTER\b',
                r'\bCREATE\b',
                r'\bTRUNCATE\b',
                r'\bREPLACE\b',
                r'\bGRANT\b',
                r'\bREVOKE\b',
                r'\bEXEC\b',
                r'\bEXECUTE\b',
            ]
            
            query_upper = query.upper()
            for pattern in dangerous_patterns:
                if re.search(pattern, query_upper):
                    error = f"Dangerous operation detected: {pattern}. Only SELECT queries are allowed."
                    break
            
            if not error:
                try:
                    import time
                    start_time = time.time()
                    
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                        
                        # Get column names
                        columns = [col[0] for col in cursor.description] if cursor.description else []
                        
                        # Get results
                        rows = cursor.fetchall()
                        
                        execution_time = round((time.time() - start_time) * 1000, 2)  # ms
                        
                        results = {
                            'columns': columns,
                            'rows': rows,
                            'row_count': len(rows),
                            'execution_time': execution_time
                        }
                        
                        messages.success(request, f"Query executed successfully. {len(rows)} rows returned in {execution_time}ms.")
                
                except Exception as e:
                    error = str(e)
                    messages.error(request, f"Query error: {error}")
    
    # Get list of tables
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
    
    context = {
        'title': 'SQL Console (Superuser Only)',
        'query': query,
        'results': results,
        'error': error,
        'tables': tables,
        'has_permission': True,
    }
    
    return render(request, 'admin/sql_console.html', context)


# Register a dummy model just to get it in the admin menu
from django.db import models

class SQLConsole(models.Model):
    """Dummy model for SQL Console admin menu item"""
    
    class Meta:
        managed = False  # Don't create table
        verbose_name = "SQL Console"
        verbose_name_plural = "SQL Console"
        app_label = 'accounts'  # Put it in accounts app


# Register in admin
@admin.register(SQLConsole)
class SQLConsoleModelAdmin(admin.ModelAdmin):
    """Admin interface for SQL Console"""
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Override to show our custom SQL console"""
        return sql_console_view(request)
