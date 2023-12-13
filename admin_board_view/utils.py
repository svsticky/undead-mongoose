from django.core.paginator import Paginator
from django.db.models.query import QuerySet

def create_paginator(data, page_n, p_len=5):
    """
    Create paginator for data.
    
    Args:
        data: Data to paginate
        page: Page number
        p_len: Length of the page, defaults to 5
    """
    if isinstance(data, QuerySet):
        # Order data, most recent date first
        data = data.order_by('date', 'id').reverse()

    page = None
    paginator = Paginator(data, p_len)
    try:
        page = paginator.get_page(page_n)
    except Exception as e:
        page = paginator.page(1)

    return page
