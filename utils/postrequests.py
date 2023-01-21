'''
This file contains functions that create the requests for the Google API
It contains the default formats for requests in the right format for the Google API.
'''

def create_styling_request(start_index, end_index, color):
    '''
    Returns a dictionary in the right format for styling a part of a text.
    Using color from the COLORS dictionary in utils/constants.py
    '''
    request  = {
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                },
                'textStyle': {
                    'foregroundColor': {
                        'color': {
                            'rgbColor': color
                        }
                    }
                },

                'fields': 'foregroundColor'
            }
        }
    return request

def create_deletion_request(p_range):
    """
    Deletes a part of a text with start and end index, given by p_range.
    Returns a dictionary in the right format for deleting a part of a text.
    """

    request = {
        'deleteContentRange': {
            'range': {
                'startIndex': p_range.get('startIndex'),
                'endIndex': p_range.get('endIndex'),
            }
        }
    }
    return request

def create_insert_request(index, text):
    """
    Inserts text at an index. Work from the end of the document to the beginning to avoid index errors.
    Returns a dictionary in the right format for inserting text at an index.
    """

    request = {
        'insertText': {
            'location': {
                'index': index,
            },
            'text': text
        }
    }
    return request
