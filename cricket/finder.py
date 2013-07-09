import copy

def fetch_all_items(treeview):
    '''
    This is a hand-rolled find method which is capable of searching a
    Tkinter.Treeview object, given the kinds of entries normally present
    in the cricket application.
    '''

    all_children = []
    children = list(treeview.get_children())

    while(children):
        next_child = children.pop()

        next_children = treeview.get_children(next_child)
        if next_children:
            children.extend(next_children)
        else:
            all_children.append(next_child)

    return all_children


def search_tree_for_matching(search_str, treeview):
    '''
    Given a thing to search in, and a string to search for, get
    matching entries
    '''

    names = fetch_all_items(treeview)
    matching = [name for name in names
                if search_str in name]

    return matching

class Finder:
    '''
    A Finder requires some state. In order to support operations like 
    "find next", it maintains the following concepts:

        -- An "active list", the results of the last find operation
        -- An active pointer, used to find the next result
    '''

    def __init__(self, needle, haystack):

        self.needle = needle
        self.haystack = haystack
        self.search_fn = search_tree_for_matching
        self.activelist = []
        self.activepointer = 0

        self._update()

    def _update(self):
        '''
        Actually run the search. The finder maintains a results cache
        rather than re-searching when doing find-next operations since
        "find next" is context-sensitive. An update will reset the
        active pointer. Conceivably, it would be desirable for the active
        pointer to point to the same actual item, regardless of its index,
        if it were contained in the updated list. There is no guarantee of that
        so simple behaviour is probably the easiest for a user to understand
        at this point in time.
        '''

        self.activelist = self.search_fn(self.needle, self.haystack)
        self.activepointer = 0

    def find_current(self):
        '''
        Getting the last-found-item is useful
        '''

        return self.activelist[self.activepointer]


    def find_next(self):
        '''
        Simple wraparound find-next search
        '''

        self.activepointer += 1
        self.activepointer %= len(self.activelist)
        return self.activelist[self.activepointer]

    def find_all(self):
        '''
        We definitely want a copy here. We have no idea of the use case
        really, and don't want anyone else updating our active set for us
        '''

        return copy.copy(self.activelist)

