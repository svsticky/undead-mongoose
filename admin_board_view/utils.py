from django.core.paginator import Paginator

def create_paginator(data, page, p_len=5):
    """
    Create paginator for data.
    
    Args:
        data: Data to paginate
        page: Page number
        p_len: Length of the page, defaults to 5
    """
    page = None
    paginator = Paginator(data, p_len)
    try:
        page = paginator.get_page(page)
    except Exception:
        page = paginator.page(1)

    return page
