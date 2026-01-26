"""
Custom schema generator for public API endpoints only.
"""
from drf_spectacular.generators import SchemaGenerator


class PublicSchemaGenerator(SchemaGenerator):
    """
    Schema generator that only includes public API endpoints.
    Filters out admin and non-public endpoints.
    """
    
    def get_endpoints(self, request=None):
        """
        Override to filter only public API endpoints.
        """
        endpoints = super().get_endpoints(request)
        
        # Filter to only include /api/public/ endpoints
        public_endpoints = []
        for endpoint in endpoints:
            path, path_regex, method, callback = endpoint
            if path.startswith('/api/public/'):
                public_endpoints.append(endpoint)
        
        return public_endpoints
