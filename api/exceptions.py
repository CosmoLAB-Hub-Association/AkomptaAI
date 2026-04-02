from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Handler personnalisé pour formater les erreurs selon la spec du frontend
    Format attendu:
    {
        "type": "validation_error",
        "errors": {
            "field_name": ["Error message"]
        }
    }
    """
    # Appeler le handler par défaut de DRF
    response = exception_handler(exc, context)
    
    if response is not None:
        # Formater les erreurs de validation
        if isinstance(exc, ValidationError):
            custom_response = {
                'type': 'validation_error',
                'errors': response.data
            }
            response.data = custom_response
        
        # Pour les autres erreurs, ajouter un type
        else:
            error_type = 'error'
            if response.status_code == 401:
                error_type = 'authentication_error'
            elif response.status_code == 403:
                error_type = 'permission_error'
            elif response.status_code == 404:
                error_type = 'not_found_error'
            elif response.status_code >= 500:
                error_type = 'server_error'
            
            custom_response = {
                'type': error_type,
                'message': response.data.get('detail', str(exc))
            }
            response.data = custom_response
    
    return response