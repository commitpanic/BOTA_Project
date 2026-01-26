"""
Simple API documentation view.
"""
from django.shortcuts import render


def api_documentation(request):
    """
    Render simple API documentation page.
    """
    return render(request, 'api_docs.html')
